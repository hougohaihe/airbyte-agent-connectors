"""Airbyte Agent Connectors

A library of connectors and utilities for building AI agents that interact
with Airbyte's data integration platform.

Note: Personal fork for learning/experimentation purposes.
Upstream: https://github.com/airbytehq/airbyte-agent-connectors

Fork notes:
- Using '0.0.0-dev' as fallback version for local dev installs
- See CHANGELOG.md for upstream changes I've pulled in
"""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("airbyte-agent-connectors")
except PackageNotFoundError:
    # Default version used when package is installed in development mode
    # or run directly from source without being installed.
    # Using '0.0.0-dev' so version comparisons don't accidentally treat
    # this as a real release (e.g. 0.0.0 could collide with a real tag).
    __version__ = "0.0.0-dev"

__all__ = ["__version__"]
