"""Authentication API endpoints for Pi-hole.

Handles login, logout, and session management via Pi-hole v6 REST API.
"""

from datetime import datetime, timedelta
from typing import Optional

from pydantic import BaseModel, Field

from pihole_tui.api.client import PiHoleAPIClient
from pihole_tui.constants import API_AUTH_LOGIN, API_AUTH_LOGOUT


class AuthRequest(BaseModel):
    """Authentication request payload."""

    password: str = Field(..., min_length=1, description="Pi-hole admin password")
    totp: Optional[str] = Field(default=None, description="TOTP code if 2FA enabled")


class SessionInfo(BaseModel):
    """Session information from authentication response."""

    sid: str = Field(..., description="Session ID for subsequent requests")
    validity: int = Field(..., description="Session validity duration in seconds")

    def get_expires_at(self) -> datetime:
        """Calculate session expiry timestamp.

        Returns:
            Datetime when session expires
        """
        return datetime.now() + timedelta(seconds=self.validity)


class AuthResponse(BaseModel):
    """Authentication response from Pi-hole API."""

    session: SessionInfo = Field(..., description="Session information")


async def login(
    client: PiHoleAPIClient, password: str, totp: Optional[str] = None
) -> AuthResponse:
    """Authenticate with Pi-hole and obtain session ID.

    Args:
        client: PiHoleAPIClient instance
        password: Pi-hole admin password
        totp: Optional TOTP code for 2FA

    Returns:
        AuthResponse with session information

    Raises:
        AuthenticationError: If authentication fails (invalid password/TOTP)
        NetworkError: If network communication fails
    """
    request = AuthRequest(password=password, totp=totp)

    response = await client.post(
        API_AUTH_LOGIN,
        json_data=request.model_dump(exclude_none=True),
        include_auth=False,
    )

    return AuthResponse(**response)


async def logout(client: PiHoleAPIClient) -> bool:
    """Logout and invalidate current session.

    Args:
        client: PiHoleAPIClient instance with active session

    Returns:
        True if logout successful

    Raises:
        SessionExpiredError: If session already expired
        NetworkError: If network communication fails
    """
    response = await client.delete(API_AUTH_LOGOUT)
    return response.get("success", False)


async def renew_session(client: PiHoleAPIClient, password: str) -> AuthResponse:
    """Renew session by re-authenticating.

    This is used for automatic session renewal before expiry.

    Args:
        client: PiHoleAPIClient instance
        password: Pi-hole admin password

    Returns:
        AuthResponse with new session information

    Raises:
        AuthenticationError: If authentication fails
        NetworkError: If network communication fails
    """
    # Session renewal is done by re-authenticating
    return await login(client, password)
