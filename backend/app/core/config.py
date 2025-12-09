from pydantic_settings import BaseSettings
from typing import List
import os
from pathlib import Path


def find_project_root():
    """找到项目根目录（包含.env文件的目录）"""
    current = Path(__file__).resolve()
    # 从当前文件向上查找，找到包含.env文件的目录
    for parent in [current.parents[i] for i in range(4)]:
        env_file = parent / '.env'
        if env_file.exists():
            return str(parent / '.env')
    # 如果没找到，返回项目根目录（默认是backend的父目录的父目录）
    return str(current.parents[3] / '.env')


class Settings(BaseSettings):
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_TITLE: str = "Agent System API"
    API_VERSION: str = "1.0.0"
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str
    
    # ChromaDB
    CHROMA_HOST: str = "chromadb"
    CHROMA_PORT: int = 8000
    CHROMA_PERSIST_DIR: str = "/data/chroma"
    
    # 阿里百炼平台配置（必填）
    DASHSCOPE_API_KEY: str
    DASHSCOPE_MODEL: str = "qwen-max"  # qwen-turbo, qwen-plus, qwen-max, qwen3-max, qwen3-vl-plus
    DASHSCOPE_EMBEDDING_MODEL: str = "text-embedding-v3"  # 阿里百炼向量化模型
    
    # LLM提供商选择: openai 或 dashscope
    LLM_PROVIDER: str = "dashscope"
    
    # OpenAI/LLM（可选，用于多模型切换）
    OPENAI_API_KEY: str = ""
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    MODEL_NAME: str = "gpt-3.5-turbo"
    
    # Embedding
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    USE_DASHSCOPE_EMBEDDING: bool = True  # 是否使用阿里百炼向量化
    
    # 搜索工具配置
    TAVILY_API_KEY: str = ""
    
    # 百度搜索工具配置
    BAIDU_API_KEY: str = ""  # 百度API Key（可选，使用网页搜索不需要API Key）
    BAIDU_ENABLED: bool = True  # 是否启用百度搜索
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        # 自动从项目根目录加载 .env
        # 尝试从根目录加载，如果不存在则从当前目录加载
        env_file = [find_project_root(), ".env"]
        case_sensitive = True
        extra = "ignore"


# 创建settings实例，自动从根目录的.env加载
settings = Settings()

