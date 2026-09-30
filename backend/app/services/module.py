import logging
import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.module import Module
from app.schemas.module import ModuleCreate, ModuleUpdate

logger = logging.getLogger(__name__)


_PRIVILEGED_ROLES = {"admin", "security_specialist"}


async def list_modules(db: AsyncSession, role: str) -> list[Module]:
    query = select(Module)
    if role not in _PRIVILEGED_ROLES:
        query = query.where(Module.is_published.is_(True)).where(
            or_(
                func.cardinality(Module.target_roles) == 0,
                func.array_position(Module.target_roles, role) != None,  # noqa: E711
            )
        )
    result = await db.execute(query.order_by(Module.order_index))
    modules = result.scalars().all()
    logger.info("module.list role=%s count=%d", role, len(modules))
    return modules


async def get_module(db: AsyncSession, module_id: uuid.UUID) -> Module:
    result = await db.execute(select(Module).where(Module.id == module_id))
    module = result.scalar_one_or_none()
    if module is None:
        logger.warning("module.not_found id=%s", module_id)
        raise NotFoundException
    return module


async def create_module(db: AsyncSession, data: ModuleCreate) -> Module:
    module = Module(
        title=data.title,
        description=data.description,
        content_md=data.content_md,
        target_roles=data.target_roles,
        order_index=data.order_index,
        briefing_type=data.briefing_type,
        is_published=False,
    )
    db.add(module)
    await db.commit()
    await db.refresh(module)
    logger.info("module.create id=%s title=%r order=%d", module.id, module.title, module.order_index)
    return module


async def update_module(db: AsyncSession, module_id: uuid.UUID, data: ModuleUpdate) -> Module:
    module = await get_module(db, module_id)
    fields = data.model_dump(exclude_unset=True)
    for field, value in fields.items():
        setattr(module, field, value)
    await db.commit()
    logger.info("module.update id=%s fields=%s", module_id, list(fields.keys()))
    return module


async def publish_module(db: AsyncSession, module_id: uuid.UUID) -> Module:
    module = await get_module(db, module_id)
    module.is_published = True
    await db.commit()
    logger.info("module.publish id=%s title=%r", module_id, module.title)
    return module


async def delete_module(db: AsyncSession, module_id: uuid.UUID) -> None:
    module = await get_module(db, module_id)
    await db.delete(module)
    await db.commit()
    logger.info("module.delete id=%s title=%r", module_id, module.title)
