"""HTTP-based source connector implementation for Airbyte Agent Connectors.

Provides a base class and utilities for building source connectors
that fetch data from HTTP/REST APIs.
"""

from __future__ import annotations

import logging
from abc import abstractmethod
from typing import Any, Generator, Iterable, Optional

import requests
from requests.adapters import HTTPAdapter
from requests.auth import AuthBase
from urllib3.util.retry import Retry

from airbyte_agent_connectors.base import (
    AirbyteRecord,
    AirbyteStream,
    ConnectorCatalog,
    ConnectorConfig,
)

logger = logging.getLogger(__name__)

DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_BACKOFF_FACTOR = 0.5
DEFAULT_TIMEOUT_SECONDS = 30


class HttpSourceConfig(ConnectorConfig):
    """Configuration for HTTP-based source connectors."""

    base_url: str
    timeout: int = DEFAULT_TIMEOUT_SECONDS
    max_retries: int = DEFAULT_RETRY_ATTEMPTS


class BearerTokenAuth(AuthBase):
    """Attaches a Bearer token to the Authorization header of each request."""

    def __init__(self, token: str) -> None:
        self.token = token

    def __call__(self, r: requests.PreparedRequest) -> requests.PreparedRequest:
        r.headers["Authorization"] = f"Bearer {self.token}"
        return r


def build_session(
    max_retries: int = DEFAULT_RETRY_ATTEMPTS,
    backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
    status_forcelist: tuple[int, ...] = (429, 500, 502, 503, 504),
) -> requests.Session:
    """Create a requests Session with retry logic pre-configured.

    Args:
        max_retries: Maximum number of retry attempts.
        backoff_factor: Multiplier applied between retry attempts.
        status_forcelist: HTTP status codes that trigger a retry.

    Returns:
        A configured :class:`requests.Session` instance.
    """
    session = requests.Session()
    retry_strategy = Retry(
        total=max_retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=["GET", "POST"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


class HttpSource:
    """Base class for HTTP-based Airbyte source connectors.

    Subclasses must implement :meth:`get_catalog` and :meth:`read_records`.
    The :meth:`check_connection` method may optionally be overridden to
    provide a more meaningful health-check against the upstream API.
    """

    def __init__(self, config: HttpSourceConfig, auth: Optional[AuthBase] = None) -> None:
        self.config = config
        self._session = build_session(max_retries=config.max_retries)
        if auth:
            self._session.auth = auth

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
    def get_catalog(self) -> ConnectorCatalog:
        """Return the catalog of streams available from this source."""
        ...

    @abstractmethod
    def read_records(
        self,
        stream: AirbyteStream,
        state: Optional[dict[str, Any]] = None,
    ) -> Generator[AirbyteRecord, None, None]:
        """Yield records from *stream*, optionally resuming from *state*."""
        ...

    # ------------------------------------------------------------------
    # Helpers available to subclasses
    # ------------------------------------------------------------------

    def get(
        self,
        path: str,
        params: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> requests.Response:
        """Perform a GET request against the configured base URL.

        Args:
            path: URL path (will be joined with :attr:`config.base_url`).
            params: Optional query-string parameters.
            **kwargs: Extra keyword arguments forwarded to :meth:`requests.Session.get`.

        Returns:
            The HTTP response object.

        Raises:
            requests.HTTPError: If the response status indicates an error.
        """
        url = f"{self.config.base_url.rstrip('/')}/{path.lstrip('/')}"
        logger.debug("GET %s params=%s", url, params)
        response = self._session.get(
            url,
            params=params,
            timeout=self.config.timeout,
            **kwargs,
        )
        response.raise_for_status()
        return response

    def check_connection(self) -> tuple[bool, Optional[str]]:
        """Verify that the connector can reach the upstream API.

        Returns:
            A tuple of ``(success, error_message)``.  *error_message* is
            ``None`` when *success* is ``True``.
        """
        try:
            self._session.get(
                self.config.base_url,
                timeout=self.config.timeout,
            ).raise_for_status()
            return True, None
        except Exception as exc:  # noqa: BLE001
            return False, str(exc)

    def paginate(
        self,
        path: str,
        page_size: int = 100,
        page_param: str = "page",
        size_param: str = "per_page",
        results_key: str = "data",
    ) -> Iterable[dict[str, Any]]:
        """Simple page-number–based pagination helper.

        Yields individual items from each page until an empty page is
        returned by the API.

        Args:
            path: API endpoint path.
            page_size: Number of records to request per page.
            page_param: Query parameter name for the page number.
            size_param: Query parameter name for the page size.
            results_key: JSON key that contains the list of records.
        """
        page = 1
        while True:
            response = self.get(
                path,
                params={page_param: page, size_param: page_size},
            )
            items: list[dict[str, Any]] = response.json().get(results_key, [])
            if not items:
                break
            yield from items
            if len(items) < page_size:
                # Last page — no need for an extra round-trip.
                break
            page += 1
