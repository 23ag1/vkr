import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

import app.services.phishing_campaigns as campaign_service
import app.services.phishing_templates as template_service
from app.deps import get_current_user, get_db, require_role
from app.models.user import User
from app.schemas.common import ApiResponse, ok
from app.schemas.phishing import (
    CampaignCreate,
    CampaignResponse,
    InboxItem,
    RecipientResult,
    TemplateCreate,
    TemplateResponse,
    TemplateUpdate,
)

router = APIRouter()

_admin = Depends(require_role("admin"))
_privileged = Depends(require_role("admin", "security_specialist"))


@router.get("/templates", response_model=ApiResponse[list[TemplateResponse]], dependencies=[_privileged])
async def list_templates(db: AsyncSession = Depends(get_db)):
    return ok([TemplateResponse.model_validate(t) for t in await template_service.list_templates(db)])


@router.post("/templates", response_model=ApiResponse[TemplateResponse],
             status_code=status.HTTP_201_CREATED, dependencies=[_admin])
async def create_template(body: TemplateCreate, db: AsyncSession = Depends(get_db)):
    return ok(TemplateResponse.model_validate(await template_service.create_template(db, body)))


@router.get("/templates/{template_id}", response_model=ApiResponse[TemplateResponse],
            dependencies=[_privileged])
async def get_template(template_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return ok(TemplateResponse.model_validate(await template_service.get_template(db, template_id)))


@router.put("/templates/{template_id}", response_model=ApiResponse[TemplateResponse],
            dependencies=[_admin])
async def update_template(template_id: uuid.UUID, body: TemplateUpdate,
                          db: AsyncSession = Depends(get_db)):
    return ok(TemplateResponse.model_validate(
        await template_service.update_template(db, template_id, body)
    ))


@router.delete("/templates/{template_id}", response_model=ApiResponse[None], dependencies=[_admin])
async def delete_template(template_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    await template_service.delete_template(db, template_id)
    return ok(None)


@router.get("/campaigns", response_model=ApiResponse[list[CampaignResponse]],
            dependencies=[_privileged])
async def list_campaigns(db: AsyncSession = Depends(get_db)):
    return ok([CampaignResponse.model_validate(c) for c in await campaign_service.list_campaigns(db)])


@router.post("/campaigns", response_model=ApiResponse[CampaignResponse],
             status_code=status.HTTP_201_CREATED, dependencies=[_admin])
async def create_campaign(
    body: CampaignCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    campaign = await campaign_service.create_campaign(db, body, current_user.id)
    return ok(CampaignResponse.model_validate(campaign))


@router.post("/campaigns/{campaign_id}/launch", response_model=ApiResponse[CampaignResponse],
             dependencies=[_admin])
async def launch_campaign(campaign_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return ok(CampaignResponse.model_validate(await campaign_service.launch_campaign(db, campaign_id)))


@router.post("/campaigns/{campaign_id}/complete", response_model=ApiResponse[CampaignResponse],
             dependencies=[_admin])
async def complete_campaign(campaign_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return ok(CampaignResponse.model_validate(await campaign_service.complete_campaign(db, campaign_id)))


@router.get("/campaigns/{campaign_id}/results", response_model=ApiResponse[list[RecipientResult]],
            dependencies=[_privileged])
async def get_results(campaign_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return ok([RecipientResult.model_validate(r) for r in await campaign_service.get_results(db, campaign_id)])


@router.get("/my-inbox", response_model=ApiResponse[list[InboxItem]])
async def my_inbox(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items = await campaign_service.get_my_inbox(db, current_user.id)
    return ok([InboxItem.model_validate(i) for i in items])


@router.post("/report/{token}", response_model=ApiResponse[None])
async def report_phishing(
    token: str,
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await campaign_service.record_tracking_event(db, token, "reported_at")
    return ok(None)
