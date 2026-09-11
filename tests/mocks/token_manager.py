from typing import Optional
from datetime import timedelta

from security.interfaces import JWTAuthManagerInterface


class MockJWTAuthManager(JWTAuthManagerInterface):
    def create_access_token(
        self, data: dict, expires_delta: Optional[timedelta] = None
    ) -> str:
        return "mocked_access_token"

    def create_refresh_token(
        self, data: dict, expires_delta: Optional[timedelta] = None
    ) -> str:
        return "mocked_refresh_token"

    def decode_access_token(self, token: str) -> dict:
        return {"sub": "1", "email": "user@example.com"}

    def decode_refresh_token(self, token: str) -> dict:
        return {"sub": "1", "email": "user@example.com"}

    def verify_refresh_token_or_raise(self, token: str) -> None:
        pass

    def verify_access_token_or_raise(self, token: str) -> None:
        pass
