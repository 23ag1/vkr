import logging
import secrets
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

import app.services.audit as audit_service
import app.services.learning as learning_service
from app.core.exceptions import NotFoundException
from app.models.learning import UserModuleProgress
from app.models.module import Module
from app.models.phishing import PhishingCampaign, PhishingRecipient, PhishingTemplate
from app.schemas.common import CampaignStatus
from app.schemas.phishing import CampaignCreate

_REMEDIATION_ROLE = "phishing_remediation"

logger = logging.getLogger(__name__)


async def list_campaigns(db: AsyncSession) -> list[PhishingCampaign]:
    result = await db.execute(
        select(PhishingCampaign).order_by(PhishingCampaign.created_at.desc())
    )
    campaigns = result.scalars().all()
    logger.info("phishing_campaign.list count=%d", len(campaigns))
    return campaigns


async def get_campaign(db: AsyncSession, campaign_id: uuid.UUID) -> PhishingCampaign:
    result = await db.execute(
        select(PhishingCampaign).where(PhishingCampaign.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()
    if campaign is None:
        logger.warning("phishing_campaign.not_found id=%s", campaign_id)
        raise NotFoundException
    return campaign


async def create_campaign(
    db: AsyncSession, data: CampaignCreate, created_by: uuid.UUID
) -> PhishingCampaign:
    campaign = PhishingCampaign(
        name=data.name,
        template_id=data.template_id,
        created_by=created_by,
        status=CampaignStatus.DRAFT,
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)

    for user_id in data.user_ids:
        db.add(
            PhishingRecipient(
                campaign_id=campaign.id,
                user_id=user_id,
                tracking_token=secrets.token_urlsafe(32),
            )
        )
    await db.commit()

    logger.info(
        "phishing_campaign.create id=%s name=%r recipients=%d created_by=%s",
        campaign.id,
        campaign.name,
        len(data.user_ids),
        created_by,
    )
    return campaign


async def launch_campaign(db: AsyncSession, campaign_id: uuid.UUID) -> PhishingCampaign:
    campaign = await get_campaign(db, campaign_id)
    campaign.status = CampaignStatus.ACTIVE
    await db.commit()
    logger.info("phishing_campaign.launch id=%s name=%r", campaign_id, campaign.name)
    return campaign


async def complete_campaign(
    db: AsyncSession, campaign_id: uuid.UUID
) -> PhishingCampaign:
    campaign = await get_campaign(db, campaign_id)
    campaign.status = CampaignStatus.COMPLETED
    await db.commit()
    logger.info("phishing_campaign.complete id=%s name=%r", campaign_id, campaign.name)
    return campaign


async def get_results(
    db: AsyncSession, campaign_id: uuid.UUID
) -> list[PhishingRecipient]:
    await get_campaign(db, campaign_id)
    result = await db.execute(
        select(PhishingRecipient).where(PhishingRecipient.campaign_id == campaign_id)
    )
    recipients = result.scalars().all()
    logger.info(
        "phishing_campaign.results campaign_id=%s count=%d",
        campaign_id,
        len(recipients),
    )
    return recipients


async def get_my_inbox(db: AsyncSession, user_id: uuid.UUID) -> list[dict]:
    result = await db.execute(
        select(
            PhishingRecipient.id,
            PhishingRecipient.tracking_token,
            PhishingRecipient.clicked_at,
            PhishingRecipient.reported_at,
            PhishingRecipient.created_at,
            PhishingCampaign.name.label("campaign_name"),
            PhishingCampaign.status.label("campaign_status"),
            PhishingTemplate.subject,
            PhishingTemplate.body_html,
            PhishingTemplate.difficulty,
        )
        .join(PhishingCampaign, PhishingRecipient.campaign_id == PhishingCampaign.id)
        .join(PhishingTemplate, PhishingCampaign.template_id == PhishingTemplate.id)
        .where(PhishingRecipient.user_id == user_id)
        .order_by(PhishingRecipient.created_at.desc())
    )
    rows = [dict(r._mapping) for r in result.fetchall()]
    logger.info("phishing_campaign.inbox user_id=%s count=%d", user_id, len(rows))
    return rows


async def record_tracking_event(
    db: AsyncSession, token: str, field: str
) -> PhishingRecipient:
    result = await db.execute(
        select(PhishingRecipient).where(PhishingRecipient.tracking_token == token)
    )
    recipient = result.scalar_one_or_none()
    if recipient is None:
        logger.warning(
            "phishing.tracking_not_found token=%s field=%s", token[:8], field
        )
        raise NotFoundException
    _field_to_action = {
        "clicked_at": "phishing_clicked",
        "reported_at": "phishing_reported",
    }
    if getattr(recipient, field) is None:
        setattr(recipient, field, datetime.now(timezone.utc))
        await db.flush()
        logger.info(
            "phishing.event field=%s recipient_id=%s campaign_id=%s",
            field,
            recipient.id,
            recipient.campaign_id,
        )
        action = _field_to_action.get(field)
        if action:
            # Audit shares the tracking-event transaction: the click/report flag
            # and its audit row commit atomically (no crash-gap).
            await audit_service.write(
                db,
                user_id=recipient.user_id,
                action=action,
                details={"campaign_id": str(recipient.campaign_id)},
                commit=False,
            )
        await db.commit()
        if field == "clicked_at":
            # Remediation assignment owns its own transaction (best-effort,
            # independent of the tracking record above).
            await _maybe_assign_remediation(db, recipient.user_id)
    else:
        logger.info(
            "phishing.event_duplicate field=%s recipient_id=%s", field, recipient.id
        )
    return recipient


async def _maybe_assign_remediation(db: AsyncSession, user_id: uuid.UUID) -> None:
    module_result = await db.execute(
        select(Module)
        .where(Module.is_published.is_(True))
        .where(func.array_position(Module.target_roles, _REMEDIATION_ROLE) != None)  # noqa: E711
    )
    module = module_result.scalar_one_or_none()
    if module is None:
        return
    already = await db.execute(
        select(UserModuleProgress)
        .where(UserModuleProgress.user_id == user_id)
        .where(UserModuleProgress.module_id == module.id)
    )
    if already.scalar_one_or_none() is not None:
        return
    await learning_service.assign_module(db, user_id, module.id)
    logger.info(
        "phishing.remediation_assigned user_id=%s module_id=%s", user_id, module.id
    )
