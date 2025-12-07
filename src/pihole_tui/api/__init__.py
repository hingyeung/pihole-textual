"""API client modules for Pi-hole REST API.

Exports API client and specific endpoint handlers.
"""

from pihole_tui.api.client import (
    AuthenticationError,
    NetworkError,
    PiHoleAPIClient,
    PiHoleAPIError,
    SessionExpiredError,
)

__all__ = [
    "PiHoleAPIClient",
    "PiHoleAPIError",
    "AuthenticationError",
    "SessionExpiredError",
    "NetworkError",
]
