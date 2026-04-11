"""Base classes and interfaces for Airbyte agent connectors.

This module defines the foundational abstractions that all connectors
must implement, providing a consistent interface for the agent layer.
"""

from __future__ import annotations

import abc
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ConnectorConfig:
    """Base configuration for all connectors."""

    connector_name: str
    connector_version: str = "0.1.0"
    log_level: str = "INFO"
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AirbyteRecord:
    """Represents a single record emitted by a connector."""

    stream: str
    data: Dict[str, Any]
    emitted_at: Optional[int] = None  # Unix timestamp in milliseconds
    namespace: Optional[str] = None


@dataclass
class AirbyteStream:
    """Metadata describing a data stream exposed by a connector."""

    name: str
    json_schema: Dict[str, Any]
    supported_sync_modes: List[str] = field(default_factory=lambda: ["full_refresh"])
    namespace: Optional[str] = None
    source_defined_cursor: bool = False
    default_cursor_field: List[str] = field(default_factory=list)


@dataclass
class ConnectorCatalog:
    """Collection of streams available from a connector."""

    streams: List[AirbyteStream] = field(default_factory=list)

    def stream_names(self) -> List[str]:
        """Return a list of all stream names in the catalog."""
        return [s.name for s in self.streams]


class BaseConnector(abc.ABC):
    """Abstract base class for all Airbyte agent connectors.

    Subclasses must implement `check`, `discover`, and `read` to provide
    a fully functional connector compatible with the agent runtime.
    """

    def __init__(self, config: ConnectorConfig) -> None:
        self.config = config
        self._logger = logging.getLogger(
            f"{__name__}.{config.connector_name}"
        )
        logging.basicConfig(level=getattr(logging, config.log_level.upper(), logging.INFO))

    @abc.abstractmethod
    def check(self) -> bool:
        """Validate that the connector can reach the source/destination.

        Returns:
            True if the connection is healthy, False otherwise.
        """

    @abc.abstractmethod
    def discover(self) -> ConnectorCatalog:
        """Return the catalog of streams available from this connector.

        Returns:
            A ConnectorCatalog describing all available streams.
        """

    @abc.abstractmethod
    def read(
        self,
        catalog: ConnectorCatalog,
        state: Optional[Dict[str, Any]] = None,
    ) -> Iterator[AirbyteRecord]:
        """Read records from the source and yield them one by one.

        Args:
            catalog: The catalog of streams to read.
            state: Optional incremental state from a previous sync.

        Yields:
            AirbyteRecord instances for each row of data.
        """

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"name={self.config.connector_name!r}, "
            f"version={self.config.connector_version!r})"
        )
