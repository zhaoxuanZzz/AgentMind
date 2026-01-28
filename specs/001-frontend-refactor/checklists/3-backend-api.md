# 后端 API 集成检查清单

**检查类别**: Backend API Integration  
**优先级**: CRITICAL  
**门控**: 必须在 Phase 3 US1 开始前 100% 通过

---

## 1. 流式 API 契约验证

### 1.1 后端响应格式符合性

- [ ] **CRITICAL** 后端必须返回符合 `contracts/stream-api.md` 的数据格式
  - **当前状态**: ✅ PASS - 后端已实现
  - **验证文件**: `backend/app/api/routes/chat.py`, `backend/app/services/streaming/stream_handler.py`
  - **验证项**:
    - ✅ `timestamp` 字段存在于所有 chunk
    - ✅ `tool_call` 和 `tool_result` 分离
    - ✅ `type` 字段使用正确的枚举值

- [ ] **CRITICAL** 前端类型定义必须匹配后端实际返回格式
  - **当前状态**: ❌ FAIL - `types/stream.ts` 与后端不匹配
  - **差异清单**:
    | 字段 | 后端 | 前端类型定义 | 状态 |
    |------|------|--------------|------|
    | `timestamp` | ✅ 所有 chunk 包含 | ❌ 类型定义中缺失 | FAIL |
    | `tool_result` 类型 | ✅ 独立类型 | ❌ 合并在 `tool` 类型中 | FAIL |
    | `data` 字段嵌套 | ✅ `{type, data: {...}, timestamp}` | ⚠️ 部分扁平化 | WARN |

### 1.2 XRequest 集成测试

- [ ] **CRITICAL** `useStreamChat` 正确处理后端所有 chunk 类型
  - **测试场景**:
    1. 简单对话（仅 `content` 和 `done`）
    2. 深度推理对话（包含 `thinking`）
    3. 工具调用对话（包含 `tool_call` 和 `tool_result`）
    4. 错误场景（`error` chunk）

- [ ] **HIGH** `XRequest` 回调正确解析 SSE 数据
  - **验证位置**: `hooks/useStreamChat.ts` 第 88-100 行
  - **验证项**:
    - `onUpdate` 接收的 chunk 是否已 JSON 解析
    - 是否正确累积流式数据
    - 是否触发 `onSuccess` 和 `onError`

---

## 2. API 请求参数验证

### 2.1 ChatRequest 完整性

- [ ] **CRITICAL** 所有可选参数正确传递给后端
  - **参数清单**:
    | 参数 | 前端发送 | 后端接收 | 状态 |
    |------|----------|----------|------|
    | `message` | ✅ | ✅ | PASS |
    | `conversation_id` | ✅ | ✅ | PASS |
    | `use_knowledge_base` | ⚠️ 需验证 | ✅ | WARN |
    | `llm_config.provider` | ⚠️ 需验证 | ✅ | WARN |
    | `llm_config.model` | ⚠️ 需验证 | ✅ | WARN |
    | `search_provider` | ⚠️ 需验证 | ✅ | WARN |
    | `role_preset_id` | ⚠️ 需验证 | ✅ | WARN |
    | `deep_reasoning` | ⚠️ 需验证 | ✅ | WARN |

- [ ] **HIGH** `buildChatStreamRequest` 正确构建请求体
  - **验证位置**: `api/streamAPI.ts`
  - **验证方法**: 
    1. 在浏览器 Network 面板查看实际请求
    2. 对比 `backend/app/api/schemas.py` 中的 `ChatRequest` 定义

### 2.2 知识库选择集成

- [ ] **CRITICAL** 知识库选择器正确传递 `use_knowledge_base` 参数
  - **当前状态**: ❌ FAIL - 知识库选择器组件缺失
  - **规格要求**: `tasks.md` T035-1
  - **验收标准**:
    1. 用户可以选择知识库
    2. 选择后发送消息时，`use_knowledge_base` 参数正确传递
    3. API 请求包含正确的知识库名称

- [ ] **HIGH** 角色预设选择集成
  - **当前状态**: ⚠️ 需验证
  - **规格要求**: `spec.md` 第 46 行（移至知识库页面）
  - **验证**: 知识库页面是否有角色预设管理功能

---

## 3. 消息持久化

### 3.1 消息保存和加载

- [ ] **HIGH** 用户消息在发送前乐观更新到 UI
  - **当前状态**: ✅ PASS - `ChatPage/index.tsx` 第 70-77 行

- [ ] **CRITICAL** 流式完成后刷新消息列表
  - **当前状态**: ✅ PASS - `ChatPage/index.tsx` 第 53-57 行 `onComplete` 回调
  - **验证**: 
    1. 发送消息后等待流式完成
    2. 刷新页面，检查消息是否持久化

- [ ] **HIGH** 后端保存完整的消息元数据
  - **验证文件**: `backend/app/api/routes/chat.py` 第 163-172 行
  - **验证项**:
    - ✅ `content` 保存最终答案
    - ✅ `meta_info.intermediate_steps` 保存工具调用
    - ✅ `meta_info.thinking` 保存推理过程

### 3.2 历史消息加载

- [ ] **HIGH** 切换会话时正确加载历史消息
  - **验证位置**: `hooks/useConversationMessages.ts`
  - **测试步骤**:
    1. 创建多个会话并发送消息
    2. 切换会话
    3. 验证历史消息是否正确显示（包括 thinking 和 tool 信息）

- [ ] **MEDIUM** 历史消息显示工具调用和思考过程
  - **当前状态**: ⚠️ 需验证 `meta_info` 字段是否正确映射到 `Message` 类型
  - **验证**: 检查 `types/api.ts` 中的 `Message` 接口

---

## 4. 错误处理

### 4.1 网络错误处理

- [ ] **CRITICAL** 流式请求失败有明确的错误提示
  - **验证位置**: `hooks/useStreamChat.ts` 第 98-108 行
  - **测试场景**:
    1. 停止后端服务，发送消息
    2. 验证是否显示错误消息
    3. 验证 `error` 状态是否正确更新

- [ ] **HIGH** 错误信息对用户友好
  - **示例**: "网络连接失败，请检查您的网络" 而非 "Error: fetch failed"

### 4.2 后端错误处理

- [ ] **CRITICAL** 后端返回 `error` chunk 时前端正确处理
  - **验证文件**: `backend/app/api/routes/chat.py` 第 177-179 行
  - **测试场景**:
    1. 发送触发后端错误的消息（如 LLM API 密钥无效）
    2. 验证前端是否显示错误消息
    3. 验证流式状态是否变为 `error`

- [ ] **HIGH** 部分流式失败有重试机制
  - **当前状态**: ❌ FAIL - `useStreamChat` 无重试逻辑
  - **优先级**: MEDIUM（可延后到 Phase 7）

---

## 5. 性能与优化

### 5.1 流式响应延迟

- [ ] **CRITICAL** 首字节延迟 < 500ms
  - **规格要求**: `spec.md` 第 175 行（< 100ms，但 500ms 为可接受阈值）
  - **测试方法**: Chrome DevTools Network 面板查看 TTFB (Time To First Byte)

- [ ] **HIGH** 流式数据累积无内存泄漏
  - **测试方法**: 发送 10+ 条长消息，观察 Chrome DevTools Memory 面板

### 5.2 长连接管理

- [ ] **MEDIUM** XRequest 支持连接超时处理
  - **当前状态**: ⚠️ 需验证 `@ant-design/x-sdk` 是否有超时配置
  - **验证**: 查看 XRequest 文档或源码

- [ ] **MEDIUM** 支持取消正在进行的流式请求
  - **当前状态**: ❌ FAIL - `useStreamChat.ts` 第 127 行注释表明无取消 API
  - **优先级**: MEDIUM（可延后）

---

## 6. 集成测试场景

### 6.1 端到端测试用例

- [ ] **TEST-1**: 简单对话
  - **步骤**:
    1. 发送消息: "你好"
    2. 验证收到 `content` chunk
    3. 验证收到 `done` chunk
    4. 验证消息保存到数据库

- [ ] **TEST-2**: 深度推理对话
  - **步骤**:
    1. 启用深度推理模式
    2. 发送消息: "解释量子纠缠"
    3. 验证收到 `thinking` chunk
    4. 验证思考过程在 UI 中显示

- [ ] **TEST-3**: 工具调用对话
  - **步骤**:
    1. 发送消息: "武汉明天天气如何?"
    2. 验证收到 `tool_call` chunk
    3. 验证收到 `tool_result` chunk
    4. 验证工具调用在 UI 中展示

- [ ] **TEST-4**: 知识库增强对话
  - **步骤**:
    1. 选择知识库
    2. 发送相关问题
    3. 验证 `use_knowledge_base` 参数传递
    4. 验证响应包含知识库内容

- [ ] **TEST-5**: 错误恢复
  - **步骤**:
    1. 关闭后端服务
    2. 发送消息
    3. 验证错误提示
    4. 重启后端
    5. 重新发送，验证恢复正常

---

## 验证步骤

### 自动化验证

1. **类型契约测试**:
   ```typescript
   // 在 api/streamAPI.test.ts 中
   import { SSEChunkSchema } from './streamAPI'
   
   test('后端响应符合 schema', () => {
     const backendChunk = {
       type: 'content',
       data: { content: 'Hello' },
       timestamp: '2026-01-26T00:00:00Z'
     }
     expect(SSEChunkSchema.safeParse(backendChunk).success).toBe(true)
   })
   ```

2. **集成测试**:
   ```bash
   # 使用 Playwright 或 Cypress 进行端到端测试
   npm run test:e2e
   ```

### 手动验证

1. **Network 面板检查**:
   - 打开 Chrome DevTools Network 面板
   - 筛选 `stream` 请求
   - 验证请求体和响应格式

2. **实际对话测试**:
   - 按照 TEST-1 到 TEST-5 逐个执行
   - 记录失败场景和错误日志

---

## 完成标准

**门控条件** (必须 100% 通过):
- [ ] 所有 CRITICAL 项已修复
- [ ] 所有 TEST-1 到 TEST-5 通过
- [ ] 前端类型定义与后端完全匹配
- [ ] 无内存泄漏或性能问题

**质量指标**:
- 首字节延迟: < 500ms
- 流式更新延迟: < 100ms
- 错误率: < 1%（100 次请求中失败 < 1 次）
- 消息持久化成功率: 100%

---

**最后更新**: 2026-01-26  
**状态**: 🔴 BLOCKED - 需修复类型定义不匹配问题
