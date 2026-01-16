"""Main Textual application for Pi-hole TUI.

Coordinates authentication, session management, screen navigation,
and overall application flow.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Footer, Header, Static

from pihole_tui.api import AuthenticationError, NetworkError, PiHoleAPIClient, SessionExpiredError
from pihole_tui.api.auth import login, logout
from pihole_tui.api.queries import QueriesAPI
from pihole_tui.constants import ConnectionStatus, SESSION_RENEWAL_THRESHOLD
from pihole_tui.models import ConnectionProfile, SessionState, UserPreferences
from pihole_tui.screens.dashboard import DashboardScreen
from pihole_tui.screens.login import LoginScreen, TOTPDialog
from pihole_tui.screens.query_log import QueryLogScreen
from pihole_tui.screens.settings import SettingsScreen
from pihole_tui.utils.config_manager import ConfigManager
from pihole_tui.utils.formatters import format_countdown
from pihole_tui.widgets.status_indicator import StatusIndicator


class PiHoleTUI(App):
    """Main Pi-hole TUI application."""

    TITLE = "Pi-hole TUI"
    CSS = """
    Screen {
        background: $surface;
    }

    #status-bar {
        dock: bottom;
        height: 1;
        background: $panel;
        padding: 0 1;
        layout: horizontal;
    }

    #status-left {
        width: 1fr;
        content-align: left middle;
    }

    #status-right {
        width: auto;
        content-align: right middle;
    }

    #main-content {
        width: 100%;
        height: 100%;
        align: center middle;
    }

    .welcome-text {
        text-align: center;
        width: 100%;
    }
    """

    BINDINGS = [
        Binding("s", "show_settings", "Settings"),
        Binding("q", "show_query_log", "Query Log", show=True),
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+c", "quit", "Quit", show=False),
    ]

    def __init__(self):
        """Initialize Pi-hole TUI application."""
        super().__init__()
        self.config_manager = ConfigManager()
        self.preferences = self.config_manager.load_preferences()
        self.session = SessionState()
        self.api_client: Optional[PiHoleAPIClient] = None
        self._renewal_task: Optional[asyncio.Task] = None

        # Configure logging
        self._configure_logging()

    def _configure_logging(self):
        """Configure logging to file and console."""
        # Create log directory
        log_dir = Path.home() / ".config" / "pihole-tui"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "pihole-tui.log"

        # Configure root logger
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()  # Also log to console for textual console
            ]
        )

        logger = logging.getLogger(__name__)
        logger.info("Pi-hole TUI starting up")
        logger.info(f"Logging to {log_file}")

    def compose(self) -> ComposeResult:
        """Compose main application UI."""
        yield Header()

        with Container(id="main-content"):
            yield Static(
                "Welcome to Pi-hole TUI\n\nPress 'S' for Settings or connect to Pi-hole",
                classes="welcome-text",
            )

        with Container(id="status-bar"):
            with Container(id="status-left"):
                yield StatusIndicator(id="status-indicator")
            with Container(id="status-right"):
                yield Static("Not connected", id="session-info")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize application on mount."""
        # Try to auto-login with saved credentials
        self.run_worker(self.try_auto_login(), exclusive=True)

    async def try_auto_login(self) -> None:
        """Attempt automatic login with saved credentials."""
        # Load active profile
        active_profile = self.config_manager.get_active_profile()

        if active_profile and active_profile.saved_password:
            # Update status
            status_indicator = self.query_one("#status-indicator", StatusIndicator)
            status_indicator.set_status(ConnectionStatus.CONNECTING)

            # Create API client and open it
            base_url = active_profile.get_base_url()
            self.api_client = PiHoleAPIClient(base_url)
            await self.api_client.__aenter__()  # Open the client connection

            try:
                # Attempt login
                auth_response = await login(self.api_client, active_profile.saved_password)

                # Update session
                self.session.sid = auth_response.session.sid
                self.session.expires_at = auth_response.session.get_expires_at()
                self.session.connection_profile = active_profile
                self.session.is_authenticated = True
                self.session.last_renewal = datetime.now()

                # Set SID in client
                self.api_client.set_session(auth_response.session.sid)

                # Update UI
                status_indicator.set_status(ConnectionStatus.CONNECTED)
                await self.update_session_info()

                # Start session renewal task
                self._start_session_renewal()

                # Show dashboard
                self.notify("Connected successfully", severity="information")
                await self.show_dashboard()

            except (AuthenticationError, NetworkError) as e:
                # Auto-login failed, close client and show login screen
                if self.api_client:
                    try:
                        await self.api_client.__aexit__(None, None, None)
                    except Exception:
                        pass
                    self.api_client = None
                status_indicator.set_status(ConnectionStatus.DISCONNECTED)
                await self.show_login_screen()
        else:
            # No saved credentials, show login screen
            await self.show_login_screen()

    async def show_login_screen(self, profile: Optional[ConnectionProfile] = None) -> None:
        """Show login screen for authentication.

        Args:
            profile: Optional profile to pre-fill
        """
        result = await self.push_screen(LoginScreen(profile), wait_for_dismiss=True)

        if result is None:
            # User cancelled
            return

        profile, password, remember = result

        # Update status
        status_indicator = self.query_one("#status-indicator", StatusIndicator)
        status_indicator.set_status(ConnectionStatus.CONNECTING)

        # Create API client and open it
        base_url = profile.get_base_url()
        self.api_client = PiHoleAPIClient(base_url)
        await self.api_client.__aenter__()  # Open the client connection

        try:
            # Attempt login
            auth_response = await login(self.api_client, password)

            # Update session
            self.session.sid = auth_response.session.sid
            self.session.expires_at = auth_response.session.get_expires_at()
            self.session.connection_profile = profile
            self.session.is_authenticated = True
            self.session.last_renewal = datetime.now()

            # Set SID in client
            self.api_client.set_session(auth_response.session.sid)

            # Save profile if remember is checked
            if remember:
                profile.saved_password = password
                profiles = self.config_manager.load_connection_profiles()

                # Check if profile already exists
                existing = next((p for p in profiles if p.name == profile.name), None)
                if existing:
                    # Update existing
                    existing.hostname = profile.hostname
                    existing.port = profile.port
                    existing.use_https = profile.use_https
                    existing.saved_password = password
                    existing.is_active = True
                else:
                    # Add new
                    profile.is_active = True
                    profiles.append(profile)

                # Deactivate others
                for p in profiles:
                    if p.name != profile.name:
                        p.is_active = False

                self.config_manager.save_connection_profiles(profiles)

            # Update UI
            status_indicator.set_status(ConnectionStatus.CONNECTED)
            await self.update_session_info()

            # Start session renewal
            self._start_session_renewal()

            self.notify("Connected successfully", severity="information")

            # Show dashboard
            await self.show_dashboard()

        except AuthenticationError as e:
            # Check if 2FA is required (403 error)
            if e.status_code == 403:
                # Show TOTP dialog
                totp_code = await self.push_screen(TOTPDialog(), wait_for_dismiss=True)

                if totp_code:
                    # Retry with TOTP
                    try:
                        auth_response = await login(self.api_client, password, totp_code)

                        # Update session and UI (same as above)
                        self.session.sid = auth_response.session.sid
                        self.session.expires_at = auth_response.session.get_expires_at()
                        self.session.connection_profile = profile
                        self.session.is_authenticated = True
                        self.session.last_renewal = datetime.now()

                        self.api_client.set_session(auth_response.session.sid)

                        if remember:
                            profile.saved_password = password
                            profile.totp_enabled = True
                            # Save profile...

                        status_indicator.set_status(ConnectionStatus.CONNECTED)
                        await self.update_session_info()
                        self._start_session_renewal()

                        self.notify("Connected successfully", severity="information")

                        # Show dashboard
                        await self.show_dashboard()

                    except AuthenticationError as e2:
                        status_indicator.set_status(ConnectionStatus.ERROR)
                        self.notify(f"Authentication failed: {e2.message}", severity="error")
                        # Close client on failure
                        if self.api_client:
                            try:
                                await self.api_client.__aexit__(None, None, None)
                            except Exception:
                                pass
                            self.api_client = None
                        await self.show_login_screen(profile)
            else:
                status_indicator.set_status(ConnectionStatus.ERROR)
                self.notify(f"Authentication failed: {e.message}", severity="error")
                # Close client on failure
                if self.api_client:
                    try:
                        await self.api_client.__aexit__(None, None, None)
                    except Exception:
                        pass
                    self.api_client = None
                await self.show_login_screen(profile)

        except NetworkError as e:
            status_indicator.set_status(ConnectionStatus.ERROR)
            self.notify(f"Network error: {e.message}", severity="error")
            # Close client on failure
            if self.api_client:
                try:
                    await self.api_client.__aexit__(None, None, None)
                except Exception:
                    pass
                self.api_client = None
            await self.show_login_screen(profile)

    async def show_dashboard(self) -> None:
        """Show the main dashboard screen."""
        if not self.api_client or not self.session.is_authenticated:
            self.notify("Not authenticated. Please log in first.", severity="warning")
            return

        # Push the dashboard screen
        dashboard = DashboardScreen(self.api_client)
        await self.push_screen(dashboard)

    def action_show_query_log(self) -> None:
        """Show query log screen."""
        self.run_worker(self._show_query_log_worker(), exclusive=True)

    async def _show_query_log_worker(self) -> None:
        """Worker method for showing query log screen."""
        if not self.api_client or not self.session.is_authenticated:
            self.notify("Not authenticated. Please log in first.", severity="warning")
            return

        # Create queries API instance
        queries_api = QueriesAPI(self.api_client)

        # Push the query log screen
        query_log = QueryLogScreen(queries_api)
        await self.push_screen(query_log)

    def _start_session_renewal(self) -> None:
        """Start background task for session renewal."""
        if self._renewal_task:
            self._renewal_task.cancel()

        self._renewal_task = asyncio.create_task(self._session_renewal_loop())

    async def _session_renewal_loop(self) -> None:
        """Background loop to renew session before expiry."""
        while self.session.is_authenticated:
            try:
                # Check if renewal needed
                if self.session.should_renew(SESSION_RENEWAL_THRESHOLD):
                    await self._renew_session()

                # Wait before next check (check every 30 seconds)
                await asyncio.sleep(30)

            except asyncio.CancelledError:
                break
            except Exception:
                # Continue loop even if renewal fails
                await asyncio.sleep(30)

    async def _renew_session(self) -> None:
        """Renew session by re-authenticating."""
        if not self.session.connection_profile or not self.session.connection_profile.saved_password:
            return

        try:
            if self.api_client:
                auth_response = await login(
                    self.api_client,
                    self.session.connection_profile.saved_password,
                )

                # Update session
                self.session.sid = auth_response.session.sid
                self.session.expires_at = auth_response.session.get_expires_at()
                self.session.last_renewal = datetime.now()

                # Update client SID
                self.api_client.set_session(auth_response.session.sid)

                await self.update_session_info()

        except (AuthenticationError, NetworkError):
            # Renewal failed, clear session
            self.session.clear()
            status_indicator = self.query_one("#status-indicator", StatusIndicator)
            status_indicator.set_status(ConnectionStatus.ERROR)
            self.notify("Session renewal failed. Please reconnect.", severity="warning")

    async def update_session_info(self) -> None:
        """Update session information display in status bar."""
        session_info = self.query_one("#session-info", Static)

        if self.session.is_authenticated and self.session.expires_at:
            profile_name = self.session.connection_profile.name if self.session.connection_profile else "Unknown"
            expiry_text = format_countdown(self.session.expires_at)
            session_info.update(f"{profile_name} | Session: {expiry_text}")
        else:
            session_info.update("Not connected")

    def action_show_settings(self) -> None:
        """Show settings screen."""
        self.run_worker(self._show_settings_worker(), exclusive=True)

    async def _show_settings_worker(self) -> None:
        """Worker method for showing settings screen."""
        profiles = self.config_manager.load_connection_profiles()
        result = await self.push_screen(
            SettingsScreen(profiles, self.preferences),
            wait_for_dismiss=True,
        )

        if result:
            action, data = result

            if action == "save_preferences":
                self.preferences = data
                self.config_manager.save_preferences(data)
                self.notify("Preferences saved", severity="information")

            elif action == "add_profile":
                await self.show_login_screen()

            elif action == "set_active":
                self.config_manager.set_active_profile(data.name)
                self.notify(f"Active profile set to: {data.name}", severity="information")

    async def action_quit(self) -> None:
        """Quit application."""
        # Cancel renewal task
        if self._renewal_task:
            self._renewal_task.cancel()

        # Close API client if open
        if self.api_client:
            try:
                await self.api_client.__aexit__(None, None, None)
            except Exception:
                pass  # Ignore errors during cleanup

        self.exit()
