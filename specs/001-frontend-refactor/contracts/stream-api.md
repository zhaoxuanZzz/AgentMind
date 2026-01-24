# Stream API 契约

**文件**: `contracts/stream-api.ts`  
**用途**: 流式聊天 API 的 TypeScript 接口定义

---

## 流式响应类型

### SSE 数据块

```typescript
/**
 * 流式数据块类型枚举
 */
export type StreamChunkType = 
  | 'conversation_id'  // 会话创建通知
  | 'thinking'         // AI 思考过程
  | 'tool'             // 工具调用信息
  | 'content'          // 消息内容片段
  | 'done'             // 流式响应完成
  | 'error'            // 错误信息

/**
 * SSE 数据块（后端流式响应格式）
 * 
 * SSE 格式：data: {JSON}\n\n
 */
export interface SSEChunk {
  /** 数据块类型 */
  type: StreamChunkType
  
  /** 文本内容（用于 thinking/content 类型） */
  content?: string
  
  /** 会话 ID（用于 conversation_id/done 类型） */
  conversation_id?: number
  
  /** 工具调用信息（用于 tool 类型） */
  tool_info?: ToolInfo
  
  /** 错误消息（用于 error 类型） */
  message?: string
  
  /** 错误代码（可选） */
  code?: string
}

/**
 * 工具调用信息
 */
export interface ToolInfo {
  /** 工具名称（如 'web_search'、'knowledge_retrieval'） */
  tool: string
  
  /** 工具输入参数（JSON 字符串） */
  input: string
  
  /** 工具输出结果（JSON 字符串） */
  output: string
  
  /** 调用时间戳（ISO 8601 格式） */
  timestamp?: string
}
```

---

## 请求接口

### 聊天请求

```typescript
/**
 * 流式聊天请求参数
 * 
 * POST /api/chat/stream
 */
export interface ChatStreamRequest {
  /** 用户消息内容 */
  message: string
  
  /** 会话 ID（可选，不提供则创建新会话） */
  conversation_id?: number
  
  /** LLM 配置（可选） */
  llm_config?: {
    /** 提供商（如 'dashscope'、'openai'） */
    provider?: string
    
    /** 模型（如 'qwen-max'） */
    model?: string
    
    /** 温度参数（0-2，可选） */
    temperature?: number
    
    /** 最大 token 数（可选） */
    max_tokens?: number
  }
  
  /** 搜索提供商（如 'tavily'、'baidu'、'bing'） */
  search_provider?: string
  
  /** 知识库 ID（可选） */
  use_knowledge_base?: string
  
  /** 角色预设 ID（可选） */
  role_preset_id?: string
  
  /** 深度推理模式（默认 false） */
  deep_reasoning?: boolean
}
```

---

## XRequest 集成

### XRequest 使用示例

```typescript
import { XRequest } from '@ant-design/x-sdk'
import type { SSEChunk, ChatStreamRequest } from './stream-api'

/**
 * 发送流式聊天请求
 */
export async function sendStreamChat(
  request: ChatStreamRequest,
  callbacks: {
    onConversationId?: (id: number) => void
    onThinking?: (content: string) => void
    onToolCall?: (toolInfo: ToolInfo) => void
    onContent?: (content: string) => void
    onDone?: (conversationId: number) => void
    onError?: (error: string) => void
  }
) {
  await XRequest<ChatStreamRequest, SSEChunk>('/api/chat/stream', {
    params: request,
    timeout: 60000,        // 总请求 60 秒超时
    streamTimeout: 10000,  // 流 10 秒无数据超时
    headers: {
      'Content-Type': 'application/json'
    },
    callbacks: {
      onUpdate: (chunk) => {
        switch (chunk.type) {
          case 'conversation_id':
            callbacks.onConversationId?.(chunk.conversation_id!)
            break
          
          case 'thinking':
            callbacks.onThinking?.(chunk.content!)
            break
          
          case 'tool':
            callbacks.onToolCall?.(chunk.tool_info!)
            break
          
          case 'content':
            callbacks.onContent?.(chunk.content!)
            break
          
          case 'done':
            callbacks.onDone?.(chunk.conversation_id!)
            break
          
          case 'error':
            callbacks.onError?.(chunk.message!)
            break
        }
      },
      
      onSuccess: (allChunks) => {
        console.log(`Stream completed with ${allChunks.length} chunks`)
      },
      
      onError: (error, errorInfo) => {
        if (error.message === 'TimeoutError') {
          callbacks.onError?.('请求超时')
        } else if (error.message === 'StreamTimeoutError') {
          callbacks.onError?.('流传输超时')
        } else if (error instanceof DOMException && error.name === 'AbortError') {
          callbacks.onError?.('请求已取消')
        } else {
          callbacks.onError?.(error.message)
        }
      }
    }
  })
}
```

### 请求取消

```typescript
import { XRequest } from '@ant-design/x-sdk'

/**
 * 可取消的流式请求类
 */
export class CancellableStreamRequest {
  private requestInstance: any = null
  
  /**
   * 开始流式请求
   */
  async start(request: ChatStreamRequest, callbacks: any) {
    this.requestInstance = XRequest<ChatStreamRequest, SSEChunk>(
      '/api/chat/stream',
      {
        manual: true,  // 手动模式
        params: request,
        callbacks
      }
    )
    
    await this.requestInstance.run(request)
  }
  
  /**
   * 取消正在进行的请求
   */
  cancel() {
    if (this.requestInstance) {
      this.requestInstance.abort()
      this.requestInstance = null
    }
  }
  
  /**
   * 检查是否有正在进行的请求
   */
  isActive(): boolean {
    return this.requestInstance !== null
  }
}

// 使用示例
const streamRequest = new CancellableStreamRequest()

// 开始请求
await streamRequest.start(
  { message: 'Hello', conversation_id: 123 },
  {
    onContent: (content) => console.log(content),
    onDone: () => console.log('Done')
  }
)

// 用户点击停止按钮
streamRequest.cancel()
```

---

## 错误处理

### 错误类型

```typescript
/**
 * 流式响应错误类型
 */
export type StreamErrorType = 
  | 'timeout'           // 请求超时
  | 'stream_timeout'    // 流超时
  | 'network'           // 网络错误
  | 'server'            // 服务器错误
  | 'cancelled'         // 用户取消
  | 'unknown'           // 未知错误

/**
 * 流式错误对象
 */
export interface StreamError {
  type: StreamErrorType
  message: string
  code?: string
  details?: any
}

/**
 * 错误处理工具函数
 */
export function handleStreamError(
  error: Error,
  errorInfo?: any
): StreamError {
  if (error.message === 'TimeoutError') {
    return {
      type: 'timeout',
      message: '请求超时，请检查网络连接后重试'
    }
  }
  
  if (error.message === 'StreamTimeoutError') {
    return {
      type: 'stream_timeout',
      message: '数据传输中断，请重试'
    }
  }
  
  if (error instanceof DOMException && error.name === 'AbortError') {
    return {
      type: 'cancelled',
      message: '请求已取消'
    }
  }
  
  if (error.message.includes('fetch')) {
    return {
      type: 'network',
      message: '网络连接失败，请检查网络设置'
    }
  }
  
  return {
    type: 'unknown',
    message: error.message || '未知错误',
    details: errorInfo
  }
}
```

---

## 重试策略

### 自动重试

```typescript
/**
 * 带重试的流式请求
 * 
 * @param request 请求参数
 * @param callbacks 回调函数
 * @param maxRetries 最大重试次数（默认 3）
 * @param retryDelay 重试延迟（毫秒，默认 1000）
 */
export async function streamChatWithRetry(
  request: ChatStreamRequest,
  callbacks: any,
  maxRetries: number = 3,
  retryDelay: number = 1000
) {
  let attempt = 0
  
  const makeRequest = async (): Promise<void> => {
    attempt++
    
    try {
      await sendStreamChat(request, {
        ...callbacks,
        onError: async (error) => {
          // 判断是否应该重试
          const shouldRetry = 
            attempt < maxRetries &&
            (error.includes('超时') || error.includes('中断'))
          
          if (shouldRetry) {
            console.log(`Retry attempt ${attempt}/${maxRetries}`)
            await new Promise(resolve => 
              setTimeout(resolve, retryDelay * attempt)  // 指数退避
            )
            await makeRequest()
          } else {
            // 达到最大重试次数或不可重试错误
            callbacks.onError?.(error)
          }
        }
      })
    } catch (error) {
      callbacks.onError?.(error.message)
    }
  }
  
  await makeRequest()
}
```

---

## 性能优化

### 批量更新

```typescript
import { debounce } from 'lodash-es'

/**
 * 防抖的内容更新
 * 
 * 避免频繁的 UI 更新影响性能
 */
export function createDebouncedContentHandler(
  onContentUpdate: (content: string) => void,
  delay: number = 100
) {
  let accumulatedContent = ''
  
  const debouncedUpdate = debounce(() => {
    onContentUpdate(accumulatedContent)
    accumulatedContent = ''
  }, delay)
  
  return (chunk: string) => {
    accumulatedContent += chunk
    debouncedUpdate()
  }
}

// 使用示例
const debouncedHandler = createDebouncedContentHandler(
  (content) => setStreamingContent(prev => prev + content),
  100  // 100ms 批量更新一次
)

await sendStreamChat(request, {
  onContent: debouncedHandler
})
```

---

## 类型导出

```typescript
// 导出所有类型
export type {
  StreamChunkType,
  SSEChunk,
  ToolInfo,
  ChatStreamRequest,
  StreamErrorType,
  StreamError
}

// 导出工具函数
export {
  sendStreamChat,
  CancellableStreamRequest,
  handleStreamError,
  streamChatWithRetry,
  createDebouncedContentHandler
}
```

---

## 使用示例

### 完整的 React Hook

```typescript
import { useState, useCallback, useRef } from 'react'
import { message } from 'antd'
import { sendStreamChat, CancellableStreamRequest } from './stream-api'
import type { ChatStreamRequest } from './stream-api'

export function useStreamChat() {
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')
  const [streamingThinking, setStreamingThinking] = useState('')
  const [toolCalls, setToolCalls] = useState<ToolInfo[]>([])
  
  const requestRef = useRef<CancellableStreamRequest | null>(null)
  
  const sendMessage = useCallback(async (request: ChatStreamRequest) => {
    setIsStreaming(true)
    setStreamingContent('')
    setStreamingThinking('')
    setToolCalls([])
    
    requestRef.current = new CancellableStreamRequest()
    
    try {
      await requestRef.current.start(request, {
        onConversationId: (id) => {
          console.log('Conversation ID:', id)
        },
        onThinking: (content) => {
          setStreamingThinking(prev => prev + content)
        },
        onToolCall: (toolInfo) => {
          setToolCalls(prev => [...prev, toolInfo])
        },
        onContent: (content) => {
          setStreamingContent(prev => prev + content)
        },
        onDone: (conversationId) => {
          setIsStreaming(false)
          requestRef.current = null
        },
        onError: (error) => {
          message.error(error)
          setIsStreaming(false)
          requestRef.current = null
        }
      })
    } catch (error) {
      message.error('发送消息失败')
      setIsStreaming(false)
      requestRef.current = null
    }
  }, [])
  
  const cancelStream = useCallback(() => {
    if (requestRef.current) {
      requestRef.current.cancel()
      requestRef.current = null
      setIsStreaming(false)
    }
  }, [])
  
  return {
    isStreaming,
    streamingContent,
    streamingThinking,
    toolCalls,
    sendMessage,
    cancelStream
  }
}
```

---

**契约版本**: v1.0.0  
**兼容后端版本**: AgentMind Backend v1.x  
**最后更新**: 2026-01-24
