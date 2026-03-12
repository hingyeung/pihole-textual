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
        upstream: Optional[str] = None,
        client_ip: Optional[str] = None,
        domain_pattern: Optional[str] = None,
        query_type: Optional[str] = None,
        reply_type: Optional[str] = None,
        cursor: Optional[int] = None,
        length: int = 50
    ) -> QueryLogResponse:
        """Get query log with filtering and pagination.

        Args:
            from_timestamp: Start of time range
            until_timestamp: End of time range
            upstream: Filter by upstream; special values: 'blocklist', 'cache', 'permitted'
            client_ip: Filter by client IP address
            domain_pattern: Search pattern for domain names
            query_type: Filter by query type (A, AAAA, etc.)
            reply_type: Filter by reply type (IP, CNAME, etc.)
            cursor: DB row ID of the oldest query on the previous page (for pagination)
            length: Number of results to return

        Returns:
            QueryLogResponse with paginated query entries
        """
        params = {
            "length": length,
        }

        if cursor is not None:
            params["cursor"] = cursor

        if from_timestamp is not None:
            params["from"] = int(from_timestamp.timestamp())

        if until_timestamp is not None:
            params["until"] = int(until_timestamp.timestamp())

        if upstream is not None:
            params["upstream"] = upstream

        if client_ip:
            params["client_ip"] = client_ip

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
            upstream=filters.upstream,
            client_ip=filters.client,
            domain_pattern=filters.domain_pattern,
            query_type=filters.query_type,
            reply_type=filters.reply_type,
            cursor=filters.cursor,
            length=filters.limit
        )
