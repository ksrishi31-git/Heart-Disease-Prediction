import hashlib

from app.core.config import get_settings


def hash_ip(ip: str) -> str:
    settings = get_settings()
    return hashlib.sha256(f"{settings.AUDIT_SALT}:{ip}".encode()).hexdigest()
