import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

import app.services.audit as audit_service
from app.deps import get_db, require_role
from app.schemas.audit import AuditLogResponse
from app.schemas.common import ApiResponse, ok

router = APIRouter()

_privileged = Depends(require_role("admin", "security_specialist"))


@router.get("", response_model=ApiResponse[list[AuditLogResponse]], dependencies=[_privileged])
async def list_audit(
    user_id: uuid.UUID | None = Query(None),
    action: str | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    logs = await audit_service.list_logs(
        db,
        user_id=user_id,
        action=action,
        date_from=date_from,
        date_to=date_to,
        page=page,
        limit=limit,
    )
    return ok([AuditLogResponse.model_validate(l) for l in logs])


@router.get("/export", dependencies=[_privileged])
async def export_audit(
    user_id: uuid.UUID | None = Query(None),
    action: str | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    format: str = Query("csv"),
    db: AsyncSession = Depends(get_db),
):
    csv_text = await audit_service.export_csv(
        db,
        user_id=user_id,
        action=action,
        date_from=date_from,
        date_to=date_to,
    )
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit_log.csv"},
    )
