"""Constants, enums, and default values for Pi-hole TUI."""

from enum import Enum, IntEnum


# API Configuration
DEFAULT_API_PORT = 8080
DEFAULT_API_TIMEOUT = 30  # seconds
DEFAULT_SESSION_VALIDITY = 300  # seconds (5 minutes)
SESSION_RENEWAL_THRESHOLD = 0.8  # Renew at 80% of validity period

# API Endpoints
API_AUTH_LOGIN = "/api/auth"
API_AUTH_LOGOUT = "/api/auth"
API_STATS_SUMMARY = "/api/stats/summary"
API_STATS_DATABASE_SUMMARY = "/api/stats/database/summary"
API_DNS_BLOCKING = "/api/dns/blocking"
API_QUERIES = "/api/queries"
API_DOMAINS = "/api/domains"
# Pi-hole v6 uses path-based type filtering with "allow" and "deny"
DOMAIN_TYPE_PATHS = {0: "allow", 1: "deny"}  # DomainListType.ALLOW=0, BLOCK=1

# Configuration Paths
CONFIG_DIR_NAME = "pihole-tui"
CONFIG_FILE_NAME = "config.toml"
CONNECTIONS_FILE_NAME = "connections.enc"
LOG_FILE_NAME = "pihole-tui.log"

# UI Defaults
DEFAULT_DASHBOARD_REFRESH_INTERVAL = 5  # seconds
DEFAULT_QUERY_LOG_REFRESH_INTERVAL = 5  # seconds
DEFAULT_QUERY_LOG_PAGE_SIZE = 50
DEFAULT_DATE_FORMAT = "relative"  # or "absolute"
DEFAULT_THEME = "textual-dark"

# Refresh Interval Options
DASHBOARD_REFRESH_OPTIONS = [5, 10, 30, 60]  # seconds
QUERY_LOG_REFRESH_OPTIONS = [3, 5, 10]  # seconds
QUERY_LOG_PAGE_SIZE_OPTIONS = [25, 50, 100]

# Blocking Timer Presets (seconds)
BLOCKING_TIMER_PRESETS = [
    30,    # 30 seconds
    60,    # 1 minute
    300,   # 5 minutes
    900,   # 15 minutes
    1800,  # 30 minutes
    3600,  # 1 hour
]

# Performance Limits
MAX_BULK_OPERATIONS = 100  # Maximum domains in bulk operation
MAX_MEMORY_MB = 150  # Maximum memory usage target
MIN_TERMINAL_WIDTH = 80
MIN_TERMINAL_HEIGHT = 24

# Responsive Layout Breakpoints
LAYOUT_BREAKPOINT_3COL = 120  # 3 columns at 120+ characters
LAYOUT_BREAKPOINT_2COL = 80   # 2 columns at 80-119 characters
# Below 80 = 1 column (already MIN_TERMINAL_WIDTH)

# Retry Configuration
MAX_RETRY_ATTEMPTS = 3
RETRY_BACKOFF_BASE = 1  # seconds (exponential backoff: 1s, 2s, 4s)


class QueryStatus(str, Enum):
    """DNS query status types."""

    ALLOWED = "allowed"
    BLOCKED = "blocked"
    FORWARDED = "forwarded"
    CACHED = "cached"


class DomainListType(IntEnum):
    """Domain list types for Pi-hole."""

    ALLOW = 0  # Allowlist (whitelist)
    BLOCK = 1  # Blocklist (blacklist)


class BulkOperationType(str, Enum):
    """Bulk operation types for domain lists."""

    ENABLE = "enable"
    DISABLE = "disable"
    DELETE = "delete"


class ConnectionStatus(str, Enum):
    """Connection status to Pi-hole."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"


# DNS Query Types (common types)
COMMON_QUERY_TYPES = ["A", "AAAA", "PTR", "SRV", "TXT", "ANY", "CNAME", "MX", "NS", "SOA"]

# DNS Reply Types (common types)
COMMON_REPLY_TYPES = ["IP", "CNAME", "NODATA", "NXDOMAIN"]

# Colour Codes for Query Status
QUERY_STATUS_COLOURS = {
    QueryStatus.ALLOWED: "green",
    QueryStatus.BLOCKED: "red",
    QueryStatus.CACHED: "blue",
    QueryStatus.FORWARDED: "yellow",
}

# Blocking Status Colours
BLOCKING_STATUS_COLOURS = {
    "enabled": "green",
    "disabled": "red",
    "temp_disabled": "yellow",
}
