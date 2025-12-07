"""HTTP client for Pi-hole API communication.

Provides base HTTP client with session management, SID header handling,
auto-retry logic, and error handling.
"""

import asyncio
from typing import Any, Dict, Optional

import httpx

from pihole_tui.constants import (
    DEFAULT_API_TIMEOUT,
    MAX_RETRY_ATTEMPTS,
    RETRY_BACKOFF_BASE,
)


class PiHoleAPIError(Exception):
    """Base exception for Pi-hole API errors."""

    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Dict] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(PiHoleAPIError):
    """Raised when authentication fails."""

    pass


class SessionExpiredError(PiHoleAPIError):
    """Raised when session has expired."""

    pass


class NetworkError(PiHoleAPIError):
    """Raised when network communication fails."""

    pass


class PiHoleAPIClient:
    """Async HTTP client for Pi-hole API communication."""

    def __init__(self, base_url: str, timeout: int = DEFAULT_API_TIMEOUT):
        """Initialize API client.

        Args:
            base_url: Base URL for Pi-hole API (e.g., "http://pi.hole:8080")
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.sid: Optional[str] = None
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    def set_session(self, sid: str):
        """Set session ID for authenticated requests.

        Args:
            sid: Session ID from authentication
        """
        self.sid = sid

    def clear_session(self):
        """Clear session ID (logout)."""
        self.sid = None

    def _get_headers(self, include_auth: bool = True) -> Dict[str, str]:
        """Get request headers with optional authentication.

        Args:
            include_auth: Whether to include X-FTL-SID header

        Returns:
            Dictionary of headers
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        if include_auth and self.sid:
            headers["X-FTL-SID"] = self.sid

        return headers

    async def _request(
        self,
        method: str,
        endpoint: str,
        include_auth: bool = True,
        retry: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """Make HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, PATCH)
            endpoint: API endpoint path
            include_auth: Whether to include authentication header
            retry: Whether to retry on failure
            **kwargs: Additional arguments for httpx request

        Returns:
            Response JSON as dictionary

        Raises:
            AuthenticationError: If authentication fails (401)
            SessionExpiredError: If session expired (401 with session context)
            NetworkError: If network communication fails
            PiHoleAPIError: For other API errors
        """
        if not self._client:
            raise NetworkError("Client not initialized. Use async context manager.")

        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers(include_auth)

        # Merge headers with kwargs
        if "headers" in kwargs:
            headers.update(kwargs.pop("headers"))

        attempts = MAX_RETRY_ATTEMPTS if retry else 1

        for attempt in range(attempts):
            try:
                response = await self._client.request(
                    method=method, url=url, headers=headers, **kwargs
                )

                # Handle HTTP errors
                if response.status_code == 401:
                    if self.sid:
                        raise SessionExpiredError("Session expired", status_code=401)
                    else:
                        raise AuthenticationError("Authentication required", status_code=401)

                if response.status_code == 403:
                    error_data = response.json() if response.text else {}
                    raise AuthenticationError(
                        error_data.get("message", "Forbidden"),
                        status_code=403,
                        details=error_data,
                    )

                if response.status_code == 404:
                    raise PiHoleAPIError("Resource not found", status_code=404)

                if response.status_code == 429:
                    raise PiHoleAPIError("Rate limit exceeded", status_code=429)

                if response.status_code >= 400:
                    error_data = response.json() if response.text else {}
                    raise PiHoleAPIError(
                        error_data.get("message", f"HTTP {response.status_code}"),
                        status_code=response.status_code,
                        details=error_data,
                    )

                # Parse response
                return response.json()

            except httpx.TimeoutException:
                if attempt < attempts - 1:
                    # Exponential backoff
                    await asyncio.sleep(RETRY_BACKOFF_BASE * (2**attempt))
                    continue
                raise NetworkError("Request timeout")

            except httpx.NetworkError as e:
                if attempt < attempts - 1:
                    await asyncio.sleep(RETRY_BACKOFF_BASE * (2**attempt))
                    continue
                raise NetworkError(f"Network error: {str(e)}")

            except (AuthenticationError, SessionExpiredError, PiHoleAPIError):
                # Don't retry auth errors
                raise

            except Exception as e:
                raise PiHoleAPIError(f"Unexpected error: {str(e)}")

        raise NetworkError("Max retries exceeded")

    async def get(self, endpoint: str, params: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """Make GET request.

        Args:
            endpoint: API endpoint path
            params: Query parameters
            **kwargs: Additional request arguments

        Returns:
            Response JSON
        """
        return await self._request("GET", endpoint, params=params, **kwargs)

    async def post(
        self, endpoint: str, json_data: Optional[Dict] = None, **kwargs
    ) -> Dict[str, Any]:
        """Make POST request.

        Args:
            endpoint: API endpoint path
            json_data: JSON request body
            **kwargs: Additional request arguments

        Returns:
            Response JSON
        """
        return await self._request("POST", endpoint, json=json_data, **kwargs)

    async def put(
        self, endpoint: str, json_data: Optional[Dict] = None, **kwargs
    ) -> Dict[str, Any]:
        """Make PUT request.

        Args:
            endpoint: API endpoint path
            json_data: JSON request body
            **kwargs: Additional request arguments

        Returns:
            Response JSON
        """
        return await self._request("PUT", endpoint, json=json_data, **kwargs)

    async def patch(
        self, endpoint: str, json_data: Optional[Dict] = None, **kwargs
    ) -> Dict[str, Any]:
        """Make PATCH request.

        Args:
            endpoint: API endpoint path
            json_data: JSON request body
            **kwargs: Additional request arguments

        Returns:
            Response JSON
        """
        return await self._request("PATCH", endpoint, json=json_data, **kwargs)

    async def delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make DELETE request.

        Args:
            endpoint: API endpoint path
            **kwargs: Additional request arguments

        Returns:
            Response JSON
        """
        return await self._request("DELETE", endpoint, **kwargs)
