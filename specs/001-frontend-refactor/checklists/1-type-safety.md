# 类型安全检查清单

**检查类别**: Type Safety & Data Contracts  
**优先级**: CRITICAL  
**门控**: 必须在 Phase 3 US1 开始前 100% 通过

---

## 1. 流式 API 类型定义

### 1.1 Discriminated Union 实现

- [ ] **CRITICAL** `types/stream.ts` 必须使用 Discriminated Union 替代 loose interface
  - **当前状态**: ❌ FAIL - 使用的是 `SSEChunk` loose interface
  - **规格要求**: `contracts/stream-api.md` 定义了 7 种具体类型（SSEConversationChunk, SSEThinkingChunk等）
  - **修复**: 
    ```typescript
    // ❌ 错误（当前）
    export interface SSEChunk {
      type: StreamChunkType
      content?: string
      conversation_id?: number
      ...
    }
    
    // ✅ 正确（规格）
    export type SSEChunk = 
      | SSEConversationChunk
      | SSEThinkingChunk
      | SSEToolCallChunk
      | SSEToolResultChunk
      | SSEContentChunk
      | SSEDoneChunk
      | SSEErrorChunk
    ```
  - **影响**: 无法进行编译时类型窄化，容易出现运行时类型错误

- [ ] **CRITICAL** 每个 chunk 类型必须有 `timestamp: string` 字段
  - **当前状态**: ⚠️ 后端已提供，前端类型定义缺失
  - **规格要求**: `contracts/stream-api.md` 第 19 行 `SSEChunkBase` 定义
  - **验证**: 检查 `types/stream.ts` 是否所有类型都继承 `SSEChunkBase`

- [ ] **HIGH** `tool_call` 和 `tool_result` 必须分离为不同类型
  - **当前状态**: ❌ FAIL - 当前仅有 `type: 'tool'` 类型
  - **规格要求**: `contracts/stream-api.md` 第 52-77 行
  - **修复**: 创建 `SSEToolCallChunk` 和 `SSEToolResultChunk`

### 1.2 类型守卫函数

- [ ] **HIGH** 为每种 chunk 类型实现类型守卫（Type Guards）
  - **位置**: `types/stream.ts` 或 `utils/typeGuards.ts`
  - **示例**:
    ```typescript
    export function isContentChunk(chunk: SSEChunk): chunk is SSEContentChunk {
      return chunk.type === 'content'
    }
    ```
  - **使用场景**: `useStreamChat.ts` 和 `MessageBubble.tsx` 中的类型窄化

- [ ] **MEDIUM** 导出类型窄化辅助函数
  - **规格参考**: `contracts/stream-api.md` 第 142-167 行（使用示例）

---

## 2. 运行时验证

### 2.1 Schema 验证库集成

- [ ] **HIGH** 安装并配置 `zod` 用于运行时 schema 验证
  - **当前状态**: ❌ 未安装
  - **规格要求**: `plan.md` 第 67 行（宪章检查-类型安全建议）
  - **安装**: `npm install zod`
  - **位置**: 在 `api/streamAPI.ts` 中定义 schema

- [ ] **HIGH** 为 `SSEChunk` 定义 zod schema
  - **示例**:
    ```typescript
    import { z } from 'zod'
    
    const SSEChunkBaseSchema = z.object({
      timestamp: z.string().datetime()
    })
    
    const SSEContentChunkSchema = SSEChunkBaseSchema.extend({
      type: z.literal('content'),
      data: z.object({
        content: z.string()
      })
    })
    
    export const SSEChunkSchema = z.discriminatedUnion('type', [
      SSEConversationChunkSchema,
      SSEThinkingChunkSchema,
      SSEToolCallChunkSchema,
      SSEToolResultChunkSchema,
      SSEContentChunkSchema,
      SSEDoneChunkSchema,
      SSEErrorChunkSchema,
    ])
    ```

- [ ] **HIGH** 在 `useStreamChat.ts` 的 `onUpdate` 回调中验证后端数据
  - **位置**: `hooks/useStreamChat.ts` 第 88-100 行
  - **实现**:
    ```typescript
    onUpdate: (chunk: unknown) => {
      // 运行时验证
      const parseResult = SSEChunkSchema.safeParse(chunk)
      if (!parseResult.success) {
        console.error('Invalid chunk format:', parseResult.error)
        return
      }
      const validChunk = parseResult.data
      // 继续处理...
    }
    ```

### 2.2 错误处理

- [ ] **MEDIUM** 为类型验证失败添加错误日志和上报
  - **当前状态**: ❌ 无验证
  - **规格要求**: `plan.md` 第 69 行（可观测性建议：loglevel + Sentry）
  - **实现**: 使用 `console.error()` 或 Sentry

- [ ] **MEDIUM** 在开发环境启用严格类型检查
  - **位置**: `tsconfig.json`
  - **验证**: `strict: true`, `strictNullChecks: true`, `noImplicitAny: true`

---

## 3. API 客户端类型安全

### 3.1 请求类型

- [ ] **HIGH** `ChatRequest` 必须包含所有后端所需字段
  - **当前状态**: ✅ PASS - `types/api.ts` 已定义
  - **验证字段**:
    - `message: string` ✅
    - `conversation_id?: number` ✅
    - `use_knowledge_base?: string` ✅
    - `llm_config?: LLMConfig` ✅
    - `search_provider?: string` ✅
    - `role_preset_id?: number` ✅
    - `deep_reasoning?: boolean` ✅

### 3.2 响应类型

- [ ] **CRITICAL** `StreamingMessage` 必须支持所有流式数据块类型
  - **当前状态**: ⚠️ PARTIAL - 缺少 `timestamp`, `tool_result` 处理
  - **规格要求**:
    ```typescript
    export interface StreamingMessage {
      conversation_id?: number
      role: 'assistant'
      content: string
      thinking: string
      intermediate_steps: ToolInfo[]  // 必须包含 tool_call 和 tool_result
      is_complete: boolean
      timestamp?: string  // NEW: 最后更新时间
    }
    ```

- [ ] **HIGH** `ToolInfo` 必须区分输入和输出
  - **当前状态**: ⚠️ 需验证
  - **规格要求**: `contracts/stream-api.md` 第 52-77 行
  - **验证**: 检查 `types/api.ts` 中的 `ToolInfo` 定义

---

## 4. 组件类型约束

### 4.1 Props 类型定义

- [ ] **HIGH** `MessageBubble` 组件必须接受 union 类型
  - **当前状态**: ✅ PASS - `Message | StreamingMessage`
  - **位置**: `pages/ChatPage/components/MessageBubble.tsx` 第 18 行

- [ ] **MEDIUM** 所有组件 props 必须使用 `interface` 或 `type`，禁止 `any`
  - **验证方法**: 运行 `tsc --noEmitOnError` 检查类型错误

### 4.2 Hooks 返回类型

- [ ] **HIGH** `useStreamChat` 必须返回明确的类型
  - **当前状态**: ✅ PASS - 已定义 `UseStreamChatReturn`
  - **位置**: `hooks/useStreamChat.ts` 第 37 行

---

## 验证步骤

### 自动化验证

1. **TypeScript 编译检查**:
   ```bash
   cd frontend && npx tsc --noEmit
   ```
   预期: 0 errors

2. **ESLint 类型规则检查**:
   ```bash
   npx eslint src/**/*.ts src/**/*.tsx --ext .ts,.tsx
   ```
   预期: 无 `@typescript-eslint/no-explicit-any` 警告

### 手动验证

1. **类型窄化测试**:
   - 在 `useStreamChat.ts` 中使用类型守卫
   - 验证 IDE 能正确推断类型

2. **运行时验证测试**:
   - 启动前端和后端
   - 发送包含工具调用的消息（如"武汉天气如何?"）
   - 检查浏览器控制台是否有类型验证错误

---

## 完成标准

**门控条件** (必须 100% 通过):
- [ ] 所有 CRITICAL 项已修复
- [ ] 所有 HIGH 项已修复或有明确的延后计划
- [ ] TypeScript 编译无错误
- [ ] 运行时能正确处理所有 7 种 chunk 类型

**质量指标**:
- TypeScript `strict` 模式: ✅ 已启用
- 类型覆盖率: 目标 95%+（无 `any` 类型）
- 运行时验证覆盖: 关键数据流 100%

---

**最后更新**: 2026-01-26  
**状态**: 🔴 BLOCKED - 需要修复 CRITICAL 问题
