"""Configuration models for Pi-hole TUI.

Defines ConnectionProfile for saved Pi-hole connections and
UserPreferences for application settings.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ConnectionProfile(BaseModel):
    """Represents a saved Pi-hole connection configuration."""

    name: str = Field(..., min_length=1, max_length=50, description="Profile display name")
    hostname: str = Field(..., min_length=1, description="Pi-hole hostname or IP address")
    port: int = Field(default=8080, ge=1, le=65535, description="API port")
    use_https: bool = Field(default=False, description="Use HTTPS for connection")
    saved_password: Optional[str] = Field(
        default=None, description="Encrypted password if remembered"
    )
    totp_enabled: bool = Field(default=False, description="Whether 2FA/TOTP is enabled")
    last_used: Optional[datetime] = Field(default=None, description="Last connection timestamp")
    is_active: bool = Field(default=False, description="Currently active connection")

    @field_validator("hostname")
    @classmethod
    def validate_hostname(cls, v: str) -> str:
        """Validate hostname is not empty after stripping whitespace."""
        v = v.strip()
        if not v:
            raise ValueError("Hostname cannot be empty")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate profile name is not empty after stripping whitespace."""
        v = v.strip()
        if not v:
            raise ValueError("Profile name cannot be empty")
        return v

    def get_base_url(self) -> str:
        """Construct the base URL for the Pi-hole API."""
        protocol = "https" if self.use_https else "http"
        return f"{protocol}://{self.hostname}:{self.port}"


class UserPreferences(BaseModel):
    """User-configurable application settings."""

    dashboard_refresh_interval: int = Field(
        default=5, description="Dashboard auto-refresh interval in seconds"
    )
    query_log_refresh_interval: int = Field(
        default=5, description="Query log refresh interval in seconds"
    )
    query_log_page_size: int = Field(default=50, description="Number of queries per page")
    date_format: str = Field(default="relative", description="Date display format")
    confirm_blocking_changes: bool = Field(
        default=True, description="Show confirmation before enabling/disabling blocking"
    )
    confirm_domain_deletes: bool = Field(
        default=True, description="Show confirmation before deleting domains"
    )
    theme: str = Field(default="textual-dark", description="UI theme name")

    @field_validator("dashboard_refresh_interval")
    @classmethod
    def validate_dashboard_refresh(cls, v: int) -> int:
        """Validate dashboard refresh interval is in allowed options."""
        allowed = [5, 10, 30, 60]
        if v not in allowed:
            raise ValueError(f"Dashboard refresh interval must be one of {allowed}")
        return v

    @field_validator("query_log_refresh_interval")
    @classmethod
    def validate_query_log_refresh(cls, v: int) -> int:
        """Validate query log refresh interval is in allowed options."""
        allowed = [3, 5, 10]
        if v not in allowed:
            raise ValueError(f"Query log refresh interval must be one of {allowed}")
        return v

    @field_validator("query_log_page_size")
    @classmethod
    def validate_page_size(cls, v: int) -> int:
        """Validate page size is in allowed options."""
        allowed = [25, 50, 100]
        if v not in allowed:
            raise ValueError(f"Query log page size must be one of {allowed}")
        return v

    @field_validator("date_format")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Validate date format is either 'relative' or 'absolute'."""
        if v not in ["relative", "absolute"]:
            raise ValueError("Date format must be 'relative' or 'absolute'")
        return v
