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

    # Get summary stats
    logger.debug(f"Fetching summary from {API_STATS_SUMMARY}")
    summary_response = await client.get(API_STATS_SUMMARY)
    logger.debug(f"Summary response keys: {list(summary_response.keys())}")

    # Get database summary for query type/reply type distributions
    # Pi-hole requires from/until parameters - use last 24 hours
    now = datetime.now()
    from_timestamp = int((now - timedelta(days=1)).timestamp())
    until_timestamp = int(now.timestamp())

    logger.debug(f"Fetching database summary from {API_STATS_DATABASE_SUMMARY} (from={from_timestamp}, until={until_timestamp})")
    database_response = await client.get(
        API_STATS_DATABASE_SUMMARY,
        params={"from": from_timestamp, "until": until_timestamp}
    )
    logger.debug(f"Database response keys: {list(database_response.keys())}")

    # Extract statistics from summary response
    stats_data = summary_response.get("stats", {})

    # Parse query type distribution
    query_type_dist = []
    query_types_data = database_response.get("query_types", {})
    total_queries = stats_data.get("queries_all_types", 0)

    if total_queries > 0:
        for query_type, count in query_types_data.items():
            percent = round((count / total_queries) * 100, 2)
            query_type_dist.append(
                QueryTypeDistribution(
                    query_type=query_type,
                    count=count,
                    percent=percent,
                )
            )

    # Parse reply type distribution
    reply_type_dist = []
    reply_types_data = database_response.get("reply_types", {})
    total_replies = sum(reply_types_data.values()) if reply_types_data else 0

    if total_replies > 0:
        for reply_type, count in reply_types_data.items():
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
    gravity_updated_ts = stats_data.get("gravity_last_updated")
    if gravity_updated_ts:
        try:
            gravity_last_updated = datetime.fromtimestamp(gravity_updated_ts)
        except (ValueError, TypeError):
            pass

    # Build DashboardStats model
    dashboard_stats = DashboardStats(
        queries_total=stats_data.get("queries_all_types", 0),
        queries_blocked=stats_data.get("queries_blocked", 0),
        percent_blocked=stats_data.get("percent_blocked", 0.0),
        domains_on_blocklist=stats_data.get("domains_being_blocked", 0),
        clients_active=stats_data.get("clients_active", 0),
        clients_ever_seen=stats_data.get("clients_ever_seen", 0),
        queries_forwarded=stats_data.get("queries_forwarded", 0),
        queries_cached=stats_data.get("queries_cached", 0),
        blocking_status=stats_data.get("status", "enabled") == "enabled",
        gravity_last_updated=gravity_last_updated,
        fetched_at=datetime.now(),
        query_type_distribution=query_type_dist,
        reply_type_distribution=reply_type_dist,
    )

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
