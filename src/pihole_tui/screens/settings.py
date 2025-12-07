"""Settings screen for managing connection profiles and preferences.

Provides UI for adding, editing, deleting, and switching between connection profiles,
as well as configuring user preferences.
"""

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, DataTable, Footer, Header, Label, Select, Static, TabbedContent, TabPane

from pihole_tui.models.config import ConnectionProfile, UserPreferences


class SettingsScreen(Screen):
    """Screen for managing settings and connection profiles."""

    CSS = """
    SettingsScreen {
        padding: 1 2;
    }

    #settings-title {
        dock: top;
        width: 100%;
        height: 3;
        content-align: center middle;
        text-style: bold;
    }

    TabbedContent {
        height: 100%;
    }

    #profiles-table {
        height: 1fr;
    }

    .button-row {
        height: auto;
        layout: horizontal;
        margin-top: 1;
    }

    Button {
        margin-right: 1;
    }

    .pref-row {
        height: auto;
        layout: horizontal;
        margin-bottom: 1;
    }

    .pref-label {
        width: 40;
        padding: 1 0;
    }

    Select {
        width: 30;
    }
    """

    def __init__(
        self,
        profiles: list[ConnectionProfile],
        preferences: UserPreferences,
    ):
        """Initialize settings screen.

        Args:
            profiles: List of connection profiles
            preferences: User preferences
        """
        super().__init__()
        self.profiles = profiles
        self.preferences = preferences

    def compose(self) -> ComposeResult:
        """Compose settings screen UI."""
        yield Header()
        yield Static("Settings", id="settings-title")

        with TabbedContent():
            with TabPane("Connection Profiles", id="profiles-tab"):
                yield DataTable(id="profiles-table")

                with Horizontal(classes="button-row"):
                    yield Button("Add Profile", variant="primary", id="add-profile-btn")
                    yield Button("Edit", id="edit-profile-btn")
                    yield Button("Delete", id="delete-profile-btn")
                    yield Button("Set Active", id="set-active-btn")

            with TabPane("Preferences", id="preferences-tab"):
                with Vertical():
                    with Horizontal(classes="pref-row"):
                        yield Label("Dashboard Refresh Interval:", classes="pref-label")
                        yield Select(
                            [(f"{s}s", s) for s in [5, 10, 30, 60]],
                            value=self.preferences.dashboard_refresh_interval,
                            id="dashboard-refresh-select",
                        )

                    with Horizontal(classes="pref-row"):
                        yield Label("Query Log Refresh Interval:", classes="pref-label")
                        yield Select(
                            [(f"{s}s", s) for s in [3, 5, 10]],
                            value=self.preferences.query_log_refresh_interval,
                            id="query-log-refresh-select",
                        )

                    with Horizontal(classes="pref-row"):
                        yield Label("Query Log Page Size:", classes="pref-label")
                        yield Select(
                            [(str(s), s) for s in [25, 50, 100]],
                            value=self.preferences.query_log_page_size,
                            id="page-size-select",
                        )

                    with Horizontal(classes="pref-row"):
                        yield Label("Date Format:", classes="pref-label")
                        yield Select(
                            [("Relative (5 minutes ago)", "relative"), ("Absolute (2025-12-05 14:30)", "absolute")],
                            value=self.preferences.date_format,
                            id="date-format-select",
                        )

                    with Horizontal(classes="button-row"):
                        yield Button("Save Preferences", variant="primary", id="save-prefs-btn")
                        yield Button("Reset to Defaults", id="reset-prefs-btn")

        yield Footer()

    def on_mount(self) -> None:
        """Set up the screen when mounted."""
        # Populate profiles table
        table = self.query_one("#profiles-table", DataTable)
        table.add_columns("Name", "Hostname", "Port", "HTTPS", "Active")

        for profile in self.profiles:
            table.add_row(
                profile.name,
                profile.hostname,
                str(profile.port),
                "Yes" if profile.use_https else "No",
                "✓" if profile.is_active else "",
            )

    @on(Button.Pressed, "#add-profile-btn")
    def handle_add_profile(self) -> None:
        """Handle add profile button press."""
        # This would open the login screen in "add profile" mode
        # For now, just dismiss to trigger app to show login screen
        self.dismiss(("add_profile", None))

    @on(Button.Pressed, "#edit-profile-btn")
    def handle_edit_profile(self) -> None:
        """Handle edit profile button press."""
        table = self.query_one("#profiles-table", DataTable)
        if table.cursor_row is not None and table.cursor_row < len(self.profiles):
            profile = self.profiles[table.cursor_row]
            self.dismiss(("edit_profile", profile))

    @on(Button.Pressed, "#delete-profile-btn")
    def handle_delete_profile(self) -> None:
        """Handle delete profile button press."""
        table = self.query_one("#profiles-table", DataTable)
        if table.cursor_row is not None and table.cursor_row < len(self.profiles):
            profile = self.profiles[table.cursor_row]
            self.dismiss(("delete_profile", profile))

    @on(Button.Pressed, "#set-active-btn")
    def handle_set_active(self) -> None:
        """Handle set active button press."""
        table = self.query_one("#profiles-table", DataTable)
        if table.cursor_row is not None and table.cursor_row < len(self.profiles):
            profile = self.profiles[table.cursor_row]
            self.dismiss(("set_active", profile))

    @on(Button.Pressed, "#save-prefs-btn")
    def handle_save_preferences(self) -> None:
        """Handle save preferences button press."""
        # Get updated preferences from inputs
        dashboard_refresh = self.query_one("#dashboard-refresh-select", Select).value
        query_log_refresh = self.query_one("#query-log-refresh-select", Select).value
        page_size = self.query_one("#page-size-select", Select).value
        date_format = self.query_one("#date-format-select", Select).value

        updated_prefs = UserPreferences(
            dashboard_refresh_interval=dashboard_refresh,
            query_log_refresh_interval=query_log_refresh,
            query_log_page_size=page_size,
            date_format=date_format,
            confirm_blocking_changes=self.preferences.confirm_blocking_changes,
            confirm_domain_deletes=self.preferences.confirm_domain_deletes,
            theme=self.preferences.theme,
        )

        self.dismiss(("save_preferences", updated_prefs))

    @on(Button.Pressed, "#reset-prefs-btn")
    def handle_reset_preferences(self) -> None:
        """Handle reset preferences button press."""
        # Reset to defaults
        default_prefs = UserPreferences()
        self.dismiss(("save_preferences", default_prefs))
