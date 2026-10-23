"""Password hashing and login tokens."""
from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from .core.errors import AuthenticationFailed


class PasswordHasher:
    """bcrypt: slow on purpose and salted, so stolen hashes are hard to reverse."""

    def __init__(self):
        self._context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash(self, password: str) -> str:
        return self._context.hash(password)

    def verify(self, password: str, hashed: str) -> bool:
        return self._context.verify(password, hashed)


class TokenService:
    """Signed JWT access tokens (HS256) that expire after a fixed time."""

    ALGORITHM = "HS256"
    INVALID = "Invalid or expired token"

    def __init__(self, secret_key: str, lifetime_minutes: int):
        self._secret = secret_key
        self._lifetime = timedelta(minutes=lifetime_minutes)

    def issue(self, user_id: int) -> str:
        expires = datetime.now(timezone.utc) + self._lifetime
        return jwt.encode({"sub": str(user_id), "exp": expires}, self._secret, algorithm=self.ALGORITHM)

    def user_id_from(self, token: str) -> int:
        try:
            return int(jwt.decode(token, self._secret, algorithms=[self.ALGORITHM])["sub"])
        except (jwt.PyJWTError, ValueError, KeyError):
            raise AuthenticationFailed(self.INVALID)
