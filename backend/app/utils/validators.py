import re

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_email(email: str) -> str | None:
    if not EMAIL_RE.match(email):
        return "Please enter a valid email address."
    return None


def validate_password(password: str) -> str | None:
    if len(password) < 8:
        return "Password must be at least 8 characters long."
    if len(password) > 128:
        return "Password must be at most 128 characters long."
    if not re.search(r"[A-Z]", password):
        return "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return "Password must contain at least one lowercase letter."
    if not re.search(r"\d", password):
        return "Password must contain at least one digit."
    return None


def validate_name(name: str) -> str | None:
    if len(name.strip()) < 2:
        return "Name must be at least 2 characters long."
    if len(name) > 120:
        return "Name must be at most 120 characters long."
    return None
