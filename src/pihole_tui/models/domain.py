"""Domain list data models for Pi-hole allow/blocklist management."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from pihole_tui.constants import DomainListType

# Pi-hole v6 API returns type as a string ("allow"/"deny") in responses.
_TYPE_STRING_MAP = {"allow": 0, "allowlist": 0, "deny": 1, "block": 1, "blocklist": 1}


class DomainListEntry(BaseModel):
    """A single entry in an allow or denylist."""

    id: int = Field(..., description="Unique domain entry ID")
    domain: str = Field(..., description="Domain name or wildcard pattern")
    type: int = Field(..., description="0=allowlist, 1=denylist")
    kind: str = Field("exact", description="'exact' or 'regex'")

    @field_validator("type", mode="before")
    @classmethod
    def coerce_type(cls, v) -> int:
        """Accept both integer (0/1) and string ('allow'/'deny') type values."""
        if isinstance(v, str):
            return _TYPE_STRING_MAP.get(v.lower(), 0)
        return int(v)
    enabled: bool = Field(True, description="Whether this entry is active")
    comment: Optional[str] = Field(None, description="Optional user comment")
    date_added: Optional[int] = Field(None, description="Unix timestamp of when entry was added")

    @property
    def list_type(self) -> DomainListType:
        return DomainListType(self.type)

    @property
    def date_added_dt(self) -> Optional[datetime]:
        if self.date_added is not None:
            return datetime.fromtimestamp(self.date_added)
        return None


class DomainListFilters(BaseModel):
    """Filters for fetching domain list entries.

    Note: Pi-hole v6 returns all entries in one response with no server-side
    filtering. list_type is expressed via URL path; all other filtering is
    done client-side.
    """

    list_type: DomainListType = Field(DomainListType.ALLOW, description="Which list to fetch")


class PaginationInfo(BaseModel):
    """Pagination metadata returned by list endpoints."""

    total_count: int = Field(0, ge=0)
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1)
    total_pages: int = Field(1, ge=1)


class DomainListResponse(BaseModel):
    """Paginated response from GET /api/domains."""

    domains: List[DomainListEntry] = Field(default_factory=list)
    pagination: PaginationInfo = Field(default_factory=PaginationInfo)


class DomainAddRequest(BaseModel):
    """Request body for POST /api/domains/{type}/{kind}."""

    domain: str = Field(..., description="Domain name or wildcard")
    type: int = Field(..., description="0=allowlist, 1=denylist")
    kind: str = Field("exact", description="'exact' or 'regex'")
    comment: Optional[str] = Field(None, description="Optional comment")
    enabled: bool = Field(True, description="Whether to enable immediately")

    def to_payload(self) -> dict:
        payload: dict = {"domain": self.domain, "enabled": self.enabled}
        if self.comment:
            payload["comment"] = self.comment
        return payload


class DomainUpdateRequest(BaseModel):
    """Request body for PUT /api/domains/{id} (full update)."""

    comment: Optional[str] = Field(None)
    enabled: Optional[bool] = Field(None)

    def to_payload(self) -> dict:
        payload: dict = {}
        if self.comment is not None:
            payload["comment"] = self.comment
        if self.enabled is not None:
            payload["enabled"] = self.enabled
        return payload


class BulkDomainOperation(BaseModel):
    """Describes a bulk operation across multiple domain entries."""

    domain_ids: List[int] = Field(..., description="IDs of domains to operate on")
    operation: str = Field(..., description="enable | disable | delete")


class DomainImportRequest(BaseModel):
    """Request to import domains from a text file."""

    domains: List[str] = Field(..., description="Raw domain strings from file")
    list_type: DomainListType = Field(..., description="Target list")
    skip_duplicates: bool = Field(True, description="Skip instead of error on duplicates")
    comment: Optional[str] = Field(None, description="Comment to attach to each imported domain")


class DomainImportResult(BaseModel):
    """Summary of a bulk import operation."""

    total: int = 0
    added: int = 0
    skipped_duplicate: int = 0
    failed: int = 0
    errors: List[str] = Field(default_factory=list)
