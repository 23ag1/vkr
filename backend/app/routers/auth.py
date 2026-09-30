import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import app.services.audit as audit_service
import app.services.auth as _auth_service
import app.services.mfa as mfa_service
from app.core.exceptions import CredentialsException
from app.core.security import decode_token, create_access_token
from app.deps import bearer_scheme, get_current_user, get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest, TokenResponse, UserProfileResponse,
    MfaSetupResponse, MfaVerifyRequest, MfaLoginRequest,
)
from app.schemas.common import ApiResponse, ok

router = APIRouter()


@router.post("/login", response_model=ApiResponse[TokenResponse])
async def login(body: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    user = await _auth_service.authenticate_user(db, body.email, body.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if user.mfa_enabled:
        # issue a short-lived temp token scoped only to MFA challenge
        temp_token = create_access_token({"sub": str(user.id), "token_type": "mfa_challenge"})
        return ok(TokenResponse(
            access_token=temp_token,
            refresh_token="",
            mfa_required=True,
        ))

    tokens = _auth_service.build_token_pair(user)
    await audit_service.write(
        db, user_id=user.id, action="login",
        details={"role": user.role},
        ip_address=request.client.host if request.client else None,
    )
    return ok(TokenResponse(**tokens))


@router.post("/mfa/complete", response_model=ApiResponse[TokenResponse])
async def mfa_complete(body: MfaLoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(body.temp_token)
        if payload.get("token_type") != "mfa_challenge":
            raise ValueError("not an mfa token")
        user_id = payload["sub"]
    except (JWTError, ValueError, KeyError):
        raise CredentialsException

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    if not mfa_service.check_totp(user, body.code):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid MFA code")

    tokens = _auth_service.build_token_pair(user)
    await audit_service.write(
        db, user_id=user.id, action="login",
        details={"role": user.role, "mfa": True},
        ip_address=request.client.host if request.client else None,
    )
    return ok(TokenResponse(**tokens))


@router.post("/mfa/setup", response_model=ApiResponse[MfaSetupResponse])
async def mfa_setup(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role not in ("admin", "security_specialist"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="MFA setup restricted to admins")
    result = await mfa_service.setup_mfa(db, current_user)
    return ok(MfaSetupResponse(**result))


@router.post("/mfa/verify", response_model=ApiResponse[dict])
async def mfa_verify(
    body: MfaVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ok_flag = await mfa_service.verify_and_enable_mfa(db, current_user, body.code)
    if not ok_flag:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid code")
    return ok({"mfa_enabled": True})


@router.post("/refresh", response_model=ApiResponse[TokenResponse])
async def refresh(
    db: AsyncSession = Depends(get_db),
    credentials=Depends(bearer_scheme),
):
    if credentials is None:
        raise CredentialsException
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("token_type") != "refresh":
            raise ValueError("not a refresh token")
        user_id = payload["sub"]
    except (JWTError, ValueError, KeyError):
        raise CredentialsException

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return ok(TokenResponse(**_auth_service.build_token_pair(user)))


@router.get("/me", response_model=ApiResponse[UserProfileResponse])
async def me(current_user: User = Depends(get_current_user)):
    return ok(UserProfileResponse.model_validate(current_user))
