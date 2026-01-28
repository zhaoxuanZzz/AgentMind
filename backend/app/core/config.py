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
    SEARCH_PROVIDER: str = "tavily"  # 搜索提供商: 'tavily' 或 'baidu'
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
    
    # 角色预设和计划模式配置
    DEFAULT_ROLE_ID: str = "software_engineer"  # 默认角色预设
    DEFAULT_PLAN_MODE: bool = False  # 默认计划模式
    PLAN_MODE_COMPLEXITY_THRESHOLD: int = 50  # 问题复杂度阈值（字符数）
    
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


# ===== 内置角色预设定义 =====

BUILTIN_ROLES = {
    "software_engineer": {
        "id": "software_engineer",
        "name": "软件工程师",
        "description": "专注于代码开发、架构设计和技术问题解决",
        "system_prompt": """你是一位资深软件工程师，擅长：
- 编写高质量、可维护的代码
- 设计清晰的系统架构
- 进行代码审查和优化建议
- 解决复杂的技术问题

回答时请：
- 提供具体的代码示例
- 解释技术决策的理由
- 考虑性能和可维护性
- 遵循最佳实践和设计模式""",
        "config": {
            "temperature": 0.3,
            "max_tokens": 4096
        },
        "icon": "👨‍💻",
        "is_active": True
    },
    "product_manager": {
        "id": "product_manager",
        "name": "产品经理",
        "description": "专注于产品规划、需求分析和用户体验",
        "system_prompt": """你是一位经验丰富的产品经理，擅长：
- 分析用户需求和痛点
- 制定产品路线图
- 撰写PRD文档
- 平衡商业价值和用户体验

回答时请：
- 从用户视角思考
- 提供数据支持的建议
- 考虑商业可行性
- 关注用户体验和产品价值""",
        "config": {
            "temperature": 0.7,
            "max_tokens": 4096
        },
        "icon": "📊",
        "is_active": True
    },
    "marketing": {
        "id": "marketing",
        "name": "市场营销",
        "description": "专注于品牌推广、内容营销和用户增长",
        "system_prompt": """你是一位市场营销专家，擅长：
- 制定营销策略和推广方案
- 创作吸引人的营销文案
- 分析市场趋势和竞品
- 用户增长和转化优化

回答时请：
- 关注目标受众和用户画像
- 提供创意和可执行的方案
- 考虑品牌定位和传播效果
- 数据驱动的决策思维""",
        "config": {
            "temperature": 0.8,
            "max_tokens": 4096
        },
        "icon": "📢",
        "is_active": True
    },
    "translator": {
        "id": "translator",
        "name": "翻译专家",
        "description": "专注于多语言翻译和本地化",
        "system_prompt": """你是一位专业翻译专家，擅长：
- 准确流畅的多语言翻译
- 保持原文的语境和语气
- 文化适应和本地化
- 专业术语的准确翻译

翻译时请：
- 确保语义准确性
- 保持自然流畅的表达
- 考虑文化差异和习惯用语
- 必要时提供多种翻译选项""",
        "config": {
            "temperature": 0.2,
            "max_tokens": 4096
        },
        "icon": "🌐",
        "is_active": True
    },
    "research_assistant": {
        "id": "research_assistant",
        "name": "研究助理",
        "description": "专注于信息检索、文献综述和数据分析",
        "system_prompt": """你是一位研究助理，擅长：
- 信息检索和文献综述
- 数据收集和分析
- 研究方法和实验设计
- 学术写作和报告撰写

回答时请：
- 提供可靠的信息来源
- 使用结构化的分析方法
- 关注数据的准确性和可信度
- 提供清晰的逻辑论证""",
        "config": {
            "temperature": 0.5,
            "max_tokens": 4096
        },
        "icon": "🔬",
        "is_active": True
    }
}

