# 后端 API 需求文档

**目的**: 明确前端重构所需的后端 API 契约和调整项

## 当前后端 API 状态

### `/api/chat/stream` - 流式聊天接口

**现有实现**: ✅ 已实现  
**位置**: `backend/app/api/routes/chat.py`

#### 当前响应格式

后端目前返回 Server-Sent Events (SSE) 格式的流式数据:

```
data: {"type": "content", "data": {"content": "..."}}
data: {"type": "thinking", "data": {"thinking": "..."}}
data: {"type": "tool_call", "data": {"tool_name": "...", "tool_input": {...}}}
data: {"type": "done", "data": {}}
```

#### 前端所需格式 (contracts/stream-api.md)

```typescript
interface SSEChunk {
  type: 'content' | 'thinking' | 'tool_call' | 'tool_result' | 'done';
  data: {
    content?: string;
    thinking?: string;
    tool_name?: string;
    tool_input?: any;
    tool_output?: any;
    metadata?: Record<string, any>;
  };
  timestamp: string;
}
```

## 需要的后端调整

### ⚠️ REQUIRED - 必须修改

| 调整项 | 优先级 | 说明 | 影响 |
|--------|--------|------|------|
| 添加 `timestamp` 字段 | **HIGH** | 每个流式块需要包含 ISO 8601 格式的时间戳 | 前端无法正确排序和去重流式消息 |
| 添加 `tool_result` 类型 | **HIGH** | 需要单独的 chunk 类型来返回工具调用结果 | 前端无法区分工具输入和输出 |

### ✅ OPTIONAL - 可选优化

| 调整项 | 优先级 | 说明 | 影响 |
|--------|--------|------|------|
| 添加 `metadata` 字段 | MEDIUM | 用于传递额外的上下文信息(如 token 消耗、模型信息) | 前端无法展示详细调试信息 |
| 流式错误处理 | MEDIUM | 当发生错误时,发送 `{"type": "error", "data": {"error": "..."}}` | 前端需要手动处理 HTTP 错误码 |

## 后端修改建议

### 修改文件: `backend/app/api/routes/chat.py`

在流式响应生成器中添加 timestamp:

```python
from datetime import datetime

async def stream_chat_response(...):
    # ... existing code ...
    
    # 添加 timestamp
    timestamp = datetime.now().isoformat()
    
    # 内容块
    yield f"data: {json.dumps({
        'type': 'content',
        'data': {'content': chunk},
        'timestamp': timestamp  # NEW
    })}\n\n"
    
    # 思考过程块
    yield f"data: {json.dumps({
        'type': 'thinking',
        'data': {'thinking': thought},
        'timestamp': datetime.now().isoformat()  # NEW
    })}\n\n"
    
    # 工具调用块
    yield f"data: {json.dumps({
        'type': 'tool_call',
        'data': {
            'tool_name': tool.name,
            'tool_input': tool.args
        },
        'timestamp': datetime.now().isoformat()  # NEW
    })}\n\n"
    
    # NEW: 工具结果块
    yield f"data: {json.dumps({
        'type': 'tool_result',
        'data': {
            'tool_name': tool.name,
            'tool_output': result
        },
        'timestamp': datetime.now().isoformat()
    })}\n\n"
```

## 前后端契约验证步骤

### 前端验证清单

- [ ] **Step 1**: 使用 `zod` 或 `io-ts` 定义 `SSEChunk` schema
- [ ] **Step 2**: 在 `useStreamChat.ts` 中验证后端响应格式
- [ ] **Step 3**: 添加类型不匹配的错误处理和日志
- [ ] **Step 4**: 在开发环境启用严格类型检查

### 后端验证清单

- [ ] **Step 1**: 更新 `/api/chat/stream` 添加 `timestamp` 字段
- [ ] **Step 2**: 添加 `tool_result` 类型的流式块
- [ ] **Step 3**: 更新 OpenAPI 文档 (`/docs`)
- [ ] **Step 4**: 与前端团队进行集成测试

## 测试计划

### 场景 1: 简单对话
**请求**: "你好"  
**预期流式输出**:
```
data: {"type":"content","data":{"content":"你"},"timestamp":"2026-01-25T10:00:00.000Z"}
data: {"type":"content","data":{"content":"好"},"timestamp":"2026-01-25T10:00:00.050Z"}
data: {"type":"done","data":{},"timestamp":"2026-01-25T10:00:00.100Z"}
```

### 场景 2: 使用工具的对话
**请求**: "武汉明天天气如何?"  
**预期流式输出**:
```
data: {"type":"thinking","data":{"thinking":"我需要查询天气..."},"timestamp":"..."}
data: {"type":"tool_call","data":{"tool_name":"web_search","tool_input":{"query":"武汉 明天 天气"}},"timestamp":"..."}
data: {"type":"tool_result","data":{"tool_name":"web_search","tool_output":{"result":"..."}},"timestamp":"..."}
data: {"type":"content","data":{"content":"根据查询..."},"timestamp":"..."}
data: {"type":"done","data":{},"timestamp":"..."}
```

## 向后兼容性

**Breaking Change**: ❌ 否  
**说明**: 添加字段不会破坏现有客户端,旧客户端可以忽略新字段

## 责任分工

| 任务 | 负责方 | 截止日期 |
|------|--------|----------|
| 后端 API 调整 | 后端团队 | Phase 1 Setup 完成前 |
| 前端类型定义更新 | 前端团队 | T009-T010 (Phase 2) |
| 集成测试 | 前后端联合 | Phase 3 US1 开始时 |

## 相关文档

- 前端流式 API 契约: [stream-api.md](./stream-api.md)
- 前端聊天 API 契约: [chat-api.md](./chat-api.md)
- 后端 LangChain Agent: `backend/app/services/agent_service.py`

---

**创建日期**: 2026-01-25  
**状态**: ✅ 待后端团队确认  
**优先级**: **CRITICAL** - 必须在 Phase 3 US1 开始前确认
