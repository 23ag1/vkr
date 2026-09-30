import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

import app.services.department as dept_service
from app.deps import get_db, require_role
from app.schemas.common import ApiResponse, ok
from app.schemas.department import DepartmentCreate, DepartmentResponse, DepartmentUpdate

router = APIRouter()

_admin = Depends(require_role("admin"))


@router.get("", response_model=ApiResponse[list[DepartmentResponse]], dependencies=[_admin])
async def list_departments(db: AsyncSession = Depends(get_db)):
    depts = await dept_service.list_departments(db)
    return ok([DepartmentResponse.model_validate(d) for d in depts])


@router.post("", response_model=ApiResponse[DepartmentResponse], status_code=status.HTTP_201_CREATED, dependencies=[_admin])
async def create_department(body: DepartmentCreate, db: AsyncSession = Depends(get_db)):
    dept = await dept_service.create_department(db, body)
    return ok(DepartmentResponse.model_validate(dept))


@router.get("/{dept_id}", response_model=ApiResponse[DepartmentResponse], dependencies=[_admin])
async def get_department(dept_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    dept = await dept_service.get_department(db, dept_id)
    return ok(DepartmentResponse.model_validate(dept))


@router.put("/{dept_id}", response_model=ApiResponse[DepartmentResponse], dependencies=[_admin])
async def update_department(dept_id: uuid.UUID, body: DepartmentUpdate, db: AsyncSession = Depends(get_db)):
    dept = await dept_service.update_department(db, dept_id, body)
    return ok(DepartmentResponse.model_validate(dept))


@router.delete("/{dept_id}", response_model=ApiResponse[None], dependencies=[_admin])
async def delete_department(dept_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    await dept_service.delete_department(db, dept_id)
    return ok(None)
