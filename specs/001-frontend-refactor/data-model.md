# Phase 1: 前端数据模型设计

**日期**：2026-01-24  
**特性**：001-frontend-refactor  
**目标**：定义前端核心数据结构和状态管理策略

---

## 1. 核心数据模型

### 1.1 消息相关

```typescript
// 消息角色
type MessageRole = 'user' | 'assistant' | 'system'

// 工具调用信息
interface ToolInfo {
  tool: string              // 工具名称（如 'web_search'、'knowledge_retrieval'）
  input: string             // 工具输入参数
  output: string            // 工具输出结果
  timestamp?: string        // 调用时间戳
}

// 完整消息
interface Message {
  id: number
  conversation_id: number
  role: MessageRole
  content: string                   // 消息主内容
  thinking?: string                 // AI 的思考过程
  intermediate_steps?: ToolInfo[]  // 工具调用列表
  created_at: string
  updated_at?: string
}

// @ant-design/x Bubble 组件所需类型
interface BubbleMessage {
  key: string | number
  role: 'user' | 'assistant'
  content: string
  avatar?: string | { src: string; alt?: string }
  typing?: boolean          // 是否显示打字机效果
  status?: 'loading' | 'success' | 'error'
}

// 临时流式消息（UI 状态）
interface StreamingMessage {
  conversation_id?: number
  role: 'assistant'
  content: string                   // 累积的内容
  thinking: string                  // 累积的思考过程
  tool_calls: ToolInfo[]           // 累积的工具调用
  is_complete: boolean             // 是否完成
}
```

### 1.2 会话相关

```typescript
// 会话对象
interface Conversation {
  id: number
  title: string
  created_at: string
  updated_at: string
  message_count?: number    // 消息数量（可选）
}

// 会话创建请求
interface ConversationCreate {
  title: string
}
```

### 1.3 LLM 配置

```typescript
// LLM 提供商
interface LLMProvider {
  id: string                // 如 'dashscope'、'openai'
  name: string              // 显示名称
  models: LLMModel[]        // 支持的模型列表
}

// LLM 模型
interface LLMModel {
  id: string                // 模型 ID（如 'qwen-max'）
  name: string              // 显示名称
  context_length?: number   // 上下文长度（可选）
}

// LLM 配置对象
interface LLMConfig {
  provider: string
  model: string
  temperature?: number
  max_tokens?: number
}

// LLM 提供商响应
interface LLMProvidersResponse {
  providers: LLMProvider[]
  default: {
    provider: string
    model: string
  }
}
```

### 1.4 角色预设

```typescript
// 角色预设对象
interface RolePreset {
  id: string
  title: string
  content: string           // 系统提示词
  category: string          // 分类（如 '编程'、'写作'）
  tags: string[]            // 标签
  score?: number            // 评分（可选）
  created_at?: string
  updated_at?: string
}

// 角色预设表单
interface RolePresetFormValues {
  title: string
  content: string
  category: string
  tags: string              // 逗号分隔的标签字符串
}
```

### 1.5 知识库

```typescript
// 知识库对象
interface KnowledgeBase {
  id: string
  name: string
  description: string
  document_count: number
  created_at: string
}

// 知识卡片
interface KnowledgeCard {
  id: string
  title: string
  content: string
  knowledge_base_id: string
  created_at: string
}
```

---

## 2. 请求/响应类型

### 2.1 聊天请求

```typescript
// 聊天请求
interface ChatRequest {
  message: string
  conversation_id?: number
  llm_config?: LLMConfig
  search_provider?: string          // 搜索提供商（'tavily'、'baidu'）
  use_knowledge_base?: string       // 知识库 ID
  role_preset_id?: string           // 角色预设 ID
  deep_reasoning?: boolean          // 深度推理模式
}

// 聊天响应（非流式）
interface ChatResponse {
  conversation_id: number
  message: Message
}
```

### 2.2 流式响应

```typescript
// 流式数据块类型
type StreamChunkType = 
  | 'conversation_id'  // 会话创建
  | 'thinking'         // 思考过程
  | 'tool'             // 工具调用
  | 'content'          // 消息内容
  | 'done'             // 完成标记
  | 'error'            // 错误

// SSE 数据块（后端返回）
interface SSEChunk {
  type: StreamChunkType
  content?: string              // thinking/content 使用
  conversation_id?: number      // conversation_id/done 使用
  tool_info?: ToolInfo          // tool 使用
  message?: string              // error 使用
}
```

---

## 3. 状态管理设计

### 3.1 全局状态（ChatPage 组件）

```typescript
interface ChatPageState {
  // ===== 会话管理 =====
  conversations: Conversation[]
  conversationId?: number
  messages: Message[]
  loading: boolean
  
  // ===== 流式输出状态 =====
  streamingMessage: StreamingMessage | null
  isStreaming: boolean
  
  // ===== LLM 配置（持久化到 localStorage） =====
  selectedProvider: string
  selectedModel: string
  selectedSearchProvider: string
  providers: LLMProvider[]
  
  // ===== 角色预设 =====
  rolePresets: RolePreset[]
  selectedRolePresetId?: string
  useKnowledge: boolean
  deepReasoning: boolean
  
  // ===== 输入 =====
  inputValue: string
  
  // ===== 知识库（可选） =====
  knowledgeBases: KnowledgeBase[]
  selectedKnowledgeBaseId?: string
}
```

### 3.2 组件本地状态

**ConversationSidebar**:
```typescript
{
  // 无需本地状态，完全受控
}
```

**RolePresetSidebar**:
```typescript
{
  selectedCategories: string[]          // 分类过滤
  isPromptModalOpen: boolean           // 弹窗显示
  editingPrompt: RolePreset | null     // 正在编辑的预设
  viewingPrompt: RolePreset | null     // 正在查看的预设
  isViewModalOpen: boolean
  promptForm: FormInstance             // Ant Design Form 实例
}
```

**MessageItem**:
```typescript
{
  isToolCallsExpanded: boolean         // 工具调用折叠状态
}
```

**ChatInputArea**:
```typescript
{
  inputRef: RefObject<TextAreaRef>     // 输入框引用
}
```

### 3.3 状态更新模式

**消息加载**：
```typescript
const loadMessages = async (conversationId: number) => {
  setLoading(true)
  try {
    const response = await api.getMessages(conversationId)
    setMessages(response.data)
  } catch (error) {
    message.error('加载消息失败')
  } finally {
    setLoading(false)
  }
}
```

**流式消息处理**：
```typescript
const handleStreamChunk = (chunk: SSEChunk) => {
  switch (chunk.type) {
    case 'conversation_id':
      setConversationId(chunk.conversation_id!)
      break
      
    case 'thinking':
      setStreamingMessage(prev => ({
        ...prev!,
        thinking: prev!.thinking + chunk.content!
      }))
      break
      
    case 'tool':
      setStreamingMessage(prev => ({
        ...prev!,
        tool_calls: [...prev!.tool_calls, chunk.tool_info!]
      }))
      break
      
    case 'content':
      setStreamingMessage(prev => ({
        ...prev!,
        content: prev!.content + chunk.content!
      }))
      break
      
    case 'done':
      finalizeStreamingMessage()
      break
      
    case 'error':
      message.error(chunk.message)
      setIsStreaming(false)
      break
  }
}

const finalizeStreamingMessage = () => {
  const finalMessage: Message = {
    id: Date.now(), // 临时 ID
    conversation_id: conversationId!,
    role: 'assistant',
    content: streamingMessage!.content,
    thinking: streamingMessage!.thinking || undefined,
    intermediate_steps: streamingMessage!.tool_calls.length > 0 
      ? streamingMessage!.tool_calls 
      : undefined,
    created_at: new Date().toISOString()
  }
  
  setMessages(prev => [...prev, finalMessage])
  setStreamingMessage(null)
  setIsStreaming(false)
  setInputValue('')
}
```

---

## 4. LocalStorage 持久化

### 4.1 持久化数据

```typescript
// 需要持久化的配置
interface PersistedConfig {
  llmProvider: string
  llmModel: string
  searchProvider: string
  deepReasoning: boolean
  useKnowledge: boolean
  selectedKnowledgeBaseId?: string
}

// LocalStorage Keys
const STORAGE_KEYS = {
  LLM_PROVIDER: 'agentmind_llm_provider',
  LLM_MODEL: 'agentmind_llm_model',
  SEARCH_PROVIDER: 'agentmind_search_provider',
  DEEP_REASONING: 'agentmind_deep_reasoning',
  USE_KNOWLEDGE: 'agentmind_use_knowledge',
  KNOWLEDGE_BASE_ID: 'agentmind_knowledge_base_id'
} as const
```

### 4.2 自定义 Hook

```typescript
// useLocalStorage.ts
function useLocalStorage<T>(
  key: string, 
  defaultValue: T
): [T, (value: T) => void] {
  const [value, setValue] = useState<T>(() => {
    try {
      const saved = localStorage.getItem(key)
      return saved ? JSON.parse(saved) : defaultValue
    } catch {
      return defaultValue
    }
  })
  
  useEffect(() => {
    try {
      localStorage.setItem(key, JSON.stringify(value))
    } catch (error) {
      console.error('Failed to save to localStorage:', error)
    }
  }, [key, value])
  
  return [value, setValue]
}

// 使用示例
const [selectedProvider, setSelectedProvider] = useLocalStorage(
  STORAGE_KEYS.LLM_PROVIDER, 
  'dashscope'
)
```

---

## 5. 数据流图

### 5.1 用户发送消息流程

```
用户输入消息
    ↓
点击发送按钮
    ↓
验证输入（非空）
    ↓
构建 ChatRequest
    ↓
XRequest 发起流式请求
    ↓
SSE 数据块到达（循环）
    ├─ conversation_id → 设置 conversationId
    ├─ thinking → 累积 streamingMessage.thinking
    ├─ tool → 累积 streamingMessage.tool_calls
    ├─ content → 累积 streamingMessage.content
    ├─ done → 完成消息，添加到 messages 列表
    └─ error → 显示错误提示
    ↓
UI 实时更新
    ↓
完成后重置输入框
```

### 5.2 会话切换流程

```
用户点击会话项
    ↓
onSelectConversation(id)
    ↓
setConversationId(id)
    ↓
触发 useEffect
    ↓
loadMessages(id)
    ↓
setMessages(loaded)
    ↓
UI 更新显示新会话消息
```

### 5.3 配置变更流程

```
用户修改 LLM 配置
    ↓
onProviderChange(provider)
    ↓
setSelectedProvider(provider)
    ↓
useLocalStorage Hook 自动保存
    ↓
localStorage 持久化
    ↓
下次打开自动恢复
```

---

## 6. 性能优化策略

### 6.1 React.memo 使用

```typescript
// 消息组件（避免所有消息重新渲染）
export const MessageItem = React.memo<MessageItemProps>(
  ({ message, isStreaming }) => {
    // 渲染逻辑
  },
  (prev, next) => {
    // 自定义比较
    return prev.message.id === next.message.id &&
           prev.isStreaming === next.isStreaming
  }
)

// 会话项组件
export const ConversationItem = React.memo<ConversationItemProps>(
  ({ conversation, isActive, onSelect }) => {
    // 渲染逻辑
  }
)
```

### 6.2 useCallback/useMemo 优化

```typescript
// 缓存回调函数
const handleSendMessage = useCallback(() => {
  if (!inputValue.trim() || loading) return
  
  sendChatMessage({
    message: inputValue,
    conversation_id: conversationId,
    llm_config: { provider: selectedProvider, model: selectedModel },
    deep_reasoning: deepReasoning
  })
}, [inputValue, loading, conversationId, selectedProvider, selectedModel, deepReasoning])

// 缓存计算结果
const filteredRolePresets = useMemo(() => {
  return rolePresets.filter(preset => 
    selectedCategories.length === 0 || selectedCategories.includes(preset.category)
  )
}, [rolePresets, selectedCategories])
```

### 6.3 防抖节流

```typescript
import { debounce } from 'lodash-es'

// 搜索框防抖
const debouncedSearch = useMemo(
  () => debounce((value: string) => {
    searchRolePresets(value)
  }, 300),
  []
)

// 滚动监听节流
const throttledScroll = useMemo(
  () => throttle(() => {
    checkIfNeedLoadMore()
  }, 100),
  []
)
```

---

## 7. 错误处理

### 7.1 错误类型

```typescript
// API 错误
interface APIError {
  code: string
  message: string
  details?: any
}

// 流式响应错误
interface StreamError {
  type: 'error'
  message: string
  code?: string
}
```

### 7.2 错误处理策略

```typescript
// XRequest 错误处理
callbacks: {
  onError: (error, errorInfo) => {
    if (error.message === 'TimeoutError') {
      message.error('请求超时，请重试')
    } else if (error.message === 'StreamTimeoutError') {
      message.warning('连接中断，正在重试...')
      // 自动重试逻辑
    } else if (error instanceof DOMException && error.name === 'AbortError') {
      // 用户主动取消，静默处理
      console.log('Request cancelled by user')
    } else {
      message.error(`请求失败: ${error.message}`)
      logError(error, errorInfo)
    }
    
    setIsStreaming(false)
    setLoading(false)
  }
}

// 全局错误边界
class ErrorBoundary extends React.Component<Props, State> {
  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    logError(error, errorInfo)
    message.error('应用遇到错误，请刷新页面')
  }
  
  render() {
    if (this.state.hasError) {
      return <ErrorFallback />
    }
    return this.props.children
  }
}
```

---

## 8. 数据验证

### 8.1 输入验证

```typescript
// 消息内容验证
const validateMessage = (content: string): boolean => {
  if (!content.trim()) {
    message.warning('请输入消息内容')
    return false
  }
  
  if (content.length > 10000) {
    message.warning('消息内容过长（最多 10000 字符）')
    return false
  }
  
  return true
}

// 角色预设验证
const validateRolePreset = (values: RolePresetFormValues): boolean => {
  if (!values.title.trim()) {
    message.warning('请输入标题')
    return false
  }
  
  if (!values.content.trim()) {
    message.warning('请输入提示词内容')
    return false
  }
  
  return true
}
```

### 8.2 数据清洗

```typescript
// 清理流式响应数据
const sanitizeStreamContent = (content: string): string => {
  return content
    .replace(/\0/g, '')  // 移除 null 字符
    .trim()
}

// 格式化时间戳
const formatTimestamp = (timestamp: string): string => {
  return new Date(timestamp).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}
```

---

## 总结

本文档定义了前端重构所需的核心数据模型和状态管理策略：

✅ **完整的数据类型定义**（Message、Conversation、LLMConfig 等）  
✅ **清晰的状态管理策略**（全局状态 vs 组件状态）  
✅ **LocalStorage 持久化方案**（自定义 Hook）  
✅ **数据流设计**（用户操作 → 状态变更 → UI 更新）  
✅ **性能优化指南**（Memo、防抖节流、缓存）  
✅ **错误处理机制**（错误类型、处理策略）  

**下一步**：
1. 生成 API 契约文件（contracts/）
2. 生成快速开始指南（quickstart.md）
3. 更新 Copilot 上下文
