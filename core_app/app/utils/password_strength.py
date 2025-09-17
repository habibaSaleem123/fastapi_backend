from zxcvbn import zxcvbn
from app.core.config.settings import settings

class PasswordTooWeak(Exception):
    def __init__(self, message: str, score: int, feedback: dict):
        super().__init__(message)
        self.score = score
        self.feedback = feedback

def validate_password_strength(password: str, user_inputs: list[str] = []):
    if len(password) < settings.MIN_PASSWORD_LENGTH:
        raise PasswordTooWeak(
            f"Password must be at least {settings.MIN_PASSWORD_LENGTH} characters long",
            score=0,
            feedback={"warning": "Too short", "suggestions": []},
        )
    result = zxcvbn(password, user_inputs=user_inputs)
    score = result.get("score", 0)  # 0-4
    if score < settings.MIN_PASSWORD_SCORE:
        raise PasswordTooWeak(
            "Password is too weak",
            score=score,
            feedback=result.get("feedback", {}) or {},
        )
