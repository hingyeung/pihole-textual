"""Configuration file management for Pi-hole TUI.

Handles reading and writing config.toml for user preferences and
connections.enc for encrypted connection profiles.
"""

import json
import os
from pathlib import Path
from typing import List, Optional

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # type: ignore

from pihole_tui.constants import CONFIG_DIR_NAME, CONFIG_FILE_NAME, CONNECTIONS_FILE_NAME
from pihole_tui.models.config import ConnectionProfile, UserPreferences
from pihole_tui.utils.crypto import decrypt_string, encrypt_string, generate_key


class ConfigManager:
    """Manages configuration file operations."""

    def __init__(self):
        """Initialize configuration manager with config directory."""
        self.config_dir = self._get_config_dir()
        self.config_file = self.config_dir / CONFIG_FILE_NAME
        self.connections_file = self.config_dir / CONNECTIONS_FILE_NAME
        self.key_file = self.config_dir / ".key"

        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Initialize or load encryption key
        self._encryption_key = self._load_or_create_key()

    def _get_config_dir(self) -> Path:
        """Get the configuration directory path based on OS."""
        if os.name == "nt":  # Windows
            base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        else:  # Linux, macOS, etc.
            base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))

        return base / CONFIG_DIR_NAME

    def _load_or_create_key(self) -> bytes:
        """Load existing encryption key or create a new one."""
        if self.key_file.exists():
            with open(self.key_file, "rb") as f:
                return f.read()
        else:
            # Generate new key
            key = generate_key()
            with open(self.key_file, "wb") as f:
                f.write(key)
            # Set restrictive permissions (owner read/write only)
            self.key_file.chmod(0o600)
            return key

    def load_preferences(self) -> UserPreferences:
        """Load user preferences from config.toml.

        Returns:
            UserPreferences object with loaded or default values
        """
        if not self.config_file.exists():
            return UserPreferences()

        try:
            with open(self.config_file, "rb") as f:
                data = tomllib.load(f)

            # Extract preferences section
            prefs_data = data.get("preferences", {})
            return UserPreferences(**prefs_data)
        except Exception:
            # Return defaults if file is corrupted
            return UserPreferences()

    def save_preferences(self, preferences: UserPreferences) -> bool:
        """Save user preferences to config.toml.

        Args:
            preferences: UserPreferences object to save

        Returns:
            True if successful, False otherwise
        """
        try:
            # Load existing config or create new
            if self.config_file.exists():
                with open(self.config_file, "rb") as f:
                    data = tomllib.load(f)
            else:
                data = {}

            # Update preferences section
            data["preferences"] = preferences.model_dump()

            # Write TOML file
            with open(self.config_file, "w") as f:
                self._write_toml(f, data)

            return True
        except Exception:
            return False

    def load_connection_profiles(self) -> List[ConnectionProfile]:
        """Load connection profiles from encrypted file.

        Returns:
            List of ConnectionProfile objects
        """
        if not self.connections_file.exists():
            return []

        try:
            with open(self.connections_file, "r") as f:
                encrypted_data = f.read()

            # Decrypt the data
            decrypted = decrypt_string(encrypted_data, self._encryption_key)
            if decrypted is None:
                return []

            # Parse JSON
            profiles_data = json.loads(decrypted)
            return [ConnectionProfile(**profile) for profile in profiles_data]
        except Exception:
            return []

    def save_connection_profiles(self, profiles: List[ConnectionProfile]) -> bool:
        """Save connection profiles to encrypted file.

        Args:
            profiles: List of ConnectionProfile objects to save

        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert to JSON
            profiles_data = [profile.model_dump(mode="json") for profile in profiles]
            json_data = json.dumps(profiles_data, default=str, indent=2)

            # Encrypt the data
            encrypted = encrypt_string(json_data, self._encryption_key)

            # Write to file
            with open(self.connections_file, "w") as f:
                f.write(encrypted)

            # Set restrictive permissions
            self.connections_file.chmod(0o600)

            return True
        except Exception:
            return False

    def get_active_profile(self) -> Optional[ConnectionProfile]:
        """Get the currently active connection profile.

        Returns:
            Active ConnectionProfile or None if no active profile
        """
        profiles = self.load_connection_profiles()
        for profile in profiles:
            if profile.is_active:
                return profile
        return None

    def set_active_profile(self, profile_name: str) -> bool:
        """Set a profile as active and deactivate others.

        Args:
            profile_name: Name of profile to activate

        Returns:
            True if successful, False if profile not found
        """
        profiles = self.load_connection_profiles()
        found = False

        for profile in profiles:
            if profile.name == profile_name:
                profile.is_active = True
                found = True
            else:
                profile.is_active = False

        if found:
            return self.save_connection_profiles(profiles)
        return False

    def _write_toml(self, f, data: dict, indent: int = 0):
        """Write data as TOML format (simple implementation).

        Args:
            f: File object to write to
            data: Dictionary to write
            indent: Current indentation level
        """
        indent_str = "  " * indent

        for key, value in data.items():
            if isinstance(value, dict):
                # Write section header
                f.write(f"\n{indent_str}[{key}]\n")
                # Write section contents
                for k, v in value.items():
                    self._write_toml_value(f, k, v, indent + 1)
            else:
                self._write_toml_value(f, key, value, indent)

    def _write_toml_value(self, f, key: str, value, indent: int):
        """Write a single TOML key-value pair."""
        indent_str = "  " * indent

        if isinstance(value, bool):
            f.write(f"{indent_str}{key} = {str(value).lower()}\n")
        elif isinstance(value, (int, float)):
            f.write(f"{indent_str}{key} = {value}\n")
        elif isinstance(value, str):
            # Escape quotes in string
            escaped = value.replace('"', '\\"')
            f.write(f'{indent_str}{key} = "{escaped}"\n')
        elif isinstance(value, list):
            items = ", ".join(f'"{item}"' if isinstance(item, str) else str(item) for item in value)
            f.write(f"{indent_str}{key} = [{items}]\n")
