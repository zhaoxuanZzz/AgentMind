# 前后端集成测试指南

## 测试新的流式 API

### 1. 启动后端服务

```bash
cd backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 使用 curl 测试

```bash
# 简单对话测试
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "message": "你好",
    "llm_config": {
      "provider": "dashscope",
      "model": "qwen-turbo"
    }
  }' \
  --no-buffer
```

**预期输出**:
```
data: {"type":"conversation_id","data":{"conversation_id":1},"timestamp":"2026-01-25T23:57:00.123456"}
data: {"type":"thinking","data":{"thinking":"你好！"},"timestamp":"2026-01-25T23:57:00.234567"}
data: {"type":"content","data":{"content":"有什么可以帮助你的吗？"},"timestamp":"2026-01-25T23:57:01.345678"}
data: {"type":"done","data":{"conversation_id":1},"timestamp":"2026-01-25T23:57:02.456789"}
```

### 3. 使用 Python 测试

```python
import requests
import json

url = "http://localhost:8000/api/chat/stream"
payload = {
    "message": "你好",
    "llm_config": {
        "provider": "dashscope",
        "model": "qwen-turbo"
    }
}

response = requests.post(url, json=payload, stream=True)

for line in response.iter_lines():
    if line:
        line_str = line.decode('utf-8')
        if line_str.startswith('data: '):
            chunk = json.loads(line_str[6:])
            print(f"Type: {chunk['type']}")
            print(f"Data: {chunk['data']}")
            print(f"Timestamp: {chunk['timestamp']}")
            print("---")
```

### 4. 使用前端 TypeScript

```typescript
import { SSEChunk } from './contracts/stream-api'

async function testStreamAPI() {
  const response = await fetch('http://localhost:8000/api/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message: '你好',
      llm_config: { provider: 'dashscope', model: 'qwen-turbo' }
    })
  })

  const reader = response.body?.getReader()
  const decoder = new TextDecoder()

  while (true) {
    const { done, value } = await reader!.read()
    if (done) break

    const text = decoder.decode(value)
    const lines = text.split('\n')

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const chunk: SSEChunk = JSON.parse(line.slice(6))
        
        // TypeScript 会自动根据 type 字段推断类型
        switch (chunk.type) {
          case 'thinking':
            console.log('Thinking:', chunk.data.thinking)
            break
          case 'tool_call':
            console.log('Tool:', chunk.data.tool_name, chunk.data.tool_input)
            break
          case 'tool_result':
            console.log('Result:', chunk.data.tool_name, chunk.data.tool_output)
            break
          case 'content':
            console.log('Content:', chunk.data.content)
            break
          case 'done':
            console.log('Done!')
            break
        }
      }
    }
  }
}
```

## 验证清单

在前端集成时，请验证以下内容：

### 必需字段验证
- [ ] 所有 chunk 都有 `type` 字段
- [ ] 所有 chunk 都有 `timestamp` 字段（ISO 8601 格式）
- [ ] 所有 chunk 都有 `data` 字段（done 可以是空对象）

### 数据结构验证
- [ ] `conversation_id` chunk: `data.conversation_id` 存在
- [ ] `thinking` chunk: `data.thinking` 存在
- [ ] `tool_call` chunk: `data.tool_name` 和 `data.tool_input` 存在
- [ ] `tool_result` chunk: `data.tool_name` 和 `data.tool_output` 存在
- [ ] `content` chunk: `data.content` 存在
- [ ] `error` chunk: `data.message` 存在

### 工具调用配对验证
- [ ] 每个 `tool_call` 都有对应的 `tool_result`
- [ ] `tool_result` 的 `tool_name` 与 `tool_call` 匹配

### 类型安全验证
- [ ] 使用 zod 或 io-ts 验证 chunk 格式
- [ ] TypeScript 类型推断正常工作
- [ ] 错误处理能捕获格式不匹配的情况

## 故障排查

### 问题 1: 缺少 timestamp 字段
**症状**: 前端解析失败，提示缺少 timestamp  
**解决**: 确保后端已更新到最新版本，检查 stream_handler.py 是否正确添加了 datetime.now().isoformat()

### 问题 2: tool_call 和 tool_result 不配对
**症状**: 显示工具调用但没有结果  
**解决**: 检查 on_tool_end() 是否正确发送 tool_result chunk

### 问题 3: 数据在 content 而不是 data.content
**症状**: TypeScript 类型错误  
**解决**: 确保使用最新版本的后端代码，所有数据都应该在 data 对象中

## 性能测试

推荐测试场景：

1. **简单对话** (预期 < 2s 首次响应)
   - 消息: "你好"
   - 预期: 1-3 个 chunks

2. **复杂推理** (预期 < 5s 首次响应)
   - 消息: "解释量子计算的工作原理"
   - 预期: 多个 thinking chunks

3. **工具调用** (预期 < 10s 完成)
   - 消息: "北京今天天气怎么样？"
   - 预期: tool_call + tool_result + content

## 监控指标

建议监控的指标：

- **首次响应时间** (TTFB): conversation_id chunk 到达时间
- **首次内容时间**: 第一个 content chunk 到达时间
- **完成时间**: done chunk 到达时间
- **chunk 数量**: 每次请求的 chunk 总数
- **工具调用频率**: tool_call chunk 比例
- **错误率**: error chunk 比例

---

**最后更新**: 2026-01-25  
**兼容版本**: Backend >= v2.0.0, Frontend >= v2.0.0
