"""Connection status indicator widget.

Displays current connection status with colour-coded visual indicator.
"""

from textual.reactive import reactive
from textual.widgets import Static

from pihole_tui.constants import ConnectionStatus


class StatusIndicator(Static):
    """Widget showing connection status with colour indicators."""

    status: reactive[ConnectionStatus] = reactive(ConnectionStatus.DISCONNECTED)

    CSS = """
    StatusIndicator {
        width: auto;
        height: 1;
        padding: 0 1;
    }

    StatusIndicator.disconnected {
        background: $error;
        color: $text;
    }

    StatusIndicator.connecting {
        background: $warning;
        color: $text;
    }

    StatusIndicator.connected {
        background: $success;
        color: $text;
    }

    StatusIndicator.reconnecting {
        background: $warning;
        color: $text;
    }

    StatusIndicator.error {
        background: $error;
        color: $text;
    }
    """

    def __init__(self, initial_status: ConnectionStatus = ConnectionStatus.DISCONNECTED, **kwargs):
        """Initialize status indicator.

        Args:
            initial_status: Initial connection status
            **kwargs: Additional keyword arguments passed to Static parent class
        """
        super().__init__(**kwargs)
        self.status = initial_status

    def watch_status(self, new_status: ConnectionStatus) -> None:
        """Update display when status changes.

        Args:
            new_status: New connection status
        """
        # Update CSS classes
        self.remove_class("disconnected", "connecting", "connected", "reconnecting", "error")
        self.add_class(new_status.value)

        # Update text content
        status_text = {
            ConnectionStatus.DISCONNECTED: "⚫ Disconnected",
            ConnectionStatus.CONNECTING: "🟡 Connecting...",
            ConnectionStatus.CONNECTED: "🟢 Connected",
            ConnectionStatus.RECONNECTING: "🟡 Reconnecting...",
            ConnectionStatus.ERROR: "🔴 Connection Error",
        }

        self.update(status_text.get(new_status, "Unknown"))

    def on_mount(self) -> None:
        """Initialize display when widget is mounted."""
        self.watch_status(self.status)

    def set_status(self, status: ConnectionStatus) -> None:
        """Set connection status.

        Args:
            status: New connection status
        """
        self.status = status
