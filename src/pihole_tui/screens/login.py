"""Login screen for Pi-hole TUI authentication.

Provides UI for entering Pi-hole connection details and credentials.
"""

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Button, Checkbox, Footer, Header, Input, Label, Static

from pihole_tui.models.config import ConnectionProfile
from pihole_tui.utils.validators import validate_hostname_or_ip, validate_port, validate_totp_code


class LoginScreen(Screen):
    """Screen for Pi-hole authentication."""

    CSS = """
    LoginScreen {
        align: center middle;
    }

    #login-container {
        width: 60;
        height: auto;
        border: solid $primary;
        padding: 1 2;
    }

    #login-title {
        width: 100%;
        content-align: center middle;
        text-style: bold;
        margin-bottom: 1;
    }

    .input-group {
        height: auto;
        margin-bottom: 1;
    }

    .input-label {
        width: 100%;
        margin-bottom: 0;
    }

    Input {
        width: 100%;
    }

    #button-container {
        width: 100%;
        height: auto;
        layout: horizontal;
        margin-top: 1;
    }

    Button {
        margin-right: 1;
    }

    .error-message {
        color: $error;
        margin-top: 1;
        text-align: center;
    }

    .success-message {
        color: $success;
        margin-top: 1;
        text-align: center;
    }
    """

    def __init__(self, profile: ConnectionProfile | None = None):
        """Initialize login screen.

        Args:
            profile: Optional connection profile to pre-fill
        """
        super().__init__()
        self.profile = profile
        self.error_message = ""

    def compose(self) -> ComposeResult:
        """Compose login screen UI."""
        yield Header()

        with Vertical(id="login-container"):
            yield Static("Pi-hole TUI Login", id="login-title")

            with Container(classes="input-group"):
                yield Label("Hostname / IP Address:", classes="input-label")
                yield Input(
                    placeholder="pi.hole or 192.168.1.1",
                    id="hostname",
                    value=self.profile.hostname if self.profile else "",
                )

            with Container(classes="input-group"):
                yield Label("Port:", classes="input-label")
                yield Input(
                    placeholder="8080",
                    id="port",
                    value=str(self.profile.port) if self.profile else "8080",
                )

            with Container(classes="input-group"):
                yield Label("Password:", classes="input-label")
                yield Input(
                    placeholder="Admin password",
                    password=True,
                    id="password",
                )

            with Container(classes="input-group"):
                yield Checkbox("Use HTTPS", id="use-https", value=self.profile.use_https if self.profile else False)
                yield Checkbox("Remember credentials", id="remember")

            with Container(id="button-container"):
                yield Button("Connect", variant="primary", id="connect-btn")
                yield Button("Cancel", variant="default", id="cancel-btn")

            if self.error_message:
                yield Static(self.error_message, classes="error-message")

        yield Footer()

    @on(Button.Pressed, "#connect-btn")
    async def handle_connect(self) -> None:
        """Handle connect button press."""
        # Get input values
        hostname_input = self.query_one("#hostname", Input)
        port_input = self.query_one("#port", Input)
        password_input = self.query_one("#password", Input)
        use_https_cb = self.query_one("#use-https", Checkbox)
        remember_cb = self.query_one("#remember", Checkbox)

        hostname = hostname_input.value.strip()
        port_str = port_input.value.strip()
        password = password_input.value

        # Validate hostname
        is_valid, error = validate_hostname_or_ip(hostname)
        if not is_valid:
            await self.show_error(error or "Invalid hostname")
            hostname_input.focus()
            return

        # Validate port
        try:
            port = int(port_str)
            is_valid, error = validate_port(port)
            if not is_valid:
                await self.show_error(error or "Invalid port")
                port_input.focus()
                return
        except ValueError:
            await self.show_error("Port must be a number")
            port_input.focus()
            return

        # Validate password
        if not password:
            await self.show_error("Password is required")
            password_input.focus()
            return

        # Create connection profile
        profile = ConnectionProfile(
            name=f"{hostname}:{port}",
            hostname=hostname,
            port=port,
            use_https=use_https_cb.value,
            saved_password=password if remember_cb.value else None,
        )

        # Dismiss screen with profile and credentials
        self.dismiss((profile, password, remember_cb.value))

    @on(Button.Pressed, "#cancel-btn")
    def handle_cancel(self) -> None:
        """Handle cancel button press."""
        self.dismiss(None)

    async def show_error(self, message: str) -> None:
        """Show error message on screen.

        Args:
            message: Error message to display
        """
        # Remove existing error/success messages
        for widget in self.query(".error-message, .success-message"):
            await widget.remove()

        # Add new error message
        container = self.query_one("#login-container")
        await container.mount(Static(message, classes="error-message"))

    async def show_success(self, message: str) -> None:
        """Show success message on screen.

        Args:
            message: Success message to display
        """
        # Remove existing error/success messages
        for widget in self.query(".error-message, .success-message"):
            await widget.remove()

        # Add new success message
        container = self.query_one("#login-container")
        await container.mount(Static(message, classes="success-message"))


class TOTPDialog(Screen):
    """Modal dialog for entering TOTP 2FA code."""

    CSS = """
    TOTPDialog {
        align: center middle;
    }

    #totp-container {
        width: 40;
        height: auto;
        border: solid $accent;
        background: $surface;
        padding: 1 2;
    }

    #totp-title {
        width: 100%;
        content-align: center middle;
        text-style: bold;
        margin-bottom: 1;
    }

    .totp-info {
        margin-bottom: 1;
        text-align: center;
    }

    Input {
        width: 100%;
    }

    #button-container {
        width: 100%;
        height: auto;
        layout: horizontal;
        margin-top: 1;
    }

    Button {
        margin-right: 1;
    }

    .error-message {
        color: $error;
        margin-top: 1;
        text-align: center;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose TOTP dialog UI."""
        with Vertical(id="totp-container"):
            yield Static("Two-Factor Authentication", id="totp-title")
            yield Static("Enter your 6-digit TOTP code:", classes="totp-info")

            yield Input(placeholder="000000", id="totp-input", max_length=6)

            with Container(id="button-container"):
                yield Button("Submit", variant="primary", id="submit-btn")
                yield Button("Cancel", variant="default", id="cancel-btn")

    @on(Button.Pressed, "#submit-btn")
    async def handle_submit(self) -> None:
        """Handle submit button press."""
        totp_input = self.query_one("#totp-input", Input)
        totp_code = totp_input.value.strip()

        # Validate TOTP code
        is_valid, error = validate_totp_code(totp_code)
        if not is_valid:
            await self.show_error(error or "Invalid TOTP code")
            totp_input.focus()
            return

        self.dismiss(totp_code)

    @on(Button.Pressed, "#cancel-btn")
    def handle_cancel(self) -> None:
        """Handle cancel button press."""
        self.dismiss(None)

    async def show_error(self, message: str) -> None:
        """Show error message in dialog.

        Args:
            message: Error message to display
        """
        # Remove existing error messages
        for widget in self.query(".error-message"):
            await widget.remove()

        # Add new error message
        container = self.query_one("#totp-container")
        await container.mount(Static(message, classes="error-message"))
