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
    enable_planning: Optional[bool] = False  # 启用任务规划模式


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


# 任务规划相关
class PlanningRequest(BaseModel):
    conversation_id: int
    task_description: str
    llm_config: Optional[LLMConfig] = None


class TaskStep(BaseModel):
    step_id: str
    description: str
    status: str
    priority: Optional[str] = None
    estimated_time: Optional[str] = None
    dependencies: List[str] = []
    result: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class TaskDependencyNode(BaseModel):
    id: str
    data: Dict[str, Any]


class TaskDependencyEdge(BaseModel):
    source: str
    target: str


class TaskDependencyGraph(BaseModel):
    nodes: List[TaskDependencyNode]
    edges: List[TaskDependencyEdge]


class PlanningResponse(BaseModel):
    success: bool
    task_id: int
    steps: List[TaskStep]
    dependencies: TaskDependencyGraph


class TaskStatusResponse(BaseModel):
    task_id: int
    status: str
    total_steps: int
    completed_steps: int
    progress: float
    status_count: Dict[str, int]
