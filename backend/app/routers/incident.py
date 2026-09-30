from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

import app.services.incident as incident_service
from app.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.common import ApiResponse, ok

router = APIRouter()


class IncidentRequest(BaseModel):
    description: str


@router.post("/report", response_model=ApiResponse[dict])
async def report(
    body: IncidentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await incident_service.report_incident(db, user_id=current_user.id, description=body.description)
    return ok(result)
