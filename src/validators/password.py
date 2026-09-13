import re


def validate_password(password: str) -> str:
    pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z0-9]+$"

    if not re.match(pattern, password) or len(password) < 8:
        raise ValueError(
            "Password must contain only Latin letters and digits, "
            "with at least one uppercase letter, one lowercase letter, and one digit."
        )

    return password
