"""
会话配置和全局设置 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json
from app.db.database import get_db
from app.db import models
from app.api.schemas import (
    ConversationConfigResponse,
    ConversationConfigUpdateRequest,
    GlobalSettingsResponse,
    GlobalSettingsUpdateRequest,
)
from app.core.config import BUILTIN_ROLES, settings
from loguru import logger

router = APIRouter(tags=["settings"])


@router.get("/settings/global", response_model=GlobalSettingsResponse)
def get_global_settings(db: Session = Depends(get_db)):
    """获取全局设置"""
    try:
        # 从数据库读取设置
        settings_dict = {}
        settings_records = db.query(models.GlobalSettings).all()
        
        for record in settings_records:
            try:
                # 尝试解析 JSON
                value = json.loads(record.setting_value) if record.setting_value else None
                settings_dict[record.setting_key] = value
            except:
                settings_dict[record.setting_key] = record.setting_value
        
        # 获取默认值
        default_role_id = settings_dict.get('default_role_id', settings.DEFAULT_ROLE_ID)
        default_plan_mode = settings_dict.get('default_plan_mode', settings.DEFAULT_PLAN_MODE)
        
        # 获取角色名称
        role_name = BUILTIN_ROLES.get(default_role_id, {}).get('name', default_role_id)
        
        return GlobalSettingsResponse(
            default_role_id=default_role_id,
            default_role_name=role_name,
            default_plan_mode=default_plan_mode
        )
    except Exception as e:
        logger.error(f"Failed to get global settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/settings/global", response_model=GlobalSettingsResponse)
def update_global_settings(
    body: GlobalSettingsUpdateRequest,
    db: Session = Depends(get_db)
):
    """更新全局设置"""
    try:
        # 验证角色ID
        if body.default_role_id and body.default_role_id not in BUILTIN_ROLES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid role_id: {body.default_role_id}"
            )
        
        # 更新设置
        if body.default_role_id is not None:
            setting = db.query(models.GlobalSettings).filter(
                models.GlobalSettings.setting_key == 'default_role_id'
            ).first()
            
            if setting:
                setting.setting_value = json.dumps(body.default_role_id)
            else:
                setting = models.GlobalSettings(
                    setting_key='default_role_id',
                    setting_value=json.dumps(body.default_role_id)
                )
                db.add(setting)
        
        if body.default_plan_mode is not None:
            setting = db.query(models.GlobalSettings).filter(
                models.GlobalSettings.setting_key == 'default_plan_mode'
            ).first()
            
            if setting:
                setting.setting_value = json.dumps(body.default_plan_mode)
            else:
                setting = models.GlobalSettings(
                    setting_key='default_plan_mode',
                    setting_value=json.dumps(body.default_plan_mode)
                )
                db.add(setting)
        
        db.commit()
        
        # 返回更新后的设置
        return get_global_settings(db)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update global settings: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}/config", response_model=ConversationConfigResponse)
def get_conversation_config(conversation_id: int, db: Session = Depends(get_db)):
    """获取会话配置"""
    try:
        # 检查会话是否存在
        conversation = db.query(models.Conversation).filter(
            models.Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # 获取会话配置
        config = db.query(models.ConversationConfig).filter(
            models.ConversationConfig.conversation_id == conversation_id
        ).first()
        
        if config and (config.role_id is not None or config.plan_mode_enabled is not None):
            # 有覆盖配置
            role_id = config.role_id
            plan_mode = bool(config.plan_mode_enabled) if config.plan_mode_enabled is not None else None
            
            # 如果没有设置，使用全局默认
            if role_id is None or plan_mode is None:
                global_settings = get_global_settings(db)
                if role_id is None:
                    role_id = global_settings.default_role_id
                if plan_mode is None:
                    plan_mode = global_settings.default_plan_mode
            
            role_name = BUILTIN_ROLES.get(role_id, {}).get('name', role_id)
            
            return ConversationConfigResponse(
                conversation_id=conversation_id,
                role_id=role_id,
                role_name=role_name,
                plan_mode_enabled=plan_mode,
                is_override=True
            )
        else:
            # 使用全局默认
            global_settings = get_global_settings(db)
            
            return ConversationConfigResponse(
                conversation_id=conversation_id,
                role_id=global_settings.default_role_id,
                role_name=global_settings.default_role_name,
                plan_mode_enabled=global_settings.default_plan_mode,
                is_override=False
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/conversations/{conversation_id}/config", response_model=ConversationConfigResponse)
def update_conversation_config(
    conversation_id: int,
    body: ConversationConfigUpdateRequest,
    db: Session = Depends(get_db)
):
    """更新会话配置"""
    try:
        # 检查会话是否存在
        conversation = db.query(models.Conversation).filter(
            models.Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # 验证角色ID
        if body.role_id and body.role_id not in BUILTIN_ROLES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid role_id: {body.role_id}"
            )
        
        # 获取或创建配置
        config = db.query(models.ConversationConfig).filter(
            models.ConversationConfig.conversation_id == conversation_id
        ).first()
        
        if not config:
            config = models.ConversationConfig(
                conversation_id=conversation_id
            )
            db.add(config)
        
        # 更新配置
        if body.role_id is not None:
            config.role_id = body.role_id
        if body.plan_mode_enabled is not None:
            config.plan_mode_enabled = 1 if body.plan_mode_enabled else 0
        
        db.commit()
        
        # 返回更新后的配置
        return get_conversation_config(conversation_id, db)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update conversation config: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/conversations/{conversation_id}/config", status_code=204)
def delete_conversation_config(conversation_id: int, db: Session = Depends(get_db)):
    """删除会话配置（恢复使用全局默认）"""
    try:
        # 检查会话是否存在
        conversation = db.query(models.Conversation).filter(
            models.Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # 删除配置
        config = db.query(models.ConversationConfig).filter(
            models.ConversationConfig.conversation_id == conversation_id
        ).first()
        
        if config:
            db.delete(config)
            db.commit()
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete conversation config: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
