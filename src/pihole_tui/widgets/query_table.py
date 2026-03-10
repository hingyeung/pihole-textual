"""Query log table widget."""
from typing import List, Optional
from datetime import datetime

from textual.app import ComposeResult
from textual.widgets import DataTable, Static
from textual.binding import Binding
from textual.message import Message

from pihole_tui.models.query import QueryLogEntry
from pihole_tui.utils.formatters import format_relative_time


class QueryTable(DataTable):
    """Custom DataTable widget for displaying query log entries with colour coding."""

    DEFAULT_CSS = """
    QueryTable {
        height: 1fr;
    }
    """

    BINDINGS = [
        Binding("enter", "select_query", "View Details", show=True),
        Binding("a", "add_to_allowlist", "Add to Allowlist", show=False),
        Binding("b", "add_to_blocklist", "Add to Blocklist", show=False),
    ]

    class QuerySelected(Message):
        """Message emitted when a query is selected."""
        def __init__(self, query: QueryLogEntry) -> None:
            self.query = query
            super().__init__()

    class AddToAllowlist(Message):
        """Message emitted when user wants to add domain to allowlist."""
        def __init__(self, query: QueryLogEntry) -> None:
            self.query = query
            super().__init__()

    class AddToBlocklist(Message):
        """Message emitted when user wants to add domain to blocklist."""
        def __init__(self, query: QueryLogEntry) -> None:
            self.query = query
            super().__init__()

    def __init__(self, *args, **kwargs):
        """Initialize query table."""
        super().__init__(*args, **kwargs)
        self.queries: List[QueryLogEntry] = []
        self._sort_column: Optional[str] = None
        self._sort_reverse: bool = False

    def on_mount(self) -> None:
        """Set up the table columns."""
        self.cursor_type = "row"
        self.zebra_stripes = True

        # Add columns
        self.add_column("Time", key="timestamp")
        self.add_column("Client", key="client")
        self.add_column("Domain", key="domain")
        self.add_column("Type", key="type")
        self.add_column("Status", key="status")
        self.add_column("Reply", key="reply")
        self.add_column("Response", key="response")

    def update_queries(self, queries: List[QueryLogEntry]) -> None:
        """Update the table with new query entries.

        Args:
            queries: List of query log entries to display
        """
        self.queries = queries
        self.clear()

        for query in queries:
            # Format timestamp (convert from Unix timestamp)
            time_str = format_relative_time(query.timestamp_dt)

            # Format client (prefer hostname if available)
            client_str = query.client_hostname or query.client_ip

            # Format status with colour coding
            status_str = self._format_status(query.status)

            # Format response time
            response_str = f"{query.response_time_ms}ms"

            # Add row with styled status (handle None values)
            self.add_row(
                time_str,
                client_str,
                query.domain,
                query.query_type or "N/A",
                status_str,
                query.reply_type or "N/A",
                response_str,
                key=str(query.id)
            )

            # Apply row styling based on status
            row_key = self.get_row_key_from_id(query.id)
            if row_key is not None:
                self._apply_row_style(row_key, query.status)

    _BLOCKED_STATUSES = {
        "GRAVITY", "BLACKLIST", "REGEX",
        "GRAVITY_CNAME", "BLACKLIST_CNAME", "REGEX_CNAME",
        "EXTERNAL_BLOCKED_IP", "EXTERNAL_BLOCKED_NULL", "EXTERNAL_BLOCKED_NXRA",
        "BLOCKED",
    }
    _CACHED_STATUSES = {"CACHE", "CACHED", "CACHE_STALE"}
    _FORWARDED_STATUSES = {"FORWARD", "FORWARDED"}

    def _format_status(self, status: str) -> str:
        """Format status for display with appropriate symbol.

        Args:
            status: Query status string from API

        Returns:
            Formatted status string
        """
        s = status.upper()
        if s in self._BLOCKED_STATUSES:
            return "✗ Blocked"
        if s in self._CACHED_STATUSES:
            return "⊙ Cached"
        if s in self._FORWARDED_STATUSES:
            return "→ Forwarded"
        if s in ("ALLOWED", "SPECIAL_DOMAIN"):
            return "✓ Allowed"
        return status

    def _apply_row_style(self, row_key: str, status: str) -> None:
        """Apply colour coding to a row based on query status.

        Args:
            row_key: Row key to style
            status: Query status string from API
        """
        s = status.upper()
        if s in self._BLOCKED_STATUSES:
            style = "red"
        elif s in self._CACHED_STATUSES:
            style = "blue"
        elif s in self._FORWARDED_STATUSES:
            style = "yellow"
        elif s in ("ALLOWED", "SPECIAL_DOMAIN"):
            style = "green"
        else:
            style = "white"

        # Apply style to the status column (index 4)
        try:
            self.update_cell(row_key, "status", self._format_status(status), update_width=False)
        except Exception:
            pass  # Ignore styling errors

    def get_row_key_from_id(self, query_id: int) -> Optional[str]:
        """Get row key from query ID.

        Args:
            query_id: Query ID

        Returns:
            Row key or None if not found
        """
        return str(query_id)

    def get_selected_query(self) -> Optional[QueryLogEntry]:
        """Get the currently selected query.

        Returns:
            Selected QueryLogEntry or None
        """
        if not self.queries:
            return None

        # Get the cursor row
        if self.cursor_row < 0 or self.cursor_row >= len(self.queries):
            return None

        return self.queries[self.cursor_row]

    def action_select_query(self) -> None:
        """Action to view query details."""
        query = self.get_selected_query()
        if query:
            self.post_message(self.QuerySelected(query))

    def action_add_to_allowlist(self) -> None:
        """Action to add selected domain to allowlist."""
        query = self.get_selected_query()
        if query:
            self.post_message(self.AddToAllowlist(query))

    def action_add_to_blocklist(self) -> None:
        """Action to add selected domain to blocklist."""
        query = self.get_selected_query()
        if query:
            self.post_message(self.AddToBlocklist(query))

    def sort_by_column(self, column: str, reverse: bool = False) -> None:
        """Sort queries by specified column.

        Args:
            column: Column name to sort by
            reverse: Whether to sort in reverse order
        """
        sort_keys = {
            "timestamp": lambda q: q.timestamp,  # Use Unix timestamp for sorting
            "client": lambda q: q.client_hostname or q.client_ip,
            "domain": lambda q: q.domain,
            "type": lambda q: q.query_type,
            "status": lambda q: q.status,
            "reply": lambda q: q.reply_type,
            "response": lambda q: q.response_time_ms,
        }

        if column in sort_keys:
            self.queries.sort(key=sort_keys[column], reverse=reverse)
            self._sort_column = column
            self._sort_reverse = reverse
            self.update_queries(self.queries)
