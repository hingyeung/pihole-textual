"""DNS blocking control API endpoints for Pi-hole."""

from typing import Optional

from pihole_tui.api.client import PiHoleAPIClient
from pihole_tui.constants import API_DNS_BLOCKING


async def get_blocking_status(client: PiHoleAPIClient) -> dict:
    """Get current DNS blocking status.

    Args:
        client: Authenticated API client

    Returns:
        Dictionary with blocking status information:
        - blocking: bool - Whether blocking is enabled
        - timer: Optional[int] - Seconds remaining if temporary disable active

    Raises:
        PiHoleAPIError: If API request fails
    """
    response = await client.get(API_DNS_BLOCKING)
    return response


async def set_blocking_status(
    client: PiHoleAPIClient,
    enabled: bool,
    timer: Optional[int] = None,
) -> dict:
    """Enable or disable DNS blocking.

    Args:
        client: Authenticated API client
        enabled: True to enable blocking, False to disable
        timer: Optional timer duration in seconds (only if enabled=False)

    Returns:
        Response from API with updated blocking status

    Raises:
        PiHoleAPIError: If API request fails
    """
    payload = {"blocking": enabled}

    if not enabled and timer is not None:
        payload["timer"] = timer

    response = await client.post(API_DNS_BLOCKING, json_data=payload)
    return response
