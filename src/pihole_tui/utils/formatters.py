"""Data formatting utilities for display.

Provides formatters for time, percentages, file sizes, and other
data types displayed in the TUI.
"""

from datetime import datetime, timedelta
from typing import Optional


def format_percentage(value: float, decimals: int = 1) -> str:
    """Format a float as a percentage string.

    Args:
        value: Percentage value (0-100)
        decimals: Number of decimal places (default: 1)

    Returns:
        Formatted percentage string (e.g., "21.5%")
    """
    return f"{value:.{decimals}f}%"


def format_number(value: int, use_separators: bool = True) -> str:
    """Format an integer with thousand separators.

    Args:
        value: Integer to format
        use_separators: Whether to use comma separators (default: True)

    Returns:
        Formatted number string (e.g., "1,234,567")
    """
    if use_separators:
        return f"{value:,}"
    return str(value)


def format_relative_time(dt: datetime) -> str:
    """Format a datetime as relative time string (e.g., '5 minutes ago').

    Args:
        dt: Datetime to format

    Returns:
        Relative time string
    """
    now = datetime.now()

    # Ensure dt is timezone-naive for comparison
    if dt.tzinfo is not None:
        dt = dt.replace(tzinfo=None)

    diff = now - dt

    # Future times
    if diff.total_seconds() < 0:
        diff = -diff
        suffix = "from now"
    else:
        suffix = "ago"

    # Less than a minute
    if diff.total_seconds() < 60:
        return "just now" if suffix == "ago" else "in a moment"

    # Minutes
    if diff.total_seconds() < 3600:
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} {suffix}"

    # Hours
    if diff.total_seconds() < 86400:
        hours = int(diff.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} {suffix}"

    # Days
    days = diff.days
    if days < 7:
        return f"{days} day{'s' if days != 1 else ''} {suffix}"

    # Weeks
    weeks = days // 7
    if weeks < 4:
        return f"{weeks} week{'s' if weeks != 1 else ''} {suffix}"

    # Months (approximate)
    months = days // 30
    if months < 12:
        return f"{months} month{'s' if months != 1 else ''} {suffix}"

    # Years
    years = days // 365
    return f"{years} year{'s' if years != 1 else ''} {suffix}"


def format_absolute_time(dt: datetime, include_seconds: bool = True) -> str:
    """Format a datetime as absolute time string.

    Args:
        dt: Datetime to format
        include_seconds: Whether to include seconds (default: True)

    Returns:
        Formatted time string (e.g., "2025-12-05 14:30:45")
    """
    if include_seconds:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return dt.strftime("%Y-%m-%d %H:%M")


def format_datetime(
    dt: datetime, mode: str = "relative", include_seconds: bool = True
) -> str:
    """Format a datetime based on display mode preference.

    Args:
        dt: Datetime to format
        mode: Format mode - "relative" or "absolute"
        include_seconds: Whether to include seconds in absolute mode

    Returns:
        Formatted datetime string
    """
    if mode == "relative":
        return format_relative_time(dt)
    return format_absolute_time(dt, include_seconds)


def format_duration(seconds: int) -> str:
    """Format a duration in seconds as human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration (e.g., "5m 30s", "2h 15m")
    """
    if seconds < 60:
        return f"{seconds}s"

    if seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        if remaining_seconds > 0:
            return f"{minutes}m {remaining_seconds}s"
        return f"{minutes}m"

    hours = seconds // 3600
    remaining_minutes = (seconds % 3600) // 60
    if remaining_minutes > 0:
        return f"{hours}h {remaining_minutes}m"
    return f"{hours}h"


def format_countdown(expires_at: datetime) -> str:
    """Format a countdown to a future datetime.

    Args:
        expires_at: Target datetime

    Returns:
        Countdown string (e.g., "5m 30s remaining")
    """
    now = datetime.now()

    # Ensure timezone-naive for comparison
    if expires_at.tzinfo is not None:
        expires_at = expires_at.replace(tzinfo=None)

    if now >= expires_at:
        return "Expired"

    diff = expires_at - now
    seconds = int(diff.total_seconds())

    return f"{format_duration(seconds)} remaining"


def format_file_size(size_bytes: int) -> str:
    """Format file size in bytes to human-readable string.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string (e.g., "1.5 MB")
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def format_response_time(ms: int) -> str:
    """Format response time in milliseconds.

    Args:
        ms: Response time in milliseconds

    Returns:
        Formatted response time (e.g., "12ms" or "1.2s")
    """
    if ms < 1000:
        return f"{ms}ms"
    return f"{ms / 1000:.1f}s"
