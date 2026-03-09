"""Countdown timer widget for displaying temporary blocking disable duration."""

from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Static


def _format_seconds(seconds: int) -> str:
    """Format a number of seconds into a human-readable countdown string.

    Args:
        seconds: Number of seconds remaining

    Returns:
        Formatted string such as "4m 30s", "1h 2m", "45s"
    """
    if seconds <= 0:
        return "0s"

    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)

    parts = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if secs or not parts:
        parts.append(f"{secs}s")

    return " ".join(parts)


class CountdownTimer(Static):
    """Widget that displays a live countdown of remaining seconds.

    Updates every second via an internal interval.  When the timer reaches
    zero it emits a ``CountdownTimer.Expired`` message so the parent screen
    can re-enable blocking automatically.
    """

    remaining: reactive[int] = reactive(0)

    DEFAULT_CSS = """
    CountdownTimer {
        width: auto;
        height: 1;
        color: $warning;
        text-style: bold;
    }
    """

    class Expired(Message):
        """Posted when the countdown reaches zero."""

    def __init__(self, seconds: int = 0, **kwargs) -> None:
        """Initialise the countdown timer.

        Args:
            seconds: Initial number of seconds to count down from.
            **kwargs: Forwarded to ``Static``.
        """
        super().__init__(**kwargs)
        self.remaining = seconds
        self._interval = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def on_mount(self) -> None:
        """Start ticking when mounted (if there is time remaining)."""
        if self.remaining > 0:
            self._start_ticking()

    def on_unmount(self) -> None:
        """Stop the interval on unmount."""
        self._stop_ticking()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def start(self, seconds: int) -> None:
        """Start (or restart) the countdown.

        Args:
            seconds: Number of seconds to count down from.
        """
        self._stop_ticking()
        self.remaining = seconds
        if seconds > 0:
            self._start_ticking()

    def stop(self) -> None:
        """Stop the countdown and reset to zero."""
        self._stop_ticking()
        self.remaining = 0

    # ------------------------------------------------------------------
    # Reactive watcher
    # ------------------------------------------------------------------

    def watch_remaining(self, value: int) -> None:
        """Refresh the displayed text whenever ``remaining`` changes."""
        self.update(_format_seconds(value))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _start_ticking(self) -> None:
        self._interval = self.set_interval(1.0, self._tick)

    def _stop_ticking(self) -> None:
        if self._interval is not None:
            self._interval.stop()
            self._interval = None

    def _tick(self) -> None:
        """Decrement the counter by one second."""
        if self.remaining > 0:
            self.remaining -= 1

        if self.remaining <= 0:
            self._stop_ticking()
            self.post_message(self.Expired())
