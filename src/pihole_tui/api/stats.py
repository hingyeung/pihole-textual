"""Statistics API endpoints for Pi-hole."""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from pihole_tui.api.client import PiHoleAPIClient
from pihole_tui.constants import API_STATS_SUMMARY, API_STATS_DATABASE_SUMMARY
from pihole_tui.models.stats import (
    DashboardStats,
    QueryTypeDistribution,
    ReplyTypeDistribution,
)

logger = logging.getLogger(__name__)


async def get_summary_stats(client: PiHoleAPIClient) -> DashboardStats:
    """Get summary statistics from Pi-hole.

    Args:
        client: Authenticated API client

    Returns:
        Dashboard statistics

    Raises:
        PiHoleAPIError: If API request fails
    """
    logger.info("Fetching dashboard statistics")

    # Get summary stats - this includes everything we need
    logger.debug(f"Fetching summary from {API_STATS_SUMMARY}")
    summary_response = await client.get(API_STATS_SUMMARY)
    logger.debug(f"Summary response keys: {list(summary_response.keys())}")

    # Note: We don't need /api/stats/database/summary anymore
    # All query types and reply types are included in /api/stats/summary

    # Extract statistics from summary response
    # Pi-hole v6 API structure: {queries: {...}, clients: {...}, gravity: {...}}
    queries_data = summary_response.get("queries", {})
    clients_data = summary_response.get("clients", {})
    gravity_data = summary_response.get("gravity", {})

    logger.debug(f"Queries data keys: {list(queries_data.keys())}")
    logger.debug(f"Clients data keys: {list(clients_data.keys())}")
    logger.debug(f"Gravity data keys: {list(gravity_data.keys())}")

    total_queries = queries_data.get("total", 0)
    queries_blocked = queries_data.get("blocked", 0)
    logger.debug(f"Extracted: total={total_queries}, blocked={queries_blocked}")

    # Parse query type distribution from queries.types
    query_type_dist = []
    query_types_data = queries_data.get("types", {})

    if total_queries > 0 and query_types_data:
        for query_type, count in query_types_data.items():
            if count > 0:  # Only include non-zero types
                percent = round((count / total_queries) * 100, 2)
                query_type_dist.append(
                    QueryTypeDistribution(
                        query_type=query_type,
                        count=count,
                        percent=percent,
                    )
                )

    # Parse reply type distribution from queries.replies
    reply_type_dist = []
    reply_types_data = queries_data.get("replies", {})
    total_replies = sum(reply_types_data.values()) if reply_types_data else 0

    if total_replies > 0:
        for reply_type, count in reply_types_data.items():
            if count > 0:  # Only include non-zero types
                percent = round((count / total_replies) * 100, 2)
                reply_type_dist.append(
                    ReplyTypeDistribution(
                        reply_type=reply_type,
                        count=count,
                        percent=percent,
                    )
                )

    # Parse gravity last updated timestamp
    gravity_last_updated = None
    gravity_updated_ts = gravity_data.get("last_update")
    if gravity_updated_ts:
        try:
            gravity_last_updated = datetime.fromtimestamp(gravity_updated_ts)
        except (ValueError, TypeError):
            pass

    # Build DashboardStats model
    dashboard_stats = DashboardStats(
        queries_total=total_queries,
        queries_blocked=queries_blocked,
        percent_blocked=queries_data.get("percent_blocked", 0.0),
        domains_on_blocklist=gravity_data.get("domains_being_blocked", 0),
        clients_active=clients_data.get("active", 0),
        clients_ever_seen=clients_data.get("total", 0),
        queries_forwarded=queries_data.get("forwarded", 0),
        queries_cached=queries_data.get("cached", 0),
        blocking_status=True,  # We'll determine this from the actual blocking endpoint later
        gravity_last_updated=gravity_last_updated,
        fetched_at=datetime.now(),
        query_type_distribution=query_type_dist,
        reply_type_distribution=reply_type_dist,
    )

    logger.info(f"Dashboard stats created: {dashboard_stats.queries_total} total queries, "
                f"{dashboard_stats.queries_blocked} blocked ({dashboard_stats.percent_blocked}%)")

    return dashboard_stats


async def get_database_summary(client: PiHoleAPIClient) -> dict:
    """Get database summary statistics.

    Args:
        client: Authenticated API client

    Returns:
        Database summary with query type and reply type distributions

    Raises:
        PiHoleAPIError: If API request fails
    """
    response = await client.get(API_STATS_DATABASE_SUMMARY)
    return response
