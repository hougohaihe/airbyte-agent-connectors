"""SQL source connector for Airbyte Agent Connectors.

Provides a generic SQL source that can connect to relational databases
using SQLAlchemy, supporting stream-based data extraction.
"""

from __future__ import annotations

from typing import Any, Generator, Optional

try:
    import sqlalchemy
    from sqlalchemy import create_engine, inspect, text
    from sqlalchemy.engine import Engine
except ImportError as e:
    raise ImportError(
        "SQLAlchemy is required for the SQL source connector. "
        "Install it with: pip install sqlalchemy"
    ) from e

from pydantic import Field, SecretStr, field_validator

from airbyte_agent_connectors.base import (
    AirbyteRecord,
    AirbyteStream,
    ConnectorCatalog,
    ConnectorConfig,
    SourceConnector,
)


class SqlSourceConfig(ConnectorConfig):
    """Configuration for the SQL source connector."""

    connection_string: SecretStr = Field(
        description="SQLAlchemy connection string (e.g. postgresql://user:pass@host/db)"
    )
    schemas: Optional[list[str]] = Field(
        default=None,
        description="List of schemas to include. Defaults to all accessible schemas.",
    )
    tables: Optional[list[str]] = Field(
        default=None,
        description="List of tables to include (format: schema.table or just table). "
                    "Defaults to all tables in the selected schemas.",
    )
    batch_size: int = Field(
        default=1000,
        ge=1,
        le=100_000,
        description="Number of rows to fetch per batch.",
    )

    @field_validator("connection_string", mode="before")
    @classmethod
    def validate_connection_string(cls, v: Any) -> Any:
        """Ensure the connection string is not empty."""
        raw = v.get_secret_value() if hasattr(v, "get_secret_value") else str(v)
        if not raw.strip():
            raise ValueError("connection_string must not be empty")
        return v


class SqlSource(SourceConnector):
    """A generic SQL source connector backed by SQLAlchemy.

    Supports any database engine that SQLAlchemy can connect to, including
    PostgreSQL, MySQL, SQLite, and more.
    """

    def __init__(self, config: SqlSourceConfig) -> None:
        self.config = config
        self._engine: Optional[Engine] = None

    @property
    def engine(self) -> Engine:
        """Lazy-initialised SQLAlchemy engine."""
        if self._engine is None:
            self._engine = create_engine(
                self.config.connection_string.get_secret_value(),
                pool_pre_ping=True,
            )
        return self._engine

    def get_catalog(self) -> ConnectorCatalog:
        """Discover available tables and return them as AirbyteStreams."""
        inspector = inspect(self.engine)
        streams: list[AirbyteStream] = []

        target_schemas = self.config.schemas or inspector.get_schema_names()

        for schema in target_schemas:
            for table_name in inspector.get_table_names(schema=schema):
                qualified = f"{schema}.{table_name}"
                # Filter by explicit table list when provided
                if self.config.tables and qualified not in self.config.tables \
                        and table_name not in self.config.tables:
                    continue

                columns = inspector.get_columns(table_name, schema=schema)
                json_schema: dict[str, Any] = {
                    "type": "object",
                    "properties": {
                        col["name"]: {"type": _sa_type_to_json(col["type"])}
                        for col in columns
                    },
                }
                streams.append(
                    AirbyteStream(
                        name=qualified,
                        json_schema=json_schema,
                    )
                )

        return ConnectorCatalog(streams=streams)

    def read(
        self,
        stream_name: str,
        state: Optional[dict[str, Any]] = None,
    ) -> Generator[AirbyteRecord, None, None]:
        """Yield records from the specified table stream.

        Args:
            stream_name: Fully-qualified table name (schema.table).
            state: Optional cursor state (not yet used — full-refresh only).

        Yields:
            AirbyteRecord for each row in the table.
        """
        # Accept both "schema.table" and plain "table" formats
        parts = stream_name.split(".", maxsplit=1)
        if len(parts) == 2:
            schema, table = parts
            quoted = f'"{schema}"."{table}"'
        else:
            quoted = f'"{stream_name}"'

        query = text(f"SELECT * FROM {quoted}")

        with self.engine.connect() as conn:
            result = conn.execution_options(
                stream_results=True,
                max_row_buffer=self.config.batch_size,
            ).execute(query)

            keys = list(result.keys())
            while True:
                rows = result.fetchmany(self.config.batch_size)
                if not rows:
                    break
                for row in rows:
                    yield AirbyteRecord(
                        stream=stream_name,
                        data=dict(zip(keys, row)),
                    )

    def close(self) -> None:
        """Dispose of the underlying database engine and connection pool."""
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None


def _sa_type_to_json(sa_type: Any) -> str:
    """Map a SQLAlchemy column type to a JSON Schema type string."""
    type_str = str(sa_type).upper()
    if any(t in type_str for t in ("INT", "NUMERIC", "DECIMAL", "FLOAT", "REAL", "DOUBLE")):
        return "number"
    if "BOOL" in type_str:
        return "boolean"
    return "string"
