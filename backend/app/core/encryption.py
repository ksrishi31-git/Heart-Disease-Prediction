import argparse
import base64
import hashlib
import os
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import get_settings

NONCE_SIZE = 12
TAG_SIZE = 16


def _derive_key(key_material: str) -> bytes:
    key_material = key_material.strip()
    try:
        decoded = base64.b64decode(key_material, validate=True)
        if len(decoded) == 32:
            return decoded
    except Exception:
        pass
    return hashlib.sha256(key_material.encode("utf-8")).digest()


def get_encryption_key() -> bytes:
    settings = get_settings()
    if not settings.ENCRYPTION_KEY or settings.ENCRYPTION_KEY in ("", "CHANGE_ME"):
        raise RuntimeError(
            "ENCRYPTION_KEY is not configured. Copy backend/.env.example to "
            "backend/.env and run: python -m app.core.encryption --generate-key"
        )
    return _derive_key(settings.ENCRYPTION_KEY)


def encrypt_bytes(plaintext: bytes, key: bytes | None = None) -> bytes:
    key = key or get_encryption_key()
    nonce = os.urandom(NONCE_SIZE)
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, None)
    return nonce + ciphertext


def decrypt_bytes(payload: bytes, key: bytes | None = None) -> bytes:
    key = key or get_encryption_key()
    nonce, ciphertext = payload[:NONCE_SIZE], payload[NONCE_SIZE:]
    return AESGCM(key).decrypt(nonce, ciphertext, None)


def encrypt_data(data: bytes) -> str:
    return base64.urlsafe_b64encode(encrypt_bytes(data)).decode("ascii")


def decrypt_data(token: str) -> bytes:
    payload = base64.urlsafe_b64decode(token.encode("ascii"))
    return decrypt_bytes(payload)


def encrypt_str(text: str) -> str:
    return encrypt_data(text.encode("utf-8"))


def decrypt_str(token: str) -> str:
    return decrypt_data(token).decode("utf-8")


def encrypt_file(src: Path, dst: Path, key: bytes | None = None) -> None:
    plaintext = src.read_bytes()
    dst.write_bytes(encrypt_bytes(plaintext, key=key))


def decrypt_file(src: Path, dst: Path, key: bytes | None = None) -> None:
    payload = src.read_bytes()
    dst.write_bytes(decrypt_bytes(payload, key=key))


def generate_key() -> str:
    import secrets

    return base64.b64encode(secrets.token_bytes(32)).decode("ascii")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Encryption helpers")
    parser.add_argument("--generate-key", action="store_true",
                        help="Print a fresh ENCRYPTION_KEY value")
    args = parser.parse_args()
    if args.generate_key:
        print(generate_key())
