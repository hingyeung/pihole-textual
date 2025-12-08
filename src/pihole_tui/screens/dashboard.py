"""Dashboard screen for displaying Pi-hole statistics."""

import logging
from datetime import datetime
from typing import Optional

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Label
from textual.reactive import reactive

from pihole_tui.api.client import PiHoleAPIError
from pihole_tui.api.stats import get_summary_stats
from pihole_tui.api.blocking import get_blocking_status
from pihole_tui.models.stats import DashboardStats
from pihole_tui.widgets.stat_card import (
    StatCard,
    DistributionCard,
    BlockingStatusCard,
)
from pihole_tui.utils.formatters import (
    format_number,
    format_percentage,
    format_datetime,
)
from pihole_tui.constants import DEFAULT_DASHBOARD_REFRESH_INTERVAL

logger = logging.getLogger(__name__)


class DashboardScreen(Screen):
    """Main dashboard screen showing Pi-hole statistics."""

    BINDINGS = [
        ("f5", "refresh", "Refresh"),
        ("q", "query_log", "Query Log"),
        ("d", "domains", "Domains"),
        ("ctrl+b", "toggle_blocking", "Toggle Blocking"),
    ]

    DEFAULT_CSS = """
    DashboardScreen {
        layout: vertical;
    }

    DashboardScreen .dashboard-title {
        dock: top;
        width: 100%;
        height: 3;
        content-align: center middle;
        text-style: bold;
        color: $primary;
        border: solid $primary;
        margin-bottom: 1;
    }

    DashboardScreen .dashboard-grid {
        layout: grid;
        grid-size: 3;
        grid-gutter: 1;
        padding: 0 2;
    }

    DashboardScreen .stats-row {
        layout: horizontal;
        height: auto;
        width: 100%;
        padding: 1 2;
    }

    DashboardScreen .distributions-row {
        layout: horizontal;
        height: auto;
        width: 100%;
        padding: 1 2;
    }

    DashboardScreen .footer-info {
        dock: bottom;
        layout: horizontal;
        height: 3;
        background: $panel;
        padding: 1 2;
    }

    DashboardScreen .footer-info Label {
        width: 1fr;
        color: $text-muted;
    }
    """

    # Reactive properties
    stats: reactive[Optional[DashboardStats]] = reactive(None)
    refresh_interval: reactive[int] = reactive(DEFAULT_DASHBOARD_REFRESH_INTERVAL)
    last_update: reactive[Optional[datetime]] = reactive(None)
    is_loading: reactive[bool] = reactive(False)

    def __init__(self, api_client, **kwargs):
        """Initialize dashboard screen.

        Args:
            api_client: Authenticated API client
            **kwargs: Additional arguments for Screen
        """
        super().__init__(**kwargs)
        self.api_client = api_client
        self._refresh_timer = None

    def compose(self) -> ComposeResult:
        """Compose the dashboard layout."""
        yield Header()

        # Title
        yield Label("Pi-hole Dashboard", classes="dashboard-title")

        # Main statistics grid
        with Container(classes="dashboard-grid"):
            # Row 1: Blocking status and main stats
            with Horizontal(classes="stats-row"):
                yield BlockingStatusCard(id="blocking-status")
                yield StatCard("Total Queries", id="stat-queries-total")
                yield StatCard("Queries Blocked", id="stat-queries-blocked")

            # Row 2: More statistics
            with Horizontal(classes="stats-row"):
                yield StatCard("Percentage Blocked", id="stat-percent-blocked", large=True)
                yield StatCard("Domains on Blocklists", id="stat-domains-blocklist")
                yield StatCard("Active Clients", id="stat-clients-active")

            # Row 3: Query forwarding/caching
            with Horizontal(classes="stats-row"):
                yield StatCard("Queries Forwarded", id="stat-queries-forwarded")
                yield StatCard("Queries Cached", id="stat-queries-cached")
                yield StatCard("Clients Ever Seen", id="stat-clients-ever")

            # Row 4: Distributions
            with Horizontal(classes="distributions-row"):
                yield DistributionCard("Query Type Distribution", id="dist-query-types")
                yield DistributionCard("Reply Type Distribution", id="dist-reply-types")

        # Footer with timestamps
        with Container(classes="footer-info"):
            yield Label("Gravity last updated: --", id="footer-gravity")
            yield Label("Last update: --", id="footer-last-update")

        yield Footer()

    async def on_mount(self) -> None:
        """Handle mount event."""
        # Initial data fetch
        await self.refresh_data()

        # Start auto-refresh timer
        self._refresh_timer = self.set_interval(
            self.refresh_interval, self.refresh_data
        )

    def on_unmount(self) -> None:
        """Handle unmount event."""
        # Stop auto-refresh timer
        if self._refresh_timer:
            self._refresh_timer.stop()

    async def refresh_data(self) -> None:
        """Fetch fresh statistics from Pi-hole API."""
        if self.is_loading:
            return

        self.is_loading = True

        try:
            # Fetch statistics
            logger.debug("Refreshing dashboard statistics")
            stats = await get_summary_stats(self.api_client)
            self.stats = stats
            self.last_update = datetime.now()

            # Update all widgets
            await self.update_widgets()
            logger.debug("Dashboard refresh completed successfully")

        except PiHoleAPIError as e:
            # Log detailed API error
            logger.error(f"API error during refresh: {e.message} (status: {e.status_code})")
            logger.debug(f"Error details: {e.details}")

            # Show user-friendly error notification
            error_msg = f"HTTP {e.status_code}: {e.message}"
            if e.details:
                error_msg += f" - {e.details}"

            self.notify(
                f"Failed to refresh statistics: {error_msg}",
                severity="error",
                timeout=10,
            )

        except Exception as e:
            # Log unexpected error
            logger.exception("Unexpected error during dashboard refresh")

            # Show error notification
            self.notify(
                f"Failed to refresh statistics: {type(e).__name__}: {str(e)}",
                severity="error",
                timeout=10,
            )
        finally:
            self.is_loading = False

    async def update_widgets(self) -> None:
        """Update all dashboard widgets with current stats."""
        if not self.stats:
            return

        stats = self.stats

        # Update blocking status
        blocking_card = self.query_one("#blocking-status", BlockingStatusCard)
        blocking_card.update_status(stats.blocking_status)

        # Update main statistics
        self.query_one("#stat-queries-total", StatCard).update_value(
            format_number(stats.queries_total)
        )
        self.query_one("#stat-queries-blocked", StatCard).update_value(
            format_number(stats.queries_blocked)
        )
        self.query_one("#stat-percent-blocked", StatCard).update_value(
            format_percentage(stats.percent_blocked, decimals=2)
        )
        self.query_one("#stat-domains-blocklist", StatCard).update_value(
            format_number(stats.domains_on_blocklist)
        )
        self.query_one("#stat-clients-active", StatCard).update_value(
            format_number(stats.clients_active)
        )
        self.query_one("#stat-clients-ever", StatCard).update_value(
            format_number(stats.clients_ever_seen)
        )

        # Update forwarded vs cached breakdown
        self.query_one("#stat-queries-forwarded", StatCard).update_value(
            format_number(stats.queries_forwarded)
        )
        self.query_one("#stat-queries-cached", StatCard).update_value(
            format_number(stats.queries_cached)
        )

        # Update distributions
        query_type_card = self.query_one("#dist-query-types", DistributionCard)
        query_type_card.update_distributions(stats.query_type_distribution)

        reply_type_card = self.query_one("#dist-reply-types", DistributionCard)
        reply_type_card.update_distributions(stats.reply_type_distribution)

        # Update footer timestamps
        gravity_label = self.query_one("#footer-gravity", Label)
        if stats.gravity_last_updated:
            gravity_text = f"Gravity last updated: {format_datetime(stats.gravity_last_updated)}"
        else:
            gravity_text = "Gravity last updated: Unknown"
        gravity_label.update(gravity_text)

        last_update_label = self.query_one("#footer-last-update", Label)
        if self.last_update:
            update_text = f"Last update: {format_datetime(self.last_update)}"
        else:
            update_text = "Last update: --"
        last_update_label.update(update_text)

    async def action_refresh(self) -> None:
        """Handle manual refresh action (F5)."""
        await self.refresh_data()
        self.notify("Dashboard refreshed", timeout=2)

    def action_query_log(self) -> None:
        """Navigate to query log screen."""
        self.notify("Query log not yet implemented", severity="warning")

    def action_domains(self) -> None:
        """Navigate to domains screen."""
        self.notify("Domain management not yet implemented", severity="warning")

    def action_toggle_blocking(self) -> None:
        """Toggle blocking status."""
        self.notify("Blocking toggle not yet implemented", severity="warning")

    def update_refresh_interval(self, interval: int) -> None:
        """Update auto-refresh interval.

        Args:
            interval: New refresh interval in seconds
        """
        self.refresh_interval = interval

        # Restart timer with new interval
        if self._refresh_timer:
            self._refresh_timer.stop()

        self._refresh_timer = self.set_interval(interval, self.refresh_data)
        self.notify(f"Refresh interval updated to {interval}s", timeout=2)
