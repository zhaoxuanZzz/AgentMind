# 研究文档：聊天界面增强

**特性**：002-chat-ui-enhancement  
**日期**：2026-01-26  
**阶段**：Phase 0

## 研究概述

本文档记录了实现聊天界面增强功能所需的技术研究结果，包括ant-design-x组件使用、LangChain/LangGraph计划模式实现、消息格式设计和角色预设系统。

---

## 1. Ant Design X 消息渲染方案

### 1.1 研究目标

如何使用@ant-design/x组件渲染不同类型的消息（thinking、tools、plan、text）

### 1.2 核心发现

**可用组件**：
- `Bubble`：消息气泡组件，支持自定义内容和样式
- `Sender`：发送者信息组件
- `Conversations`：对话列表组件
- `Prompts`：提示词组件

**消息渲染策略**：
```tsx
// 基于消息类型渲染不同样式
interface MessageChunk {
  type: 'text' | 'thinking' | 'tool' | 'plan' | 'system';
  content: string;
  metadata?: any;
}

// 使用Bubble组件的variant属性区分类型
<Bubble
  content={renderContentByType(message)}
  variant={message.type === 'thinking' ? 'shadow' : 'filled'}
  styles={{
    content: getStylesByType(message.type)
  }}
/>
```

**决策**：使用Bubble组件作为基础，通过自定义content渲染器处理不同消息类型。每种类型有独特的视觉样式（图标、背景色、边框）。

**理由**：
- Bubble提供了足够的灵活性，可以自定义内容和样式
- 不需要完全重写消息组件，利用现有的ant-design-x生态
- 保持设计系统的一致性

**替代方案考虑**：
- 完全自定义组件：被拒绝，因为失去了ant-design-x的样式一致性和内置功能
- 使用多个不同组件：被拒绝，因为增加了复杂度，难以统一管理

---

## 2. 消息格式设计

### 2.1 研究目标

设计前后端统一的消息格式，支持流式传输和多种消息类型

### 2.2 核心发现

**流式消息格式**：
```typescript
// SSE (Server-Sent Events) 格式
data: {"type": "thinking", "content": "我正在思考如何解决这个问题..."}
data: {"type": "tool", "tool_name": "calculator", "tool_input": {"expr": "2+2"}, "tool_output": "4"}
data: {"type": "plan", "step": 1, "description": "分析问题需求", "status": "completed"}
data: {"type": "text", "content": "最终答案是..."}
data: {"type": "done"}
```

**消息类型定义**：
```python
# 后端 Pydantic 模型
from enum import Enum
from pydantic import BaseModel

class MessageType(str, Enum):
    TEXT = "text"
    THINKING = "thinking"
    TOOL = "tool"
    PLAN = "plan"
    SYSTEM = "system"

class MessageChunk(BaseModel):
    type: MessageType
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
class ThinkingChunk(MessageChunk):
    type: Literal[MessageType.THINKING]
    content: str

class ToolChunk(MessageChunk):
    type: Literal[MessageType.TOOL]
    tool_name: str
    tool_input: Dict[str, Any]
    tool_output: Optional[str] = None
    
class PlanChunk(MessageChunk):
    type: Literal[MessageType.PLAN]
    step: int
    description: str
    status: Literal["pending", "in_progress", "completed", "failed"]
```

**决策**：使用SSE格式的JSON流，每个chunk都是类型化的消息对象。

**理由**：
- JSON格式易于解析和扩展
- 类型化确保前后端一致性
- SSE是HTTP标准，浏览器原生支持
- 可以逐步渲染，提供流畅的用户体验

**替代方案考虑**：
- WebSocket：被拒绝，因为增加了基础设施复杂度，且HTTP/2下SSE性能足够
- 普通JSON响应：被拒绝，因为无法实现流式渲染
- 纯文本流：被拒绝，因为难以处理结构化数据

---

## 3. LangChain/LangGraph 计划模式实现

### 3.1 研究目标

如何在LangChain/LangGraph中实现计划-执行模式，以及问题复杂度判断

### 3.2 核心发现

**计划-执行模式（Plan-and-Execute）**：
```python
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage

# 计划模式的提示词
PLAN_MODE_PROMPT = """你是一个善于制定计划的AI助手。
对于用户的请求，你应该：
1. 首先分析问题的复杂度
2. 如果是复杂任务，制定详细的执行计划
3. 按计划步骤逐一执行
4. 每完成一步，报告进度

计划格式：
Step 1: [步骤描述]
Step 2: [步骤描述]
...
"""

def should_use_plan_mode(message: str) -> bool:
    """判断是否需要使用计划模式
    
    简单问题特征：
    - 问候语（你好、hi等）
    - 单一事实查询（今天天气、1+1等）
    - 简短对话（<20字符）
    
    复杂任务特征：
    - 包含"帮我"、"规划"、"设计"等关键词
    - 多步骤任务（"首先...然后...最后..."）
    - 代码生成、分析等需要推理的任务
    """
    # 启发式规则
    simple_patterns = [
        r'^(你好|hi|hello)',
        r'^\d+[\+\-\*\/]\d+$',  # 简单数学
        r'^.{1,20}$'  # 短消息
    ]
    
    complex_patterns = [
        r'(帮我|请|规划|设计|开发|分析|创建)',
        r'(首先|然后|最后|接下来)',
        r'(代码|程序|函数|类|模块)'
    ]
    
    # 检查简单模式
    for pattern in simple_patterns:
        if re.search(pattern, message):
            return False
    
    # 检查复杂模式
    for pattern in complex_patterns:
        if re.search(pattern, message):
            return True
    
    # 默认：中等长度视为复杂
    return len(message) > 50

async def plan_and_execute(message: str, tools: List, llm):
    """计划-执行模式"""
    # 第一步：生成计划
    plan_prompt = f"{PLAN_MODE_PROMPT}\n\n用户请求：{message}\n\n请制定执行计划："
    plan_response = await llm.ainvoke([SystemMessage(content=plan_prompt)])
    
    # 解析计划步骤
    steps = parse_plan_steps(plan_response.content)
    
    # 第二步：逐步执行
    for i, step in enumerate(steps):
        yield {
            "type": "plan",
            "step": i + 1,
            "description": step,
            "status": "in_progress"
        }
        
        # 执行当前步骤
        result = await execute_step(step, tools, llm)
        
        yield {
            "type": "plan",
            "step": i + 1,
            "description": step,
            "status": "completed",
            "result": result
        }
```

**决策**：使用启发式规则判断问题复杂度，复杂任务采用二阶段执行（先计划后执行）。

**理由**：
- 启发式规则实现简单，响应快速
- 二阶段执行让用户清楚看到AI的计划过程
- LangChain支持多步骤流式输出

**替代方案考虑**：
- 使用LLM判断复杂度：被拒绝，因为增加延迟和成本
- 始终使用计划模式：被拒绝，因为简单问题会显得冗余
- ReAct模式：保留，作为非计划模式的执行方式

---

## 4. 角色预设系统实现

### 4.1 研究目标

如何管理和应用角色预设，支持全局默认+对话级覆盖

### 4.2 核心发现

**角色预设数据结构**：
```python
class RolePreset(BaseModel):
    id: str
    name: str  # 显示名称
    description: str  # 角色描述
    system_prompt: str  # 系统提示词
    config: Dict[str, Any]  # 额外配置（温度、max_tokens等）
    
# 预定义角色
ROLE_PRESETS = {
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
        - 考虑性能和可维护性
        """,
        config={"temperature": 0.3}
    ),
    "product_manager": RolePreset(
        id="product_manager",
        name="产品经理",
        description="专注于产品规划、需求分析和用户体验",
        system_prompt="""你是一位经验丰富的产品经理，擅长：
        - 分析用户需求和痛点
        - 制定产品路线图
        - 撰写PRD文档
        - 平衡商业价值和用户体验
        
        回答时请：
        - 从用户视角思考
        - 提供数据支持的建议
        - 考虑商业可行性
        """,
        config={"temperature": 0.7}
    ),
    # ... 其他角色
}
```

**状态管理策略**：
```python
# 数据库模型
class GlobalSettings(Base):
    __tablename__ = "global_settings"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=True)  # 未来支持多用户
    default_role_id = Column(String, default="software_engineer")
    default_plan_mode = Column(Boolean, default=False)
    
class ConversationConfig(Base):
    __tablename__ = "conversation_configs"
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    role_id = Column(String, nullable=True)  # null = 使用全局默认
    plan_mode_enabled = Column(Boolean, nullable=True)  # null = 使用全局默认

# 获取当前对话的有效角色
def get_effective_role(conversation_id: int, db: Session) -> str:
    # 1. 尝试获取对话级配置
    config = db.query(ConversationConfig).filter_by(
        conversation_id=conversation_id
    ).first()
    
    if config and config.role_id:
        return config.role_id
    
    # 2. 使用全局默认
    global_settings = db.query(GlobalSettings).first()
    return global_settings.default_role_id if global_settings else "software_engineer"
```

**决策**：角色预设初期硬编码在代码中，存储在Python字典。配置采用三层结构：硬编码角色定义 → 全局默认设置 → 对话级覆盖。

**理由**：
- 硬编码角色简化初期开发，无需管理UI
- 三层结构提供了灵活性和便利性的平衡
- 数据库仅存储引用（role_id），不存储完整提示词，便于统一更新

**替代方案考虑**：
- 角色存储在数据库：保留为未来扩展，但初期不实现
- 仅全局角色设置：被拒绝，因为用户可能需要不同对话使用不同角色
- 仅对话级角色：被拒绝，因为每次都要选择，用户体验差

---

## 5. 流式传输优化

### 5.1 研究目标

如何优化流式传输性能，确保<100ms的渲染延迟

### 5.2 核心发现

**后端优化**：
```python
async def stream_chat_v2(message: str, config: ChatConfig):
    """优化的流式聊天接口"""
    async def generate():
        buffer = []
        buffer_size = 0
        BUFFER_THRESHOLD = 50  # 字符数阈值
        
        async for chunk in agent_stream(message, config):
            # 累积小块，减少网络往返
            buffer.append(chunk)
            buffer_size += len(chunk.get("content", ""))
            
            # 达到阈值或遇到特殊类型，立即发送
            if buffer_size >= BUFFER_THRESHOLD or chunk["type"] != "text":
                for item in buffer:
                    yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"
                buffer = []
                buffer_size = 0
        
        # 发送剩余内容
        for item in buffer:
            yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"
        
        yield "data: {\"type\": \"done\"}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
```

**前端优化**：
```typescript
// 使用requestAnimationFrame批量更新DOM
class MessageStreamRenderer {
  private pendingUpdates: MessageChunk[] = [];
  private isScheduled = false;
  
  addChunk(chunk: MessageChunk) {
    this.pendingUpdates.push(chunk);
    
    if (!this.isScheduled) {
      this.isScheduled = true;
      requestAnimationFrame(() => this.flush());
    }
  }
  
  private flush() {
    // 批量应用所有更新
    const chunks = this.pendingUpdates;
    this.pendingUpdates = [];
    this.isScheduled = false;
    
    // 合并相同类型的连续chunks
    const merged = this.mergeChunks(chunks);
    
    // 一次性更新状态
    setState(prevMessages => updateMessages(prevMessages, merged));
  }
}
```

**决策**：后端进行适度缓冲，前端使用requestAnimationFrame批量渲染。

**理由**：
- 减少网络往返次数，降低延迟
- 避免频繁DOM更新导致的性能问题
- 保持流式体验的同时优化性能

---

## 6. 向后兼容性

### 6.1 研究目标

如何确保新消息格式与现有对话历史兼容

### 6.2 核心发现

**迁移策略**：
```python
# 旧消息格式到新格式的转换
def migrate_legacy_message(old_message: Message) -> List[MessageChunk]:
    """将旧格式消息转换为新格式"""
    chunks = []
    
    # 1. 处理thinking字段
    if old_message.thinking:
        chunks.append({
            "type": "thinking",
            "content": old_message.thinking
        })
    
    # 2. 处理intermediate_steps（工具调用）
    if old_message.intermediate_steps:
        for step in old_message.intermediate_steps:
            chunks.append({
                "type": "tool",
                "tool_name": step.get("tool"),
                "tool_input": step.get("tool_input"),
                "tool_output": step.get("observation")
            })
    
    # 3. 处理主内容
    if old_message.content:
        chunks.append({
            "type": "text",
            "content": old_message.content
        })
    
    return chunks

# 前端处理
function renderMessage(message: Message) {
  // 检测消息格式
  if (message.chunks) {
    // 新格式：直接渲染chunks
    return message.chunks.map(renderChunk);
  } else {
    // 旧格式：转换后渲染
    const chunks = migrateLegacyMessage(message);
    return chunks.map(renderChunk);
  }
}
```

**决策**：在前端进行格式检测和转换，后端保持两个API端点（/stream和/stream-v2）。

**理由**：
- 不影响现有功能
- 前端转换逻辑简单
- 给予足够的迁移时间

---

## 7. 总结和决策汇总

| 技术点 | 决策 | 关键理由 |
|--------|------|----------|
| 消息渲染 | 使用ant-design-x的Bubble组件，自定义content | 平衡灵活性和一致性 |
| 消息格式 | SSE格式的类型化JSON流 | 标准化、易扩展、流式友好 |
| 计划模式 | 启发式规则+二阶段执行 | 简单高效，用户体验好 |
| 复杂度判断 | 基于关键词和消息长度的启发式规则 | 快速响应，无需额外LLM调用 |
| 角色预设 | 硬编码定义+三层配置（角色→全局→对话） | 初期简单，保留扩展性 |
| 状态管理 | 数据库存储role_id引用，不存储完整提示词 | 便于统一更新角色定义 |
| 流式优化 | 后端缓冲+前端RAF批量渲染 | 性能和体验平衡 |
| 向后兼容 | 前端格式检测+转换，双API端点 | 平滑迁移，无破坏性变更 |

**未解决问题/后续研究**：
- 角色预设的动态管理UI（Phase 2或后续版本）
- 更智能的复杂度判断（可能引入轻量级分类模型）
- 计划步骤的并行执行（当前是串行）
