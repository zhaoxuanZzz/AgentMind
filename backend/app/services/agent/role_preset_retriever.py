"""角色预设检索器 - 统一处理角色预设检索逻辑"""
from typing import Optional
from app.services.knowledge_service import knowledge_service
from loguru import logger


class RolePresetRetriever:
    """角色预设检索器 - 统一处理角色预设检索逻辑"""
    
    @staticmethod
    def retrieve_prompts(
        role_preset_id: Optional[str] = None,
        collection: Optional[str] = None,
        message: Optional[str] = None,
        db_session = None,
        top_k: int = 3
    ) -> str:
        """检索角色预设提示词
        
        Args:
            role_preset_id: 指定的角色预设ID（如果提供则直接使用该预设）
            collection: 知识库集合名称（用于检索相关预设）
            message: 用户消息（用于语义搜索相关预设）
            db_session: 数据库会话
            top_k: 检索的预设数量
        
        Returns:
            格式化的提示词字符串，如果没有找到则返回空字符串
        """
        role_prompts = ""
        
        if role_preset_id and db_session:
            # 直接使用指定预设
            try:
                preset = knowledge_service.get_role_preset_by_id(db_session, role_preset_id)
                if preset:
                    role_prompts = "\n\n📋 角色预设提示（你应遵循这些指导原则）:\n"
                    role_prompts += f"\n[{preset.get('title', '')}]\n{preset.get('content', '')}\n"
                    logger.info(f"Using specified role preset: {preset.get('title', '')}")
                else:
                    logger.warning(f"Role preset with id {role_preset_id} not found")
            except Exception as e:
                logger.warning(f"Failed to get role preset by id: {e}")
        
        elif collection and message:
            # 根据对话内容检索相关预设
            try:
                search_results = knowledge_service.search("prompts", message, top_k=top_k)
                if search_results:
                    role_prompts = "\n\n📋 角色预设提示（你应遵循这些指导原则）:\n"
                    for idx, result in enumerate(search_results, 1):
                        title = result.get('metadata', {}).get('title', '')
                        content = result.get('content', '')
                        role_prompts += f"\n{idx}. [{title}]\n{content}\n"
                    logger.info(f"Retrieved {len(search_results)} role presets")
            except Exception as e:
                logger.warning(f"Failed to search role presets: {e}")
        
        return role_prompts

