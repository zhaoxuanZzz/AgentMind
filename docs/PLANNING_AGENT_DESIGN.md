# 任务规划 Agent 设计方案

## 📋 目录

1. [产品概述](#产品概述)
2. [功能需求](#功能需求)
3. [架构设计](#架构设计)
4. [数据模型设计](#数据模型设计)
5. [后端实现设计](#后端实现设计)
6. [前端实现设计](#前端实现设计)
7. [技术选型](#技术选型)
8. [实施计划](#实施计划)

---

## 产品概述

### 1.1 产品定位

任务规划 Agent 是一个基于 deepagents 的智能任务分解与执行系统，能够将复杂任务自动拆解为可执行的子任务，支持任务依赖管理、上下文隔离、子代理生成和长期记忆等功能。

### 1.2 核心价值

- **智能分解**：自动将复杂任务拆解为清晰的执行步骤
- **依赖管理**：支持任务间的依赖关系，确保执行顺序
- **上下文隔离**：通过子代理和文件系统工具管理大型上下文
- **持久记忆**：跨对话保存任务规划历史，支持长期追踪

### 1.3 使用场景

- 软件开发项目规划
- 研究任务分解
- 业务流程设计
- 复杂问题解决
- 多步骤任务执行

---

## 功能需求

### 2.1 核心功能

#### 2.1.1 规划与任务分解

**功能描述**：
- Agent 能够分析用户输入的复杂任务
- 自动拆解为离散的、可执行的子任务
- 每个任务包含：描述、状态、依赖关系、优先级
- 支持任务状态的实时跟踪和更新

**实现方式**：
- 使用 deepagents 内置的 `write_todos` 工具
- 工具输入：任务描述、依赖关系列表
- 工具输出：结构化的任务列表（JSON格式）

**任务数据结构**：
```json
{
  "task_id": "task_001",
  "description": "设计数据库架构",
  "status": "pending",
  "dependencies": ["task_000"],
  "priority": "high",
  "estimated_time": "2h",
  "assignee": null
}
```

#### 2.1.2 上下文管理

**功能描述**：
- 将大型上下文卸载到文件系统
- 防止上下文窗口溢出
- 支持可变长度工具结果的处理
- 通过文件系统工具管理中间结果

**实现方式**：
- 使用 deepagents 内置文件系统工具：
  - `ls`: 列出目录内容
  - `read_file`: 读取文件内容
  - `write_file`: 写入文件内容
  - `edit_file`: 编辑文件内容

**使用场景**：
- 保存任务规划的详细内容
- 存储子任务的执行结果
- 管理大型文档和代码片段
- 缓存中间计算结果

#### 2.1.3 子代理生成

**功能描述**：
- 为特定子任务生成专门的子代理
- 实现上下文隔离，保持主代理上下文干净
- 子代理专注于处理具体子任务
- 支持子代理的结果回传和整合

**实现方式**：
- 使用 deepagents 内置的 `task_agent` 工具
- 工具输入：子任务描述、所需工具列表、上下文信息
- 工具输出：子代理执行结果

**子代理特性**：
- 独立的上下文环境
- 可配置的工具集
- 结果自动回传主代理
- 支持异步执行

#### 2.1.4 长期记忆

**功能描述**：
- 利用 LangGraph 的存储机制
- 跨对话保存任务规划信息
- 支持任务历史的检索和复用
- 实现持久化的任务状态管理

**实现方式**：
- 使用 LangGraph 的 Checkpoint 机制
- 结合 PostgreSQL 存储任务元数据
- 使用 Redis 缓存活跃任务状态

**存储内容**：
- 任务规划历史
- 任务执行状态
- 任务依赖关系图
- 子代理执行记录

### 2.2 用户交互功能

#### 2.2.1 任务规划开关

**位置**：对话框上方，与"深度推理"开关并列

**功能**：
- 开启/关闭任务规划模式
- 开启后，Agent 会自动使用任务规划功能
- 关闭后，使用普通对话模式

**UI设计**：
- Switch 开关组件
- 图标：📋 或 🎯
- 标签："任务规划"
- 状态提示：开启时显示"已启用任务规划模式"

#### 2.2.2 任务依赖关系可视化

**功能描述**：
- 以流程图形式展示任务依赖关系
- 支持节点状态可视化（待执行/执行中/已完成/失败）
- 支持交互操作（查看详情、手动触发、跳过）

**展示方式**：
- 使用流程图库（如 react-flow、dagre）
- 节点表示任务
- 箭头表示依赖关系
- 颜色区分任务状态

**交互功能**：
- 点击节点查看任务详情
- 拖拽调整布局
- 缩放和平移视图
- 导出为图片

---

## 架构设计

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        前端层                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  ChatPage    │  │ 任务规划开关  │  │ 流程图组件    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            ↓ HTTP/WebSocket
┌─────────────────────────────────────────────────────────────┐
│                        API 层                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Chat API    │  │ Planning API │  │  Task API    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      服务层                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          Planning Agent Service                      │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  │  │
│  │  │ DeepAgents   │  │ LangGraph    │  │ Memory   │  │  │
│  │  │   Agent      │  │  Checkpoint  │  │ Manager  │  │  │
│  │  └──────────────┘  └──────────────┘  └──────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Tools Integration                        │  │
│  │  write_todos | task_agent | file_system_tools        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      存储层                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  PostgreSQL  │  │    Redis     │  │  FileSystem  │     │
│  │  (任务元数据) │  │  (状态缓存)  │  │  (上下文)    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 核心组件设计

#### 3.2.1 Planning Agent Service

**职责**：
- 管理任务规划 Agent 的生命周期
- 协调工具调用和子代理生成
- 处理任务状态更新和依赖检查
- 管理长期记忆的存储和检索

**主要方法**：
```python
class PlanningAgentService:
    async def create_planning_agent(
        self, 
        llm_config: LLMConfig,
        enable_planning: bool = True
    ) -> DeepAgent
    
    async def plan_task(
        self,
        task_description: str,
        conversation_id: int,
        agent: DeepAgent
    ) -> TaskPlan
    
    async def execute_task_step(
        self,
        task_id: str,
        agent: DeepAgent
    ) -> TaskResult
    
    async def update_task_status(
        self,
        task_id: str,
        status: TaskStatus
    )
    
    async def get_task_dependencies(
        self,
        task_id: str
    ) -> List[str]
```

#### 3.2.2 DeepAgents 工具集成

**write_todos 工具**：
```python
def write_todos(
    todos: List[Dict[str, Any]],
    dependencies: Optional[Dict[str, List[str]]] = None
) -> str:
    """
    创建任务列表
    
    Args:
        todos: 任务列表，每个任务包含：
            - id: 任务ID
            - description: 任务描述
            - priority: 优先级
            - estimated_time: 预估时间
        dependencies: 依赖关系映射 {task_id: [dependency_ids]}
    
    Returns:
        任务创建结果
    """
```

**task_agent 工具**：
```python
def create_task_agent(
    task_description: str,
    tools: List[str],
    context: Optional[Dict] = None
) -> TaskAgentResult:
    """
    创建子代理处理特定任务
    
    Args:
        task_description: 子任务描述
        tools: 需要的工具列表
        context: 上下文信息
    
    Returns:
        子代理执行结果
    """
```

**文件系统工具**：
- `ls(path: str) -> List[str]`: 列出目录内容
- `read_file(path: str) -> str`: 读取文件
- `write_file(path: str, content: str) -> str`: 写入文件
- `edit_file(path: str, edits: List[Edit]) -> str`: 编辑文件

#### 3.2.3 LangGraph 集成

**Checkpoint 配置**：
```python
from langgraph.checkpoint.postgres import PostgresSaver

checkpointer = PostgresSaver.from_conn_string(
    connection_string=settings.DATABASE_URL
)

# 创建带持久化的 Agent
agent = create_agent(
    tools=[...],
    checkpointer=checkpointer,
    thread_id=conversation_id
)
```

**状态管理**：
- 使用 LangGraph 的 StateGraph 管理任务状态
- 每个对话线程有独立的状态空间
- 支持状态快照和恢复

### 3.3 数据流设计

#### 3.3.1 任务规划流程

```
用户输入任务
    ↓
判断是否开启任务规划
    ↓ (是)
创建 Planning Agent
    ↓
调用 write_todos 工具
    ↓
生成任务列表和依赖关系
    ↓
保存到数据库
    ↓
返回任务规划结果
    ↓
前端展示流程图
```

#### 3.3.2 任务执行流程

```
用户触发任务执行
    ↓
检查任务依赖
    ↓
依赖未完成？
    ↓ (是) → 等待依赖完成
    ↓ (否)
更新任务状态为"执行中"
    ↓
创建子代理（如需要）
    ↓
执行任务步骤
    ↓
保存执行结果到文件系统
    ↓
更新任务状态
    ↓
检查后续任务依赖
    ↓
触发可执行的任务
```

---

## 数据模型设计

### 4.1 数据库表设计

#### 4.1.1 planning_tasks 表

存储任务规划的主任务信息。

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | INTEGER | 任务ID | PRIMARY KEY |
| conversation_id | INTEGER | 所属对话ID | FOREIGN KEY, NOT NULL |
| title | VARCHAR(200) | 任务标题 | NOT NULL |
| description | TEXT | 任务描述 | NOT NULL |
| status | VARCHAR(20) | 任务状态 | NOT NULL, DEFAULT 'pending' |
| plan_data | JSONB | 规划数据 | NULLABLE |
| created_at | TIMESTAMP | 创建时间 | NOT NULL |
| updated_at | TIMESTAMP | 更新时间 | NOT NULL |

**索引**：
- `idx_planning_tasks_conversation_id` - 对话ID索引
- `idx_planning_tasks_status` - 状态索引

#### 4.1.2 task_steps 表

存储任务拆解后的子步骤。

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | INTEGER | 步骤ID | PRIMARY KEY |
| planning_task_id | INTEGER | 所属规划任务ID | FOREIGN KEY, NOT NULL |
| step_id | VARCHAR(50) | 步骤唯一标识 | NOT NULL, UNIQUE |
| description | TEXT | 步骤描述 | NOT NULL |
| status | VARCHAR(20) | 步骤状态 | NOT NULL, DEFAULT 'pending' |
| priority | VARCHAR(10) | 优先级 | NULLABLE |
| estimated_time | VARCHAR(20) | 预估时间 | NULLABLE |
| dependencies | JSONB | 依赖的步骤ID列表 | NULLABLE |
| result | JSONB | 执行结果 | NULLABLE |
| sub_agent_id | VARCHAR(100) | 子代理ID | NULLABLE |
| context_file_path | VARCHAR(500) | 上下文文件路径 | NULLABLE |
| created_at | TIMESTAMP | 创建时间 | NOT NULL |
| updated_at | TIMESTAMP | 更新时间 | NOT NULL |

**索引**：
- `idx_task_steps_planning_task_id` - 规划任务ID索引
- `idx_task_steps_step_id` - 步骤ID索引
- `idx_task_steps_status` - 状态索引

**依赖关系存储格式**：
```json
{
  "dependencies": ["step_001", "step_002"],
  "dependents": ["step_004", "step_005"]
}
```

#### 4.1.3 task_execution_logs 表

存储任务执行日志。

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | INTEGER | 日志ID | PRIMARY KEY |
| task_step_id | INTEGER | 所属步骤ID | FOREIGN KEY, NOT NULL |
| action | VARCHAR(50) | 执行动作 | NOT NULL |
| tool_name | VARCHAR(100) | 使用的工具 | NULLABLE |
| input_data | JSONB | 输入数据 | NULLABLE |
| output_data | JSONB | 输出数据 | NULLABLE |
| execution_time | FLOAT | 执行时间（秒） | NULLABLE |
| created_at | TIMESTAMP | 创建时间 | NOT NULL |

**索引**：
- `idx_execution_logs_task_step_id` - 步骤ID索引
- `idx_execution_logs_created_at` - 创建时间索引

#### 4.1.4 langgraph_checkpoints 表

存储 LangGraph 的检查点数据（由 LangGraph 自动管理）。

| 字段名 | 类型 | 说明 |
|--------|------|------|
| thread_id | VARCHAR(255) | 线程ID（对应conversation_id） |
| checkpoint_ns | VARCHAR(255) | 命名空间 |
| checkpoint_id | VARCHAR(255) | 检查点ID |
| checkpoint | JSONB | 检查点数据 |
| parent_checkpoint_id | VARCHAR(255) | 父检查点ID |
| metadata | JSONB | 元数据 |

### 4.2 文件系统结构

```
workspace/
├── planning/
│   ├── {conversation_id}/
│   │   ├── task_{task_id}/
│   │   │   ├── plan.json          # 任务规划数据
│   │   │   ├── context/           # 上下文文件
│   │   │   │   ├── step_{step_id}_context.txt
│   │   │   │   └── ...
│   │   │   ├── results/           # 执行结果
│   │   │   │   ├── step_{step_id}_result.json
│   │   │   │   └── ...
│   │   │   └── sub_agents/        # 子代理数据
│   │   │       └── agent_{agent_id}/
│   │   └── ...
│   └── ...
└── ...
```

### 4.3 Redis 缓存结构

**任务状态缓存**：
```
Key: planning:task:{task_id}:status
Value: {
  "status": "in_progress",
  "current_step": "step_003",
  "progress": 0.6,
  "updated_at": "2024-01-01T12:00:00Z"
}
TTL: 3600秒
```

**依赖关系缓存**：
```
Key: planning:task:{task_id}:dependencies
Value: {
  "graph": {
    "step_001": ["step_002", "step_003"],
    "step_002": ["step_004"],
    ...
  },
  "ready_steps": ["step_001"],
  "blocked_steps": ["step_002", "step_003"]
}
TTL: 3600秒
```

---

## 后端实现设计

### 5.1 依赖安装

在 `backend/requirements.txt` 中添加：

```txt
# DeepAgents
deepagents>=0.1.0  # 需要确认实际版本号

# LangGraph
langgraph>=0.2.0
langgraph-checkpoint-postgres>=0.1.0

# 流程图数据处理
networkx>=3.0  # 用于依赖关系图分析
```

### 5.2 服务层实现

#### 5.2.1 PlanningAgentService

**文件路径**：`backend/app/services/planning_agent_service.py`

**核心实现**：

```python
from typing import List, Dict, Optional, Any
from deepagents import DeepAgent, create_agent
from langgraph.checkpoint.postgres import PostgresSaver
from app.services.llm_factory import llm_factory
from app.db import models
from sqlalchemy.orm import Session

class PlanningAgentService:
    """任务规划 Agent 服务"""
    
    def __init__(self):
        self.checkpointer = PostgresSaver.from_conn_string(
            settings.DATABASE_URL
        )
    
    async def create_planning_agent(
        self,
        conversation_id: int,
        llm_config: Optional[Dict] = None,
        enable_planning: bool = True
    ) -> DeepAgent:
        """创建任务规划 Agent"""
        
        # 获取 LLM
        llm = llm_factory.create_llm(
            provider=llm_config.get('provider') if llm_config else None,
            model_name=llm_config.get('model') if llm_config else None
        )
        
        # 创建工具列表
        tools = self._create_planning_tools()
        
        # 创建 Agent
        agent = create_agent(
            llm=llm,
            tools=tools,
            checkpointer=self.checkpointer,
            thread_id=str(conversation_id),
            system_prompt=self._get_planning_prompt() if enable_planning else None
        )
        
        return agent
    
    def _create_planning_tools(self) -> List:
        """创建规划相关工具"""
        from deepagents.tools import (
            write_todos,
            task_agent,
            ls,
            read_file,
            write_file,
            edit_file
        )
        
        return [
            write_todos,
            task_agent,
            ls,
            read_file,
            write_file,
            edit_file
        ]
    
    def _get_planning_prompt(self) -> str:
        """获取任务规划系统提示词"""
        return """
        你是一个专业的任务规划助手。你的职责是：
        1. 分析用户输入的复杂任务
        2. 将任务拆解为可执行的子步骤
        3. 识别步骤间的依赖关系
        4. 为每个步骤分配优先级和预估时间
        5. 使用 write_todos 工具创建任务列表
        
        在规划任务时，请考虑：
        - 任务的逻辑顺序
        - 步骤间的依赖关系
        - 资源的可用性
        - 时间的合理性
        """
    
    async def plan_task(
        self,
        task_description: str,
        conversation_id: int,
        agent: DeepAgent,
        db: Session
    ) -> Dict[str, Any]:
        """规划任务"""
        
        # 调用 Agent 进行规划
        response = await agent.invoke({
            "messages": [{
                "role": "user",
                "content": f"请为以下任务制定详细的执行计划：\n\n{task_description}"
            }]
        })
        
        # 从响应中提取任务列表
        todos = self._extract_todos_from_response(response)
        
        # 保存到数据库
        planning_task = self._save_planning_task(
            conversation_id=conversation_id,
            description=task_description,
            todos=todos,
            db=db
        )
        
        return {
            "task_id": planning_task.id,
            "steps": todos,
            "dependencies": self._build_dependency_graph(todos)
        }
    
    def _extract_todos_from_response(self, response: Dict) -> List[Dict]:
        """从 Agent 响应中提取任务列表"""
        # 解析 write_todos 工具的输出
        # 实现细节...
        pass
    
    def _save_planning_task(
        self,
        conversation_id: int,
        description: str,
        todos: List[Dict],
        db: Session
    ) -> models.PlanningTask:
        """保存规划任务到数据库"""
        # 实现细节...
        pass
    
    def _build_dependency_graph(self, todos: List[Dict]) -> Dict:
        """构建依赖关系图"""
        import networkx as nx
        
        G = nx.DiGraph()
        for todo in todos:
            G.add_node(todo['id'], **todo)
            for dep in todo.get('dependencies', []):
                G.add_edge(dep, todo['id'])
        
        return {
            "nodes": list(G.nodes(data=True)),
            "edges": list(G.edges())
        }
```

#### 5.2.2 工具包装器

**文件路径**：`backend/app/services/planning_tools.py`

```python
from typing import List, Dict, Any, Optional
from deepagents.tools import write_todos as _write_todos
import json
import os

class PlanningTools:
    """任务规划工具包装器"""
    
    @staticmethod
    def write_todos(
        todos: List[Dict[str, Any]],
        dependencies: Optional[Dict[str, List[str]]] = None
    ) -> str:
        """创建任务列表"""
        
        # 验证任务格式
        validated_todos = PlanningTools._validate_todos(todos)
        
        # 应用依赖关系
        if dependencies:
            for task_id, deps in dependencies.items():
                if task_id in validated_todos:
                    validated_todos[task_id]['dependencies'] = deps
        
        # 调用 deepagents 工具
        result = _write_todos(validated_todos, dependencies)
        
        return result
    
    @staticmethod
    def _validate_todos(todos: List[Dict]) -> Dict[str, Dict]:
        """验证任务格式"""
        validated = {}
        for todo in todos:
            if 'id' not in todo or 'description' not in todo:
                raise ValueError("任务必须包含 id 和 description")
            validated[todo['id']] = todo
        return validated
    
    @staticmethod
    def create_task_agent(
        task_description: str,
        tools: List[str],
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """创建子代理"""
        from deepagents.tools import task_agent as _task_agent
        
        result = _task_agent(
            task_description=task_description,
            tools=tools,
            context=context
        )
        
        return {
            "agent_id": result.get("agent_id"),
            "status": result.get("status"),
            "result": result.get("result")
        }
    
    @staticmethod
    def save_context_to_file(
        conversation_id: int,
        task_id: str,
        step_id: str,
        content: str
    ) -> str:
        """保存上下文到文件"""
        base_dir = os.path.join(
            settings.WORKSPACE_DIR,
            "planning",
            str(conversation_id),
            f"task_{task_id}"
        )
        os.makedirs(base_dir, exist_ok=True)
        
        file_path = os.path.join(
            base_dir,
            "context",
            f"step_{step_id}_context.txt"
        )
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return file_path
```

### 5.3 API 路由实现

#### 5.3.1 扩展 Chat API

**文件路径**：`backend/app/api/routes/chat.py`

在 `ChatRequest` schema 中添加：

```python
class ChatRequest(BaseModel):
    # ... 现有字段 ...
    enable_planning: Optional[bool] = False  # 新增：启用任务规划
```

在 `chat_stream` 路由中：

```python
@router.post("/stream")
async def chat_stream(request: ChatRequest, db: Session = Depends(get_db)):
    """流式处理聊天请求"""
    async def generate():
        # ... 现有代码 ...
        
        # 如果启用任务规划，创建 Planning Agent
        if request.enable_planning:
            from app.services.planning_agent_service import planning_agent_service
            
            planning_agent = await planning_agent_service.create_planning_agent(
                conversation_id=conversation.id,
                llm_config={
                    "provider": provider,
                    "model": model
                } if provider and model else None,
                enable_planning=True
            )
            
            # 使用 Planning Agent 处理消息
            # ... 实现细节 ...
        else:
            # 使用普通 Agent
            # ... 现有代码 ...
```

#### 5.3.2 Planning API

**文件路径**：`backend/app/api/routes/planning.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.api.schemas import (
    PlanningRequest,
    PlanningResponse,
    TaskDependencyGraph
)
from app.services.planning_agent_service import planning_agent_service

router = APIRouter(prefix="/planning", tags=["planning"])

@router.post("/plan", response_model=PlanningResponse)
async def plan_task(
    request: PlanningRequest,
    db: Session = Depends(get_db)
):
    """规划任务"""
    try:
        # 创建 Planning Agent
        agent = await planning_agent_service.create_planning_agent(
            conversation_id=request.conversation_id,
            llm_config=request.llm_config,
            enable_planning=True
        )
        
        # 执行规划
        result = await planning_agent_service.plan_task(
            task_description=request.task_description,
            conversation_id=request.conversation_id,
            agent=agent,
            db=db
        )
        
        return PlanningResponse(
            success=True,
            task_id=result["task_id"],
            steps=result["steps"],
            dependencies=result["dependencies"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tasks/{task_id}/dependencies", response_model=TaskDependencyGraph)
async def get_task_dependencies(
    task_id: int,
    db: Session = Depends(get_db)
):
    """获取任务依赖关系图"""
    # 实现细节...
    pass

@router.get("/tasks/{task_id}/status")
async def get_task_status(
    task_id: int,
    db: Session = Depends(get_db)
):
    """获取任务执行状态"""
    # 实现细节...
    pass
```

### 5.4 Schema 定义

**文件路径**：`backend/app/api/schemas.py`

```python
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

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
```

---

## 前端实现设计

### 6.1 UI 组件设计

#### 6.1.1 任务规划开关

**位置**：`ChatPage.tsx` 的输入区域上方

**实现**：

```tsx
// 在 ChatPage.tsx 中添加状态
const [enablePlanning, setEnablePlanning] = useState<boolean>(() => {
  const saved = localStorage.getItem('enablePlanning')
  return saved === 'true'
})

// 在输入区域上方添加开关
<div className="planning-controls">
  <Space>
    <Switch
      checked={enablePlanning}
      onChange={(checked) => {
        setEnablePlanning(checked)
        localStorage.setItem('enablePlanning', String(checked))
      }}
      checkedChildren="任务规划"
      unCheckedChildren="普通对话"
    />
    {enablePlanning && (
      <Tag color="blue" icon={<CheckCircleOutlined />}>
        已启用任务规划模式
      </Tag>
    )}
  </Space>
</div>
```

#### 6.1.2 任务依赖流程图组件

**文件路径**：`frontend/src/components/TaskDependencyGraph.tsx`

**实现**：

```tsx
import React, { useCallback, useMemo } from 'react'
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType
} from 'reactflow'
import 'reactflow/dist/style.css'
import { Card, Tag, Tooltip } from 'antd'
import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  CloseCircleOutlined,
  SyncOutlined
} from '@ant-design/icons'

interface TaskNode {
  id: string
  description: string
  status: 'pending' | 'in_progress' | 'completed' | 'failed'
  priority?: string
  estimated_time?: string
}

interface TaskDependencyGraphProps {
  tasks: TaskNode[]
  dependencies: Array<{ source: string; target: string }>
  onTaskClick?: (taskId: string) => void
}

const TaskDependencyGraph: React.FC<TaskDependencyGraphProps> = ({
  tasks,
  dependencies,
  onTaskClick
}) => {
  // 节点配置
  const nodes: Node[] = useMemo(() => {
    return tasks.map((task) => {
      const statusConfig = {
        pending: { color: '#d9d9d9', icon: <ClockCircleOutlined /> },
        in_progress: { color: '#1890ff', icon: <SyncOutlined spin /> },
        completed: { color: '#52c41a', icon: <CheckCircleOutlined /> },
        failed: { color: '#ff4d4f', icon: <CloseCircleOutlined /> }
      }[task.status]

      return {
        id: task.id,
        type: 'taskNode',
        position: { x: 0, y: 0 }, // 将由布局算法计算
        data: {
          label: (
            <Card
              size="small"
              style={{
                width: 200,
                borderColor: statusConfig.color,
                borderWidth: 2
              }}
            >
              <div style={{ marginBottom: 8 }}>
                <Tag color={statusConfig.color} icon={statusConfig.icon}>
                  {task.status}
                </Tag>
                {task.priority && (
                  <Tag>{task.priority}</Tag>
                )}
              </div>
              <div style={{ fontSize: 12, color: '#666' }}>
                {task.description}
              </div>
              {task.estimated_time && (
                <div style={{ fontSize: 11, color: '#999', marginTop: 4 }}>
                  预估: {task.estimated_time}
                </div>
              )}
            </Card>
          )
        },
        style: {
          border: `2px solid ${statusConfig.color}`,
          borderRadius: 8
        }
      }
    })
  }, [tasks])

  // 边配置
  const edges: Edge[] = useMemo(() => {
    return dependencies.map((dep) => ({
      id: `${dep.source}-${dep.target}`,
      source: dep.source,
      target: dep.target,
      type: 'smoothstep',
      animated: tasks.find(t => t.id === dep.target)?.status === 'in_progress',
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: '#1890ff'
      },
      style: {
        strokeWidth: 2,
        stroke: '#1890ff'
      }
    }))
  }, [dependencies, tasks])

  // 布局算法（使用 dagre）
  const layoutedNodes = useMemo(() => {
    // 使用 dagre 进行自动布局
    // 实现细节...
    return nodes
  }, [nodes, edges])

  const [nodesState, setNodes, onNodesChange] = useNodesState(layoutedNodes)
  const [edgesState, setEdges, onEdgesChange] = useEdgesState(edges)

  return (
    <div style={{ width: '100%', height: '600px', border: '1px solid #d9d9d9', borderRadius: 8 }}>
      <ReactFlow
        nodes={nodesState}
        edges={edgesState}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={(event, node) => {
          onTaskClick?.(node.id)
        }}
        fitView
      >
        <Background />
        <Controls />
        <MiniMap />
      </ReactFlow>
    </div>
  )
}

export default TaskDependencyGraph
```

#### 6.1.3 任务规划结果展示

**在 ChatPage.tsx 中集成**：

```tsx
// 添加状态管理任务规划结果
const [planningResult, setPlanningResult] = useState<any>(null)

// 在消息渲染中添加任务规划展示
{planningResult && (
  <Card
    title={
      <Space>
        <ThunderboltFilled />
        <span>任务规划结果</span>
      </Space>
    }
    style={{ marginTop: 16 }}
  >
    <TaskDependencyGraph
      tasks={planningResult.steps}
      dependencies={planningResult.dependencies.edges}
      onTaskClick={(taskId) => {
        // 显示任务详情
        Modal.info({
          title: '任务详情',
          content: (
            <div>
              <p>任务ID: {taskId}</p>
              {/* 更多详情 */}
            </div>
          )
        })
      }}
    />
  </Card>
)}
```

### 6.2 API 集成

**文件路径**：`frontend/src/api/services.ts`

```typescript
// 添加 Planning API
export const planningApi = {
  planTask: (data: {
    conversation_id: number
    task_description: string
    llm_config?: { provider?: string; model?: string }
  }) => apiClient.post<any, PlanningResponse>('/planning/plan', data),
  
  getTaskDependencies: (taskId: number) =>
    apiClient.get<any, TaskDependencyGraph>(`/planning/tasks/${taskId}/dependencies`),
  
  getTaskStatus: (taskId: number) =>
    apiClient.get<any, TaskStatus>(`/planning/tasks/${taskId}/status`)
}
```

**文件路径**：`frontend/src/api/types.ts`

```typescript
export interface PlanningResponse {
  success: boolean
  task_id: number
  steps: TaskStep[]
  dependencies: TaskDependencyGraph
}

export interface TaskStep {
  step_id: string
  description: string
  status: 'pending' | 'in_progress' | 'completed' | 'failed'
  priority?: string
  estimated_time?: string
  dependencies: string[]
  result?: any
}

export interface TaskDependencyGraph {
  nodes: Array<{
    id: string
    data: any
  }>
  edges: Array<{
    source: string
    target: string
  }>
}
```

### 6.3 样式设计

**文件路径**：`frontend/src/pages/ChatPage.css`

```css
/* 任务规划控制区域 */
.planning-controls {
  padding: 12px 16px;
  background: #fafafa;
  border-bottom: 1px solid #e8e8e8;
  margin-bottom: 16px;
}

/* 任务流程图容器 */
.task-graph-container {
  margin: 16px 0;
  padding: 16px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* 任务节点样式 */
.task-node {
  padding: 12px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.3s;
}

.task-node:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

/* 任务状态颜色 */
.task-status-pending {
  border-left: 4px solid #d9d9d9;
}

.task-status-in_progress {
  border-left: 4px solid #1890ff;
}

.task-status-completed {
  border-left: 4px solid #52c41a;
}

.task-status-failed {
  border-left: 4px solid #ff4d4f;
}
```

---

## 技术选型

### 7.1 核心依赖

| 依赖包 | 版本 | 用途 |
|--------|------|------|
| deepagents | >=0.1.0 | 核心 Agent 框架 |
| langgraph | >=0.2.0 | 状态管理和持久化 |
| langgraph-checkpoint-postgres | >=0.1.0 | PostgreSQL 检查点 |
| networkx | >=3.0 | 依赖关系图分析 |

### 7.2 前端依赖

| 依赖包 | 版本 | 用途 |
|--------|------|------|
| reactflow | >=11.0 | 流程图可视化 |
| dagre | >=0.8.0 | 自动布局算法 |
| @ant-design/icons | 已安装 | 图标库 |

### 7.3 安装命令

**后端**：
```bash
cd backend
pip install deepagents langgraph langgraph-checkpoint-postgres networkx
```

**前端**：
```bash
cd frontend
npm install reactflow dagre
```

---

## 实施计划

### 8.1 阶段一：基础框架搭建（1-2周）

**任务**：
1. 安装 deepagents 和相关依赖
2. 创建 PlanningAgentService 基础框架
3. 实现数据库表结构（planning_tasks, task_steps）
4. 创建基础 API 路由

**交付物**：
- PlanningAgentService 基础实现
- 数据库迁移脚本
- Planning API 基础路由

### 8.2 阶段二：核心功能实现（2-3周）

**任务**：
1. 集成 write_todos 工具
2. 实现任务依赖关系管理
3. 集成文件系统工具（ls, read_file, write_file, edit_file）
4. 实现上下文管理功能

**交付物**：
- 完整的任务规划功能
- 上下文文件管理系统
- 任务依赖关系存储和查询

### 8.3 阶段三：子代理和记忆（2周）

**任务**：
1. 集成 task_agent 工具
2. 实现子代理创建和管理
3. 集成 LangGraph Checkpoint
4. 实现长期记忆功能

**交付物**：
- 子代理生成和执行
- 持久化状态管理
- 跨对话记忆功能

### 8.4 阶段四：前端实现（2-3周）

**任务**：
1. 实现任务规划开关 UI
2. 开发任务依赖流程图组件
3. 集成到 ChatPage
4. 实现任务状态实时更新

**交付物**：
- 完整的任务规划 UI
- 流程图可视化组件
- 实时状态更新功能

### 8.5 阶段五：测试和优化（1-2周）

**任务**：
1. 单元测试和集成测试
2. 性能优化
3. UI/UX 优化
4. 文档完善

**交付物**：
- 测试报告
- 性能优化报告
- 用户使用文档

---

## 总结

本设计方案基于 deepagents 框架，实现了一个完整的任务规划 Agent 系统。系统具备以下特点：

1. **智能规划**：自动分解复杂任务，识别依赖关系
2. **上下文管理**：通过文件系统工具管理大型上下文
3. **子代理支持**：为特定任务生成专门的子代理
4. **持久记忆**：利用 LangGraph 实现跨对话记忆
5. **可视化展示**：流程图形式展示任务依赖关系

该方案遵循了现有项目的架构模式，具有良好的可扩展性和可维护性。实施过程中需要重点关注 deepagents 的具体 API 和 LangGraph 的集成细节。

---

## 附录

### A. 参考资源

- [DeepAgents 文档](https://github.com/deepagents/deepagents)（需要确认实际地址）
- [LangGraph 文档](https://langchain-ai.github.io/langgraph/)
- [ReactFlow 文档](https://reactflow.dev/)

### B. 注意事项

1. **deepagents 版本**：需要确认 deepagents 的实际版本号和 API
2. **工具可用性**：确认 write_todos、task_agent 等工具的具体实现
3. **性能考虑**：大量任务时的流程图渲染性能
4. **安全性**：文件系统操作的权限控制

### C. 后续扩展

- 任务优先级自动调整
- 任务执行时间预估优化
- 多用户协作支持
- 任务模板和复用
- 任务执行监控和告警
