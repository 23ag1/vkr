import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

import app.services.module as module_service
from app.deps import get_current_user, get_db, require_role
from app.models.user import User
from app.schemas.common import ApiResponse, ok
from app.schemas.module import ModuleCreate, ModuleResponse, ModuleUpdate

router = APIRouter()

_admin = Depends(require_role("admin"))


@router.get("", response_model=ApiResponse[list[ModuleResponse]])
async def list_modules(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    modules = await module_service.list_modules(db, role=current_user.role)
    return ok([ModuleResponse.model_validate(m) for m in modules])


@router.post("", response_model=ApiResponse[ModuleResponse], status_code=status.HTTP_201_CREATED, dependencies=[_admin])
async def create_module(body: ModuleCreate, db: AsyncSession = Depends(get_db)):
    module = await module_service.create_module(db, body)
    return ok(ModuleResponse.model_validate(module))


@router.get("/{module_id}", response_model=ApiResponse[ModuleResponse])
async def get_module(
    module_id: uuid.UUID,
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    module = await module_service.get_module(db, module_id)
    return ok(ModuleResponse.model_validate(module))


@router.put("/{module_id}", response_model=ApiResponse[ModuleResponse], dependencies=[_admin])
async def update_module(module_id: uuid.UUID, body: ModuleUpdate, db: AsyncSession = Depends(get_db)):
    module = await module_service.update_module(db, module_id, body)
    return ok(ModuleResponse.model_validate(module))


@router.post("/{module_id}/publish", response_model=ApiResponse[ModuleResponse], dependencies=[_admin])
async def publish_module(module_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    module = await module_service.publish_module(db, module_id)
    return ok(ModuleResponse.model_validate(module))


@router.delete("/{module_id}", response_model=ApiResponse[None], dependencies=[_admin])
async def delete_module(module_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    await module_service.delete_module(db, module_id)
    return ok(None)
