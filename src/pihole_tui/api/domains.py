"""Domain list API endpoints for Pi-hole allow/denylist management.

Pi-hole v6 uses path-based filtering:
  GET    /api/domains/{type}/{kind}          — list entries
  POST   /api/domains/{type}/{kind}          — add entry
  PUT    /api/domains/{type}/{kind}/{domain} — update entry
  DELETE /api/domains/{type}/{kind}/{domain} — delete entry

Where {type} is "allow" or "deny", and {kind} is "exact" or "regex".
"""

import logging
from typing import Optional

from pihole_tui.api.client import PiHoleAPIClient, PiHoleAPIError
from pihole_tui.constants import API_DOMAINS, DOMAIN_TYPE_PATHS, DomainListType
from pihole_tui.models.domain import (
    DomainAddRequest,
    DomainListEntry,
    DomainListFilters,
    DomainListResponse,
    DomainUpdateRequest,
    PaginationInfo,
)

logger = logging.getLogger(__name__)


def _type_path(list_type: DomainListType) -> str:
    """Return the URL path segment for a list type: 'allow' or 'deny'."""
    return DOMAIN_TYPE_PATHS[int(list_type)]


def _entry_path(entry: DomainListEntry) -> str:
    """Return the full URL path for a specific domain entry."""
    type_str = DOMAIN_TYPE_PATHS.get(entry.type, "allow")
    return f"{API_DOMAINS}/{type_str}/{entry.kind}/{entry.domain}"


async def get_domains(
    client: PiHoleAPIClient,
    filters: DomainListFilters,
) -> DomainListResponse:
    """Fetch domain list entries for the given list type.

    Args:
        client: Authenticated API client.
        filters: Query filters (list type, optional search/enabled filter).

    Returns:
        Domain list response (no server-side pagination — all entries returned).
    """
    type_str = _type_path(filters.list_type)
    endpoint = f"{API_DOMAINS}/{type_str}"
    response = await client.get(endpoint)

    domains = [DomainListEntry(**d) for d in response.get("domains", [])]
    # Pi-hole v6 returns all entries in one response — synthesise pagination info
    pagination = PaginationInfo(
        total_count=len(domains),
        page=1,
        page_size=len(domains) or 1,
        total_pages=1,
    )
    return DomainListResponse(domains=domains, pagination=pagination)


async def add_domain(
    client: PiHoleAPIClient,
    request: DomainAddRequest,
) -> DomainListEntry:
    """Add a new domain to the allow or denylist.

    Args:
        client: Authenticated API client.
        request: Domain add request.

    Returns:
        Created domain entry.

    Raises:
        PiHoleAPIError: 409 if domain already exists, 400 for invalid format.
    """
    type_str = _type_path(DomainListType(request.type))
    endpoint = f"{API_DOMAINS}/{type_str}/{request.kind}"
    payload = request.to_payload()
    response = await client.post(endpoint, json_data=payload)
    # Response wraps result under "domains" list on success
    domains = response.get("domains", [])
    if domains:
        return DomainListEntry(**domains[0])
    # Fallback: try to parse the response directly
    return DomainListEntry(**response)


async def update_domain(
    client: PiHoleAPIClient,
    entry: DomainListEntry,
    request: DomainUpdateRequest,
) -> DomainListEntry:
    """Update a domain entry (comment and/or enabled status).

    Args:
        client: Authenticated API client.
        entry: The existing domain entry (provides type, kind, domain for URL).
        request: Fields to update.

    Returns:
        Updated domain entry.
    """
    endpoint = _entry_path(entry)
    payload = request.to_payload()
    response = await client.put(endpoint, json_data=payload)
    domains = response.get("domains", [])
    if domains:
        return DomainListEntry(**domains[0])
    return DomainListEntry(**response)


async def patch_domain(
    client: PiHoleAPIClient,
    entry: DomainListEntry,
    enabled: bool,
) -> DomainListEntry:
    """Toggle the enabled status of a domain entry.

    Args:
        client: Authenticated API client.
        entry: The existing domain entry.
        enabled: New enabled state.

    Returns:
        Updated domain entry.
    """
    endpoint = _entry_path(entry)
    response = await client.put(endpoint, json_data={"enabled": enabled})
    domains = response.get("domains", [])
    if domains:
        return DomainListEntry(**domains[0])
    return DomainListEntry(**response)


async def delete_domain(
    client: PiHoleAPIClient,
    entry: DomainListEntry,
) -> bool:
    """Delete a domain entry.

    Args:
        client: Authenticated API client.
        entry: The domain entry to delete (provides type, kind, domain for URL).

    Returns:
        True on success.
    """
    endpoint = _entry_path(entry)
    await client.delete(endpoint)
    return True
