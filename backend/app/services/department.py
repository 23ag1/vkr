import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.department import Department
from app.schemas.department import DepartmentCreate, DepartmentUpdate

logger = logging.getLogger(__name__)


async def list_departments(db: AsyncSession) -> list[Department]:
    result = await db.execute(select(Department))
    depts = result.scalars().all()
    logger.info("department.list count=%d", len(depts))
    return depts


async def get_department(db: AsyncSession, dept_id: uuid.UUID) -> Department:
    result = await db.execute(select(Department).where(Department.id == dept_id))
    dept = result.scalar_one_or_none()
    if dept is None:
        logger.warning("department.not_found id=%s", dept_id)
        raise NotFoundException
    return dept


async def create_department(db: AsyncSession, data: DepartmentCreate) -> Department:
    dept = Department(name=data.name, parent_id=data.parent_id)
    db.add(dept)
    await db.commit()
    await db.refresh(dept)
    logger.info("department.create id=%s name=%r parent=%s", dept.id, dept.name, dept.parent_id)
    return dept


async def update_department(
    db: AsyncSession, dept_id: uuid.UUID, data: DepartmentUpdate
) -> Department:
    dept = await get_department(db, dept_id)
    fields = data.model_dump(exclude_unset=True)
    for field, value in fields.items():
        setattr(dept, field, value)
    await db.commit()
    logger.info("department.update id=%s fields=%s", dept_id, list(fields.keys()))
    return dept


async def delete_department(db: AsyncSession, dept_id: uuid.UUID) -> None:
    dept = await get_department(db, dept_id)
    await db.delete(dept)
    await db.commit()
    logger.info("department.delete id=%s name=%r", dept_id, dept.name)
