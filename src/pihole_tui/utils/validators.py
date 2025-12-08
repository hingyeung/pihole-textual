"""Validation utilities for user input.

Provides validation functions for domains, IP addresses,
and other user-provided data.
"""

import ipaddress
import re
from typing import Optional


def validate_domain(domain: str) -> tuple[bool, Optional[str]]:
    """Validate a domain name or wildcard pattern.

    Args:
        domain: Domain name to validate (e.g., "example.com" or "*.example.com")

    Returns:
        Tuple of (is_valid, error_message). error_message is None if valid.
    """
    if not domain:
        return False, "Domain cannot be empty"

    domain = domain.strip()

    # Check length constraints
    if len(domain) > 253:
        return False, "Domain cannot exceed 253 characters"

    # Handle wildcard patterns
    if domain.startswith("*."):
        # Validate the part after wildcard
        domain_part = domain[2:]
        if not domain_part:
            return False, "Wildcard pattern must have domain after '*'"
        return validate_domain(domain_part)

    # Domain regex pattern
    # Allows alphanumeric, hyphens, and dots
    # Each label (between dots) must be 1-63 chars
    # Cannot start or end with hyphen or dot
    domain_pattern = re.compile(
        r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))*$"
    )

    if not domain_pattern.match(domain):
        return False, "Invalid domain format"

    # Check label lengths
    labels = domain.split(".")
    for label in labels:
        if len(label) > 63:
            return False, f"Domain label '{label}' exceeds 63 characters"
        if not label:
            return False, "Domain cannot have empty labels"

    return True, None


def validate_ip_address(ip: str) -> tuple[bool, Optional[str]]:
    """Validate an IPv4 or IPv6 address.

    Args:
        ip: IP address string to validate

    Returns:
        Tuple of (is_valid, error_message). error_message is None if valid.
    """
    if not ip:
        return False, "IP address cannot be empty"

    ip = ip.strip()

    try:
        ipaddress.ip_address(ip)
        return True, None
    except ValueError:
        return False, "Invalid IP address format"


def validate_hostname_or_ip(value: str) -> tuple[bool, Optional[str]]:
    """Validate a value as either a hostname or IP address.

    Args:
        value: String to validate as hostname or IP

    Returns:
        Tuple of (is_valid, error_message). error_message is None if valid.
    """
    if not value:
        return False, "Hostname/IP cannot be empty"

    # Try IP first
    is_valid_ip, _ = validate_ip_address(value)
    if is_valid_ip:
        return True, None

    # Try domain (hostname)
    is_valid_domain, domain_error = validate_domain(value)
    if is_valid_domain:
        return True, None

    # If neither, return domain error (usually more informative)
    return False, domain_error or "Invalid hostname or IP address"


def validate_port(port: int) -> tuple[bool, Optional[str]]:
    """Validate a port number.

    Args:
        port: Port number to validate

    Returns:
        Tuple of (is_valid, error_message). error_message is None if valid.
    """
    if port < 1 or port > 65535:
        return False, "Port must be between 1 and 65535"
    return True, None


def validate_totp_code(code: str) -> tuple[bool, Optional[str]]:
    """Validate a TOTP (2FA) code.

    Args:
        code: TOTP code to validate

    Returns:
        Tuple of (is_valid, error_message). error_message is None if valid.
    """
    if not code:
        return False, "TOTP code cannot be empty"

    code = code.strip()

    if len(code) != 6:
        return False, "TOTP code must be exactly 6 digits"

    if not code.isdigit():
        return False, "TOTP code must contain only digits"

    return True, None


def validate_timer_duration(duration: int) -> tuple[bool, Optional[str]]:
    """Validate a timer duration in seconds.

    Args:
        duration: Duration in seconds

    Returns:
        Tuple of (is_valid, error_message). error_message is None if valid.
    """
    if duration < 1:
        return False, "Duration must be at least 1 second"

    if duration > 3600:
        return False, "Duration cannot exceed 1 hour (3600 seconds)"

    return True, None
