import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

import app.services.analytics as analytics_service
from app.services.maturity import compute_maturity
from app.deps import get_current_user, get_db, require_role
from app.models.user import User
from app.core.exceptions import ForbiddenException
from app.schemas.common import ApiResponse, ok

router = APIRouter()

_privileged = Depends(require_role("admin", "manager", "security_specialist"))


@router.get("/overview", response_model=ApiResponse[dict], dependencies=[_privileged])
async def overview(db: AsyncSession = Depends(get_db)):
    data = await analytics_service.get_overview(db)
    return ok(data)


@router.get("/departments", response_model=ApiResponse[list[dict]], dependencies=[_privileged])
async def departments(db: AsyncSession = Depends(get_db)):
    data = await analytics_service.get_departments_analytics(db)
    return ok(data)


@router.get("/maturity", response_model=ApiResponse[dict], dependencies=[_privileged])
async def maturity(db: AsyncSession = Depends(get_db)):
    overview = await analytics_service.get_overview(db)
    return ok(compute_maturity(overview))


@router.get("/briefings", response_model=ApiResponse[list[dict]], dependencies=[_privileged])
async def briefing_stats(db: AsyncSession = Depends(get_db)):
    return ok(await analytics_service.get_briefing_stats(db))


@router.get("/users/{user_id}", response_model=ApiResponse[dict])
async def user_profile(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("admin", "security_specialist") and current_user.id != user_id:
        raise ForbiddenException
    data = await analytics_service.get_user_profile(db, user_id)
    return ok(data)
