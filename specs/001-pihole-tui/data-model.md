# Data Model: Pi-hole TUI Management Interface

**Feature**: Pi-hole TUI Management Interface
**Date**: 2025-12-05
**Purpose**: Define data structures for configuration, API requests/responses, and application state

## Overview

Data models are implemented using Pydantic for validation, type safety, and JSON serialisation. Models are organised into functional areas matching the API client structure.

## Configuration Models

### ConnectionProfile

Represents a saved Pi-hole connection configuration.

**Fields**:
- `name`: str - Profile display name (e.g., "Home Pi-hole", "Office Pi-hole")
- `hostname`: str - Pi-hole hostname or IP address
- `port`: int - API port (default: 8080)
- `use_https`: bool - Whether to use HTTPS (default: false for Pi-hole v6)
- `saved_password`: Optional[str] - Encrypted password (if "remember credentials" enabled)
- `totp_enabled`: bool - Whether 2FA/TOTP is enabled (default: false)
- `last_used`: datetime - Last connection timestamp
- `is_active`: bool - Currently active connection

**Validation**:
- `hostname`: Valid hostname or IP address format
- `port`: Integer between 1-65535
- `name`: Non-empty string, max 50 characters

**Relationships**:
- One active ConnectionProfile per application session
- Multiple saved profiles supported

---

### UserPreferences

Represents user-configurable application settings.

**Fields**:
- `dashboard_refresh_interval`: int - Dashboard auto-refresh interval in seconds (5, 10, 30, 60)
- `query_log_refresh_interval`: int - Query log refresh interval in seconds (3, 5, 10)
- `query_log_page_size`: int - Number of queries per page (25, 50, 100)
- `date_format`: str - Date display format ("relative" or "absolute")
- `confirm_blocking_changes`: bool - Show confirmation before enabling/disabling blocking
- `confirm_domain_deletes`: bool - Show confirmation before deleting domains
- `theme`: str - UI theme name (default: "textual-dark")

**Validation**:
- `dashboard_refresh_interval`: Must be in [5, 10, 30, 60]
- `query_log_refresh_interval`: Must be in [3, 5, 10]
- `query_log_page_size`: Must be in [25, 50, 100]
- `date_format`: Must be "relative" or "absolute"

**Defaults**:
- dashboard_refresh_interval: 5
- query_log_refresh_interval: 5
- query_log_page_size: 50
- date_format: "relative"
- confirm_blocking_changes: true
- confirm_domain_deletes: true
- theme: "textual-dark"

---

## Authentication Models

### AuthRequest

Represents authentication request payload.

**Fields**:
- `password`: str - Pi-hole admin password
- `totp`: Optional[str] - TOTP code (if 2FA enabled, 6 digits)

**Validation**:
- `password`: Non-empty string
- `totp`: If provided, exactly 6 digits

---

### AuthResponse

Represents authentication response from Pi-hole API.

**Fields**:
- `session`: SessionInfo - Session information

---

### SessionInfo

Nested within AuthResponse, represents active session details.

**Fields**:
- `sid`: str - Session ID for subsequent API requests
- `validity`: int - Session validity duration in seconds
- `expires_at`: datetime - Calculated expiry timestamp (derived from validity)

**Derived**:
- `expires_at = current_time + timedelta(seconds=validity)`

---

### SessionState

Represents current application session state (in-memory, not persisted).

**Fields**:
- `sid`: Optional[str] - Active session ID
- `expires_at`: Optional[datetime] - Session expiry timestamp
- `connection_profile`: Optional[ConnectionProfile] - Active connection profile
- `is_authenticated`: bool - Whether currently authenticated
- `last_renewal`: Optional[datetime] - Last session renewal timestamp
- `pi_hole_version`: Optional[str] - Connected Pi-hole version (from initial handshake)

**State Transitions**:
- `NOT_AUTHENTICATED` → `AUTHENTICATED`: After successful login
- `AUTHENTICATED` → `NOT_AUTHENTICATED`: On logout, session expiry, or connection failure
- `AUTHENTICATED` → `AUTHENTICATED`: On session renewal

---

## Statistics Models

### DashboardStats

Represents comprehensive dashboard statistics from Pi-hole.

**Fields**:
- `queries_total`: int - Total queries today
- `queries_blocked`: int - Queries blocked today
- `percent_blocked`: float - Percentage of queries blocked (0-100)
- `domains_on_blocklist`: int - Total domains on active blocklists
- `clients_active`: int - Unique clients seen today
- `clients_ever_seen`: int - Total unique clients ever seen
- `queries_forwarded`: int - Queries forwarded to upstream DNS
- `queries_cached`: int - Queries answered from cache
- `blocking_status`: bool - Current blocking enabled/disabled status
- `gravity_last_updated`: datetime - Last gravity update timestamp
- `fetched_at`: datetime - When these stats were fetched

**Derived**:
- `percent_blocked = (queries_blocked / queries_total * 100) if queries_total > 0 else 0`

---

### QueryTypeDistribution

Represents distribution of DNS query types.

**Fields**:
- `query_type`: str - DNS record type (A, AAAA, PTR, SRV, ANY, etc.)
- `count`: int - Number of queries of this type
- `percent`: float - Percentage of total queries

**Common Types**:
- A (IPv4 address)
- AAAA (IPv6 address)
- PTR (Reverse DNS)
- SRV (Service record)
- TXT (Text record)
- ANY (All records)

---

### ReplyTypeDistribution

Represents distribution of DNS reply types.

**Fields**:
- `reply_type`: str - DNS reply type
- `count`: int - Number of replies of this type
- `percent`: float - Percentage of total replies

**Common Types**:
- IP (Successful resolution to IP)
- CNAME (Canonical name redirect)
- NODATA (Domain exists but no data for query type)
- NXDOMAIN (Domain does not exist)

---

## Query Log Models

### QueryLogEntry

Represents a single DNS query from the log.

**Fields**:
- `id`: int - Unique query ID
- `timestamp`: datetime - When query was made
- `client_ip`: str - Client IP address
- `client_hostname`: Optional[str] - Client hostname (if resolved)
- `domain`: str - Queried domain name
- `query_type`: str - DNS record type (A, AAAA, etc.)
- `status`: QueryStatus - Query status (enum)
- `reply_type`: str - DNS reply type
- `response_time_ms`: int - Response time in milliseconds
- `blocklist_name`: Optional[str] - Name of blocklist that blocked query (if blocked)

**Enums**:
```python
class QueryStatus(str, Enum):
    ALLOWED = "allowed"
    BLOCKED = "blocked"
    FORWARDED = "forwarded"
    CACHED = "cached"
```

**Validation**:
- `client_ip`: Valid IPv4 or IPv6 address format
- `domain`: Valid domain name format
- `response_time_ms`: Non-negative integer
- `timestamp`: Valid datetime

---

### QueryLogFilters

Represents active filters for query log.

**Fields**:
- `from_timestamp`: Optional[datetime] - Start of time range
- `until_timestamp`: Optional[datetime] - End of time range
- `blocked`: Optional[bool] - Filter by blocked status (true=blocked only, false=allowed only, null=all)
- `client`: Optional[str] - Filter by client IP or hostname
- `domain_pattern`: Optional[str] - Search pattern for domain names
- `query_type`: Optional[str] - Filter by query type
- `reply_type`: Optional[str] - Filter by reply type
- `page`: int - Current page number (1-indexed)
- `limit`: int - Items per page

**Defaults**:
- page: 1
- limit: 50
- All other filters: None (no filter)

**Validation**:
- `page`: Positive integer
- `limit`: Integer between 1-100
- `from_timestamp` < `until_timestamp` (if both provided)

---

### QueryLogResponse

Represents paginated query log response from API.

**Fields**:
- `queries`: List[QueryLogEntry] - List of query entries for current page
- `total_count`: int - Total number of matching queries
- `page`: int - Current page number
- `page_size`: int - Number of items per page
- `total_pages`: int - Total number of pages

**Derived**:
- `total_pages = ceil(total_count / page_size)`

---

## Blocking Control Models

### BlockingState

Represents current DNS blocking state.

**Fields**:
- `blocking_enabled`: bool - Whether blocking is enabled
- `timer_active`: bool - Whether temporary disable timer is active
- `timer_expires_at`: Optional[datetime] - When timer expires (if active)
- `timer_duration_seconds`: Optional[int] - Original timer duration
- `disable_reason`: Optional[str] - Reason for temporary disable (optional comment)

**State Transitions**:
- `ENABLED` → `DISABLED_PERMANENT`: User disables without timer
- `ENABLED` → `DISABLED_TEMPORARY`: User disables with timer
- `DISABLED_TEMPORARY` → `ENABLED`: Timer expires or user manually re-enables
- `DISABLED_PERMANENT` → `ENABLED`: User manually enables

**Validation**:
- If `timer_active` is true, `timer_expires_at` and `timer_duration_seconds` must be provided
- `timer_duration_seconds`: Positive integer (in seconds)

---

### BlockingToggleRequest

Represents request to change blocking state.

**Fields**:
- `blocking`: bool - Target blocking state (true=enable, false=disable)
- `timer`: Optional[int] - Temporary disable duration in seconds (only if blocking=false)
- `reason`: Optional[str] - Optional reason/comment for disable

**Validation**:
- `timer`: If provided, positive integer between 1-3600 (max 1 hour)
- `reason`: Max 200 characters

**Preset Durations** (seconds):
- 30 (30 seconds)
- 60 (1 minute)
- 300 (5 minutes)
- 900 (15 minutes)
- 1800 (30 minutes)
- 3600 (1 hour)

---

## Domain Management Models

### DomainListEntry

Represents a single entry in allowlist or blocklist.

**Fields**:
- `id`: int - Unique domain list entry ID
- `domain`: str - Domain name or wildcard pattern
- `list_type`: DomainListType - Allow or block list (enum)
- `enabled`: bool - Whether this entry is active
- `comment`: Optional[str] - User comment/description
- `date_added`: datetime - When entry was added
- `added_by`: Optional[str] - User who added (future enhancement, optional)

**Enums**:
```python
class DomainListType(int, Enum):
    ALLOW = 0  # Whitelist
    BLOCK = 1  # Blacklist
```

**Validation**:
- `domain`: Valid domain format or wildcard pattern (*.example.com)
- `comment`: Max 255 characters
- Wildcard patterns: Must start with `*.` and have valid domain after

---

### DomainListFilters

Represents filters for domain list view.

**Fields**:
- `list_type`: DomainListType - Allow or block list
- `search_pattern`: Optional[str] - Search term for filtering domains
- `enabled_only`: bool - Show only enabled entries
- `page`: int - Current page number
- `limit`: int - Items per page

**Defaults**:
- page: 1
- limit: 50
- enabled_only: false

---

### DomainListResponse

Represents paginated domain list response.

**Fields**:
- `domains`: List[DomainListEntry] - List of domain entries
- `total_count`: int - Total matching entries
- `page`: int - Current page
- `page_size`: int - Items per page
- `total_pages`: int - Total pages

---

### DomainAddRequest

Represents request to add new domain to list.

**Fields**:
- `domain`: str - Domain name or wildcard pattern
- `type`: DomainListType - Allow (0) or block (1)
- `comment`: Optional[str] - User comment
- `enabled`: bool - Whether entry is enabled (default: true)

**Validation**:
- `domain`: Valid domain or wildcard pattern
- `comment`: Max 255 characters
- Domain not already in the same list (duplicate check)

---

### DomainUpdateRequest

Represents request to update existing domain entry.

**Fields**:
- `domain`: Optional[str] - Updated domain name
- `comment`: Optional[str] - Updated comment
- `enabled`: Optional[bool] - Updated enabled status

**Validation**:
- At least one field must be provided
- Domain validation if domain is being updated

---

### BulkDomainOperation

Represents bulk operation on multiple domains.

**Fields**:
- `domain_ids`: List[int] - List of domain entry IDs to operate on
- `operation`: BulkOperationType - Type of operation (enum)

**Enums**:
```python
class BulkOperationType(str, Enum):
    ENABLE = "enable"
    DISABLE = "disable"
    DELETE = "delete"
```

**Validation**:
- `domain_ids`: Non-empty list, max 100 IDs
- All IDs must exist and belong to same list type

---

### DomainImportRequest

Represents bulk domain import from file.

**Fields**:
- `domains`: List[str] - List of domains to import
- `list_type`: DomainListType - Target list (allow or block)
- `enabled`: bool - Whether imported entries should be enabled (default: true)
- `skip_duplicates`: bool - Skip domains already in list (default: true)

**Validation**:
- `domains`: Non-empty list, max 100 domains per import
- Each domain validated individually
- Duplicates detected and skipped if `skip_duplicates=true`

---

### DomainImportResult

Represents result of bulk domain import.

**Fields**:
- `total_requested`: int - Total domains in import request
- `successfully_added`: int - Number of domains added
- `skipped_duplicates`: int - Number skipped (already exist)
- `failed_validation`: int - Number with invalid format
- `errors`: List[str] - List of error messages for failed domains

---

## Error Models

### APIError

Represents API error response.

**Fields**:
- `error`: str - Error type/code
- `message`: str - Human-readable error message
- `details`: Optional[dict] - Additional error details
- `status_code`: int - HTTP status code

**Common Error Types**:
- `authentication_failed`: Invalid credentials
- `session_expired`: SID no longer valid
- `not_found`: Resource not found
- `validation_error`: Invalid request parameters
- `server_error`: Pi-hole API internal error
- `network_error`: Connection/timeout issues

---

## State Management Notes

**Application State Hierarchy**:
1. `SessionState` - Active session and authentication (in-memory only)
2. `ConnectionProfile` - Saved connection configs (encrypted file)
3. `UserPreferences` - UI preferences (config file)
4. `DashboardStats`, `QueryLogEntry`, etc. - Transient API data (not persisted)

**Persistence Strategy**:
- `ConnectionProfile` → Encrypted file (`~/.config/pihole-tui/connections.enc`)
- `UserPreferences` → TOML file (`~/.config/pihole-tui/config.toml`)
- `SessionState` → In-memory only (not persisted between app restarts)
- API response data → Not persisted (fetched on demand)

**Validation Points**:
- User input → Validated by Pydantic models before API submission
- API responses → Validated by Pydantic models on receipt
- Configuration file load → Validated on parse, graceful fallback to defaults on error

## Model Relationships Diagram

```
┌─────────────────────┐
│ SessionState        │──┐
│ - sid               │  │
│ - expires_at        │  │
│ - is_authenticated  │  │
└─────────────────────┘  │ references
                         │
                         ▼
┌─────────────────────┐  ┌──────────────────────┐
│ ConnectionProfile   │  │ UserPreferences      │
│ - hostname          │  │ - refresh_intervals  │
│ - port              │  │ - page_sizes         │
│ - saved_password    │  │ - confirmations      │
└─────────────────────┘  └──────────────────────┘
        │
        │ authenticates to
        ▼
┌─────────────────────┐
│ Pi-hole API         │
└─────────────────────┘
        │
        ├──► DashboardStats
        ├──► QueryLogEntry
        ├──► BlockingState
        └──► DomainListEntry
```

## Implementation Notes

- All models use Pydantic `BaseModel` for validation and serialisation
- Datetime fields use `datetime` with timezone awareness (UTC for API, local for display)
- Optional fields use `Optional[Type]` with `None` default
- Enums used for fixed choice fields (QueryStatus, DomainListType, BulkOperationType)
- `Config` class in models for JSON schema generation and alias handling
- Snake_case for Python field names, map to API's camelCase/snake_case as needed using Pydantic `Field(alias=...)` where API differs
