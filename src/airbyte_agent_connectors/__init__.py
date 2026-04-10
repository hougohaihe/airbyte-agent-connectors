"""
Airbyte Agent Connectors

A library of connectors and utilities for building AI agents that interact
with Airbyte's data integration platform.
"""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("airbyte-agent-connectors")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = ["__version__"]
