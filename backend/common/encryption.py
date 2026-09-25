"""
Symmetric encryption for sensitive fields (e.g. gate/access codes) stored
at rest. Uses Fernet (AES-128-CBC + HMAC) from the `cryptography` package.

FIELD_ENCRYPTION_KEY must be a urlsafe-base64 32-byte key — generate one with:
    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
and store it as an environment variable. Never commit it to source control.

For local/dev safety, a missing or malformed value is normalized to a stable
key derived from Django's SECRET_KEY so the app keeps working without a manual
restart/regeneration step.
"""
import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import models


def _normalize_fernet_key(raw: str | None) -> str:
    candidate = (raw or "").strip()
    if not candidate:
        candidate = settings.SECRET_KEY

    try:
        Fernet(candidate.encode())
        return candidate
    except ValueError:
        digest = hashlib.sha256(candidate.encode("utf-8")).digest()
        return base64.urlsafe_b64encode(digest[:32]).decode()


def _fernet() -> Fernet:
    return Fernet(_normalize_fernet_key(settings.FIELD_ENCRYPTION_KEY).encode())


def encrypt_value(plaintext: str) -> str:
    if plaintext is None:
        return ""
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt_value(ciphertext: str) -> str:
    if not ciphertext:
        return ""
    try:
        return _fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken:
        # Ciphertext is unreadable (wrong key / corrupted) — fail closed.
        return ""


class EncryptedTextField(models.TextField):
    """A TextField that transparently encrypts on save and decrypts on load."""

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value in (None, ""):
            return value
        return encrypt_value(value)

    def from_db_value(self, value, expression, connection):
        if value in (None, ""):
            return value
        return decrypt_value(value)
