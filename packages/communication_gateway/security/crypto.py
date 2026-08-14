from __future__ import annotations

import base64
import hashlib
import hmac
import secrets

from cryptography.fernet import Fernet, InvalidToken


class SecretBox:
    """Encrypt provider secrets and OAuth tokens at rest."""

    def __init__(self, encryption_key: str | None) -> None:
        self._fernet = Fernet(self._derive_key(encryption_key))

    @staticmethod
    def _derive_key(encryption_key: str | None) -> bytes:
        raw = (encryption_key or "beacon-dev-only-change-me").encode("utf-8")
        digest = hashlib.sha256(raw).digest()
        return base64.urlsafe_b64encode(digest)

    def encrypt(self, value: str) -> str:
        return self._fernet.encrypt(value.encode("utf-8")).decode("utf-8")

    def decrypt(self, token: str) -> str:
        try:
            return self._fernet.decrypt(token.encode("utf-8")).decode("utf-8")
        except InvalidToken as exc:
            raise ValueError("Unable to decrypt secret") from exc

    def redact(self, value: str | None, *, keep: int = 4) -> str:
        if not value:
            return ""
        if len(value) <= keep:
            return "*" * len(value)
        return f"{value[:keep]}…{'*' * 8}"


def constant_time_compare(left: str, right: str) -> bool:
    return hmac.compare_digest(left.encode("utf-8"), right.encode("utf-8"))


def generate_verify_token() -> str:
    return secrets.token_urlsafe(32)


def hmac_sha256_hex(secret: str, payload: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
