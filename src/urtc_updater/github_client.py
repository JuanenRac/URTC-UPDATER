# =============================================================================
# URTC-UPDATER - GitHub version lookup: github_client.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
#
# Fetches each project's universal manifest directly from GitHub raw content.
#
# IMPORTANT:
#
# This does NOT use GitHub Releases or tags.
#
# The ecosystem's versioning convention stores the public project version in
# urtc.project.json. Builds must keep their native package/firmware
# version synchronized with that manifest; local validation catches drift.
#
# Architecture:
#
#   registry.py
#        |
#        v
#   github_raw_url()
#        |
#        v
#   GitHub raw content
#        |
#        v
#   parse_manifest()
#
# stdlib-only:
#
#   urllib
#   concurrent.futures
#   dataclasses
#
# No requests dependency is required.
# =============================================================================

from __future__ import annotations

import json
import os
import socket
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)
from dataclasses import dataclass, replace
from pathlib import Path

from .project_manifest import (
    MANIFEST_FILE,
    ManifestValidationError,
    ProjectManifest,
    parse_manifest,
)
from .registry import (
    ProjectEntry,
    entry_from_manifest,
    github_native_version_url,
    github_raw_url,
)
from .version_parse import Version, parse_version


# ---------------------------------------------------------------------------
# Network configuration
# ---------------------------------------------------------------------------

REQUEST_TIMEOUT_S = 10

#: The repository listing and its ETags, kept between runs: GitHub answers an
#: unchanged listing with 304, which does not count against the hourly quota.
REPO_LIST_CACHE_PATH = Path.home() / ".urtc_updater_repo_cache.json"

# GitHub is being queried for small text files only.
#
# Keeping this moderate avoids turning a simple version checker into a
# high-concurrency crawler.
MAX_CONCURRENT_REQUESTS = 8

USER_AGENT = "URTC-UPDATER"

# Real hosts by default; module-level so tests can point them at a local
# HTTP server instead of mocking urllib itself - real request/response
# round-trips against real fixture servers, same spirit as this
# ecosystem's Go projects using net/http/httptest.
GITHUB_API_BASE = "https://api.github.com"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com"

# Real, bounded retry for genuinely transient network failures - a
# connection that never got a response (DNS, refused, reset, timeout), or
# a real GitHub secondary rate limit (403/429 carrying a Retry-After
# header, see _retry_after_seconds() below). Every OTHER definitive HTTP
# response, even an error one (404/500, or the hourly PRIMARY rate limit -
# see describe_http_error()), is never retried here: GitHub already
# answered, retrying would not change that answer within this process's
# own lifetime, only spend more of the rate limit.
RETRY_MAX_ATTEMPTS = 3
RETRY_BACKOFF_BASE_S = 0.5
#: A longer Retry-After than this is not waited out (it would freeze the
#: window or the command line for minutes without a word): the request
#: fails with GitHub's own answer instead.
RETRY_AFTER_MAX_S = 60.0


def _retry_after_seconds(exc: urllib.error.HTTPError) -> float | None:
    """GitHub's real secondary-rate-limit signal: a 403/429 response
    carrying a `Retry-After` header telling the caller exactly how many
    seconds to wait - short (seconds, not minutes) and genuinely worth
    retrying within this same process, unlike the hourly PRIMARY rate
    limit (`X-RateLimit-Reset`, handled separately by
    `describe_http_error()` below) which can be tens of minutes away and
    isn't worth blocking a foreground CLI run for."""
    if exc.code not in (403, 429) or exc.headers is None:
        return None
    raw = exc.headers.get("Retry-After")
    if raw is None:
        return None
    try:
        seconds = float(raw)
    except ValueError:
        return None
    return seconds if 0 <= seconds <= RETRY_AFTER_MAX_S else None


def is_primary_rate_limited(exc: urllib.error.HTTPError) -> bool:
    """True when `exc` is GitHub's real PRIMARY (hourly) rate limit - a
    403/429 with `X-RateLimit-Remaining: 0` - as opposed to a real 404,
    a genuine permission error, or the SECONDARY rate limit
    `_urlopen_with_retries` already retries via `Retry-After`. Extracted
    from `describe_http_error()`'s own detection so a caller that needs
    to make a real decision (stop burning the rest of a batch against an
    already-exhausted budget, not just describe one failure) does not
    have to duplicate this condition or string-match a message."""
    return exc.code in (403, 429) and exc.headers is not None and exc.headers.get("X-RateLimit-Remaining") == "0"


def describe_http_error(exc: urllib.error.HTTPError) -> str:
    """A real, actionable message for an HTTPError - found while
    reading the code: every HTTPError used to
    become the same opaque `f"HTTP {code}"`, including GitHub's own
    PRIMARY rate limit (a 403/429 with `X-RateLimit-Remaining: 0`), which
    is genuinely transient and tells the caller exactly when it resets
    (`X-RateLimit-Reset`) - a real, common failure mode when running
    status/discovery across every URTC repository without a `GITHUB_TOKEN`
    (unauthenticated GitHub API calls are capped at 60/hour)."""
    headers = exc.headers
    if is_primary_rate_limited(exc):
        reset_raw = headers.get("X-RateLimit-Reset")
        if reset_raw is not None:
            try:
                reset_at = datetime.fromtimestamp(int(reset_raw), tz=timezone.utc)
            except (TypeError, ValueError, OSError):
                pass
            else:
                return (
                    f"rate limited by GitHub - resets at {reset_at.isoformat()} "
                    "(unauthenticated requests are capped at 60/hour; set GITHUB_TOKEN to raise the limit)"
                )
    return f"HTTP {exc.code}"


def _urlopen_with_retries(
    request: urllib.request.Request,
    *,
    timeout: float,
    max_attempts: int | None = None,
    backoff_base_s: float | None = None,
    opener=urllib.request.urlopen,
    sleep=time.sleep,
    with_headers: bool = False,
):
    """Open `request`, retrying up to `max_attempts` times on a transient
    network failure (URLError/TimeoutError/socket.timeout/OSError, or a
    real GitHub secondary rate limit - see `_retry_after_seconds()`).
    Never retries any other HTTPError, a real response GitHub already
    gave us. Waits `backoff_base_s * 2**attempt` between network-failure
    retries, or the server's own `Retry-After` value for a secondary rate
    limit. `opener`/`sleep` are injectable so tests can exercise the real
    retry/backoff logic without real network flakiness or real
    wall-clock delay. `max_attempts`/`backoff_base_s` default to the
    module-level constants, read here (not as literal defaults) so tests
    can also monkeypatch those constants directly for callers - like
    every real caller in this module - that never override them
    explicitly."""
    if max_attempts is None:
        max_attempts = RETRY_MAX_ATTEMPTS
    if backoff_base_s is None:
        backoff_base_s = RETRY_BACKOFF_BASE_S
    attempt = 0
    while True:
        attempt += 1
        try:
            with opener(request, timeout=timeout) as response:
                if with_headers:
                    return response.read(), getattr(response, "headers", None)
                return response.read()
        except urllib.error.HTTPError as exc:
            retry_after = _retry_after_seconds(exc)
            if retry_after is None or attempt >= max_attempts:
                raise
            sleep(retry_after)
        except (urllib.error.URLError, TimeoutError, socket.timeout, OSError):
            if attempt >= max_attempts:
                raise
            sleep(backoff_base_s * (2 ** (attempt - 1)))


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------

@dataclass
class RemoteStatus:
    """
    Result of looking up one project's remote version.

    version:
        Parsed semantic version, or None when the lookup failed.

    error:
        Human-readable reason for failure, or None when successful.

    http_status:
        HTTP status code when GitHub returned an HTTP error.

    url:
        Raw manifest URL that was queried. This is useful for verbose diagnostics.

    """

    entry: ProjectEntry

    version: Version | None

    error: str | None = None

    http_status: int | None = None

    url: str | None = None

    manifest: ProjectManifest | None = None


@dataclass(frozen=True)
class RemoteDiscovery:
    """Projects positively identified by their own GitHub manifest."""

    projects: tuple[RemoteStatus, ...]
    errors: tuple[str, ...]


def _fetch_discovered_manifest(owner: str, name: str, branch: str) -> RemoteStatus | None:
    """Return a project only when its own manifest opts into URTC."""
    url = f"{GITHUB_RAW_BASE}/{owner}/{name}/{branch}/{MANIFEST_FILE}"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        method="GET",
    )
    try:
        text = _urlopen_with_retries(request, timeout=REQUEST_TIMEOUT_S).decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise RuntimeError(f"{name}: manifest {describe_http_error(exc)}") from exc
    except (urllib.error.URLError, TimeoutError, socket.timeout, OSError) as exc:
        raise RuntimeError(f"{name}: manifest lookup failed: {exc}") from exc

    try:
        manifest = parse_manifest(text, expected_name=name)
    except ManifestValidationError as exc:
        # A repository that exposes this exact manifest path is relevant to
        # the maintainer even when it is malformed; surface it in workflow
        # logs rather than silently treating it as a non-ecosystem project.
        raise RuntimeError(f"{name}: invalid manifest: {exc}") from exc

    return RemoteStatus(
        entry=replace(entry_from_manifest(manifest), default_branch=branch),
        version=Version.from_string(manifest.version),
        url=url,
        manifest=manifest,
    )


def _load_repo_cache() -> dict:
    try:
        data = json.loads(REPO_LIST_CACHE_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _save_repo_cache(cache: dict) -> None:
    temporary = REPO_LIST_CACHE_PATH.with_name(REPO_LIST_CACHE_PATH.name + ".tmp")
    try:
        temporary.write_text(json.dumps(cache), encoding="utf-8")
        os.replace(temporary, REPO_LIST_CACHE_PATH)
    except OSError:
        try:
            temporary.unlink()
        except OSError:
            pass


def _fetch_listing_page(url: str, headers: dict[str, str], cache: dict, authenticated: bool) -> list:
    """One page of the repository listing, asking GitHub whether it changed
    since the copy kept in `cache` (If-None-Match); a 304 answer returns the
    kept copy without spending any of the hourly request quota."""
    key = f"{url}|{'token' if authenticated else 'anonymous'}"
    kept = cache.get(key) if isinstance(cache.get(key), dict) else None
    request_headers = dict(headers)
    if kept and isinstance(kept.get("etag"), str) and isinstance(kept.get("payload"), list):
        request_headers["If-None-Match"] = kept["etag"]
    request = urllib.request.Request(url, headers=request_headers, method="GET")
    try:
        body, response_headers = _urlopen_with_retries(request, timeout=REQUEST_TIMEOUT_S, with_headers=True)
    except urllib.error.HTTPError as exc:
        if exc.code == 304 and kept and isinstance(kept.get("payload"), list):
            return kept["payload"]
        raise
    payload = json.loads(body.decode("utf-8", errors="replace"))
    etag = response_headers.get("ETag") if response_headers is not None else None
    if isinstance(payload, list) and etag:
        cache[key] = {"etag": etag, "payload": payload}
    return payload


def discover_remote_projects(
    owner: str = "JuanenRac",
    *,
    token: str | None = None,
) -> RemoteDiscovery:
    """Discover every public ecosystem repository from GitHub, no fixed list.

    GitHub's repository listing is only a candidate list. A repository joins
    the ecosystem only after its own root manifest validates and declares
    ``ecosystem: URTC``. A newly pushed repository therefore appears on
    the next dashboard or updater scan without an index.html edit.
    """
    resolved_token = token if token is not None else os.environ.get("GITHUB_TOKEN", "")
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if resolved_token:
        headers["Authorization"] = f"Bearer {resolved_token}"

    candidates: list[tuple[str, str]] = []
    cache = _load_repo_cache()
    page = 1
    while True:
        url = f"{GITHUB_API_BASE}/users/{owner}/repos?type=owner&per_page=100&page={page}"
        try:
            payload = _fetch_listing_page(url, headers, cache, bool(resolved_token))
        except urllib.error.HTTPError as exc:
            # Found while diagnosing a real report of repeated GitHub
            # refreshes silently listing fewer and fewer projects (42 ->
            # 9 -> 0): the raw `str(exc)` this used to embed here (a bare
            # "HTTP Error 403: rate limit exceeded") never told the
            # caller it was the hourly PRIMARY rate limit, when it
            # resets, or that GITHUB_TOKEN raises the limit - all of
            # which describe_http_error() already knows how to say.
            raise RuntimeError(f"unable to list GitHub repositories for {owner}: {describe_http_error(exc)}") from exc
        except (urllib.error.URLError, TimeoutError, socket.timeout, OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"unable to list GitHub repositories for {owner}: {exc}") from exc
        if not isinstance(payload, list):
            raise RuntimeError(f"unexpected GitHub repository-list response for {owner}")
        for item in payload:
            if isinstance(item, dict) and isinstance(item.get("name"), str):
                # A fork or an archived repository never joins the ecosystem; asking for its manifest would only add a request that answers 404.
                if item.get("fork") is True or item.get("archived") is True:
                    continue
                branch = item.get("default_branch")
                candidates.append((item["name"], branch if isinstance(branch, str) and branch else "main"))
        if len(payload) < 100:
            break
        page += 1

    _save_repo_cache(cache)
    discovered: list[RemoteStatus] = []
    errors: list[str] = []
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_REQUESTS, thread_name_prefix="hydra-discovery") as pool:
        futures = {pool.submit(_fetch_discovered_manifest, owner, name, branch): name for name, branch in candidates}
        for future in as_completed(futures):
            try:
                status = future.result()
            except RuntimeError as exc:
                errors.append(str(exc))
                continue
            if status is not None:
                discovered.append(status)

    discovered.sort(key=lambda status: status.entry.name.casefold())
    return RemoteDiscovery(projects=tuple(discovered), errors=tuple(sorted(errors)))


# ---------------------------------------------------------------------------
# One project
# ---------------------------------------------------------------------------

def _fetch_one(
    entry: ProjectEntry,
) -> RemoteStatus:
    """
    Fetch and parse the version for one project.

    This function intentionally never raises ordinary network/HTTP errors
    to the caller. A single broken repository must not abort the complete
    ecosystem scan.
    """

    url = github_raw_url(entry)

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/plain,*/*",
        },
        method="GET",
    )

    try:
        raw = _urlopen_with_retries(request, timeout=REQUEST_TIMEOUT_S)
        text = raw.decode("utf-8", errors="replace")

    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            # Compatibility path for a caller that already supplied a valid
            # local manifest but whose remote manifest has not yet been
            # published. No central project metadata is used here.
            native_url = github_native_version_url(entry)
            native_request = urllib.request.Request(
                native_url,
                headers={"User-Agent": USER_AGENT, "Accept": "text/plain,*/*"},
                method="GET",
            )
            try:
                native_text = _urlopen_with_retries(native_request, timeout=REQUEST_TIMEOUT_S).decode("utf-8", errors="replace")
                native_version = parse_version(native_text, entry.pattern)
                if native_version is not None:
                    return RemoteStatus(
                        entry=entry,
                        version=native_version,
                        error=None,
                        http_status=None,
                        url=native_url,
                    )
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, socket.timeout, OSError):
                pass
        # Typical cases:
        #
        #   404 -> version file/repository/path disappeared
        #   403 -> rate limit (see describe_http_error() - distinguished from a
        #          real access restriction) or access restriction
        #   429 -> too many requests
        #   500+ -> GitHub/server problem
        #
        return RemoteStatus(
            entry=entry,
            version=None,
            error=describe_http_error(exc),
            http_status=exc.code,
            url=url,
        )

    except urllib.error.URLError as exc:
        reason = getattr(
            exc,
            "reason",
            "unknown network error",
        )

        return RemoteStatus(
            entry=entry,
            version=None,
            error=f"network error: {reason}",
            url=url,
        )

    except (TimeoutError, socket.timeout):
        return RemoteStatus(
            entry=entry,
            version=None,
            error=f"timed out after {REQUEST_TIMEOUT_S}s",
            url=url,
        )

    except OSError as exc:
        return RemoteStatus(
            entry=entry,
            version=None,
            error=f"OS/network error: {exc}",
            url=url,
        )

    except Exception as exc:
        # Last-resort protection:
        #
        # One unexpected parser/network implementation error should still
        # become an "unknown" project instead of killing all 44/45 lookups.
        return RemoteStatus(
            entry=entry,
            version=None,
            error=f"unexpected error: {type(exc).__name__}: {exc}",
            url=url,
        )

    # -----------------------------------------------------------------------
    # Manifest and version parsing
    # -----------------------------------------------------------------------

    try:
        manifest = parse_manifest(text, expected_name=entry.name)
        version = Version.from_string(manifest.version)
    except ManifestValidationError as exc:
        return RemoteStatus(
            entry=entry,
            version=None,
            error=f"invalid project manifest: {exc}",
            url=url,
        )

    return RemoteStatus(
        entry=entry,
        version=version,
        error=None,
        http_status=None,
        url=url,
        manifest=manifest,
    )


# ---------------------------------------------------------------------------
# All projects
# ---------------------------------------------------------------------------

def fetch_all(
    entries: list[ProjectEntry],
    progress=None,
) -> dict[str, RemoteStatus]:
    """
    Fetch the latest GitHub version for every given entry.

    Parameters
    ----------
    entries:
        Projects to query.

        Discovered local or remote project entries. The caller must supply
        them; this module deliberately has no fixed project catalogue.

    progress:
        Optional callback:

            progress(done, total)

        It is called after each individual request completes.

    Returns
    -------
    dict[str, RemoteStatus]

        Dictionary keyed by project name.

    Notes
    -----
    Requests are performed concurrently, but the concurrency is intentionally
    limited to MAX_CONCURRENT_REQUESTS.

    Results are inserted as soon as each request completes. Therefore the
    dictionary's insertion order is completion order. Consumers can apply
    their own family/name ordering after discovery.
    """

    targets = entries

    results: dict[str, RemoteStatus] = {}

    total = len(targets)
    done = 0

    if total == 0:
        return results

    with ThreadPoolExecutor(
        max_workers=MAX_CONCURRENT_REQUESTS,
        thread_name_prefix="hydra-github",
    ) as pool:

        futures = {
            pool.submit(
                _fetch_one,
                entry,
            ): entry
            for entry in targets
        }

        for future in as_completed(futures):
            entry = futures[future]

            try:
                status = future.result()

            except Exception as exc:
                # This should normally never happen because _fetch_one already
                # converts expected failures into RemoteStatus. It is kept as
                # a final isolation boundary anyway.
                status = RemoteStatus(
                    entry=entry,
                    version=None,
                    error=(
                        "worker failure: "
                        f"{type(exc).__name__}: {exc}"
                    ),
                    url=github_raw_url(entry),
                )

            results[
                status.entry.name
            ] = status

            done += 1

            if progress is not None:
                progress(
                    done,
                    total,
                )

    return results
