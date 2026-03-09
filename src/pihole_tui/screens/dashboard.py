"""Dashboard screen for displaying Pi-hole statistics and blocking control."""

import logging
from datetime import datetime
from typing import Optional, Tuple

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Grid, Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import ModalScreen, Screen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    Static,
)

from pihole_tui.api.blocking import get_blocking_status, set_blocking_status
from pihole_tui.api.client import PiHoleAPIError, NetworkError
from pihole_tui.api.stats import get_summary_stats
from pihole_tui.constants import (
    BLOCKING_TIMER_PRESETS,
    DEFAULT_DASHBOARD_REFRESH_INTERVAL,
    LAYOUT_BREAKPOINT_2COL,
    LAYOUT_BREAKPOINT_3COL,
)
from pihole_tui.models.blocking import BlockingToggleRequest
from pihole_tui.models.stats import DashboardStats
from pihole_tui.utils.formatters import (
    format_datetime,
    format_duration,
    format_number,
    format_percentage,
)
from pihole_tui.widgets.countdown_timer import CountdownTimer
from pihole_tui.widgets.stat_card import (
    BlockingStatusCard,
    DistributionCard,
    StatCard,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Dialogs
# ---------------------------------------------------------------------------

class BlockingConfirmDialog(ModalScreen):
    """Confirmation dialog for toggling DNS blocking on or off.

    Dismisses with ``True`` when the user confirms, ``False`` otherwise.
    """

    DEFAULT_CSS = """
    BlockingConfirmDialog {
        align: center middle;
    }

    BlockingConfirmDialog #dialog {
        width: 50;
        height: auto;
        border: solid $warning;
        background: $surface;
        padding: 1 2;
    }

    BlockingConfirmDialog #dialog-title {
        text-style: bold;
        text-align: center;
        width: 100%;
        padding-bottom: 1;
    }

    BlockingConfirmDialog #dialog-body {
        text-align: center;
        width: 100%;
        padding-bottom: 1;
    }

    BlockingConfirmDialog #buttons {
        layout: horizontal;
        align: center middle;
        height: auto;
        width: 100%;
    }

    BlockingConfirmDialog Button {
        margin: 0 1;
    }
    """

    def __init__(self, currently_enabled: bool, **kwargs) -> None:
        super().__init__(**kwargs)
        self._currently_enabled = currently_enabled

    def compose(self) -> ComposeResult:
        action = "Disable" if self._currently_enabled else "Enable"
        with Vertical(id="dialog"):
            yield Label(f"{action} DNS Blocking", id="dialog-title")
            yield Label(
                f"Are you sure you want to {action.lower()} DNS blocking?",
                id="dialog-body",
            )
            with Horizontal(id="buttons"):
                yield Button(action, variant="warning", id="btn-confirm")
                yield Button("Cancel", variant="default", id="btn-cancel")

    @on(Button.Pressed, "#btn-confirm")
    def confirm(self) -> None:
        self.dismiss(True)

    @on(Button.Pressed, "#btn-cancel")
    def cancel(self) -> None:
        self.dismiss(False)


class DurationDialog(ModalScreen):
    """Duration selection dialog for temporarily disabling blocking.

    Dismisses with a ``(seconds, reason)`` tuple, ``None`` for permanent
    disable, or raises ``False`` if the user cancels.
    """

    DEFAULT_CSS = """
    DurationDialog {
        align: center middle;
    }

    DurationDialog #dialog {
        width: 60;
        height: auto;
        border: solid $warning;
        background: $surface;
        padding: 1 2;
    }

    DurationDialog #dialog-title {
        text-style: bold;
        text-align: center;
        width: 100%;
        padding-bottom: 1;
    }

    DurationDialog #presets {
        layout: horizontal;
        height: auto;
        width: 100%;
        padding-bottom: 1;
    }

    DurationDialog .preset-btn {
        margin: 0 1 0 0;
    }

    DurationDialog #custom-row {
        layout: horizontal;
        height: auto;
        width: 100%;
        padding-bottom: 1;
    }

    DurationDialog #custom-label {
        width: auto;
        padding: 1 1 0 0;
    }

    DurationDialog #custom-input {
        width: 1fr;
    }

    DurationDialog #reason-label {
        padding-bottom: 0;
    }

    DurationDialog #reason-input {
        width: 100%;
        margin-bottom: 1;
    }

    DurationDialog #buttons {
        layout: horizontal;
        align: center middle;
        height: auto;
        width: 100%;
    }

    DurationDialog Button {
        margin: 0 1;
    }
    """

    # Preset labels mapped to their second values from constants
    _PRESET_LABELS = ["30s", "1m", "5m", "15m", "30m", "1h"]

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("How long to disable blocking?", id="dialog-title")

            # Preset buttons
            with Horizontal(id="presets"):
                for label, seconds in zip(self._PRESET_LABELS, BLOCKING_TIMER_PRESETS):
                    yield Button(
                        label,
                        variant="warning",
                        id=f"preset-{seconds}",
                        classes="preset-btn",
                    )

            # Custom duration
            with Horizontal(id="custom-row"):
                yield Label("Custom (seconds):", id="custom-label")
                yield Input(placeholder="e.g. 120", id="custom-input")

            # Optional reason
            yield Label("Reason (optional):", id="reason-label")
            yield Input(placeholder="e.g. testing, maintenance…", id="reason-input")

            # Action buttons
            with Horizontal(id="buttons"):
                yield Button("Permanent", variant="error", id="btn-permanent")
                yield Button("Cancel", variant="default", id="btn-cancel")

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    @on(Button.Pressed, ".preset-btn")
    def _preset_pressed(self, event: Button.Pressed) -> None:
        # Button id is "preset-<seconds>"
        try:
            seconds = int(str(event.button.id).replace("preset-", ""))
        except (ValueError, AttributeError):
            return
        reason = self._get_reason()
        self.dismiss((seconds, reason))

    @on(Button.Pressed, "#btn-permanent")
    def _permanent(self) -> None:
        reason = self._get_reason()
        self.dismiss((None, reason))  # None seconds = permanent

    @on(Button.Pressed, "#btn-cancel")
    def _cancel(self) -> None:
        self.dismiss(False)

    @on(Input.Submitted, "#custom-input")
    def _custom_submitted(self) -> None:
        custom_input = self.query_one("#custom-input", Input)
        try:
            seconds = int(custom_input.value.strip())
            if seconds > 0:
                reason = self._get_reason()
                self.dismiss((seconds, reason))
            else:
                self.notify("Please enter a positive number of seconds.", severity="warning")
        except ValueError:
            self.notify("Please enter a valid number of seconds.", severity="warning")

    def _get_reason(self) -> str:
        try:
            return self.query_one("#reason-input", Input).value.strip()
        except Exception:
            return ""


# ---------------------------------------------------------------------------
# Dashboard screen
# ---------------------------------------------------------------------------

class DashboardScreen(Screen):
    """Main dashboard screen showing Pi-hole statistics and blocking control."""

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

    DashboardScreen .dashboard-container {
        grid-gutter: 1;
        padding: 0 2;
        height: auto;
        width: 100%;
    }

    /* Grid items fill their cells with equal width */
    DashboardScreen .dashboard-container > * {
        width: 1fr;
        height: auto;
    }

    /* Responsive grid sizes */
    DashboardScreen.layout-3col .dashboard-container {
        grid-size: 3;
    }

    DashboardScreen.layout-2col .dashboard-container {
        grid-size: 2;
    }

    DashboardScreen.layout-1col .dashboard-container {
        grid-size: 1;
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

    DashboardScreen #countdown-container {
        dock: bottom;
        layout: horizontal;
        height: 1;
        background: $warning 30%;
        padding: 0 2;
        display: none;
    }

    DashboardScreen #countdown-container.visible {
        display: block;
    }

    DashboardScreen #countdown-label {
        color: $warning;
        text-style: bold;
    }
    """

    # Reactive state
    stats: reactive[Optional[DashboardStats]] = reactive(None)
    refresh_interval: reactive[int] = reactive(DEFAULT_DASHBOARD_REFRESH_INTERVAL)
    last_update: reactive[Optional[datetime]] = reactive(None)
    is_loading: reactive[bool] = reactive(False)
    blocking_enabled: reactive[bool] = reactive(True)
    blocking_timer_seconds: reactive[Optional[int]] = reactive(None)

    def __init__(self, api_client, **kwargs):
        """Initialise dashboard screen.

        Args:
            api_client: Authenticated API client
            **kwargs: Additional arguments for Screen
        """
        super().__init__(**kwargs)
        self.api_client = api_client
        self._refresh_timer = None

    # ------------------------------------------------------------------
    # Compose
    # ------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Header()

        yield Label("Pi-hole Dashboard", classes="dashboard-title")

        with Grid(classes="dashboard-container"):
            yield BlockingStatusCard(id="blocking-status")
            yield StatCard("Total Queries", id="stat-queries-total")
            yield StatCard("Queries Blocked", id="stat-queries-blocked")
            yield StatCard("Percentage Blocked", id="stat-percent-blocked", large=True)
            yield StatCard("Domains on Blocklists", id="stat-domains-blocklist")
            yield StatCard("Active Clients", id="stat-clients-active")
            yield StatCard("Queries Forwarded", id="stat-queries-forwarded")
            yield StatCard("Queries Cached", id="stat-queries-cached")
            yield StatCard("Clients Ever Seen", id="stat-clients-ever")
            yield DistributionCard("Query Type Distribution", id="dist-query-types")
            yield DistributionCard("Reply Type Distribution", id="dist-reply-types")

        # Countdown banner (hidden until temp-disable is active)
        with Container(id="countdown-container"):
            yield Label("Blocking disabled — re-enabling in: ", id="countdown-label")
            yield CountdownTimer(id="countdown-timer")

        with Container(classes="footer-info"):
            yield Label("Gravity last updated: --", id="footer-gravity")
            yield Label("Last update: --", id="footer-last-update")

        yield Footer()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def on_mount(self) -> None:
        self.call_after_refresh(self._apply_responsive_layout)
        await self.refresh_data()
        self._refresh_timer = self.set_interval(self.refresh_interval, self.refresh_data)

    def on_unmount(self) -> None:
        if self._refresh_timer:
            self._refresh_timer.stop()

    def on_resize(self, event) -> None:
        self._apply_responsive_layout()

    # ------------------------------------------------------------------
    # Responsive layout
    # ------------------------------------------------------------------

    def _apply_responsive_layout(self) -> None:
        terminal_width = self.app.size.width
        self.remove_class("layout-3col", "layout-2col", "layout-1col")
        if terminal_width >= LAYOUT_BREAKPOINT_3COL:
            self.add_class("layout-3col")
        elif terminal_width >= LAYOUT_BREAKPOINT_2COL:
            self.add_class("layout-2col")
        else:
            self.add_class("layout-1col")

    # ------------------------------------------------------------------
    # Data refresh
    # ------------------------------------------------------------------

    async def refresh_data(self) -> None:
        """Fetch fresh statistics from Pi-hole API."""
        if self.is_loading:
            return

        self.is_loading = True
        try:
            logger.debug("Refreshing dashboard statistics")
            stats = await get_summary_stats(self.api_client)
            self.stats = stats
            self.last_update = datetime.now()
            await self.update_widgets()
            logger.debug("Dashboard refresh completed successfully")

        except NetworkError as e:
            logger.warning(f"Network error during refresh (will retry): {e.message}")

        except PiHoleAPIError as e:
            logger.error(f"API error during refresh: {e.message} (status: {e.status_code})")
            self.notify(
                f"Failed to refresh statistics: HTTP {e.status_code}: {e.message}",
                severity="error",
                timeout=10,
            )

        except Exception:
            logger.exception("Unexpected error during dashboard refresh")
            self.notify("Failed to refresh statistics", severity="error", timeout=10)

        finally:
            self.is_loading = False

    async def update_widgets(self) -> None:
        """Update all dashboard widgets with current stats."""
        if not self.stats:
            return

        stats = self.stats

        # Keep local reactive state in sync with what the API reports
        # (only update if we're not mid-toggle to avoid race conditions)
        self.blocking_enabled = stats.blocking_status

        blocking_card = self.query_one("#blocking-status", BlockingStatusCard)
        blocking_card.update_status(stats.blocking_status)

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
        self.query_one("#stat-queries-forwarded", StatCard).update_value(
            format_number(stats.queries_forwarded)
        )
        self.query_one("#stat-queries-cached", StatCard).update_value(
            format_number(stats.queries_cached)
        )

        query_type_card = self.query_one("#dist-query-types", DistributionCard)
        query_type_card.update_distributions(stats.query_type_distribution)

        reply_type_card = self.query_one("#dist-reply-types", DistributionCard)
        reply_type_card.update_distributions(stats.reply_type_distribution)

        gravity_label = self.query_one("#footer-gravity", Label)
        if stats.gravity_last_updated:
            gravity_label.update(
                f"Gravity last updated: {format_datetime(stats.gravity_last_updated)}"
            )
        else:
            gravity_label.update("Gravity last updated: Unknown")

        last_update_label = self.query_one("#footer-last-update", Label)
        if self.last_update:
            last_update_label.update(f"Last update: {format_datetime(self.last_update)}")

    # ------------------------------------------------------------------
    # Blocking control — T067-T075
    # ------------------------------------------------------------------

    def action_toggle_blocking(self) -> None:
        """Toggle blocking on/off — launches the worker that drives the dialogs."""
        self.run_worker(self._toggle_blocking_worker(), exclusive=True)

    async def _toggle_blocking_worker(self) -> None:
        """Worker: show confirmation → duration dialog → perform API call.

        Must run inside a Textual worker so that ``push_screen`` with
        ``wait_for_dismiss=True`` is permitted.
        """
        confirmed = await self.app.push_screen(
            BlockingConfirmDialog(self.blocking_enabled),
            wait_for_dismiss=True,
        )
        if not confirmed:
            return  # User cancelled

        if self.blocking_enabled:
            # Currently enabled → disabling: ask how long
            result = await self.app.push_screen(
                DurationDialog(),
                wait_for_dismiss=True,
            )
            if result is False:
                return  # User cancelled the duration dialog

            seconds, reason = result  # seconds is None for permanent
            await self._perform_disable(seconds, reason)
        else:
            # Currently disabled (or temp-disabled) → re-enable immediately
            await self._perform_enable()

    async def _perform_enable(self) -> None:
        """Re-enable blocking and stop any active countdown."""
        try:
            request = BlockingToggleRequest(blocking=True)
            await set_blocking_status(
                self.api_client,
                enabled=True,
            )

            # Stop countdown banner
            self._stop_countdown()
            self.blocking_enabled = True
            self.blocking_timer_seconds = None

            # Update blocking status card
            blocking_card = self.query_one("#blocking-status", BlockingStatusCard)
            blocking_card.update_status(True)

            self.notify("DNS blocking enabled ✓", severity="information", timeout=4)
            logger.info("Blocking enabled by user")

        except NetworkError as e:
            logger.error(f"Network error enabling blocking: {e.message}")
            self.notify(
                f"Network error — could not enable blocking: {e.message}",
                severity="error",
                timeout=8,
            )
        except PiHoleAPIError as e:
            logger.error(f"API error enabling blocking: {e.message}")
            self.notify(
                f"Failed to enable blocking: {e.message}",
                severity="error",
                timeout=8,
            )
        except Exception:
            logger.exception("Unexpected error enabling blocking")
            self.notify("Unexpected error enabling blocking", severity="error", timeout=8)

    async def _perform_disable(self, seconds: Optional[int], reason: str) -> None:
        """Disable blocking with an optional timer.

        Args:
            seconds: Duration in seconds, or ``None`` for permanent.
            reason: Optional user-supplied reason (for logging; API ignores it).
        """
        try:
            await set_blocking_status(
                self.api_client,
                enabled=False,
                timer=seconds,
            )

            self.blocking_enabled = False
            self.blocking_timer_seconds = seconds

            # Update blocking status card
            blocking_card = self.query_one("#blocking-status", BlockingStatusCard)
            if seconds:
                timer_label = format_duration(seconds)
                blocking_card.update_status(False, timer_text=timer_label)
                self._start_countdown(seconds)
                msg = f"DNS blocking disabled for {timer_label}"
            else:
                blocking_card.update_status(False)
                msg = "DNS blocking disabled permanently"

            if reason:
                logger.info(f"Blocking disabled. Reason: {reason}. Duration: {seconds}s")
            else:
                logger.info(f"Blocking disabled. Duration: {seconds}s")

            self.notify(msg, severity="warning", timeout=5)

        except NetworkError as e:
            logger.error(f"Network error disabling blocking: {e.message}")
            self.notify(
                f"Network error — could not disable blocking: {e.message}",
                severity="error",
                timeout=8,
            )
        except PiHoleAPIError as e:
            logger.error(f"API error disabling blocking: {e.message}")
            self.notify(
                f"Failed to disable blocking: {e.message}",
                severity="error",
                timeout=8,
            )
        except Exception:
            logger.exception("Unexpected error disabling blocking")
            self.notify("Unexpected error disabling blocking", severity="error", timeout=8)

    # ------------------------------------------------------------------
    # Countdown helpers — T070, T071, T072
    # ------------------------------------------------------------------

    def _start_countdown(self, seconds: int) -> None:
        """Show the countdown banner and start the timer widget."""
        container = self.query_one("#countdown-container", Container)
        container.add_class("visible")

        timer = self.query_one("#countdown-timer", CountdownTimer)
        timer.start(seconds)

    def _stop_countdown(self) -> None:
        """Hide the countdown banner and stop the timer widget."""
        container = self.query_one("#countdown-container", Container)
        container.remove_class("visible")

        timer = self.query_one("#countdown-timer", CountdownTimer)
        timer.stop()

    @on(CountdownTimer.Expired)
    async def _on_countdown_expired(self) -> None:
        """Auto re-enable blocking when the temporary disable timer expires."""
        logger.info("Temporary disable timer expired — re-enabling blocking")
        self.notify("Re-enabling DNS blocking (timer expired)…", severity="information", timeout=4)
        await self._perform_enable()

    # ------------------------------------------------------------------
    # Navigation actions
    # ------------------------------------------------------------------

    async def action_refresh(self) -> None:
        await self.refresh_data()
        self.notify("Dashboard refreshed", timeout=2)

    def action_query_log(self) -> None:
        from pihole_tui.api.queries import QueriesAPI
        from pihole_tui.screens.query_log import QueryLogScreen

        queries_api = QueriesAPI(self.api_client)
        self.app.push_screen(QueryLogScreen(queries_api))

    def action_domains(self) -> None:
        from pihole_tui.screens.domains import DomainsScreen

        self.app.push_screen(DomainsScreen(self.api_client))

    def update_refresh_interval(self, interval: int) -> None:
        """Update auto-refresh interval.

        Args:
            interval: New refresh interval in seconds
        """
        self.refresh_interval = interval

        if self._refresh_timer:
            self._refresh_timer.stop()

        self._refresh_timer = self.set_interval(interval, self.refresh_data)
        self.notify(f"Refresh interval updated to {interval}s", timeout=2)
