# URTC-UPDATER — CLI Reference

`urtc-updater` defaults to a windowed Qt Quick GUI. Passing `--cli` switches
to the headless argparse CLI documented here, before the optional desktop
runtime is imported, so `--cli` mode works on a genuinely headless machine with
no Qt/PySide6 desktop runtime installed and no display. The `-h` blocks below
are the real help text of the installed CLI; the sample outputs after them are
illustrative of the shape, with made-up project names and versions.

## Usage

```
$ urtc-updater --cli -h
usage: urtc-updater --cli [-h] [--version]
                          {status,install,update,check,clean-backups,restore-backup,security,evidence,package,firmware,compat} ...

Detects, installs, and manually updates the URTC ecosystem's own repositories
on this machine.

positional arguments:
  {status,install,update,check,clean-backups,restore-backup,security,evidence,package,firmware,compat}
    status              Show what's installed, its version, and the latest
                        GitHub version of every project.
    install             Clone and build ONE project that isn't installed yet.
    update              Pull and rebuild ONE project that's already installed.
    check               Notify only: list what could be updated and change
                        nothing (exit code 10 when something can).
    clean-backups       Remove kept previous installations (and leftover
                        staging folders) beyond the newest N per project.
    restore-backup      Put the newest kept previous installation of ONE
                        project back in place (the current one is kept too).
    security            Show or change the security options: require signed
                        commits, ask before the build check (both off by
                        default; turning one off asks first).
    evidence            Verify the hash chain of the evidence log, optionally
                        exporting it as one JSON file.
    package             Install a program from the signed package of its
                        release (list, check, install, rollback).
    firmware            Check the release signature of a firmware image and
                        offer to open the Flasher with it (check, open).

options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
```

```
$ urtc-updater --cli --version
urtc-updater <version>
```

`install`/`update` are deliberately separate from `status` and always
take one explicit project name — there is no "update everything". A
fleet of real robots is not something to leave auto-updating
unattended: `status` shows what's outdated, a human picks what to
actually touch.

## Commands

### `status [--workspace PATH] [--offline] [--notes] [--json] [--profile NAME]`

```
$ urtc-updater --cli status -h
usage: urtc-updater --cli status [-h] [--workspace WORKSPACE] [--offline]
                                 [--notes] [--json] [--profile PROFILE]

options:
  -h, --help            show this help message and exit
  --workspace WORKSPACE
                        Workspace root to scan (default: this tool's own
                        parent directory).
  --offline             Skip the GitHub check - local state only.
  --notes               Also print each project's real notes (family/parent,
                        what's actually implemented, tech) below the table.
  --json                Machine-readable JSON instead of the human-readable
                        table (ignores --notes).
  --profile PROFILE     Only the projects of this station profile (default:
                        the profile selected in the settings).
```

Scans `--workspace` (or this tool's own parent directory by default) for
sibling folders that expose a valid `urtc.project.json` — a folder
name alone is never enough to join the ecosystem — and, unless
`--offline`, checks each one's real published version on GitHub too.

For an installed project whose version equals GitHub's, `status` also runs one
`git ls-remote` against its `origin` and compares commits: the state is
`NEW COMMITS` when the remote has commits the checkout does not contain (the
version only moves on a release build, so a fix can be published without a
version change). `--json` adds `commit_state` to each project and
`new_commits_count` to the summary.

```
$ urtc-updater --cli status --workspace /path/to/workspace --offline
Workspace root: /path/to/workspace
(--offline: not checking GitHub - showing local state only)
PROJECT         MATURITY     ROLE      STACK       LOCAL     GITHUB    STATE
----------------------------------------------------------------------------
DEMO-PROJECT-A  functional   service   python      1.2.3     -         installed (not checked)

1/1 installed, 0 outdated (GitHub not checked)
```

### `install <PROJECT-NAME> [--workspace PATH] [--no-build] [--profile NAME] [--require-signed|--no-require-signed] [--confirm-build|--no-confirm-build] [--yes]`

```
$ urtc-updater --cli install -h
usage: urtc-updater --cli install [-h] [--workspace WORKSPACE] [--no-build]
                                  [--profile PROFILE]
                                  project

positional arguments:
  project               Exact project name (see `status` for the full list).

options:
  -h, --help            show this help message and exit
  --workspace WORKSPACE
                        Workspace root (default: this tool's own parent
                        directory).
  --no-build            Clone only - skip running the project's own build
                        script.
  --profile PROFILE     Refuse a project outside this station profile.
```

`git clone`s the named project into `--workspace`, then runs its own
`build-test.sh`/`.bat` unless `--no-build` is given. A project name that
doesn't expose a valid manifest on GitHub is a real, reported failure —
never a silent no-op:

```
$ urtc-updater --cli install NOT-A-REAL-PROJECT
Unknown ecosystem project: 'NOT-A-REAL-PROJECT'
The project must expose a valid urtc.project.json on GitHub.
$ echo $?
1
```

### `update <PROJECT-NAME> [--workspace PATH] [--no-build] [--profile NAME] [--preview] [--require-signed|--no-require-signed] [--confirm-build|--no-confirm-build] [--yes]`

```
$ urtc-updater --cli update -h
usage: urtc-updater --cli update [-h] [--workspace WORKSPACE] [--no-build]
                                 [--profile PROFILE] [--preview]
                                 project

positional arguments:
  project               Exact project name (see `status` for the full list).

options:
  -h, --help            show this help message and exit
  --workspace WORKSPACE
                        Workspace root (default: this tool's own parent
                        directory).
  --no-build            Pull only - skip running the project's own build
                        script.
  --profile PROFILE     Refuse a project outside this station profile.
  --preview             Show the candidate commit, its author, signature state
                        and the build/tool files it changes, then stop without
                        updating.
```

Fetches the remote candidate, validates its repository-owned
`urtc.project.json` before modifying the checkout, rejects a candidate
whose semantic version is lower than the installed manifest (a candidate with
the same version and new commits is accepted), then builds and verifies it in
an isolated staging clone and promotes it with two directory renames; the
previous installation is kept as `<name>.backup-<8 hex digits>`. With
`--no-build` it performs a plain `git merge --ff-only` instead. The preflight
is deliberately manifest-based: a reachable Git commit is not automatically a
safe ecosystem update. `--ff-only` is deliberate and load-bearing: **a healthy
local checkout is never replaced**. A real local edit (this tool is meant to
also run on a developer machine) or a diverged branch makes the update fail
loudly — never a silent reset or a discarded change:

```
$ cd /path/to/workspace/SOME-PROJECT && git log --oneline -1
a1b2c3d local work in progress
$ urtc-updater --cli update SOME-PROJECT
FAIL /path/to/workspace/SOME-PROJECT has uncommitted change(s) to real tracked file(s): ... - refusing to update; ...
$ cd /path/to/workspace/SOME-PROJECT && git log --oneline -1
a1b2c3d local work in progress   # unchanged
```

(Exercised for real in `tests/test_install.py`'s
`test_diverged_pull_fails_without_resetting_local_checkout`: a real
diverged git history is built, the fast-forward is proven to fail, and
`HEAD`/file content are proven byte-for-byte unchanged afterward. The separate
`test_refuses_a_remote_manifest_version_lower_than_the_installed_version`
proves that an otherwise fast-forwardable downgrade leaves `HEAD` unchanged.)

`--preview` looks before approving: it fetches the candidate and prints its
commit, author, the installed and candidate versions, the signature state under
the current policy, and which build or tool files (`build-test.*`, `build*.sh`,
`build*.bat`, `tools/`, `scripts/`) it changes — then stops without modifying
the checkout.

After a successful update the newest 2 previous installations of that project
are kept (the `backups_to_keep` setting changes the number) and older ones are
removed.

### `check [--workspace PATH] [--notify] [--quiet] [--profile NAME]`

```
$ urtc-updater --cli check -h
usage: urtc-updater --cli check [-h] [--workspace WORKSPACE] [--notify]
                                [--quiet] [--profile PROFILE]

options:
  -h, --help            show this help message and exit
  --workspace WORKSPACE
                        Workspace root (default: this tool's own parent
                        directory).
  --notify              Also show a desktop notification when updates are
                        available.
  --quiet               Print nothing when everything is up to date.
  --profile PROFILE     Only the projects of this station profile.
```

Notify only: lists the installed projects that GitHub has a newer version of,
or new commits at the same version, and **changes nothing**. It exits with
`10` when something can be updated, so a scheduled task (cron, Task Scheduler)
can notify a person while the rule that nothing is updated without approval
stays intact. `--notify` also shows a desktop notification (`notify-send` on
Linux, `osascript` on macOS, a PowerShell balloon on Windows).

### `clean-backups [--workspace PATH] [--keep N] [--dry-run]`

```
$ urtc-updater --cli clean-backups -h
usage: urtc-updater --cli clean-backups [-h] [--workspace WORKSPACE]
                                        [--keep KEEP] [--dry-run]

options:
  -h, --help            show this help message and exit
  --workspace WORKSPACE
                        Workspace root (default: this tool's own parent
                        directory).
  --keep KEEP           Previous installations to keep per project (default:
                        0).
  --dry-run             Only list what would be removed.
```

Removes the kept previous installations (`<name>.backup-<8 hex digits>`) beyond
the newest `N` of each project, and every hidden staging folder
(`.<name>.update-…`, `.<name>.clone-…`) that a run which died left behind. It
holds the workspace lock, so it can never run under an install, and first heals
any promotion that was interrupted.

### `restore-backup <PROJECT-NAME> [--workspace PATH] [--backup FOLDER] [--list]`

```
$ urtc-updater --cli restore-backup -h
usage: urtc-updater --cli restore-backup [-h] [--workspace WORKSPACE]
                                         [--backup BACKUP] [--list]
                                         project

positional arguments:
  project               Exact project name.

options:
  -h, --help            show this help message and exit
  --workspace WORKSPACE
                        Workspace root (default: this tool's own parent
                        directory).
  --backup BACKUP       Folder name of the backup to restore (default: the
                        newest).
  --list                Only list the kept previous installations of the
                        project.
```

Puts a kept previous installation back in place with the same guarantees as an
update: the installation being replaced is itself kept (as a new backup, so the
swap can be undone), nothing is deleted, a failure between the two renames puts
the original back, and the program running right now is never replaced.

### `security [--require-signed on|off] [--confirm-build on|off] [--yes]`

Shows the two security options, or saves them in the settings file. Both are **off by default**:

```text
$ urtc-updater --cli security
Require signed commits:           off (saved)  off (in force now)
Ask before the build check:       off (saved)  off (in force now)
Both are off by default. Environment: URTC_UPDATER_REQUIRE_SIGNED, URTC_UPDATER_CONFIRM_BUILD (1 or 0).
```

- *Require signed commits*: the candidate commit must carry a valid GPG or SSH signature before its manifest is read or anything in it is built.
- *Ask before the build check*: after the candidate is fetched and validated, the project, commit, author, signature and the build or tool scripts that changed are shown, and nothing is run until the answer is yes. In a terminal the question is `Run the build check? [y/N]`; the window shows a dialog. With no terminal and no window the build check is not run (exit `1`, "there is nobody to ask"); `--yes`, or `URTC_UPDATER_ASSUME_YES=1`, answers yes for scripts.

Saving a **lower** level than the saved one (turning an option off) prints a warning and asks `Turn it off anyway? [y/N]`; without a terminal it needs `--yes` and otherwise changes nothing (exit `1`). The same flags exist on `install` and `update` for one run (`--require-signed` / `--no-require-signed`, `--confirm-build` / `--no-confirm-build`, `--yes`); they win over the settings and the environment variables, and a run that turns off a protection that the saved settings have on says so on standard error.

### `package {list|check|install|rollback} [APP] [--file FILE] [--yes]`

Installs a URTC program from the signed package its release carries (a `.zip`, or a `.tar.gz` outside Windows) instead of a clone and a build. `APP` is one of `urtc-flasher`, `urtc-tester` and `urtc-updater`.

```text
$ urtc-updater --cli package list
$ urtc-updater --cli package check urtc-flasher
$ urtc-updater --cli package install urtc-flasher
$ urtc-updater --cli package install urtc-flasher --file urtc-flasher-<version>-<platform>.zip
$ urtc-updater --cli package rollback urtc-flasher
```

- `list` shows the installed version and the kept releases of every program.
- `check` asks GitHub once whether a newer package exists and exits `10` when it does.
- `install` downloads the package of the latest release (or reads `--file`, with its `.sha256` and `.sig` next to it, and uses no network), checks it, shows the version and the notes and waits for a yes in the terminal (`--yes` answers it, for scripts).
- `rollback` points the program back to its previous release.

The rules are those of the programs that update themselves: only a strictly higher version, only the download hosts of GitHub, the announced size and SHA-256, the Ed25519 signature of the key of the releases pinned in this tool, a safe extraction, two releases kept and a rollback. A package that fails a check is deleted and nothing is installed. The programs live under `URTC_UPDATE_ROOT` (or the data folder of the person), one folder per program. Exit code `1` when a check fails or the network or the disk does.

### `firmware {check|open} IMAGE [--yes]`

Checks a firmware image of a release and offers to open the installed Flasher with it already selected.

```text
$ urtc-updater --cli firmware check URTC_MAIN_FIRMWARE_v<version>.bin
$ urtc-updater --cli firmware open URTC_MAIN_FIRMWARE_v<version>.bin
```

- Both read `<IMAGE>.sig` next to the image: the Ed25519 signature, by the key of the releases pinned in this tool, over the name of the file and its SHA-256. A file that is not a `.bin`, an image with no signature, with an unreadable one or with one that does not match is refused (exit code `1`, `FIRMWARE=FAIL <code>`), and nothing is started.
- `open` shows the size and SHA-256, then asks `Open the Flasher with ... selected? [y/N]` (`--yes` answers it, for scripts; without a terminal and without `--yes` nothing is started). It starts the Flasher installed with `package install urtc-flasher` as `--firmware IMAGE`.
- The Flasher only selects the file. This tool never writes to a board: you connect an adapter, choose the options and confirm the update in the Flasher, which checks the image again.

### `compat [--workspace PATH] [--json] [--language NAME]`

Compares the projects found in the workspace with the compatibility matrix of the release this program carries: each one is shown as released, newer, older, not installed or of unknown version, with the copy of the shared code it carries, and the firmware that URTC-FLASHER and URTC-WEB-STUDIO bundle is compared with the firmware of the tool head repository. It only reads manifests and file names: it changes nothing and does not use the network. `--json` prints the same result as data; `--language` picks one of the eight languages of the table.

### `evidence [--workspace PATH] [--export FILE] [--export-common FILE]`

```
$ urtc-updater --cli evidence -h
usage: urtc-updater --cli evidence [-h] [--workspace WORKSPACE]
                                   [--export FILE] [--export-common FILE]

options:
  -h, --help            show this help message and exit
  --workspace WORKSPACE
                        Workspace root (default: this tool's own parent
                        directory).
  --export FILE         Write the entries and the verification result to FILE.
  --export-common FILE  Write the attempts as urtc-evidence/1 records (one
                        JSON document per line), the shape the flasher and the
                        tester use.
```

Every install, update and restore appends a line to
`<workspace>/.urtc-updater/evidence.jsonl` with the time (UTC), updater
version, host, user, project, versions and commits before and after, and the
message. Each line carries the hash of the one before it and its own hash, so
an edited, removed or reordered line is detected. `evidence` verifies the chain
(exit `1` and a `PROBLEM` line per finding when it is broken) and, with
`--export`, writes the entries and the verdict as one JSON document. With `--export-common` it writes the attempts as `urtc-evidence/1` records, one JSON document per line, the same shape the flasher writes for an update; it says how many lines it left out because they do not fit that shape.

## Settings

`~/.urtc_updater_settings.json` (written atomically) holds the remembered
choices: `lang`, `workspace_root`, `backups_to_keep` (default 2),
`signature_policy` (`warn`, the default: an unsigned revision is installed and the steps say so; `require`: it is refused; the older `require_signed_commits: true` means `require`) / `allowed_signers_file`, `confirm_before_build` (`false`, the default; `true`: ask before the build check of a candidate runs) and the station profiles (below). A settings file that exists but cannot be read counts as `require` (signatures required) until it is fixed or removed; saving the language does not overwrite it, and saving the security options keeps it next to the new file as `.corrupt`. Environment variables win over the file: `URTC_UPDATER_REQUIRE_SIGNED`, `URTC_UPDATER_CONFIRM_BUILD` (`1`/`0`), `URTC_UPDATER_ASSUME_YES`, `URTC_UPDATER_ALLOWED_SIGNERS`. The build check of every project is run with `URTC_PYTHON` set to the interpreter that runs the updater (unless it is already set), and the build scripts of the URTC projects use it.

Station profiles:

```json
{
  "profiles": {"firmware-bench": {"projects": ["URTC", "URTC-FLASHER"], "allow_batch": false}},
  "profile": "firmware-bench"
}
```

A profile lists the projects a machine works with (empty or missing: all) and
whether the window's batch actions are allowed. `--profile NAME` (or the
`profile` setting) restricts `status`, `check`, `install` and `update` to it,
and the window follows the same profile. An undefined profile name is an error,
never "no restriction".

## Exit codes

`status` exits `0` (even when projects are outdated — that's informational,
not a failure), or `1` for an undefined profile. `install`/`update` exit `1` on
any real failure (unknown project, failed clone/pull, failed build script) and
`0` on success; `update --preview` exits `0` when it could describe the
candidate. `check` exits `0` when nothing can be updated and `10` when
something can. `clean-backups` exits `1` when another instance holds the
workspace; `restore-backup` exits `1` when it could not restore; `evidence`
exits `1` when the chain is broken; `package check` exits `10` when a newer
package exists and `package` exits `1` when a check fails.

## Network resilience

Every real GitHub request `status` makes (repository listing, manifest
fetch) retries up to 3 times with backoff for a genuinely transient
network failure (DNS/timeout/connection reset). A 403 or 429 that carries a
`Retry-After` of at most 60 seconds (GitHub's secondary rate limit) is waited
out and retried too; a longer wait, the hourly rate limit and every other HTTP
answer (404, 500, ...) are final and never retried. The repository listing is
asked for with `If-None-Match` and kept in `~/.urtc_updater_repo_cache.json`:
an unchanged listing is answered with `304`, which does not count against the
hourly request quota. If the remote catalog itself is unreachable or malformed,
`status` falls back to local-only state with a `WARNING:` line instead of
crashing.

## GUI

The preferred desktop client is the Qt Quick/QML interface. It is supplied by
the optional `PySide6` extra and uses the same discovery and update services as
this CLI; see [QML Desktop GUI](QML_DESKTOP_GUI.md). `--cli` remains fully
stdlib-only for a headless machine. A Tkinter window can still appear only as a
temporary compatibility fallback when the optional Qt runtime is absent.

Running `urtc-updater` with no arguments opens the QML desktop client.
On Windows, `run-gui.vbs` is the console-free double-click launcher; bare
`run.bat` delegates to it. The client provides a filterable project table,
explicit Install/Update actions, real in-window checkpoints and a language
selector (8 languages; the CLI itself stays English-only, since it's
meant to be scripted/piped). The text of every checkpoint and failure of an
install or update is shown in the selected language. Projects at the same
version as GitHub that have new commits show as `NEW COMMITS` and offer Update.
The window keeps its newest 20 log files under `~/.urtc_updater/logs`.
