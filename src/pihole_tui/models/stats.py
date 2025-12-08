"""Statistics data models for Pi-hole dashboard."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class QueryTypeDistribution(BaseModel):
    """Distribution of DNS query types."""

    query_type: str = Field(..., description="DNS record type (A, AAAA, PTR, SRV, ANY, etc.)")
    count: int = Field(..., ge=0, description="Number of queries of this type")
    percent: float = Field(..., ge=0.0, le=100.0, description="Percentage of total queries")


class ReplyTypeDistribution(BaseModel):
    """Distribution of DNS reply types."""

    reply_type: str = Field(..., description="DNS reply type (IP, CNAME, NODATA, NXDOMAIN)")
    count: int = Field(..., ge=0, description="Number of replies of this type")
    percent: float = Field(..., ge=0.0, le=100.0, description="Percentage of total replies")


class DashboardStats(BaseModel):
    """Comprehensive dashboard statistics from Pi-hole."""

    queries_total: int = Field(..., ge=0, description="Total queries today")
    queries_blocked: int = Field(..., ge=0, description="Queries blocked today")
    percent_blocked: float = Field(..., ge=0.0, le=100.0, description="Percentage of queries blocked")
    domains_on_blocklist: int = Field(..., ge=0, description="Total domains on active blocklists")
    clients_active: int = Field(..., ge=0, description="Unique clients seen today")
    clients_ever_seen: int = Field(..., ge=0, description="Total unique clients ever seen")
    queries_forwarded: int = Field(..., ge=0, description="Queries forwarded to upstream DNS")
    queries_cached: int = Field(..., ge=0, description="Queries answered from cache")
    blocking_status: bool = Field(..., description="Current blocking enabled/disabled status")
    gravity_last_updated: Optional[datetime] = Field(None, description="Last gravity update timestamp")
    fetched_at: datetime = Field(default_factory=datetime.now, description="When these stats were fetched")

    query_type_distribution: List[QueryTypeDistribution] = Field(
        default_factory=list,
        description="Distribution of query types"
    )
    reply_type_distribution: List[ReplyTypeDistribution] = Field(
        default_factory=list,
        description="Distribution of reply types"
    )

    @field_validator('percent_blocked', mode='before')
    @classmethod
    def calculate_percent_blocked(cls, v, info):
        """Calculate percentage blocked if not provided."""
        if v is None and 'queries_total' in info.data and 'queries_blocked' in info.data:
            queries_total = info.data['queries_total']
            queries_blocked = info.data['queries_blocked']
            if queries_total > 0:
                return round((queries_blocked / queries_total) * 100, 2)
            return 0.0
        return v

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "queries_total": 15234,
                "queries_blocked": 4521,
                "percent_blocked": 29.67,
                "domains_on_blocklist": 128453,
                "clients_active": 12,
                "clients_ever_seen": 45,
                "queries_forwarded": 8234,
                "queries_cached": 2479,
                "blocking_status": True,
                "gravity_last_updated": "2025-12-08T10:00:00Z",
                "fetched_at": "2025-12-08T15:30:00Z",
                "query_type_distribution": [
                    {"query_type": "A", "count": 9876, "percent": 64.8},
                    {"query_type": "AAAA", "count": 3456, "percent": 22.7},
                    {"query_type": "PTR", "count": 1234, "percent": 8.1}
                ],
                "reply_type_distribution": [
                    {"query_type": "IP", "count": 10234, "percent": 67.2},
                    {"query_type": "CNAME", "count": 2345, "percent": 15.4},
                    {"query_type": "NODATA", "count": 1876, "percent": 12.3}
                ]
            }
        }
