"""Airbyte Agent Connectors

A library of connectors and utilities for building AI agents that interact
with Airbyte's data integration platform.

Note: Personal fork for learning/experimentation purposes.
Upstream: https://github.com/airbytehq/airbyte-agent-connectors
"""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("airbyte-agent-connectors")
except PackageNotFoundError:
    # Default version used when package is installed in development mode
    # or run directly from source without being installed.
    __version__ = "0.0.0-dev"

__all__ = ["__version__"]
