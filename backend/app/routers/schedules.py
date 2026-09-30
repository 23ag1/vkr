import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

import app.services.schedules as schedule_service
from app.deps import get_db, require_role
from app.schemas.common import ApiResponse, ok
from app.schemas.schedules import ScheduleCreate, ScheduleResponse

router = APIRouter()

_admin = Depends(require_role("admin"))


@router.get("/", response_model=ApiResponse[list[ScheduleResponse]], dependencies=[_admin])
async def list_schedules(db: AsyncSession = Depends(get_db)):
    schedules = await schedule_service.list_schedules(db)
    return ok([ScheduleResponse.model_validate(s) for s in schedules])


@router.post("/", response_model=ApiResponse[ScheduleResponse],
             status_code=status.HTTP_201_CREATED, dependencies=[_admin])
async def create_schedule(body: ScheduleCreate, db: AsyncSession = Depends(get_db)):
    schedule = await schedule_service.create_schedule(db, body)
    return ok(ScheduleResponse.model_validate(schedule))


@router.delete("/{schedule_id}", response_model=ApiResponse[None], dependencies=[_admin])
async def delete_schedule(schedule_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    await schedule_service.delete_schedule(db, schedule_id)
    return ok(None)


@router.post("/{schedule_id}/trigger", response_model=ApiResponse[dict], dependencies=[_admin])
async def trigger_schedule(schedule_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await schedule_service.trigger_schedule(db, schedule_id)
    return ok(result)
