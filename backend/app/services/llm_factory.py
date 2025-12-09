"""
LLM工厂 - 支持多个LLM提供商
支持: OpenAI, 阿里百炼(DashScope)
"""
import json
from pathlib import Path
from typing import Optional, Dict, List
from langchain_community.chat_models import ChatOpenAI
from langchain_community.chat_models.tongyi import ChatTongyi
from app.core.config import settings
from loguru import logger

# 加载模型配置
_CONFIG_PATH = Path(__file__).parent.parent / "llm" / "config" / "models.json"

def _load_model_config() -> Dict:
    """加载模型配置文件"""
    try:
        with open(_CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"模型配置文件未找到: {_CONFIG_PATH}，使用默认配置")
        return {
            "providers": {},
            "defaults": {
                "provider": "dashscope",
                "openai_model": "gpt-3.5-turbo",
                "dashscope_model": "qwen-max"
            }
        }
    except json.JSONDecodeError as e:
        logger.error(f"模型配置文件格式错误: {e}，使用默认配置")
        return {
            "providers": {},
            "defaults": {
                "provider": "dashscope",
                "openai_model": "gpt-3.5-turbo",
                "dashscope_model": "qwen-max"
            }
        }


class LLMFactory:
    """LLM工厂类，根据配置创建不同的LLM实例"""
    
    @staticmethod
    def create_llm(
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        streaming: bool = False
    ):
        """
        创建LLM实例
        
        Args:
            provider: LLM提供商 ('openai' 或 'dashscope')，不指定则使用配置文件默认值
            model_name: 模型名称，不指定则使用配置文件默认值
            temperature: 温度参数
            
        Returns:
            LLM实例
        """
        provider = provider or settings.LLM_PROVIDER
        
        if provider == "dashscope":
            return LLMFactory._create_dashscope_llm(model_name, temperature, streaming)
        elif provider == "openai":
            return LLMFactory._create_openai_llm(model_name, temperature, streaming)
        else:
            logger.warning(f"Unknown provider: {provider}, falling back to OpenAI")
            return LLMFactory._create_openai_llm(model_name, temperature, streaming)
    
    @staticmethod
    def _create_openai_llm(model_name: Optional[str] = None, temperature: float = 0.7, streaming: bool = False):
        """创建OpenAI LLM实例"""
        model = model_name or settings.MODEL_NAME
        logger.info(f"Creating OpenAI LLM with model: {model}, streaming: {streaming}")
        
        return ChatOpenAI(
            model_name=model,
            openai_api_key=settings.OPENAI_API_KEY,
            openai_api_base=settings.OPENAI_API_BASE,
            temperature=temperature,
            streaming=streaming
        )
    
    @staticmethod
    def _create_dashscope_llm(model_name: Optional[str] = None, temperature: float = 0.7, streaming: bool = False):
        """创建阿里百炼(DashScope) LLM实例"""
        model = model_name or settings.DASHSCOPE_MODEL
        logger.info(f"Creating DashScope LLM with model: {model}, streaming: {streaming}")
        
        if not settings.DASHSCOPE_API_KEY:
            raise ValueError(
                "DASHSCOPE_API_KEY is not set. "
                "Please set it in .env file to use DashScope models."
            )
        
        llm = ChatTongyi(
            model_name=model,
            dashscope_api_key=settings.DASHSCOPE_API_KEY,
            temperature=temperature,
            streaming=streaming  # 根据参数启用流式输出
        )
        return llm
    
    @staticmethod
    def get_available_providers():
        """获取可用的LLM提供商列表"""
        config = _load_model_config()
        providers = []
        
        # 从配置文件加载提供商信息
        for provider_id, provider_config in config.get("providers", {}).items():
            # 检查是否有对应的API Key
            if provider_id == "openai" and settings.OPENAI_API_KEY:
                providers.append({
                    "id": provider_config["id"],
                    "name": provider_config["name"],
                    "models": [
                        {"id": m["id"], "name": m["name"]}
                        for m in provider_config.get("models", [])
                    ]
                })
            elif provider_id == "dashscope" and settings.DASHSCOPE_API_KEY:
                providers.append({
                    "id": provider_config["id"],
                    "name": provider_config["name"],
                    "models": [
                        {"id": m["id"], "name": m["name"]}
                        for m in provider_config.get("models", [])
                    ]
                })
        
        return providers
    
    @staticmethod
    def get_default_config():
        """获取默认LLM配置"""
        return {
            "provider": settings.LLM_PROVIDER,
            "model": settings.DASHSCOPE_MODEL if settings.LLM_PROVIDER == "dashscope" else settings.MODEL_NAME
        }


# 全局工厂实例
llm_factory = LLMFactory()

