import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_not_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("password must not be empty")
        return v


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    mfa_required: bool = False


class MfaSetupResponse(BaseModel):
    secret: str
    otpauth_uri: str


class MfaVerifyRequest(BaseModel):
    code: str


class MfaLoginRequest(BaseModel):
    temp_token: str
    code: str


class UserProfileResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    department_id: uuid.UUID | None = None
    diagnostic_completed_at: datetime | None = None

    model_config = {"from_attributes": True}
