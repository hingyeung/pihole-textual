"""Blocking state and toggle request models for Pi-hole DNS blocking control."""

from typing import Optional

from pydantic import BaseModel, Field


class BlockingState(BaseModel):
    """Current DNS blocking state from Pi-hole API."""

    blocking: bool = Field(..., description="Whether DNS blocking is currently enabled")
    timer: Optional[int] = Field(
        None,
        ge=0,
        description="Seconds remaining on temporary disable timer, or None if no timer active",
    )

    @property
    def is_temp_disabled(self) -> bool:
        """Return True if blocking is temporarily disabled with an active timer."""
        return not self.blocking and self.timer is not None and self.timer > 0

    @property
    def state_label(self) -> str:
        """Human-readable label for the current state."""
        if self.blocking:
            return "enabled"
        if self.is_temp_disabled:
            return "temp_disabled"
        return "disabled"


class BlockingToggleRequest(BaseModel):
    """Request model for enabling or disabling DNS blocking."""

    blocking: bool = Field(..., description="True to enable blocking, False to disable")
    timer: Optional[int] = Field(
        None,
        ge=1,
        description="Duration in seconds for temporary disable (only valid when blocking=False)",
    )
    reason: Optional[str] = Field(
        None,
        max_length=255,
        description="Optional reason or comment for the blocking change",
    )

    def to_api_payload(self) -> dict:
        """Convert to the payload dict expected by the Pi-hole API.

        The API only accepts 'blocking' and 'timer' fields.
        """
        payload: dict = {"blocking": self.blocking}
        if not self.blocking and self.timer is not None:
            payload["timer"] = self.timer
        return payload
