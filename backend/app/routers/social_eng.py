import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

import app.services.social_eng_sim as sim_service
from app.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.common import ApiResponse, ok

router = APIRouter()


class StartRequest(BaseModel):
    scenario_id: str


class TurnRequest(BaseModel):
    message: str


@router.get("/scenarios", response_model=ApiResponse[list[dict]])
async def list_scenarios(_: User = Depends(get_current_user)):
    return ok(sim_service.get_scenarios())


@router.post("/start", response_model=ApiResponse[dict])
async def start(
    body: StartRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await sim_service.start_simulation(db, user_id=current_user.id, scenario_id=body.scenario_id)
    return ok(result)


@router.post("/sessions/{session_id}/turn", response_model=ApiResponse[dict])
async def turn(
    session_id: uuid.UUID,
    body: TurnRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await sim_service.simulation_turn(
        db, session_id=session_id, user_id=current_user.id, user_message=body.message
    )
    return ok(result)
