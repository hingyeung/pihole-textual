"""Data models for Pi-hole TUI.

Exports all Pydantic models used throughout the application.
"""

from pihole_tui.models.blocking import BlockingState, BlockingToggleRequest
from pihole_tui.models.config import ConnectionProfile, UserPreferences
from pihole_tui.models.domain import (
    BulkDomainOperation,
    DomainAddRequest,
    DomainImportRequest,
    DomainImportResult,
    DomainListEntry,
    DomainListFilters,
    DomainListResponse,
    DomainUpdateRequest,
)
from pihole_tui.models.session import SessionState
from pihole_tui.models.stats import (
    DashboardStats,
    QueryTypeDistribution,
    ReplyTypeDistribution,
)

__all__ = [
    "BlockingState",
    "BlockingToggleRequest",
    "BulkDomainOperation",
    "ConnectionProfile",
    "DomainAddRequest",
    "DomainImportRequest",
    "DomainImportResult",
    "DomainListEntry",
    "DomainListFilters",
    "DomainListResponse",
    "DomainUpdateRequest",
    "UserPreferences",
    "SessionState",
    "DashboardStats",
    "QueryTypeDistribution",
    "ReplyTypeDistribution",
]
