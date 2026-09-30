import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

import app.services.audit as audit_service
import app.services.user as user_service
from app.deps import get_db, require_role
from app.models.user import User
from app.schemas.common import ApiResponse, PaginatedResponse, ok, paginated
from app.schemas.user import UserCreate, UserResponse, UserUpdate

router = APIRouter()

_admin = Depends(require_role("admin"))


@router.get("", response_model=PaginatedResponse[UserResponse], dependencies=[_admin])
async def list_users(
    skip: int = 0, limit: int = 20, db: AsyncSession = Depends(get_db)
):
    users, total = await user_service.list_users(db, skip=skip, limit=limit)
    return paginated([UserResponse.model_validate(u) for u in users], total=total)


@router.post(
    "", response_model=ApiResponse[UserResponse], status_code=status.HTTP_201_CREATED
)
async def create_user(
    body: UserCreate,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    user = await user_service.create_user(db, body, commit=False)
    await audit_service.write(
        db,
        user_id=current_user.id,
        action="user_created",
        details={"created_user_id": str(user.id), "role": user.role},
        commit=False,
    )
    # Single atomic commit: the new user and its audit row persist together.
    await db.commit()
    return ok(UserResponse.model_validate(user))


@router.get(
    "/{user_id}", response_model=ApiResponse[UserResponse], dependencies=[_admin]
)
async def get_user(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    user = await user_service.get_user(db, user_id)
    return ok(UserResponse.model_validate(user))


@router.put(
    "/{user_id}", response_model=ApiResponse[UserResponse], dependencies=[_admin]
)
async def update_user(
    user_id: uuid.UUID, body: UserUpdate, db: AsyncSession = Depends(get_db)
):
    user = await user_service.update_user(db, user_id, body)
    return ok(UserResponse.model_validate(user))


@router.delete("/{user_id}", response_model=ApiResponse[UserResponse])
async def deactivate_user(
    user_id: uuid.UUID,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    user = await user_service.deactivate_user(db, user_id, commit=False)
    await audit_service.write(
        db,
        user_id=current_user.id,
        action="user_deactivated",
        details={"deactivated_user_id": str(user_id)},
        commit=False,
    )
    # Single atomic commit: the deactivation and its audit row are one transaction.
    await db.commit()
    return ok(UserResponse.model_validate(user))
