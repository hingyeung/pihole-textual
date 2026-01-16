"""Query log data models."""
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator
import ipaddress


class QueryStatus(str, Enum):
    """DNS query status."""
    ALLOWED = "allowed"
    BLOCKED = "blocked"
    FORWARDED = "forwarded"
    CACHED = "cached"

    # Also accept uppercase versions from API
    ALLOWED_UPPER = "ALLOWED"
    BLOCKED_UPPER = "BLOCKED"
    BLOCKED_UPPER_ALT = "BLOCK"  # API might use 'BLOCK'
    FORWARDED_UPPER = "FORWARDED"
    FORWARD_UPPER = "FORWARD"  # API uses 'FORWARD' not 'FORWARDED'
    CACHED_UPPER = "CACHED"
    CACHE_UPPER = "CACHE"  # API uses 'CACHE' not 'CACHED'


class ReplyInfo(BaseModel):
    """Reply information for a query."""
    model_config = {"extra": "allow"}

    type: Optional[str] = Field(None, description="Reply type (IP, DOMAIN, NXDOMAIN, etc.)")
    time: Optional[float] = Field(None, description="Reply time in seconds")


class ClientInfo(BaseModel):
    """Client information for a query."""
    ip: str = Field(description="Client IP address")
    name: Optional[str] = Field(None, description="Client hostname (if resolved)", alias="hostname")

    @field_validator('ip')
    @classmethod
    def validate_ip(cls, v: str) -> str:
        """Validate client IP address format."""
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid IP address: {v}")

    @property
    def hostname(self) -> Optional[str]:
        """Get hostname (alias for name)."""
        return self.name


class QueryLogEntry(BaseModel):
    """Represents a single DNS query from the log."""
    # Allow both 'time' and 'timestamp' field names (actual API uses 'time')
    # Allow extra fields from API that we don't explicitly model
    model_config = {"populate_by_name": True, "extra": "allow"}

    id: int = Field(description="Unique query ID")
    time: float = Field(description="Unix timestamp when query was made (float with microseconds)", alias="timestamp")
    client: ClientInfo = Field(description="Client information")
    domain: str = Field(description="Queried domain name")
    query_type: Optional[str] = Field(None, description="DNS record type (A, AAAA, etc.)", alias="type")
    status: QueryStatus = Field(description="Query status")
    reply: Optional[ReplyInfo] = Field(None, description="Reply information object")
    response_time_ms: int = Field(0, description="Response time in milliseconds")
    blocklist: Optional[str] = Field(None, description="Name of blocklist that blocked query (if blocked)")

    @field_validator('response_time_ms')
    @classmethod
    def validate_response_time(cls, v: int) -> int:
        """Validate response time is non-negative."""
        if v < 0:
            raise ValueError("Response time must be non-negative")
        return v

    @property
    def timestamp(self) -> float:
        """Get timestamp (alias for time)."""
        return self.time

    @property
    def timestamp_dt(self) -> datetime:
        """Convert Unix timestamp to datetime."""
        return datetime.fromtimestamp(self.time)

    @property
    def client_ip(self) -> str:
        """Get client IP address."""
        return self.client.ip

    @property
    def client_hostname(self) -> Optional[str]:
        """Get client hostname."""
        return self.client.hostname

    @property
    def reply_type(self) -> Optional[str]:
        """Get reply type from reply object."""
        return self.reply.type if self.reply else None

    @property
    def blocklist_name(self) -> Optional[str]:
        """Get blocklist name (alias for blocklist)."""
        return self.blocklist


class QueryLogFilters(BaseModel):
    """Represents active filters for query log."""
    from_timestamp: Optional[datetime] = Field(None, description="Start of time range")
    until_timestamp: Optional[datetime] = Field(None, description="End of time range")
    blocked: Optional[bool] = Field(None, description="Filter by blocked status (true=blocked only, false=allowed only, null=all)")
    client: Optional[str] = Field(None, description="Filter by client IP or hostname")
    domain_pattern: Optional[str] = Field(None, description="Search pattern for domain names")
    query_type: Optional[str] = Field(None, description="Filter by query type")
    reply_type: Optional[str] = Field(None, description="Filter by reply type")
    page: int = Field(1, description="Current page number (1-indexed)")
    limit: int = Field(50, description="Items per page")

    @field_validator('page')
    @classmethod
    def validate_page(cls, v: int) -> int:
        """Validate page is positive integer."""
        if v < 1:
            raise ValueError("Page must be positive integer")
        return v

    @field_validator('limit')
    @classmethod
    def validate_limit(cls, v: int) -> int:
        """Validate limit is between 1-100."""
        if v < 1 or v > 100:
            raise ValueError("Limit must be between 1 and 100")
        return v

    @field_validator('until_timestamp')
    @classmethod
    def validate_time_range(cls, v: Optional[datetime], info) -> Optional[datetime]:
        """Validate time range consistency."""
        if v is not None and 'from_timestamp' in info.data:
            from_ts = info.data['from_timestamp']
            if from_ts is not None and v <= from_ts:
                raise ValueError("until_timestamp must be after from_timestamp")
        return v


class QueryLogResponse(BaseModel):
    """Represents paginated query log response from API."""
    # Allow extra fields that we don't use
    model_config = {"extra": "allow"}

    queries: List[QueryLogEntry] = Field(description="List of query entries for current page")
    # API has these fields at top level, not nested in pagination object
    cursor: Optional[int] = Field(None, description="Cursor for pagination (ID of last query)")
    recordsTotal: int = Field(0, description="Total number of records", alias="total_count")
    recordsFiltered: int = Field(0, description="Number of filtered records")

    @property
    def total_count(self) -> int:
        """Get total count."""
        return self.recordsTotal

    @property
    def page(self) -> int:
        """Get current page (derived from number of queries)."""
        # API doesn't provide page number directly
        return 1

    @property
    def page_size(self) -> int:
        """Get page size (number of queries returned)."""
        return len(self.queries)

    @property
    def total_pages(self) -> int:
        """Calculate total pages (not directly provided by API)."""
        if self.page_size > 0:
            return (self.recordsTotal + self.page_size - 1) // self.page_size
        return 1
