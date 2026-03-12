"""Query log screen with filtering and export."""
import csv
from datetime import datetime, timedelta
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, HorizontalGroup, Vertical
from textual.screen import Screen
from textual.widgets import Button, Header, Footer, Input, Select, Static, Label
from textual.binding import Binding
from textual.message import Message

from pihole_tui.models.query import QueryLogFilters, QueryLogResponse, QueryLogEntry
from pihole_tui.widgets.query_table import QueryTable
from pihole_tui.api.queries import QueriesAPI

_BLOCKED_STATUSES = {
    "GRAVITY", "BLACKLIST", "REGEX",
    "GRAVITY_CNAME", "BLACKLIST_CNAME", "REGEX_CNAME",
    "EXTERNAL_BLOCKED_IP", "EXTERNAL_BLOCKED_NULL", "EXTERNAL_BLOCKED_NXRA",
    "BLOCKED",
}


class QueryDetailsModal(Screen):
    """Modal screen for displaying detailed query information."""

    BINDINGS = [
        Binding("escape", "dismiss", "Close", show=True),
    ]

    def __init__(self, query: QueryLogEntry):
        """Initialize query details modal.

        Args:
            query: Query entry to display details for
        """
        super().__init__()
        self.query = query

    def compose(self) -> ComposeResult:
        """Compose the modal content."""
        with Container(id="query-details-modal"):
            yield Label("Query Details", id="modal-title")

            yield Static(f"Timestamp: {self.query.timestamp_dt.strftime('%Y-%m-%d %H:%M:%S')}")
            yield Static(f"Client IP: {self.query.client_ip}")
            if self.query.client_hostname:
                yield Static(f"Client Hostname: {self.query.client_hostname}")
            yield Static(f"Domain: {self.query.domain}")
            yield Static(f"Query Type: {self.query.query_type or 'N/A'}")
            yield Static(f"Status: {self.query.status}")
            yield Static(f"Reply Type: {self.query.reply_type or 'N/A'}")
            yield Static(f"Response Time: {self.query.response_time_ms}ms")
            if self.query.blocklist_name:
                yield Static(f"Blocked by: {self.query.blocklist_name}")

            with Horizontal(id="modal-buttons"):
                yield Button("Add to Allowlist", id="add-allowlist", variant="primary")
                yield Button("Add to Blocklist", id="add-blocklist", variant="default")
                yield Button("Close", id="close-modal", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "close-modal":
            self.dismiss()
        elif event.button.id == "add-allowlist":
            self.dismiss(("allowlist", self.query.domain))
        elif event.button.id == "add-blocklist":
            self.dismiss(("blocklist", self.query.domain))

    def action_dismiss(self) -> None:
        """Dismiss the modal."""
        self.dismiss()


class QueryLogScreen(Screen):
    """Query log viewer screen with filtering and export."""

    DEFAULT_CSS = """
    QueryLogScreen #query-log-container {
        height: 1fr;
        layout: vertical;
    }

    QueryLogScreen #filter-bar {
        height: auto;
        layout: horizontal;
    }

    QueryLogScreen #filter-row-1,
    QueryLogScreen #filter-row-2,
    QueryLogScreen #filter-row-3 {
        height: auto;
        width: 1fr;
        padding: 0 1;
    }

    QueryLogScreen #pagination-controls {
        height: 3;
        align: center middle;
    }
    """

    BINDINGS = [
        Binding("q", "app.pop_screen", "Back", show=True),
        Binding("f5", "refresh", "Refresh", show=True),
        Binding("ctrl+e", "export_csv", "Export CSV", show=True),
        Binding("f", "focus_filter", "Filter", show=False),
    ]

    def __init__(self, queries_api: QueriesAPI):
        """Initialize query log screen.

        Args:
            queries_api: Queries API client
        """
        super().__init__()
        self.queries_api = queries_api
        self.filters = QueryLogFilters()
        self.current_response: Optional[QueryLogResponse] = None
        self.refresh_interval = 5  # seconds
        self._refresh_timer = None
        self._client_side_status_filter: Optional[str] = None  # For forwarded/cached filtering
        self._time_range: Optional[str] = None  # Selected time range ("1h", "24h", "7d", or None)

    def compose(self) -> ComposeResult:
        """Compose the query log screen."""
        yield Header()

        with Container(id="query-log-container"):
            # Filter bar
            with Horizontal(id="filter-bar"):
                with Vertical(id="filter-row-1"):
                    with HorizontalGroup():
                        yield Label("Status:")
                        yield Select(
                            [
                                ("All", "all"),
                                ("Blocked", "blocked"),
                                ("Allowed", "allowed"),
                                ("Forwarded", "forwarded"),
                                ("Cached", "cached"),
                            ],
                            value="all",
                            id="status-filter"
                        )

                        yield Label("Time Range:")
                        yield Select(
                            [
                                ("All Time", "all"),
                                ("Last Hour", "1h"),
                                ("Last 24 Hours", "24h"),
                                ("Last 7 Days", "7d"),
                                ("Custom", "custom"),
                            ],
                            value="all",
                            id="time-filter"
                        )

                with Vertical(id="filter-row-2"):
                    with HorizontalGroup():
                        yield Label("Client:")
                        yield Input(placeholder="IP or hostname", id="client-filter")

                        yield Label("Domain:")
                        yield Input(placeholder="Search domain", id="domain-filter")

                with Vertical(id="filter-row-3"):
                    with HorizontalGroup():
                        yield Label("Query Type:")
                        yield Select(
                            [
                                ("All", "all"),
                                ("A", "A"),
                                ("AAAA", "AAAA"),
                                ("PTR", "PTR"),
                                ("SRV", "SRV"),
                                ("TXT", "TXT"),
                                ("ANY", "ANY"),
                            ],
                            value="all",
                            id="query-type-filter"
                        )

                        yield Label("Reply Type:")
                        yield Select(
                            [
                                ("All", "all"),
                                ("IP", "IP"),
                                ("CNAME", "CNAME"),
                                ("NODATA", "NODATA"),
                                ("NXDOMAIN", "NXDOMAIN"),
                            ],
                            value="all",
                            id="reply-type-filter"
                        )

                        yield Button("Apply Filters", id="apply-filters", variant="primary")
                        yield Button("Clear Filters", id="clear-filters", variant="default")

            # Query table
            yield QueryTable(id="query-table")

            # Pagination controls
            with Horizontal(id="pagination-controls"):
                yield Button("◀ Previous", id="prev-page", variant="default", disabled=True)
                yield Static("Page 1 of 1", id="page-info")
                yield Button("Next ▶", id="next-page", variant="default", disabled=True)

        yield Footer()

    async def on_mount(self) -> None:
        """Load initial query data and start auto-refresh."""
        await self.load_queries()
        self._start_auto_refresh()

    def on_unmount(self) -> None:
        """Stop auto-refresh when screen is unmounted."""
        self._stop_auto_refresh()

    def _start_auto_refresh(self) -> None:
        """Start automatic refresh timer."""
        self._refresh_timer = self.set_interval(self.refresh_interval, self.action_refresh)

    def _stop_auto_refresh(self) -> None:
        """Stop automatic refresh timer."""
        if self._refresh_timer:
            self._refresh_timer.stop()
            self._refresh_timer = None

    async def load_queries(self) -> None:
        """Load queries from API with current filters."""
        try:
            # Get table widget
            table = self.query_one("#query-table", QueryTable)

            # Recalculate time range timestamps on every load so the window stays current
            now = datetime.now()
            if self._time_range == "1h":
                self.filters.from_timestamp = now - timedelta(hours=1)
                self.filters.until_timestamp = now
            elif self._time_range == "24h":
                self.filters.from_timestamp = now - timedelta(hours=24)
                self.filters.until_timestamp = now
            elif self._time_range == "7d":
                self.filters.from_timestamp = now - timedelta(days=7)
                self.filters.until_timestamp = now
            elif self._time_range is None:
                self.filters.from_timestamp = None
                self.filters.until_timestamp = None

            # Fetch queries
            response = await self.queries_api.get_queries_with_filters(self.filters)
            self.current_response = response

            # Apply client-side status filter
            # Note: Pi-hole API indicates blocked via blocklist field, not status
            filtered_queries = response.queries
            if self._client_side_status_filter:
                status_filter = self._client_side_status_filter.lower()
                if status_filter == "blocked":
                    filtered_queries = [q for q in response.queries if q.status.upper() in _BLOCKED_STATUSES]
                elif status_filter == "allowed":
                    filtered_queries = [q for q in response.queries if q.status.upper() in ("ALLOWED", "SPECIAL_DOMAIN")]
                elif status_filter == "cached":
                    # Cached queries have status "CACHE" or "CACHE_STALE"
                    filtered_queries = [
                        q for q in response.queries
                        if q.status.upper() in ["CACHE", "CACHED", "CACHE_STALE"]
                    ]
                elif status_filter == "forwarded":
                    # Forwarded queries have status "FORWARD" or "FORWARDED"
                    filtered_queries = [
                        q for q in response.queries
                        if q.status.upper() in ["FORWARD", "FORWARDED"]
                    ]

            # Update table
            table.update_queries(filtered_queries)

            # Update pagination controls
            self._update_pagination_controls()

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to load queries: {e}", exc_info=True)

            # Show just the first line of error to user
            error_msg = str(e).split('\n')[0]
            self.notify(f"Failed to load queries: {error_msg}", severity="error")

    def _update_pagination_controls(self) -> None:
        """Update pagination controls based on current response."""
        if not self.current_response:
            return

        response = self.current_response

        # Update page info
        page_info = self.query_one("#page-info", Static)
        page_info.update(f"Page {response.page} of {response.total_pages} ({response.total_count} queries)")

        # Update button states
        prev_button = self.query_one("#prev-page", Button)
        next_button = self.query_one("#next-page", Button)

        prev_button.disabled = response.page <= 1
        next_button.disabled = response.page >= response.total_pages

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "apply-filters":
            await self.action_apply_filters()
        elif event.button.id == "clear-filters":
            await self.action_clear_filters()
        elif event.button.id == "prev-page":
            await self.action_previous_page()
        elif event.button.id == "next-page":
            await self.action_next_page()

    async def action_apply_filters(self) -> None:
        """Apply current filter values."""
        # Get filter values from UI
        status_filter = self.query_one("#status-filter", Select).value
        time_filter = self.query_one("#time-filter", Select).value
        client_filter = self.query_one("#client-filter", Input).value
        domain_filter = self.query_one("#domain-filter", Input).value
        query_type_filter = self.query_one("#query-type-filter", Select).value
        reply_type_filter = self.query_one("#reply-type-filter", Select).value

        # Update filters model
        self.filters.page = 1  # Reset to first page

        # Status filter
        # Note: Pi-hole API indicates blocked via blocklist field, not status
        # All status filters are done client-side for accuracy
        if status_filter in ["blocked", "allowed", "forwarded", "cached"]:
            self.filters.blocked = None  # Get all from API
            self._client_side_status_filter = status_filter
        else:
            # "all" - no filtering
            self.filters.blocked = None
            self._client_side_status_filter = None

        # Time range filter — store label so load_queries recalculates on every refresh
        if time_filter in ("1h", "24h", "7d"):
            self._time_range = time_filter
        else:
            self._time_range = None
            self.filters.from_timestamp = None
            self.filters.until_timestamp = None

        # Client filter
        self.filters.client = client_filter if client_filter else None

        # Domain filter
        self.filters.domain_pattern = domain_filter if domain_filter else None

        # Query type filter
        self.filters.query_type = query_type_filter if query_type_filter != "all" else None

        # Reply type filter
        self.filters.reply_type = reply_type_filter if reply_type_filter != "all" else None

        # Reload queries
        await self.load_queries()
        self.notify("Filters applied", severity="information")

    async def action_clear_filters(self) -> None:
        """Clear all filters."""
        # Reset filter model and time range selection
        self.filters = QueryLogFilters()
        self._time_range = None

        # Reset UI
        self.query_one("#status-filter", Select).value = "all"
        self.query_one("#time-filter", Select).value = "all"
        self.query_one("#client-filter", Input).value = ""
        self.query_one("#domain-filter", Input).value = ""
        self.query_one("#query-type-filter", Select).value = "all"
        self.query_one("#reply-type-filter", Select).value = "all"

        # Reload queries
        await self.load_queries()
        self.notify("Filters cleared", severity="information")

    async def action_refresh(self) -> None:
        """Refresh query data."""
        await self.load_queries()

    async def action_previous_page(self) -> None:
        """Go to previous page."""
        if self.filters.page > 1:
            self.filters.page -= 1
            await self.load_queries()

    async def action_next_page(self) -> None:
        """Go to next page."""
        if self.current_response and self.filters.page < self.current_response.total_pages:
            self.filters.page += 1
            await self.load_queries()

    async def action_export_csv(self) -> None:
        """Export current query log to CSV."""
        if not self.current_response or not self.current_response.queries:
            self.notify("No queries to export", severity="warning")
            return

        try:
            # Generate filename with timestamp
            filename = f"pihole-queries-{datetime.now().strftime('%Y-%m-%d')}.csv"

            # Write CSV
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)

                # Write header
                writer.writerow([
                    "Timestamp",
                    "Client IP",
                    "Client Hostname",
                    "Domain",
                    "Query Type",
                    "Status",
                    "Reply Type",
                    "Response Time (ms)",
                    "Blocklist"
                ])

                # Write query data
                for query in self.current_response.queries:
                    writer.writerow([
                        query.timestamp_dt.strftime('%Y-%m-%d %H:%M:%S'),
                        query.client_ip,
                        query.client_hostname or "",
                        query.domain,
                        query.query_type or "N/A",
                        query.status,
                        query.reply_type or "N/A",
                        query.response_time_ms,
                        query.blocklist_name or ""
                    ])

            self.notify(f"Exported to {filename}", severity="information")

        except Exception as e:
            self.notify(f"Export failed: {str(e)}", severity="error")

    async def on_query_table_query_selected(self, message: QueryTable.QuerySelected) -> None:
        """Handle query selection to show details modal."""
        result = await self.app.push_screen_wait(QueryDetailsModal(message.query))

        # Handle result from modal (add to allowlist/blocklist)
        if result:
            action, domain = result
            if action == "allowlist":
                self.notify(f"Adding {domain} to allowlist (not yet implemented)", severity="information")
            elif action == "blocklist":
                self.notify(f"Adding {domain} to blocklist (not yet implemented)", severity="information")

    async def on_query_table_add_to_allowlist(self, message: QueryTable.AddToAllowlist) -> None:
        """Handle add to allowlist action."""
        domain = message.query.domain
        self.notify(f"Adding {domain} to allowlist (not yet implemented)", severity="information")

    async def on_query_table_add_to_blocklist(self, message: QueryTable.AddToBlocklist) -> None:
        """Handle add to blocklist action."""
        domain = message.query.domain
        self.notify(f"Adding {domain} to blocklist (not yet implemented)", severity="information")

    def action_focus_filter(self) -> None:
        """Focus the domain filter input."""
        self.query_one("#domain-filter", Input).focus()
