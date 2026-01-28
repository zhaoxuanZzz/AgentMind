from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any, Literal, Union
from datetime import datetime
from enum import Enum


# ===== 新增：消息类型枚举和消息块schemas =====

class MessageType(str, Enum):
    """消息类型枚举"""
    TEXT = "text"
    THINKING = "thinking"
    TOOL = "tool"
    PLAN = "plan"
    SYSTEM = "system"
    CONVERSATION_ID = "conversation_id"
    DONE = "done"
    ERROR = "error"


class MessageChunk(BaseModel):
    """消息块基类"""
    type: MessageType
    timestamp: Optional[str] = Field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Optional[Dict[str, Any]] = None


class TextChunk(MessageChunk):
    """文本消息块"""
    type: Literal[MessageType.TEXT] = MessageType.TEXT
    content: str


class ThinkingChunk(MessageChunk):
    """思考过程消息块"""
    type: Literal[MessageType.THINKING] = MessageType.THINKING
    content: str
    reasoning_step: Optional[int] = None


class ToolChunk(MessageChunk):
    """工具调用消息块"""
    type: Literal[MessageType.TOOL] = MessageType.TOOL
    tool_name: str
    tool_input: Dict[str, Any]
    tool_output: Optional[str] = None
    status: Literal["pending", "running", "completed", "failed"] = "pending"
    error: Optional[str] = None


class PlanChunk(MessageChunk):
    """计划步骤消息块"""
    type: Literal[MessageType.PLAN] = MessageType.PLAN
    step_number: int
    description: str
    status: Literal["pending", "in_progress", "completed", "failed"] = "pending"
    result: Optional[str] = None
    substeps: Optional[List[str]] = None


class SystemChunk(MessageChunk):
    """系统消息块"""
    type: Literal[MessageType.SYSTEM] = MessageType.SYSTEM
    content: str
    level: Literal["info", "warning", "error"] = "info"


class ConversationIdChunk(MessageChunk):
    """对话ID消息块"""
    type: Literal[MessageType.CONVERSATION_ID] = MessageType.CONVERSATION_ID
    conversation_id: int


class DoneChunk(MessageChunk):
    """完成消息块"""
    type: Literal[MessageType.DONE] = MessageType.DONE
    conversation_id: Optional[int] = None
    message_id: Optional[int] = None


class ErrorChunk(MessageChunk):
    """错误消息块"""
    type: Literal[MessageType.ERROR] = MessageType.ERROR
    message: str
    code: Optional[str] = None


# 所有消息块类型的联合类型
AnyMessageChunk = Union[
    TextChunk,
    ThinkingChunk,
    ToolChunk,
    PlanChunk,
    SystemChunk,
    ConversationIdChunk,
    DoneChunk,
    ErrorChunk
]


# LLM配置 - 移到这里，在使用之前定义
class LLMConfig(BaseModel):
    provider: Optional[str] = None  # 'openai' 或 'dashscope'
    model: Optional[str] = None


class ChatRequestV2(BaseModel):
    """聊天请求（v2增强版）"""
    message: str
    conversation_id: Optional[int] = None
    role_id: Optional[str] = None  # 角色预设ID
    plan_mode: Optional[bool] = None  # 计划模式开关
    use_knowledge_base: Optional[str] = None
    deep_reasoning: Optional[bool] = False
    llm_config: Optional[LLMConfig] = None
    
    @field_validator('conversation_id', mode='before')
    @classmethod
    def validate_conversation_id(cls, v):
        if v is None or v == '':
            return None
        if isinstance(v, int):
            return v
        if isinstance(v, str):
            try:
                return int(v)
            except (ValueError, TypeError):
                return None
        return v


# ===== 角色预设 API schemas（v2增强版） =====

class RolePresetResponseV2(BaseModel):
    """角色预设响应（v2增强版）"""
    id: str  # 角色ID
    name: str  # 显示名称
    description: str  # 角色描述
    icon: Optional[str] = None  # 图标
    is_active: bool = True  # 是否启用


class RolePresetDetailResponse(RolePresetResponseV2):
    """角色预设详细信息响应"""
    system_prompt: str  # 系统提示词
    config: Dict[str, Any] = Field(default_factory=dict)  # LLM配置
    created_at: str


# ===== 会话配置 API schemas =====

class ConversationConfigResponse(BaseModel):
    """会话配置响应"""
    conversation_id: int
    role_id: Optional[str] = None
    role_name: Optional[str] = None
    plan_mode_enabled: Optional[bool] = None
    is_override: bool  # 是否覆盖全局默认


class ConversationConfigUpdateRequest(BaseModel):
    """会话配置更新请求"""
    role_id: Optional[str] = None
    plan_mode_enabled: Optional[bool] = None


class GlobalSettingsResponse(BaseModel):
    """全局设置响应"""
    default_role_id: str
    default_role_name: str
    default_plan_mode: bool


class GlobalSettingsUpdateRequest(BaseModel):
    """全局设置更新请求"""
    default_role_id: Optional[str] = None
    default_plan_mode: Optional[bool] = None


# ===== 原有代码继续 =====


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
    chunks: Optional[List[Dict[str, Any]]] = None
    thinking: Optional[str] = None
    intermediate_steps: Optional[List[Dict[str, Any]]] = None
    created_at: datetime
    
    @field_validator('chunks', 'intermediate_steps', mode='before')
    @classmethod
    def parse_json_fields(cls, v):
        """解析JSON字段（如果是字符串则转换为对象）"""
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except:
                return None
        return v
    
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


# Agent配置 - 封装所有可选的Agent创建参数
class AgentConfig(BaseModel):
    """Agent创建配置 - 封装所有可选的配置参数"""
    memory: Optional[Any] = None
    provider: Optional[str] = None  # LLM提供商
    model: Optional[str] = None  # 模型名称
    collection: Optional[str] = None  # 知识库集合名称
    message: Optional[str] = None  # 用户消息（用于检索角色预设）
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
    role_preset_id: Optional[str] = None  # 指定的角色预设ID，如果指定则直接使用该预设，不再检索
    deep_reasoning: Optional[bool] = False  # 深度推理模式
    
    @field_validator('conversation_id', mode='before')
    @classmethod
    def validate_conversation_id(cls, v):
        """确保 conversation_id 被正确转换为整数"""
        if v is None or v == '':
            return None
        if isinstance(v, int):
            return v
        if isinstance(v, str):
            try:
                return int(v)
            except (ValueError, TypeError):
                # 如果无法转换，返回 None 而不是抛出异常
                return None
        return v


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

