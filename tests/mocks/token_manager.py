from typing import Optional
from datetime import timedelta

from exceptions.security import InvalidTokenError, TokenExpiredError
from security.interfaces import JWTAuthManagerInterface


class MockJWTAuthManager(JWTAuthManagerInterface):
    def valid_token_or_raise(self, token: str) -> None:
        if token == "invalid_token":
            raise InvalidTokenError
        if token == "expired_token":
            raise TokenExpiredError

    def create_access_token(
        self, data: dict, expires_delta: Optional[timedelta] = None
    ) -> str:
        return "mocked_access_token"

    def create_refresh_token(
        self, data: dict, expires_delta: Optional[timedelta] = None
    ) -> str:
        return "mocked_refresh_token"

    def decode_access_token(self, token: str) -> dict:
        self.valid_token_or_raise(token)
        return {"user_id": 1, "email": "user@example.com"}

    def decode_refresh_token(self, token: str) -> dict:
        self.valid_token_or_raise(token)
        return {"user_id": 1, "email": "user@example.com"}

    def verify_refresh_token_or_raise(self, token: str) -> None:
        self.valid_token_or_raise(token)

    def verify_access_token_or_raise(self, token: str) -> None:
        self.valid_token_or_raise(token)
