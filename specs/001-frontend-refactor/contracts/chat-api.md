# Chat API 契约

**文件**: `contracts/chat-api.md`  
**用途**: 聊天管理 API 的 TypeScript 接口定义

---

## API 端点

### 1. 获取会话列表

```typescript
/**
 * GET /api/chat/conversations
 * 
 * 获取用户的会话列表
 */
export interface GetConversationsRequest {
  /** 跳过的记录数（分页） */
  skip?: number
  
  /** 返回的最大记录数（分页） */
  limit?: number
}

export interface GetConversationsResponse {
  conversations: Conversation[]
  total?: number
}

export interface Conversation {
  id: number
  title: string
  created_at: string
  updated_at: string
  message_count?: number
}
```

### 2. 获取会话详情

```typescript
/**
 * GET /api/chat/conversations/{conversation_id}
 * 
 * 获取指定会话的详细信息
 */
export interface GetConversationRequest {
  conversation_id: number
}

export interface GetConversationResponse {
  conversation: Conversation
  messages: Message[]
}

export interface Message {
  id: number
  conversation_id: number
  role: 'user' | 'assistant' | 'system'
  content: string
  thinking?: string
  intermediate_steps?: ToolInfo[]
  created_at: string
  updated_at?: string
}

export interface ToolInfo {
  tool: string
  input: string
  output: string
  timestamp?: string
}
```

### 3. 删除会话

```typescript
/**
 * DELETE /api/chat/conversations/{conversation_id}
 * 
 * 删除指定会话及其所有消息
 */
export interface DeleteConversationRequest {
  conversation_id: number
}

export interface DeleteConversationResponse {
  success: boolean
  message: string
}
```

### 4. 创建会话

```typescript
/**
 * POST /api/chat/conversations
 * 
 * 创建新会话
 */
export interface CreateConversationRequest {
  title: string
}

export interface CreateConversationResponse {
  conversation: Conversation
}
```

### 5. 更新会话

```typescript
/**
 * PUT /api/chat/conversations/{conversation_id}
 * 
 * 更新会话信息（如标题）
 */
export interface UpdateConversationRequest {
  conversation_id: number
  title?: string
}

export interface UpdateConversationResponse {
  conversation: Conversation
}
```

### 6. 获取 LLM 提供商列表

```typescript
/**
 * GET /api/chat/llm-providers
 * 
 * 获取可用的 LLM 提供商和模型列表
 */
export interface GetLLMProvidersResponse {
  providers: LLMProvider[]
  default: {
    provider: string
    model: string
  }
}

export interface LLMProvider {
  id: string              // 如 'dashscope'、'openai'
  name: string            // 显示名称
  models: LLMModel[]
}

export interface LLMModel {
  id: string              // 模型 ID（如 'qwen-max'）
  name: string            // 显示名称
  context_length?: number
}
```

---

## API 客户端

### Axios 封装

```typescript
import axios, { AxiosInstance } from 'axios'

/**
 * Chat API 客户端类
 */
export class ChatAPI {
  private client: AxiosInstance
  
  constructor(baseURL: string = '/api/chat') {
    this.client = axios.create({
      baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json'
      }
    })
  }
  
  /**
   * 获取会话列表
   */
  async getConversations(
    params?: GetConversationsRequest
  ): Promise<GetConversationsResponse> {
    const response = await this.client.get<Conversation[]>('/conversations', { 
      params 
    })
    return { conversations: response.data }
  }
  
  /**
   * 获取会话详情
   */
  async getConversation(
    conversationId: number
  ): Promise<GetConversationResponse> {
    const [convResponse, messagesResponse] = await Promise.all([
      this.client.get<Conversation>(`/conversations/${conversationId}`),
      this.client.get<Message[]>(`/conversations/${conversationId}/messages`)
    ])
    
    return {
      conversation: convResponse.data,
      messages: messagesResponse.data
    }
  }
  
  /**
   * 删除会话
   */
  async deleteConversation(
    conversationId: number
  ): Promise<DeleteConversationResponse> {
    const response = await this.client.delete<DeleteConversationResponse>(
      `/conversations/${conversationId}`
    )
    return response.data
  }
  
  /**
   * 创建会话
   */
  async createConversation(
    request: CreateConversationRequest
  ): Promise<CreateConversationResponse> {
    const response = await this.client.post<Conversation>(
      '/conversations',
      request
    )
    return { conversation: response.data }
  }
  
  /**
   * 更新会话
   */
  async updateConversation(
    conversationId: number,
    request: Omit<UpdateConversationRequest, 'conversation_id'>
  ): Promise<UpdateConversationResponse> {
    const response = await this.client.put<Conversation>(
      `/conversations/${conversationId}`,
      request
    )
    return { conversation: response.data }
  }
  
  /**
   * 获取 LLM 提供商
   */
  async getLLMProviders(): Promise<GetLLMProvidersResponse> {
    const response = await this.client.get<GetLLMProvidersResponse>(
      '/llm-providers'
    )
    return response.data
  }
}

// 导出单例
export const chatAPI = new ChatAPI()
```

---

## React Hooks

### useConversations

```typescript
import { useState, useEffect, useCallback } from 'react'
import { message } from 'antd'
import { chatAPI } from './chat-api'
import type { Conversation } from './chat-api'

/**
 * 会话管理 Hook
 */
export function useConversations() {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [loading, setLoading] = useState(false)
  
  // 加载会话列表
  const loadConversations = useCallback(async () => {
    setLoading(true)
    try {
      const response = await chatAPI.getConversations({ limit: 50 })
      setConversations(response.conversations)
    } catch (error) {
      message.error('加载会话列表失败')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }, [])
  
  // 创建新会话
  const createConversation = useCallback(async (title: string) => {
    try {
      const response = await chatAPI.createConversation({ title })
      setConversations(prev => [response.conversation, ...prev])
      return response.conversation
    } catch (error) {
      message.error('创建会话失败')
      console.error(error)
      return null
    }
  }, [])
  
  // 删除会话
  const deleteConversation = useCallback(async (conversationId: number) => {
    try {
      await chatAPI.deleteConversation(conversationId)
      setConversations(prev => prev.filter(c => c.id !== conversationId))
      message.success('会话已删除')
    } catch (error) {
      message.error('删除会话失败')
      console.error(error)
    }
  }, [])
  
  // 更新会话
  const updateConversation = useCallback(async (
    conversationId: number, 
    title: string
  ) => {
    try {
      const response = await chatAPI.updateConversation(conversationId, { title })
      setConversations(prev => 
        prev.map(c => c.id === conversationId ? response.conversation : c)
      )
    } catch (error) {
      message.error('更新会话失败')
      console.error(error)
    }
  }, [])
  
  // 初始加载
  useEffect(() => {
    loadConversations()
  }, [loadConversations])
  
  return {
    conversations,
    loading,
    loadConversations,
    createConversation,
    deleteConversation,
    updateConversation
  }
}
```

### useConversationMessages

```typescript
import { useState, useCallback } from 'react'
import { message as antdMessage } from 'antd'
import { chatAPI } from './chat-api'
import type { Message } from './chat-api'

/**
 * 会话消息管理 Hook
 */
export function useConversationMessages(conversationId?: number) {
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)
  
  // 加载消息
  const loadMessages = useCallback(async (id: number) => {
    setLoading(true)
    try {
      const response = await chatAPI.getConversation(id)
      setMessages(response.messages)
    } catch (error) {
      antdMessage.error('加载消息失败')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }, [])
  
  // 添加消息
  const addMessage = useCallback((msg: Message) => {
    setMessages(prev => [...prev, msg])
  }, [])
  
  // 清空消息
  const clearMessages = useCallback(() => {
    setMessages([])
  }, [])
  
  return {
    messages,
    loading,
    loadMessages,
    addMessage,
    clearMessages,
    setMessages
  }
}
```

### useLLMProviders

```typescript
import { useState, useEffect } from 'react'
import { message } from 'antd'
import { chatAPI } from './chat-api'
import type { LLMProvider } from './chat-api'

/**
 * LLM 提供商管理 Hook
 */
export function useLLMProviders() {
  const [providers, setProviders] = useState<LLMProvider[]>([])
  const [defaultProvider, setDefaultProvider] = useState<string>('')
  const [defaultModel, setDefaultModel] = useState<string>('')
  const [loading, setLoading] = useState(false)
  
  useEffect(() => {
    const loadProviders = async () => {
      setLoading(true)
      try {
        const response = await chatAPI.getLLMProviders()
        setProviders(response.providers)
        setDefaultProvider(response.default.provider)
        setDefaultModel(response.default.model)
      } catch (error) {
        message.error('加载 LLM 提供商失败')
        console.error(error)
      } finally {
        setLoading(false)
      }
    }
    
    loadProviders()
  }, [])
  
  return {
    providers,
    defaultProvider,
    defaultModel,
    loading
  }
}
```

---

## 错误处理

### 错误拦截器

```typescript
import { AxiosError } from 'axios'

/**
 * HTTP 错误类型
 */
export interface HTTPError {
  status: number
  code?: string
  message: string
  details?: any
}

/**
 * 错误处理工具
 */
export function handleAPIError(error: AxiosError): HTTPError {
  if (error.response) {
    // 服务器返回错误
    const { status, data } = error.response
    return {
      status,
      code: data?.code,
      message: data?.message || '服务器错误',
      details: data
    }
  } else if (error.request) {
    // 请求发送但无响应
    return {
      status: 0,
      message: '网络连接失败，请检查网络设置'
    }
  } else {
    // 请求配置错误
    return {
      status: 0,
      message: error.message || '未知错误'
    }
  }
}

// 在 Axios 实例中添加错误拦截器
client.interceptors.response.use(
  response => response,
  error => {
    const httpError = handleAPIError(error)
    console.error('API Error:', httpError)
    return Promise.reject(httpError)
  }
)
```

---

## 类型导出

```typescript
// 导出所有类型
export type {
  GetConversationsRequest,
  GetConversationsResponse,
  GetConversationRequest,
  GetConversationResponse,
  DeleteConversationRequest,
  DeleteConversationResponse,
  CreateConversationRequest,
  CreateConversationResponse,
  UpdateConversationRequest,
  UpdateConversationResponse,
  GetLLMProvidersResponse,
  Conversation,
  Message,
  ToolInfo,
  LLMProvider,
  LLMModel,
  HTTPError
}

// 导出 API 客户端
export { ChatAPI, chatAPI }

// 导出 Hooks
export { useConversations, useConversationMessages, useLLMProviders }

// 导出工具函数
export { handleAPIError }
```

---

**契约版本**: v1.0.0  
**兼容后端版本**: AgentMind Backend v1.x  
**最后更新**: 2026-01-24
