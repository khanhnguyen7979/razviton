from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


def _trim_str(v: str) -> str:
    return v.strip()


class RegisterRequest(BaseModel):
    @field_validator("username", "email", mode="before")
    @classmethod
    def trim_identity(cls, value):
        return value.strip() if isinstance(value, str) else value

    username: str = Field(min_length=3, max_length=100)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)

    def normalized_email(self) -> str:
        return self.email.strip().lower()

    def normalized_username(self) -> str:
        return self.username.strip().lower()


class LoginRequest(BaseModel):
    @field_validator("identifier", mode="before")
    @classmethod
    def trim_identifier(cls, value):
        return value.strip() if isinstance(value, str) else value

    identifier: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)

    def normalized_identifier(self) -> str:
        return self.identifier.strip().lower()


class LogoutRequest(BaseModel):
    all_devices: bool = False


class UserMe(BaseModel):
    id: int
    username: str
    email: str
    is_admin: bool
    full_name: str | None = None


class MessageResponse(BaseModel):
    ok: bool = True
    message: str
