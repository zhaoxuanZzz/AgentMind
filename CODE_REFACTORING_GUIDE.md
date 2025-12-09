# 代码规范化与重构指南

## 📋 概述

本文档基于当前项目代码分析，提出需要规范化、拆分和优化的具体建议，确保代码的可复用性和可扩展性。

---

## 🔴 主要问题

### 1. **agent_service.py 文件过大（880行）**

**问题：**
- 单个文件承担过多职责
- 包含 Agent 创建、工具管理、流式处理、回调处理、提示词构建等多个职责
- 难以维护和测试

**建议拆分：**
```
backend/app/services/
├── agent_service.py          # 核心 Agent 服务（简化）
├── agent/
│   ├── __init__.py
│   ├── agent_factory.py      # Agent 创建工厂
│   ├── agent_types.py        # Agent 类型枚举
│   └── prompt_builder.py     # 提示词构建器
├── streaming/
│   ├── __init__.py
│   ├── stream_handler.py     # 流式处理回调（从 agent_service 移出）
│   └── stream_manager.py     # 流式管理器
└── memory/
    ├── __init__.py
    └── memory_manager.py     # 内存管理器
```

---

### 2. **代码重复严重**

**问题位置：**
- `create_agent()` 和 `chat_stream()` 中有大量重复的提示词构建逻辑（行 125-152 和 439-459）
- 知识卡片检索逻辑重复（行 127-151 和 441-459）
- ReAct Agent 和 OpenAI Functions Agent 的提示词构建重复

**建议：**
- 提取 `PromptBuilder` 类统一管理提示词构建
- 提取 `KnowledgeCardRetriever` 类统一处理知识卡片检索
- 使用策略模式处理不同 Agent 类型的提示词差异

---

### 3. **工具管理不统一**

**问题：**
- 工具创建分散在 `_create_tools()` 方法中
- 添加新工具需要修改核心服务代码
- 缺少工具注册机制

**建议：**
```python
# backend/app/services/tools/registry.py
class ToolRegistry:
    """工具注册器 - 统一管理所有工具"""
    _tools: Dict[str, Callable] = {}
    
    @classmethod
    def register(cls, name: str, tool_factory: Callable):
        """注册工具工厂"""
        cls._tools[name] = tool_factory
    
    @classmethod
    def create_tools(cls, config: Dict) -> List[Tool]:
        """根据配置创建工具列表"""
        tools = []
        for name, factory in cls._tools.items():
            if cls._should_include(name, config):
                tool = factory(config)
                if tool:
                    tools.append(tool)
        return tools
```

**工具注册示例：**
```python
# backend/app/services/tools/__init__.py
from .registry import ToolRegistry
from .calculator_tool import create_calculator_tool
from .knowledge_tool import create_knowledge_retrieval_tool
from .web_search_tool import create_web_search_tool

# 注册工具
ToolRegistry.register("calculator", create_calculator_tool)
ToolRegistry.register("knowledge", create_knowledge_retrieval_tool)
ToolRegistry.register("web_search", create_web_search_tool)
```

---

### 4. **提示词硬编码**

**问题：**
- 提示词模板直接写在代码中（行 178-210, 249-260, 473-504）
- 难以维护和本地化
- 无法动态调整

**建议：**
- 提取到配置文件或模板文件
- 使用模板引擎（Jinja2）支持变量替换

```
backend/app/agent/prompts/
├── react_agent.txt
├── openai_functions_agent.txt
└── system_prompts/
    ├── base.txt
    └── with_knowledge.txt
```

---

### 5. **缺少接口抽象**

**问题：**
- 直接依赖 LangChain 具体实现
- 难以替换底层框架
- 测试困难

**建议：**
```python
# backend/app/services/agent/interfaces.py
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, AsyncIterator

class IAgent(ABC):
    """Agent 接口"""
    
    @abstractmethod
    async def chat(self, message: str, **kwargs) -> Dict:
        """处理对话"""
        pass
    
    @abstractmethod
    async def chat_stream(self, message: str, **kwargs) -> AsyncIterator[Dict]:
        """流式处理对话"""
        pass

class IAgentFactory(ABC):
    """Agent 工厂接口"""
    
    @abstractmethod
    def create_agent(self, agent_type: str, **kwargs) -> IAgent:
        """创建 Agent"""
        pass
```

---

### 6. **错误处理不统一**

**问题：**
- 错误处理分散，格式不一致
- 缺少统一的错误类型定义

**建议：**
```python
# backend/app/core/exceptions.py
class AgentSystemException(Exception):
    """基础异常"""
    pass

class LLMException(AgentSystemException):
    """LLM 相关异常"""
    pass

class ToolException(AgentSystemException):
    """工具执行异常"""
    pass

class KnowledgeBaseException(AgentSystemException):
    """知识库异常"""
    pass
```

---

### 7. **类型注解不完整**

**问题：**
- 部分方法缺少类型注解
- `db_session` 参数类型不明确（行 101, 329, 396）

**建议：**
```python
from sqlalchemy.orm import Session

def create_agent(
    self,
    db_session: Optional[Session] = None,  # 明确类型
    ...
) -> AgentExecutor:
    pass
```

---

### 8. **配置管理分散**

**问题：**
- 配置项分散在多个地方
- 缺少配置验证

**建议：**
```python
# backend/app/core/config_validator.py
from pydantic import validator

class Settings(BaseSettings):
    # ... 现有配置 ...
    
    @validator('LLM_PROVIDER')
    def validate_llm_provider(cls, v):
        if v not in ['openai', 'dashscope']:
            raise ValueError(f"Invalid LLM provider: {v}")
        return v
```

---

### 9. **内存管理可优化**

**问题：**
- 内存创建逻辑重复（行 334-347 和 401-412）
- 缺少内存策略配置

**建议：**
```python
# backend/app/services/memory/memory_manager.py
class MemoryManager:
    """统一管理对话内存"""
    
    def create_memory(
        self,
        history: Optional[List[Dict]] = None,
        max_history_length: int = 20
    ) -> ConversationBufferMemory:
        """创建并初始化内存"""
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        if history:
            self._load_history(memory, history, max_history_length)
        return memory
```

---

### 10. **Bug：未定义变量**

**问题：**
- `agent_service.py` 第 110 行使用了未定义的 `llm_instance` 变量

**修复：**
```python
# 第 109-113 行应该改为：
def create_agent(
    self,
    llm_instance: Optional[Any] = None,  # 添加参数
    ...
) -> AgentExecutor:
    if llm_instance:
        llm = llm_instance
    else:
        llm = self._get_llm(provider, model, streaming=False)
```

---

## 📁 建议的新目录结构

```
backend/app/
├── core/
│   ├── config.py
│   ├── config_validator.py      # 新增：配置验证
│   └── exceptions.py             # 新增：统一异常定义
├── services/
│   ├── agent_service.py          # 简化后的核心服务
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── interfaces.py         # 新增：接口定义
│   │   ├── agent_factory.py     # 新增：Agent 工厂
│   │   ├── agent_types.py        # 新增：Agent 类型
│   │   └── prompt_builder.py     # 新增：提示词构建器
│   ├── streaming/
│   │   ├── __init__.py
│   │   ├── stream_handler.py     # 从 agent_service 移出
│   │   └── stream_manager.py     # 新增：流式管理器
│   ├── memory/
│   │   ├── __init__.py
│   │   └── memory_manager.py     # 新增：内存管理器
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── registry.py           # 新增：工具注册器
│   │   ├── base.py               # 新增：工具基类
│   │   ├── calculator_tool.py   # 从 agent_service 移出
│   │   ├── knowledge_tool.py
│   │   ├── web_search_tool.py
│   │   └── web_scraper_tool.py
│   ├── knowledge_service.py
│   └── llm_factory.py
└── agent/
    └── prompts/                  # 新增：提示词模板目录
        ├── react_agent.txt
        ├── openai_functions_agent.txt
        └── system_prompts/
            ├── base.txt
            └── with_knowledge.txt
```

---

## 🎯 重构优先级

### 高优先级（立即处理）
1. ✅ **修复 Bug**：`llm_instance` 未定义问题
2. ✅ **拆分 agent_service.py**：将流式处理和回调处理器独立
3. ✅ **提取提示词构建逻辑**：创建 `PromptBuilder` 类
4. ✅ **统一工具管理**：实现工具注册器

### 中优先级（近期处理）
5. ⚠️ **提取知识卡片检索逻辑**：创建 `KnowledgeCardRetriever`
6. ⚠️ **提取内存管理逻辑**：创建 `MemoryManager`
7. ⚠️ **提示词外部化**：移到配置文件
8. ⚠️ **完善类型注解**：补充所有方法的类型注解

### 低优先级（长期优化）
9. 📝 **接口抽象**：定义 Agent 接口
10. 📝 **统一异常处理**：创建异常体系
11. 📝 **配置验证**：添加配置验证器

---

## 🔧 重构示例

### 示例 1：工具注册器

```python
# backend/app/services/tools/registry.py
from typing import Dict, Callable, List, Optional
from langchain.tools import Tool
from loguru import logger

class ToolRegistry:
    """工具注册器 - 统一管理所有工具"""
    
    _tools: Dict[str, Callable] = {}
    _default_tools: List[str] = []
    
    @classmethod
    def register(
        cls,
        name: str,
        tool_factory: Callable,
        default: bool = True
    ):
        """注册工具工厂
        
        Args:
            name: 工具名称
            tool_factory: 工具工厂函数，接受 config 参数
            default: 是否默认启用
        """
        cls._tools[name] = tool_factory
        if default:
            cls._default_tools.append(name)
        logger.info(f"Registered tool: {name}")
    
    @classmethod
    def create_tools(
        cls,
        config: Optional[Dict] = None
    ) -> List[Tool]:
        """根据配置创建工具列表
        
        Args:
            config: 工具配置，例如 {"search_provider": "tavily"}
        
        Returns:
            工具列表
        """
        config = config or {}
        tools = []
        
        # 获取要启用的工具列表
        enabled_tools = config.get("enabled_tools", cls._default_tools)
        
        for name in enabled_tools:
            if name not in cls._tools:
                logger.warning(f"Tool {name} not registered")
                continue
            
            try:
                tool = cls._tools[name](config)
                if tool:
                    tools.append(tool)
                    logger.debug(f"Created tool: {name}")
            except Exception as e:
                logger.error(f"Failed to create tool {name}: {e}")
        
        logger.info(f"Created {len(tools)} tools")
        return tools
    
    @classmethod
    def list_tools(cls) -> List[str]:
        """列出所有已注册的工具"""
        return list(cls._tools.keys())
```

### 示例 2：提示词构建器

```python
# backend/app/services/agent/prompt_builder.py
from typing import Optional, List, Dict
from pathlib import Path
from jinja2 import Template
from loguru import logger

class PromptBuilder:
    """提示词构建器 - 统一管理提示词模板"""
    
    def __init__(self, template_dir: Optional[Path] = None):
        self.template_dir = template_dir or Path(__file__).parent.parent.parent / "agent" / "prompts"
        self._templates = {}
    
    def _load_template(self, template_name: str) -> Template:
        """加载模板文件"""
        if template_name not in self._templates:
            template_path = self.template_dir / template_name
            if not template_path.exists():
                raise FileNotFoundError(f"Template not found: {template_path}")
            with open(template_path, 'r', encoding='utf-8') as f:
                self._templates[template_name] = Template(f.read())
        return self._templates[template_name]
    
    def build_react_prompt(
        self,
        tools: List,
        knowledge_prompts: str = "",
        history_context: str = "",
        tool_names: str = ""
    ) -> str:
        """构建 ReAct Agent 提示词"""
        template = self._load_template("react_agent.txt")
        return template.render(
            tools=tools,
            knowledge_prompts=knowledge_prompts,
            history_context=history_context,
            tool_names=tool_names
        )
    
    def build_openai_functions_prompt(
        self,
        knowledge_prompts: str = ""
    ) -> str:
        """构建 OpenAI Functions Agent 提示词"""
        template = self._load_template("openai_functions_agent.txt")
        return template.render(knowledge_prompts=knowledge_prompts)
```

### 示例 3：知识卡片检索器

```python
# backend/app/services/agent/knowledge_card_retriever.py
from typing import Optional, Dict, List
from app.services.knowledge_service import knowledge_service
from loguru import logger

class KnowledgeCardRetriever:
    """知识卡片检索器 - 统一处理知识卡片检索逻辑"""
    
    @staticmethod
    def retrieve_prompts(
        prompt_card_id: Optional[str] = None,
        collection: Optional[str] = None,
        message: Optional[str] = None,
        db_session = None,
        top_k: int = 3
    ) -> str:
        """检索知识卡片提示词
        
        Returns:
            格式化的提示词字符串
        """
        knowledge_prompts = ""
        
        if prompt_card_id and db_session:
            # 直接使用指定卡片
            try:
                card = knowledge_service.get_prompt_card_by_id(db_session, prompt_card_id)
                if card:
                    knowledge_prompts = "\n\n📋 知识卡片提示（你应遵循这些指导原则）:\n"
                    knowledge_prompts += f"\n[{card.get('title', '')}]\n{card.get('content', '')}\n"
                    logger.info(f"Using specified prompt card: {card.get('title', '')}")
                else:
                    logger.warning(f"Prompt card with id {prompt_card_id} not found")
            except Exception as e:
                logger.warning(f"Failed to get prompt card by id: {e}")
        
        elif collection and message:
            # 根据对话内容检索相关卡片
            try:
                search_results = knowledge_service.search("prompts", message, top_k=top_k)
                if search_results:
                    knowledge_prompts = "\n\n📋 知识卡片提示（你应遵循这些指导原则）:\n"
                    for idx, result in enumerate(search_results, 1):
                        title = result.get('metadata', {}).get('title', '')
                        content = result.get('content', '')
                        knowledge_prompts += f"\n{idx}. [{title}]\n{content}\n"
            except Exception as e:
                logger.warning(f"Failed to search knowledge prompts: {e}")
        
        return knowledge_prompts
```

---

## 📊 重构收益

### 可维护性
- ✅ 代码模块化，职责清晰
- ✅ 单个文件行数控制在 300 行以内
- ✅ 易于定位和修复问题

### 可扩展性
- ✅ 新增工具只需注册，无需修改核心代码
- ✅ 新增 Agent 类型只需实现接口
- ✅ 提示词模板可独立维护

### 可测试性
- ✅ 各模块可独立测试
- ✅ 接口抽象便于 Mock
- ✅ 工具注册器便于测试工具组合

### 可复用性
- ✅ 提示词构建器可在多个场景复用
- ✅ 工具注册器可用于不同 Agent
- ✅ 内存管理器可独立使用

---

## 🚀 实施建议

1. **分阶段重构**：不要一次性重构所有代码，按优先级逐步进行
2. **保持向后兼容**：重构时保持 API 接口不变
3. **充分测试**：每个重构步骤都要有对应的测试
4. **文档更新**：及时更新相关文档

---

## 📝 总结

通过以上重构，项目将具备：
- ✅ 清晰的模块划分
- ✅ 统一的工具管理机制
- ✅ 可配置的提示词系统
- ✅ 完善的类型注解
- ✅ 统一的错误处理
- ✅ 良好的可测试性

这些改进将显著提升代码的可维护性、可扩展性和可复用性。

