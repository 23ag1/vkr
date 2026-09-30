import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.phishing import PhishingTemplate
from app.schemas.phishing import TemplateCreate, TemplateUpdate

logger = logging.getLogger(__name__)


async def list_templates(db: AsyncSession) -> list[PhishingTemplate]:
    result = await db.execute(select(PhishingTemplate).order_by(PhishingTemplate.created_at.desc()))
    templates = result.scalars().all()
    logger.info("phishing_template.list count=%d", len(templates))
    return templates


async def get_template(db: AsyncSession, template_id: uuid.UUID) -> PhishingTemplate:
    result = await db.execute(select(PhishingTemplate).where(PhishingTemplate.id == template_id))
    template = result.scalar_one_or_none()
    if template is None:
        logger.warning("phishing_template.not_found id=%s", template_id)
        raise NotFoundException
    return template


async def create_template(db: AsyncSession, data: TemplateCreate) -> PhishingTemplate:
    template = PhishingTemplate(
        name=data.name,
        subject=data.subject,
        body_html=data.body_html,
        difficulty=data.difficulty,
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)
    logger.info("phishing_template.create id=%s name=%r difficulty=%s", template.id, template.name, template.difficulty)
    return template


async def update_template(
    db: AsyncSession, template_id: uuid.UUID, data: TemplateUpdate
) -> PhishingTemplate:
    template = await get_template(db, template_id)
    fields = data.model_dump(exclude_unset=True)
    for field, value in fields.items():
        setattr(template, field, value)
    await db.commit()
    logger.info("phishing_template.update id=%s fields=%s", template_id, list(fields.keys()))
    return template


async def delete_template(db: AsyncSession, template_id: uuid.UUID) -> None:
    template = await get_template(db, template_id)
    await db.delete(template)
    await db.commit()
    logger.info("phishing_template.delete id=%s name=%r", template_id, template.name)
