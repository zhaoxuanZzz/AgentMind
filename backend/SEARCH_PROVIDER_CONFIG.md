# 搜索提供商配置说明

## 概述

联网搜索工具的选择已从**传参方式**改为通过**环境变量配置**。

## 配置方法

### 环境变量配置

在 `.env` 文件中设置 `SEARCH_PROVIDER` 环境变量：

```bash
# 搜索提供商选择: tavily 或 baidu
SEARCH_PROVIDER=tavily

# Tavily搜索工具配置
TAVILY_API_KEY=your-tavily-api-key

# 百度搜索工具配置
BAIDU_API_KEY=your-baidu-api-key
BAIDU_ENABLED=true
```

### 可选值

- `tavily` - 使用 Tavily 搜索引擎（默认）
- `baidu` - 使用百度搜索引擎

## 使用方法

### 后端代码

创建搜索工具时，不再需要传递 `search_provider` 参数：

```python
from app.services.tools.web_search_tool import create_web_search_tool

# 自动从环境变量读取配置
tool = create_web_search_tool()
```

创建 Agent 时，也不再需要传递 `search_provider`：

```python
from app.services.agent_service import AgentService
from app.api.schemas import AgentConfig

agent_service = AgentService()

# AgentConfig 中已移除 search_provider 字段
config = AgentConfig(
    role_preset_id="software_engineer"
)

agent = agent_service.create_agent(config=config)
```

### API 请求

前端调用 API 时，也不再需要传递 `search_provider` 字段：

```json
{
  "message": "今天天气怎么样？",
  "llm_config": {
    "provider": "dashscope",
    "model": "qwen-turbo"
  }
}
```

## 切换搜索提供商

要切换搜索提供商，只需修改 `.env` 文件中的 `SEARCH_PROVIDER` 变量，然后重启后端服务即可。

## 已修改的文件

1. ✅ `backend/app/core/config.py` - 添加 `SEARCH_PROVIDER` 环境变量
2. ✅ `backend/app/api/schemas.py` - 从 `AgentConfig`、`ChatRequest`、`ChatRequestV2` 中移除 `search_provider` 字段
3. ✅ `backend/app/services/agent_service.py` - 移除所有 `search_provider` 参数
4. ✅ `backend/app/services/tools/web_search_tool.py` - 从环境变量读取配置
5. ✅ `backend/app/api/routes/chat.py` - 移除传递 `search_provider` 的代码
6. ✅ `env.template` - 添加 `SEARCH_PROVIDER` 配置项示例
7. ✅ `backend/test_web_search.py` - 更新测试脚本
8. ✅ `backend/test_agent_search.py` - 更新测试脚本
9. ✅ `backend/test_tool_stream.py` - 移除 `search_provider` 字段

## 优势

1. **简化配置** - 统一在环境变量中管理，无需在每次调用时传递参数
2. **易于部署** - 在不同环境（开发、测试、生产）中可以方便地使用不同的搜索提供商
3. **减少代码复杂度** - 移除了大量的参数传递代码
4. **符合12因子应用原则** - 配置与代码分离

## 向后兼容性

⚠️ **注意**: 此更改**不向后兼容**，所有传递 `search_provider` 参数的代码都需要移除该参数。

如果升级后遇到问题，请：
1. 检查 `.env` 文件是否配置了 `SEARCH_PROVIDER`
2. 移除所有 API 请求中的 `search_provider` 字段
3. 重启后端服务
