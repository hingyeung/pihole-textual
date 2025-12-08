"""Statistics card widgets for displaying dashboard data."""

from typing import List, Optional

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Static, Label, DataTable

from pihole_tui.models.stats import QueryTypeDistribution, ReplyTypeDistribution


class StatCard(Static):
    """Widget for displaying a single statistic with label and value."""

    DEFAULT_CSS = """
    StatCard {
        width: auto;
        height: auto;
        border: solid $primary;
        padding: 1 2;
        margin: 0 1;
    }

    StatCard .stat-label {
        color: $text-muted;
        text-style: bold;
    }

    StatCard .stat-value {
        color: $primary;
        text-style: bold;
        text-align: center;
        content-align: center middle;
        padding: 1 0;
    }

    StatCard .stat-value-large {
        color: $success;
        text-style: bold;
        text-align: center;
        content-align: center middle;
        padding: 1 0;
    }
    """

    def __init__(
        self,
        label: str,
        value: str = "",
        value_colour: str = "primary",
        large: bool = False,
        **kwargs,
    ):
        """Initialize stat card.

        Args:
            label: Label text for the statistic
            value: Value to display
            value_colour: Colour for the value text (primary, success, warning, error)
            large: Whether to use large text style
            **kwargs: Additional arguments for Static
        """
        super().__init__(**kwargs)
        self.label_text = label
        self.value_text = value
        self.value_colour = value_colour
        self.large = large

    def compose(self) -> ComposeResult:
        """Compose the stat card."""
        yield Label(self.label_text, classes="stat-label")
        value_class = "stat-value-large" if self.large else "stat-value"
        yield Label(self.value_text, classes=value_class)

    def update_value(self, value: str, colour: Optional[str] = None):
        """Update the statistic value.

        Args:
            value: New value to display
            colour: Optional new colour
        """
        self.value_text = value
        if colour:
            self.value_colour = colour

        # Update the label widget
        value_label = self.query_one("Label.stat-value, Label.stat-value-large", Label)
        value_label.update(value)


class DistributionCard(Static):
    """Widget for displaying query type or reply type distributions."""

    DEFAULT_CSS = """
    DistributionCard {
        width: auto;
        height: auto;
        border: solid $primary;
        padding: 1 2;
        margin: 0 1;
    }

    DistributionCard .dist-title {
        color: $text;
        text-style: bold;
        padding: 0 0 1 0;
    }

    DistributionCard DataTable {
        height: auto;
        max-height: 15;
    }
    """

    def __init__(
        self,
        title: str,
        distributions: Optional[List] = None,
        **kwargs,
    ):
        """Initialize distribution card.

        Args:
            title: Title for the distribution
            distributions: List of QueryTypeDistribution or ReplyTypeDistribution
            **kwargs: Additional arguments for Static
        """
        super().__init__(**kwargs)
        self.title_text = title
        self.distributions = distributions or []

    def compose(self) -> ComposeResult:
        """Compose the distribution card."""
        yield Label(self.title_text, classes="dist-title")
        table = DataTable()
        table.add_columns("Type", "Count", "Percent")
        table.cursor_type = "none"
        table.zebra_stripes = True
        yield table

    def on_mount(self) -> None:
        """Handle mount event to populate initial data."""
        self.update_distributions(self.distributions)

    def update_distributions(
        self, distributions: List[QueryTypeDistribution | ReplyTypeDistribution]
    ):
        """Update the distribution data.

        Args:
            distributions: New distribution data
        """
        self.distributions = distributions

        # Get the table widget
        table = self.query_one(DataTable)
        table.clear()

        # Populate table rows
        for dist in distributions:
            type_name = getattr(dist, "query_type", None) or getattr(dist, "reply_type", "")
            count = dist.count
            percent = f"{dist.percent:.1f}%"
            table.add_row(type_name, str(count), percent)

        # Refresh the table
        table.refresh()


class BlockingStatusCard(Static):
    """Widget for displaying prominent blocking status indicator."""

    DEFAULT_CSS = """
    BlockingStatusCard {
        width: auto;
        height: 7;
        border: solid $primary;
        padding: 1 2;
        margin: 0 1;
    }

    BlockingStatusCard .status-label {
        color: $text-muted;
        text-style: bold;
        text-align: center;
    }

    BlockingStatusCard .status-enabled {
        color: $success;
        text-style: bold;
        text-align: center;
        content-align: center middle;
        padding: 1 0;
    }

    BlockingStatusCard .status-disabled {
        color: $error;
        text-style: bold;
        text-align: center;
        content-align: center middle;
        padding: 1 0;
    }

    BlockingStatusCard .status-temp-disabled {
        color: $warning;
        text-style: bold;
        text-align: center;
        content-align: center middle;
        padding: 1 0;
    }
    """

    def __init__(self, enabled: bool = True, timer_text: Optional[str] = None, **kwargs):
        """Initialize blocking status card.

        Args:
            enabled: Whether blocking is enabled
            timer_text: Optional timer text for temporary disable
            **kwargs: Additional arguments for Static
        """
        super().__init__(**kwargs)
        self.enabled = enabled
        self.timer_text = timer_text

    def compose(self) -> ComposeResult:
        """Compose the blocking status card."""
        yield Label("Blocking Status", classes="status-label")

        if self.timer_text:
            status_class = "status-temp-disabled"
            status_text = f"DISABLED ({self.timer_text})"
        elif self.enabled:
            status_class = "status-enabled"
            status_text = "ENABLED"
        else:
            status_class = "status-disabled"
            status_text = "DISABLED"

        yield Label(status_text, classes=status_class)

    def update_status(self, enabled: bool, timer_text: Optional[str] = None):
        """Update the blocking status.

        Args:
            enabled: Whether blocking is enabled
            timer_text: Optional timer text for temporary disable
        """
        self.enabled = enabled
        self.timer_text = timer_text

        # Update the status label
        status_label = self.query_one(
            "Label.status-enabled, Label.status-disabled, Label.status-temp-disabled",
            Label
        )

        if timer_text:
            status_label.remove_class("status-enabled", "status-disabled")
            status_label.add_class("status-temp-disabled")
            status_label.update(f"DISABLED ({timer_text})")
        elif enabled:
            status_label.remove_class("status-disabled", "status-temp-disabled")
            status_label.add_class("status-enabled")
            status_label.update("ENABLED")
        else:
            status_label.remove_class("status-enabled", "status-temp-disabled")
            status_label.add_class("status-disabled")
            status_label.update("DISABLED")
