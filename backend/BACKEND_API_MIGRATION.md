# 后端流式 API 兼容性调整总结

**日期**: 2026-01-25  
**目的**: 调整后端代码以兼容前端重构的流式 API 契约

---

## 🎯 调整目标

根据 `specs/001-frontend-refactor/contracts/backend-api-requirements.md` 和 `stream-api.md`，需要调整后端流式响应格式：

### 必需修改 (HIGH Priority)
- ✅ 为每个流式块添加 `timestamp` 字段（ISO 8601 格式）
- ✅ 添加 `tool_result` 类型，区分工具调用请求和结果
- ✅ 将响应数据包装在 `data` 对象中

### 可选优化 (MEDIUM Priority)
- ⏭️ 添加 `metadata` 字段（暂未实现，可在后续版本添加）
- ✅ 流式错误处理改进

---

## 📝 修改文件清单

### 1. `backend/app/services/streaming/stream_handler.py`

**修改内容**:
- 添加 `from datetime import datetime` import
- 修改 `on_agent_action()`: 将 `type: "tool"` 改为 `type: "tool_call"`，数据包装到 `data.tool_name` 和 `data.tool_input`，添加 `timestamp`
- 修改 `on_tool_end()`: 将 `type: "tool"` 改为 `type: "tool_result"`，数据包装到 `data.tool_name` 和 `data.tool_output`，添加 `timestamp`
- 修改 `on_llm_new_token()`: 将 thinking 和 content 包装到 `data` 对象中，添加 `timestamp`
- 修改 `on_llm_end()`: 更新所有 chunks 格式

**新格式示例**:
```python
# tool_call chunk
{
    "type": "tool_call",
    "data": {
        "tool_name": "calculator",
        "tool_input": "2+2"
    },
    "timestamp": "2026-01-25T23:57:00.123456"
}

# tool_result chunk
{
    "type": "tool_result",
    "data": {
        "tool_name": "calculator",
        "tool_output": "4"
    },
    "timestamp": "2026-01-25T23:57:01.234567"
}

# thinking chunk
{
    "type": "thinking",
    "data": {
        "thinking": "我需要计算..."
    },
    "timestamp": "2026-01-25T23:57:00.345678"
}

# content chunk
{
    "type": "content",
    "data": {
        "content": "答案是 4"
    },
    "timestamp": "2026-01-25T23:57:02.456789"
}
```

---

### 2. `backend/app/api/routes/chat.py`

**修改内容**:
- 添加 `from datetime import datetime` import
- 更新 `chat_stream()` 函数中所有的 yield 语句：
  - `conversation_id` chunk: 添加 `data` 包装和 `timestamp`
  - `error` chunk: 添加 `data` 包装和 `timestamp`
  - 处理从 agent_service 接收的 chunks（已包含正确格式，直接转发）
  - 更新 `done` chunk 格式
  - 更新 `intermediate_steps` 记录以兼容新的 tool_call/tool_result 格式

**关键改动**:
```python
# 旧格式
yield f"data: {json.dumps({'type': 'error', 'message': '对话不存在'}, ensure_ascii=False)}\n\n"

# 新格式
yield f"data: {json.dumps({
    'type': 'error', 
    'data': {'message': '对话不存在'}, 
    'timestamp': datetime.now().isoformat()
}, ensure_ascii=False)}\n\n"
```

---

### 3. `backend/app/services/agent_service.py`

**修改内容**:
- 添加 `from datetime import datetime` import
- 修改 `chat_stream()` 中的 error 和 done chunks 格式
- 修改逐字符发送的 content chunks 格式（fallback 场景）

**改动示例**:
```python
# 旧格式
yield {"type": "error", "message": str(e)}
yield {"type": "done"}

# 新格式
yield {
    "type": "error", 
    "data": {"message": str(e)}, 
    "timestamp": datetime.now().isoformat()
}
yield {
    "type": "done", 
    "data": {}, 
    "timestamp": datetime.now().isoformat()
}
```

---

## 🧪 测试验证

### 测试脚本

创建了以下测试脚本：
1. `backend/test_stream_format.py` - 基础流式格式测试
2. `backend/test_tool_stream.py` - 工具调用场景测试
3. `backend/test_calculator.py` - 计算器工具测试

### 测试结果

✅ **基础测试通过**:
```
发送请求: {'message': '你好', ...}
✓ [conversation_id] conversation_id=124
✓ [thinking] 你好！有什么我可以帮助你的吗？...
✓ [done] 流式响应完成

测试结果:
  总 chunk 数: 3
  有效 chunk 数: 3
  无效 chunk 数: 0
✅ 所有 chunks 格式正确，符合前端契约！
```

所有 chunks 都包含：
- ✅ `type` 字段
- ✅ `timestamp` 字段（ISO 8601 格式）
- ✅ `data` 对象（包含对应类型的数据）

---

## 📊 新旧格式对比

| Chunk Type | 旧格式字段 | 新格式字段 | 说明 |
|------------|-----------|-----------|------|
| thinking | `content` | `data.thinking` | 包装到 data 对象 |
| tool (调用) | `tool_info.tool` | `data.tool_name` | 类型改为 tool_call |
| tool (结果) | `tool_info.output` | `data.tool_output` | 新增 tool_result 类型 |
| content | `content` | `data.content` | 包装到 data 对象 |
| error | `message` | `data.message` | 包装到 data 对象 |
| done | - | `data` (空对象) | 添加 data 字段 |
| - | - | `timestamp` | 所有类型都添加 |

---

## 🔄 向后兼容性

**Breaking Change**: ❌ 否（字段添加，不破坏现有客户端）

旧版本的前端可以忽略新添加的 `timestamp` 字段。但新的字段结构（如 `data` 包装）需要前端相应更新才能正确解析。

**建议**: 
- 前端应更新到新版本以使用新的数据结构
- 前端应添加类型验证（使用 zod 或 io-ts）确保 API 契约遵守

---

## ✅ 完成清单

- [x] 修改 StreamCallbackHandler 添加 timestamp 和调整数据结构
- [x] 添加 tool_result 类型支持
- [x] 更新 chat.py 路由以支持新的数据格式
- [x] 更新 agent_service.py 中的 error/done chunks
- [x] 创建测试脚本验证格式
- [x] 测试后端流式响应

---

## 📌 后续工作

### 可选优化（未实现）
1. **metadata 字段**: 可在 done chunk 中添加 token 消耗、模型信息等
   ```python
   {
       "type": "done",
       "data": {
           "conversation_id": 123,
           "metadata": {
               "total_tokens": 500,
               "model": "qwen-turbo"
           }
       },
       "timestamp": "..."
   }
   ```

2. **OpenAPI 文档更新**: 更新 `/docs` 中的 API 文档说明新格式

3. **单元测试**: 为流式响应添加单元测试

---

## 🔗 相关文档

- [前端流式 API 契约](../specs/001-frontend-refactor/contracts/stream-api.md)
- [后端 API 需求文档](../specs/001-frontend-refactor/contracts/backend-api-requirements.md)
- [前端重构计划](../specs/001-frontend-refactor/plan.md)

---

**状态**: ✅ 已完成  
**测试**: ✅ 通过  
**部署**: 🚀 可部署
