"""Session state model for Pi-hole TUI.

Tracks active session information including authentication state,
session ID, expiry, and connected Pi-hole instance details.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from pihole_tui.models.config import ConnectionProfile


class SessionState(BaseModel):
    """Represents current application session state (in-memory, not persisted)."""

    sid: Optional[str] = Field(default=None, description="Active session ID")
    expires_at: Optional[datetime] = Field(default=None, description="Session expiry timestamp")
    connection_profile: Optional[ConnectionProfile] = Field(
        default=None, description="Active connection profile"
    )
    is_authenticated: bool = Field(default=False, description="Whether currently authenticated")
    last_renewal: Optional[datetime] = Field(
        default=None, description="Last session renewal timestamp"
    )
    pi_hole_version: Optional[str] = Field(
        default=None, description="Connected Pi-hole version"
    )

    def is_session_valid(self) -> bool:
        """Check if the current session is valid (authenticated and not expired)."""
        if not self.is_authenticated or not self.sid or not self.expires_at:
            return False
        return datetime.now() < self.expires_at

    def should_renew(self, threshold: float = 0.8) -> bool:
        """Check if session should be renewed based on threshold.

        Args:
            threshold: Percentage of validity period at which to renew (default 0.8 = 80%)

        Returns:
            True if session should be renewed, False otherwise
        """
        if not self.is_session_valid():
            return False

        if not self.last_renewal:
            # No renewal yet, use a conservative approach
            return True

        # Calculate remaining time as percentage
        now = datetime.now()
        total_duration = (self.expires_at - self.last_renewal).total_seconds()
        remaining = (self.expires_at - now).total_seconds()

        if total_duration <= 0:
            return True

        remaining_percentage = remaining / total_duration
        return remaining_percentage <= (1 - threshold)

    def clear(self):
        """Clear all session data (logout)."""
        self.sid = None
        self.expires_at = None
        self.is_authenticated = False
        self.last_renewal = None
        # Note: Keep connection_profile and pi_hole_version for reconnection
