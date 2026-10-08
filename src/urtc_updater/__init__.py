"""URTC-UPDATER - detects, installs, and manually updates every one of
the URTC ecosystem's own repositories on the machine it runs on (a developer
PC with the same sibling-directory checkout layout - no CM5 or server).

pyproject.toml's own `version` field is the real source of truth -
`__version__` below is a mirror bump_version.py keeps in sync on every real
build, kept here (rather than reading it back out of installed package
metadata) so this module has a version to report even before
`pip install -e .` has ever run against a bare checkout.
"""
__version__ = "0.0.5"