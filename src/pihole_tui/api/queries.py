"""Query log API endpoints."""
from typing import Optional
from datetime import datetime

from pihole_tui.api.client import PiHoleAPIClient
from pihole_tui.models.query import QueryLogFilters, QueryLogResponse, QueryLogEntry


class QueriesAPI:
    """Query log API operations."""

    def __init__(self, client: PiHoleAPIClient):
        """Initialize queries API.

        Args:
            client: Authenticated API client
        """
        self.client = client

    async def get_queries(
        self,
        from_timestamp: Optional[datetime] = None,
        until_timestamp: Optional[datetime] = None,
        blocked: Optional[bool] = None,
        client_filter: Optional[str] = None,
        domain_pattern: Optional[str] = None,
        query_type: Optional[str] = None,
        reply_type: Optional[str] = None,
        page: int = 1,
        limit: int = 50
    ) -> QueryLogResponse:
        """Get query log with filtering and pagination.

        Args:
            from_timestamp: Start of time range
            until_timestamp: End of time range
            blocked: Filter by blocked status (true=blocked only, false=allowed only, null=all)
            client_filter: Filter by client IP or hostname
            domain_pattern: Search pattern for domain names
            query_type: Filter by query type
            reply_type: Filter by reply type
            page: Current page number (1-indexed)
            limit: Items per page

        Returns:
            QueryLogResponse with paginated query entries
        """
        # Build query parameters
        params = {
            "page": page,
            "limit": limit,
        }

        if from_timestamp is not None:
            params["from"] = int(from_timestamp.timestamp())

        if until_timestamp is not None:
            params["until"] = int(until_timestamp.timestamp())

        if blocked is not None:
            params["blocked"] = str(blocked).lower()

        if client_filter:
            params["client"] = client_filter

        if domain_pattern:
            params["domain"] = domain_pattern

        if query_type:
            params["type"] = query_type

        if reply_type:
            params["reply"] = reply_type

        response = await self.client.get("/api/queries", params=params)

        # Parse response into QueryLogResponse model
        return QueryLogResponse(**response)

    async def get_queries_with_filters(self, filters: QueryLogFilters) -> QueryLogResponse:
        """Get query log using filter model.

        Args:
            filters: QueryLogFilters instance with all filter parameters

        Returns:
            QueryLogResponse with paginated query entries
        """
        return await self.get_queries(
            from_timestamp=filters.from_timestamp,
            until_timestamp=filters.until_timestamp,
            blocked=filters.blocked,
            client_filter=filters.client,
            domain_pattern=filters.domain_pattern,
            query_type=filters.query_type,
            reply_type=filters.reply_type,
            page=filters.page,
            limit=filters.limit
        )
