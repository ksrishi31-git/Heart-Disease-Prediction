from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.security import decode_token

limiter = Limiter(key_func=get_remote_address)


def user_key(request: Request) -> str:
    token = request.cookies.get("access_token")
    try:
        payload = decode_token(token, "access")
        return f"user:{payload['sub']}"
    except Exception:
        return f"ip:{get_remote_address(request)}"
