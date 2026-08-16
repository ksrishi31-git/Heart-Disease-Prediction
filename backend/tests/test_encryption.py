import os
import pytest

from app.core import encryption
from app.core.config import get_settings


def test_round_trip_bytes():
    key = os.urandom(32)
    plaintext = b"secret patient data"
    encrypted = encryption.encrypt_bytes(plaintext, key=key)
    assert encrypted != plaintext
    assert encryption.decrypt_bytes(encrypted, key=key) == plaintext


def test_round_trip_string():
    text = '{"age": 58, "sex": "Male"}'
    token = encryption.encrypt_str(text)
    assert token != text
    assert encryption.decrypt_str(token) == text


def test_unique_nonce_per_operation():
    key = os.urandom(32)
    plaintext = b"same input"
    first = encryption.encrypt_bytes(plaintext, key=key)
    second = encryption.encrypt_bytes(plaintext, key=key)
    assert first != second


def test_tamper_detection():
    key = os.urandom(32)
    encrypted = bytearray(encryption.encrypt_bytes(b"important", key=key))
    encrypted[-1] ^= 0x01
    with pytest.raises(Exception):
        encryption.decrypt_bytes(bytes(encrypted), key=key)


def test_wrong_key_fails():
    plaintext = b"hello"
    encrypted = encryption.encrypt_bytes(plaintext, key=os.urandom(32))
    with pytest.raises(Exception):
        encryption.decrypt_bytes(encrypted, key=os.urandom(32))


def test_missing_key_raises(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "ENCRYPTION_KEY", "")
    with pytest.raises(RuntimeError, match="ENCRYPTION_KEY"):
        encryption.get_encryption_key()


def test_file_round_trip(tmp_path):
    key = os.urandom(32)
    src = tmp_path / "model.joblib"
    src.write_bytes(b"\x80\x04model-bytes")
    dst = tmp_path / "model.enc"
    out = tmp_path / "model.decrypted"

    encryption.encrypt_file(src, dst, key=key)
    assert dst.exists()
    assert dst.read_bytes() != src.read_bytes()

    encryption.decrypt_file(dst, out, key=key)
    assert out.read_bytes() == src.read_bytes()


def test_generate_key_is_base64_32_bytes():
    import base64

    key = encryption.generate_key()
    assert len(base64.b64decode(key)) == 32
