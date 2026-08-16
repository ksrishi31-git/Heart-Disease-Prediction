from app.db.database import SessionLocal
from app.db.models import AuditLog
from app.utils.hashing import hash_ip


def log_action(action: str, user_id: int | None = None,
               ip: str | None = None, success: bool = True) -> None:
    db = SessionLocal()
    try:
        entry = AuditLog(
            action=action,
            user_id=user_id,
            ip_hash=hash_ip(ip) if ip else None,
            success=success,
        )
        db.add(entry)
        db.commit()
    finally:
        db.close()
