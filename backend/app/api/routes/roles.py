"""
角色预设 API 路由
"""
from fastapi import APIRouter, HTTPException
from typing import List
from app.api.schemas import RolePresetResponseV2, RolePresetDetailResponse
from app.core.config import BUILTIN_ROLES
from loguru import logger

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("", response_model=dict)
def list_roles():
    """获取所有角色预设列表"""
    try:
        roles = [
            RolePresetResponseV2(
                id=role_data["id"],
                name=role_data["name"],
                description=role_data["description"],
                icon=role_data.get("icon"),
                is_active=role_data.get("is_active", True)
            )
            for role_data in BUILTIN_ROLES.values()
            if role_data.get("is_active", True)
        ]
        
        return {"roles": roles}
    except Exception as e:
        logger.error(f"Failed to list roles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{role_id}", response_model=RolePresetDetailResponse)
def get_role(role_id: str):
    """获取特定角色预设详情"""
    if role_id not in BUILTIN_ROLES:
        raise HTTPException(status_code=404, detail=f"Role not found: {role_id}")
    
    try:
        role_data = BUILTIN_ROLES[role_id]
        
        return RolePresetDetailResponse(
            id=role_data["id"],
            name=role_data["name"],
            description=role_data["description"],
            icon=role_data.get("icon"),
            is_active=role_data.get("is_active", True),
            system_prompt=role_data["system_prompt"],
            config=role_data.get("config", {}),
            created_at="2026-01-27T00:00:00Z"  # 内置角色的固定创建时间
        )
    except Exception as e:
        logger.error(f"Failed to get role {role_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
