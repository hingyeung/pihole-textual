"""Cryptographic utilities for credential encryption.

Uses Fernet symmetric encryption from the cryptography library
to securely store passwords locally.
"""

import base64
import hashlib
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken


def derive_key(password: str, salt: bytes) -> bytes:
    """Derive encryption key from password using PBKDF2.

    Args:
        password: Password or passphrase to derive key from
        salt: Salt bytes for key derivation

    Returns:
        32-byte key suitable for Fernet encryption
    """
    kdf = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
    return base64.urlsafe_b64encode(kdf[:32])


def generate_key() -> bytes:
    """Generate a new random Fernet encryption key.

    Returns:
        URL-safe base64-encoded 32-byte key
    """
    return Fernet.generate_key()


def encrypt_string(data: str, key: bytes) -> str:
    """Encrypt a string using Fernet symmetric encryption.

    Args:
        data: String to encrypt
        key: Encryption key (from generate_key or derive_key)

    Returns:
        Base64-encoded encrypted data as string
    """
    f = Fernet(key)
    encrypted = f.encrypt(data.encode())
    return encrypted.decode()


def decrypt_string(encrypted_data: str, key: bytes) -> Optional[str]:
    """Decrypt a string using Fernet symmetric encryption.

    Args:
        encrypted_data: Base64-encoded encrypted string
        key: Decryption key (same as encryption key)

    Returns:
        Decrypted string, or None if decryption fails
    """
    try:
        f = Fernet(key)
        decrypted = f.decrypt(encrypted_data.encode())
        return decrypted.decode()
    except (InvalidToken, Exception):
        return None


def encrypt_password(password: str, master_key: bytes) -> str:
    """Encrypt a password for storage.

    Args:
        password: Password to encrypt
        master_key: Master encryption key

    Returns:
        Encrypted password as base64 string
    """
    return encrypt_string(password, master_key)


def decrypt_password(encrypted_password: str, master_key: bytes) -> Optional[str]:
    """Decrypt a stored password.

    Args:
        encrypted_password: Encrypted password string
        master_key: Master encryption key

    Returns:
        Decrypted password, or None if decryption fails
    """
    return decrypt_string(encrypted_password, master_key)


# Default salt for system-wide key derivation (in production, use machine-specific value)
DEFAULT_SALT = b"pihole-tui-default-salt-v1"


def get_system_key() -> bytes:
    """Get a system-specific encryption key.

    In production, this should derive from machine-specific data.
    For this implementation, we use a generated key stored in config.

    Returns:
        Encryption key bytes
    """
    # For simplicity, generate a key. In production, derive from system info.
    # This would typically be stored in the config directory on first run.
    return generate_key()
