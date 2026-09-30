from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

import app.services.admin_llm as admin_llm_service
from app.deps import get_db, require_role
from app.schemas.common import ApiResponse, ok

router = APIRouter()

_privileged = Depends(require_role("admin", "security_specialist"))


class AskRequest(BaseModel):
    question: str


@router.post("/ask", response_model=ApiResponse[str], dependencies=[_privileged])
async def ask(body: AskRequest, db: AsyncSession = Depends(get_db)):
    reply = await admin_llm_service.admin_ask(db, question=body.question)
    return ok(reply)
