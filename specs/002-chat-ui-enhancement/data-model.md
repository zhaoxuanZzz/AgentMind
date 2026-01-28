# 数据模型设计：聊天界面增强

**特性**：002-chat-ui-enhancement  
**日期**：2026-01-26  
**阶段**：Phase 1

## 概述

本文档定义了聊天界面增强功能所需的核心数据模型，包括消息类型、角色预设、会话配置和全局设置。所有模型遵循AgentMind宪章的类型安全原则，使用Pydantic进行验证。

---

## 1. 消息相关模型

### 1.1 MessageType（消息类型枚举）

```python
from enum import Enum

class MessageType(str, Enum):
    """消息类型枚举"""
    TEXT = "text"           # 普通文本内容
    THINKING = "thinking"   # AI思考过程
    TOOL = "tool"          # 工具调用
    PLAN = "plan"          # 计划步骤
    SYSTEM = "system"      # 系统消息
```

**用途**：标识消息chunk的类型，指导前端渲染逻辑

**验证规则**：
- 必须是枚举值之一
- 前后端使用相同的字符串值确保一致性

---

### 1.2 MessageChunk（消息块基类）

```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class MessageChunk(BaseModel):
    """消息块基类"""
    type: MessageType
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True  # 序列化时使用枚举值
```

**字段说明**：
- `type`：消息类型，必需
- `content`：文本内容，可选（某些类型如TOOL可能没有content）
- `metadata`：额外元数据，可选
- `timestamp`：时间戳，自动生成

---

### 1.3 具体消息类型

#### ThinkingChunk（思考过程）

```python
from typing import Literal

class ThinkingChunk(MessageChunk):
    """思考过程消息块"""
    type: Literal[MessageType.THINKING] = MessageType.THINKING
    content: str  # 思考内容，必需
    reasoning_step: Optional[int] = None  # 推理步骤编号
```

**使用场景**：展示AI的推理过程，让用户了解AI如何思考问题

**前端渲染**：特殊样式（如浅灰背景、思考图标💭）

---

#### ToolChunk（工具调用）

```python
class ToolChunk(MessageChunk):
    """工具调用消息块"""
    type: Literal[MessageType.TOOL] = MessageType.TOOL
    tool_name: str  # 工具名称
    tool_input: Dict[str, Any]  # 工具输入参数
    tool_output: Optional[str] = None  # 工具执行结果
    status: Literal["pending", "running", "completed", "failed"] = "pending"
    error: Optional[str] = None  # 错误信息（如果失败）
```

**字段说明**：
- `tool_name`：工具标识符（如"calculator"、"web_search"）
- `tool_input`：JSON对象，包含工具所需参数
- `tool_output`：工具返回结果
- `status`：执行状态
- `error`：失败时的错误信息

**使用场景**：展示AI使用的工具和结果，提高透明度

**前端渲染**：可折叠的工具调用卡片，显示输入输出

---

#### PlanChunk（计划步骤）

```python
class PlanChunk(MessageChunk):
    """计划步骤消息块"""
    type: Literal[MessageType.PLAN] = MessageType.PLAN
    step_number: int  # 步骤编号（从1开始）
    description: str  # 步骤描述
    status: Literal["pending", "in_progress", "completed", "failed"] = "pending"
    result: Optional[str] = None  # 步骤执行结果
    substeps: Optional[List[str]] = None  # 子步骤（可选）
```

**字段说明**：
- `step_number`：步骤序号
- `description`：步骤内容描述
- `status`：执行状态
- `result`：步骤完成后的结果摘要
- `substeps`：详细子步骤列表

**使用场景**：展示任务分解和执行进度

**前端渲染**：时间线或步骤列表，带状态图标

---

#### TextChunk（文本内容）

```python
class TextChunk(MessageChunk):
    """普通文本消息块"""
    type: Literal[MessageType.TEXT] = MessageType.TEXT
    content: str  # 文本内容，必需
```

**使用场景**：最终答案内容

**前端渲染**：Markdown渲染，支持代码高亮

---

#### SystemChunk（系统消息）

```python
class SystemChunk(MessageChunk):
    """系统消息块"""
    type: Literal[MessageType.SYSTEM] = MessageType.SYSTEM
    content: str
    level: Literal["info", "warning", "error"] = "info"
```

**使用场景**：系统通知、错误提示等

**前端渲染**：Alert组件，根据level显示不同样式

---

### 1.4 Message（完整消息）

```python
from typing import List

class Message(BaseModel):
    """完整消息模型（数据库存储）"""
    id: int
    conversation_id: int
    role: Literal["user", "assistant", "system"]
    chunks: List[MessageChunk]  # 消息块列表
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # 兼容字段（用于旧数据迁移）
    content: Optional[str] = None  # 向后兼容
    thinking: Optional[str] = None  # 向后兼容
    intermediate_steps: Optional[List[Dict]] = None  # 向后兼容
```

**存储策略**：
- `chunks`字段存储为JSONB类型（PostgreSQL）
- 保留旧字段以支持数据迁移
- 新消息优先使用chunks，旧消息在读取时转换

---

## 2. 角色预设模型

### 2.1 RolePreset（角色预设）

```python
class RolePreset(BaseModel):
    """角色预设模型"""
    id: str  # 角色标识符（如"software_engineer"）
    name: str  # 显示名称（如"软件工程师"）
    description: str  # 角色描述
    system_prompt: str  # 系统提示词
    config: Dict[str, Any] = Field(default_factory=dict)  # LLM配置
    icon: Optional[str] = None  # 图标（emoji或URL）
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True  # 是否启用
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "software_engineer",
                "name": "软件工程师",
                "description": "专注于代码开发、架构设计和技术问题解决",
                "system_prompt": "你是一位资深软件工程师...",
                "config": {
                    "temperature": 0.3,
                    "max_tokens": 4096
                },
                "icon": "👨‍💻"
            }
        }
```

**字段说明**：
- `id`：唯一标识符，用于引用
- `name`：用户可见的角色名称
- `description`：角色能力描述
- `system_prompt`：注入到LLM的系统提示词
- `config`：角色特定的LLM配置（如temperature）
- `icon`：界面显示的图标
- `is_active`：软删除标记

**预定义角色**（硬编码在代码中）：

```python
BUILTIN_ROLES = {
    "software_engineer": RolePreset(
        id="software_engineer",
        name="软件工程师",
        description="专注于代码开发、架构设计和技术问题解决",
        system_prompt="""你是一位资深软件工程师，擅长：
        - 编写高质量、可维护的代码
        - 设计清晰的系统架构
        - 进行代码审查和优化建议
        - 解决复杂的技术问题
        
        回答时请：
        - 提供具体的代码示例
        - 解释技术决策的理由
        - 考虑性能和可维护性""",
        config={"temperature": 0.3},
        icon="👨‍💻"
    ),
    "product_manager": RolePreset(
        id="product_manager",
        name="产品经理",
        description="专注于产品规划、需求分析和用户体验",
        system_prompt="""你是一位经验丰富的产品经理...""",
        config={"temperature": 0.7},
        icon="📊"
    ),
    "marketing": RolePreset(
        id="marketing",
        name="市场营销",
        description="专注于品牌推广、内容营销和用户增长",
        system_prompt="""你是一位市场营销专家...""",
        config={"temperature": 0.8},
        icon="📢"
    ),
    "translator": RolePreset(
        id="translator",
        name="翻译专家",
        description="专注于多语言翻译和本地化",
        system_prompt="""你是一位专业翻译...""",
        config={"temperature": 0.2},
        icon="🌐"
    ),
    "research_assistant": RolePreset(
        id="research_assistant",
        name="研究助理",
        description="专注于信息检索、文献综述和数据分析",
        system_prompt="""你是一位研究助理...""",
        config={"temperature": 0.5},
        icon="🔬"
    )
}
```

---

## 3. 配置相关模型

### 3.1 ConversationConfig（会话配置）

```python
class ConversationConfig(BaseModel):
    """会话级配置模型（数据库）"""
    id: int
    conversation_id: int  # 关联的对话ID
    role_id: Optional[str] = None  # 角色ID，null表示使用全局默认
    plan_mode_enabled: Optional[bool] = None  # 计划模式，null表示使用全局默认
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
class ConversationConfigCreate(BaseModel):
    """创建会话配置请求"""
    conversation_id: int
    role_id: Optional[str] = None
    plan_mode_enabled: Optional[bool] = None

class ConversationConfigResponse(BaseModel):
    """会话配置响应"""
    conversation_id: int
    role_id: str  # 已解析的有效角色ID（可能来自全局默认）
    role_name: str  # 角色显示名称
    plan_mode_enabled: bool  # 已解析的有效计划模式（可能来自全局默认）
    is_override: bool  # 是否覆盖了全局设置
```

**数据库表设计**：
```sql
CREATE TABLE conversation_configs (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role_id VARCHAR(50),  -- null = use global default
    plan_mode_enabled BOOLEAN,  -- null = use global default
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    UNIQUE(conversation_id)  -- 每个对话只有一个配置
);

CREATE INDEX idx_conversation_configs_conversation_id ON conversation_configs(conversation_id);
```

---

### 3.2 GlobalSettings（全局设置）

```python
class GlobalSettings(BaseModel):
    """全局设置模型（数据库）"""
    id: int
    user_id: Optional[int] = None  # 未来支持多用户，当前null表示单用户
    default_role_id: str = "software_engineer"  # 默认角色
    default_plan_mode: bool = False  # 默认计划模式
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

class GlobalSettingsUpdate(BaseModel):
    """更新全局设置请求"""
    default_role_id: Optional[str] = None
    default_plan_mode: Optional[bool] = None

class GlobalSettingsResponse(BaseModel):
    """全局设置响应"""
    default_role_id: str
    default_role_name: str  # 角色显示名称
    default_plan_mode: bool
```

**数据库表设计**：
```sql
CREATE TABLE global_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,  -- null for single-user mode
    default_role_id VARCHAR(50) NOT NULL DEFAULT 'software_engineer',
    default_plan_mode BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    UNIQUE(user_id)  -- 每个用户只有一个全局设置
);

-- 插入默认配置
INSERT INTO global_settings (user_id, default_role_id, default_plan_mode)
VALUES (NULL, 'software_engineer', FALSE);
```

---

## 4. API请求/响应模型

### 4.1 ChatRequest（聊天请求）

```python
class ChatRequest(BaseModel):
    """聊天请求模型（扩展版）"""
    message: str
    conversation_id: Optional[int] = None
    
    # 新增字段
    role_id: Optional[str] = None  # 指定角色（覆盖会话配置）
    plan_mode: Optional[bool] = None  # 指定计划模式（覆盖会话配置）
    
    # 保留原有字段
    use_knowledge_base: Optional[str] = None
    search_provider: Optional[str] = None
    deep_reasoning: bool = False
    llm_config: Optional[Dict[str, str]] = None
```

**优先级**：请求级 > 会话级 > 全局级

---

### 4.2 StreamResponse（流式响应）

```python
class StreamResponse(BaseModel):
    """流式响应的单个chunk"""
    # 使用MessageChunk的子类
    chunk: MessageChunk  # 可以是ThinkingChunk、ToolChunk等
    conversation_id: Optional[int] = None  # 首次返回时包含

class StreamDoneResponse(BaseModel):
    """流式完成响应"""
    type: Literal["done"] = "done"
    conversation_id: int
    message_id: int  # 保存后的消息ID

class StreamErrorResponse(BaseModel):
    """流式错误响应"""
    type: Literal["error"] = "error"
    message: str
    code: Optional[str] = None
```

---

## 5. 数据关系图

```
┌─────────────────┐
│ GlobalSettings  │  (全局默认配置)
│                 │
│ - default_role  │
│ - plan_mode     │
└────────┬────────┘
         │
         │ 提供默认值
         ↓
┌─────────────────────────┐
│ ConversationConfig      │  (会话级覆盖)
│                         │
│ - conversation_id (FK)  │
│ - role_id (nullable)    │──→ 如果null，使用GlobalSettings.default_role
│ - plan_mode (nullable)  │──→ 如果null，使用GlobalSettings.plan_mode
└──────────┬──────────────┘
           │
           │ 1:1
           ↓
┌────────────────────┐
│ Conversation       │
│                    │
│ - id               │
│ - title            │
└─────────┬──────────┘
          │
          │ 1:N
          ↓
┌──────────────────────┐
│ Message              │
│                      │
│ - id                 │
│ - conversation_id(FK)│
│ - role               │
│ - chunks (JSONB)     │  ──→ 存储 MessageChunk[]
└──────────────────────┘

┌────────────────┐
│ RolePreset     │  (硬编码，不存数据库)
│                │
│ - id           │
│ - name         │
│ - system_prompt│
│ - config       │
└────────────────┘
     ↑
     └─ 被ConversationConfig和GlobalSettings引用
```

---

## 6. 类型安全验证

所有模型都包含Pydantic验证：

```python
# 示例：验证角色ID是否有效
from pydantic import validator

class ConversationConfigCreate(BaseModel):
    conversation_id: int
    role_id: Optional[str] = None
    
    @validator('role_id')
    def validate_role_id(cls, v):
        if v is not None and v not in BUILTIN_ROLES:
            raise ValueError(f"Invalid role_id: {v}. Must be one of {list(BUILTIN_ROLES.keys())}")
        return v

# 示例：JSON序列化配置
class MessageChunk(BaseModel):
    # ...
    class Config:
        use_enum_values = True  # 枚举序列化为字符串
        json_encoders = {
            datetime: lambda v: v.isoformat()  # datetime序列化为ISO格式
        }
```

---

## 7. 数据迁移策略

### 7.1 Message表迁移

```sql
-- 添加新字段
ALTER TABLE messages ADD COLUMN chunks JSONB;

-- 创建迁移函数
CREATE OR REPLACE FUNCTION migrate_message_to_chunks(msg_id INTEGER)
RETURNS VOID AS $$
DECLARE
    msg RECORD;
    chunks_array JSONB := '[]'::JSONB;
BEGIN
    SELECT * INTO msg FROM messages WHERE id = msg_id;
    
    -- 迁移thinking
    IF msg.thinking IS NOT NULL AND msg.thinking != '' THEN
        chunks_array := chunks_array || jsonb_build_object(
            'type', 'thinking',
            'content', msg.thinking,
            'timestamp', NOW()
        )::JSONB;
    END IF;
    
    -- 迁移intermediate_steps (工具调用)
    IF msg.intermediate_steps IS NOT NULL THEN
        -- 遍历intermediate_steps数组
        -- ... (具体逻辑)
    END IF;
    
    -- 迁移content
    IF msg.content IS NOT NULL AND msg.content != '' THEN
        chunks_array := chunks_array || jsonb_build_object(
            'type', 'text',
            'content', msg.content,
            'timestamp', NOW()
        )::JSONB;
    END IF;
    
    -- 更新chunks字段
    UPDATE messages SET chunks = chunks_array WHERE id = msg_id;
END;
$$ LANGUAGE plpgsql;

-- 批量迁移
UPDATE messages SET chunks = '[]'::JSONB WHERE chunks IS NULL;
```

### 7.2 创建新表

```sql
-- ConversationConfig表
CREATE TABLE conversation_configs (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role_id VARCHAR(50),
    plan_mode_enabled BOOLEAN,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    UNIQUE(conversation_id)
);

-- GlobalSettings表
CREATE TABLE global_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    default_role_id VARCHAR(50) NOT NULL DEFAULT 'software_engineer',
    default_plan_mode BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    UNIQUE(user_id)
);

-- 插入默认全局设置
INSERT INTO global_settings (user_id, default_role_id, default_plan_mode)
VALUES (NULL, 'software_engineer', FALSE);
```

---

## 8. 总结

### 核心实体
1. **MessageChunk**：消息块基类，支持5种类型
2. **RolePreset**：角色预设，5个预定义角色
3. **ConversationConfig**：会话级配置，支持角色和计划模式覆盖
4. **GlobalSettings**：全局默认设置

### 关键设计决策
- 使用Pydantic确保类型安全
- JSONB存储灵活的chunks数组
- 三层配置（请求 > 会话 > 全局）
- 硬编码角色定义，数据库仅存引用
- 保留旧字段支持平滑迁移

### 扩展性考虑
- MessageType枚举可添加新类型（如image、file）
- RolePreset未来可支持数据库存储和用户自定义
- chunks的JSONB格式支持任意结构扩展
