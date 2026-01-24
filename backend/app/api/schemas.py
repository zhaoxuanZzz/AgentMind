from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# 对话相关
class MessageCreate(BaseModel):
    role: str
    content: str
    metadata: Optional[Dict] = None


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    meta_info: Optional[Dict] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ConversationCreate(BaseModel):
    title: str


class ConversationResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []
    
    class Config:
        from_attributes = True


# LLM配置
class LLMConfig(BaseModel):
    provider: Optional[str] = None  # 'openai' 或 'dashscope'
    model: Optional[str] = None


# Agent配置 - 封装所有可选的Agent创建参数
class AgentConfig(BaseModel):
    """Agent创建配置 - 封装所有可选的配置参数"""
    memory: Optional[Any] = None
    provider: Optional[str] = None  # LLM提供商
    model: Optional[str] = None  # 模型名称
    collection: Optional[str] = None  # 知识库集合名称
    message: Optional[str] = None  # 用户消息（用于检索角色预设）
    search_provider: Optional[str] = None  # 搜索提供商，可选值: 'tavily', 'baidu', None(默认使用tavily)
    role_preset_id: Optional[str] = None  # 指定的角色预设ID
    db_session: Any = None  # 数据库会话
    llm_instance: Optional[Any] = None  # 可选的LLM实例（如果提供则直接使用）
    history: Optional[List[Dict]] = None  # 历史对话记录
    thread_id: Optional[str] = None  # 线程ID，用于标识不同的会话（用于 LangGraph checkpoint）
    deep_reasoning: bool = False  # 深度推理模式
    
    class Config:
        arbitrary_types_allowed = True  # 允许任意类型（如 db_session, memory, llm_instance）


class LLMProvider(BaseModel):
    id: str
    name: str
    models: List[Dict[str, str]]


class LLMProvidersResponse(BaseModel):
    providers: List[LLMProvider]
    default: LLMConfig


# Chat请求
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[int] = None
    use_knowledge_base: Optional[str] = None
    llm_config: Optional[LLMConfig] = None
    search_provider: Optional[str] = None  # 搜索提供商: 'tavily' 或 'baidu'
    role_preset_id: Optional[str] = None  # 指定的角色预设ID，如果指定则直接使用该预设，不再检索
    deep_reasoning: Optional[bool] = False  # 深度推理模式


class ChatResponse(BaseModel):
    success: bool
    response: str
    conversation_id: int
    intermediate_steps: List[Any] = []


# 知识库相关
class KnowledgeBaseCreate(BaseModel):
    name: str
    description: Optional[str] = None


class KnowledgeBaseResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    collection_name: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DocumentCreate(BaseModel):
    title: str
    content: str
    source: Optional[str] = None
    metadata: Optional[Dict] = None


class DocumentResponse(BaseModel):
    id: int
    knowledge_base_id: int
    title: str
    content: str
    source: Optional[str]
    meta_info: Optional[Dict]
    created_at: datetime
    
    class Config:
        from_attributes = True


class SearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=20)


class SearchResult(BaseModel):
    content: str
    metadata: Dict
    score: float


class SearchResponse(BaseModel):
    results: List[SearchResult]
    query: str


# 任务相关
class TaskCreate(BaseModel):
    title: str
    description: str


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    status: str
    plan: Optional[Dict]
    result: Optional[Dict]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TaskPlanRequest(BaseModel):
    description: str
    llm_config: Optional[LLMConfig] = None


class TaskPlanResponse(BaseModel):
    success: bool
    plan: str
    steps: List[Dict]


# 角色预设相关
class RolePresetCreate(BaseModel):
    title: str
    prompt_content: str
    tags: Optional[List[str]] = []
    category: Optional[str] = "general"


class RolePresetResponse(BaseModel):
    id: Optional[str] = None  # preset_id (唯一标识符)
    title: str
    content: str
    category: str
    tags: List[str]
    score: Optional[float] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class RolePresetUpdate(BaseModel):
    title: Optional[str] = None
    prompt_content: Optional[str] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None


class RolePresetSearchRequest(BaseModel):
    query: Optional[str] = ""
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    top_k: int = Field(default=100, ge=1, le=1000)


class RolePresetSearchResponse(BaseModel):
    results: List[RolePresetResponse]
    query: str


# 通用响应
class SuccessResponse(BaseModel):
    success: bool
    message: str


# 提示词生成相关
class PromptGenerateRequest(BaseModel):
    prompt: str  # 生成提示词的指令
    llm_config: Optional[LLMConfig] = None  # LLM配置


class PromptGenerateResponse(BaseModel):
    success: bool
    content: str  # 生成的内容
    error: Optional[str] = None

