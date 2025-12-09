import apiClient from './client'
import type {
  ChatRequest,
  ChatResponse,
  Conversation,
  KnowledgeBase,
  Document,
  SearchRequest,
  SearchResponse,
  Task,
  TaskPlanRequest,
  TaskPlanResponse,
  LLMProvidersResponse,
} from './types'

// 对话相关API
export const chatApi = {
  sendMessage: (data: ChatRequest) => 
    apiClient.post<any, ChatResponse>('/chat/', data),
  
  sendMessageStream: async (
    data: ChatRequest,
    onChunk: (chunk: {
      type: 'thinking' | 'tool' | 'content' | 'done' | 'error' | 'conversation_id'
      content?: string
      tool_info?: any
      conversation_id?: number
      message?: string
    }) => void
  ) => {
    // 获取baseURL，处理相对路径
    const baseURL = apiClient.defaults?.baseURL || '/api'
    console.log('Streaming request to:', `${baseURL}/chat/stream`) // 调试日志
    
    const response = await fetch(`${baseURL}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      const errorText = await response.text()
      console.error('Stream error:', response.status, errorText)
      throw new Error(`HTTP error! status: ${response.status}, ${errorText}`)
    }

    const reader = response.body?.getReader()
    const decoder = new TextDecoder()

    if (!reader) {
      throw new Error('No reader available')
    }

    let buffer = ''

    try {
      while (true) {
        const { done, value } = await reader.read()
        
        if (done) {
          console.log('Stream completed')
          break
        }

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.trim() === '') continue
          
          if (line.startsWith('data: ')) {
            try {
              const jsonStr = line.slice(6).trim()
              if (jsonStr) {
                const chunkData = JSON.parse(jsonStr)
                console.log('Parsed chunk:', chunkData) // 调试日志
                onChunk(chunkData)
              }
            } catch (e) {
              console.error('Failed to parse SSE data:', e, 'Line:', line)
            }
          } else if (line.trim()) {
            // 处理没有"data: "前缀的行
            try {
              const chunkData = JSON.parse(line.trim())
              console.log('Parsed chunk (no prefix):', chunkData)
              onChunk(chunkData)
            } catch (e) {
              // 忽略解析错误，可能是其他类型的SSE消息
            }
          }
        }
      }
    } catch (error) {
      console.error('Stream reading error:', error)
      throw error
    }
  },
  
  getConversations: (skip = 0, limit = 20) =>
    apiClient.get<any, Conversation[]>(`/chat/conversations?skip=${skip}&limit=${limit}`),
  
  getConversation: (id: number) =>
    apiClient.get<any, Conversation>(`/chat/conversations/${id}`),
  
  deleteConversation: (id: number) =>
    apiClient.delete(`/chat/conversations/${id}`),
  
  getLLMProviders: () =>
    apiClient.get<any, LLMProvidersResponse>('/chat/llm-providers'),
}

// 知识库相关API
export const knowledgeApi = {
  createKnowledgeBase: (data: { name: string; description?: string }) =>
    apiClient.post<any, KnowledgeBase>('/knowledge/bases', data),
  
  getKnowledgeBases: (skip = 0, limit = 20) =>
    apiClient.get<any, KnowledgeBase[]>(`/knowledge/bases?skip=${skip}&limit=${limit}`),
  
  getKnowledgeBase: (id: number) =>
    apiClient.get<any, KnowledgeBase>(`/knowledge/bases/${id}`),
  
  deleteKnowledgeBase: (id: number) =>
    apiClient.delete(`/knowledge/bases/${id}`),
  
  addDocument: (kbId: number, data: { title: string; content: string; source?: string }) =>
    apiClient.post<any, Document>(`/knowledge/bases/${kbId}/documents`, data),
  
  getDocuments: (kbId: number, skip = 0, limit = 20) =>
    apiClient.get<any, Document[]>(`/knowledge/bases/${kbId}/documents?skip=${skip}&limit=${limit}`),
  
  searchKnowledge: (kbId: number, data: SearchRequest) =>
    apiClient.post<any, SearchResponse>(`/knowledge/bases/${kbId}/search`, data),
  
  // 角色预设相关API
  createRolePreset: (data: { 
    title: string; 
    prompt_content: string; 
    category?: string;
    tags?: string[];
  }) => apiClient.post<any, any>('/knowledge/prompts', data),
  
  getRolePresets: (params?: { 
    skip?: number; 
    limit?: number; 
    category?: string; 
    tags?: string; 
    title?: string;
  }) => {
    const queryParams = new URLSearchParams()
    if (params?.skip !== undefined) queryParams.append('skip', params.skip.toString())
    if (params?.limit !== undefined) queryParams.append('limit', params.limit.toString())
    if (params?.category) queryParams.append('category', params.category)
    if (params?.tags) queryParams.append('tags', params.tags)
    if (params?.title) queryParams.append('title', params.title)
    const query = queryParams.toString()
    return apiClient.get<any, any[]>(`/knowledge/prompts${query ? '?' + query : ''}`)
  },
  
  updateRolePreset: (presetId: string, data: {
    title?: string;
    prompt_content?: string;
    category?: string;
    tags?: string[];
  }) => apiClient.put<any, any>(`/knowledge/prompts/${presetId}`, data),
  
  deleteRolePreset: (presetId: string) =>
    apiClient.delete<any, any>(`/knowledge/prompts/${presetId}`),
  
  searchRolePresets: (data: { query: string; category?: string; top_k?: number }) =>
    apiClient.post<any, any>('/knowledge/prompts/search', data),
  
  // 生成提示词（不保存对话记录）
  generatePrompt: (data: { 
    prompt: string; 
    llm_config?: { provider?: string; model?: string } 
  }) => apiClient.post<any, { success: boolean; content: string; error?: string }>('/knowledge/prompts/generate', data),
}

// 任务相关API
export const taskApi = {
  createTask: (data: { title: string; description: string }) =>
    apiClient.post<any, Task>('/tasks/', data),
  
  planTask: (data: TaskPlanRequest) =>
    apiClient.post<any, TaskPlanResponse>('/tasks/plan', data),
  
  planExistingTask: (id: number) =>
    apiClient.post<any, Task>(`/tasks/${id}/plan`),
  
  getTasks: (skip = 0, limit = 20, status?: string) => {
    const params = new URLSearchParams({ skip: skip.toString(), limit: limit.toString() })
    if (status) params.append('status', status)
    return apiClient.get<any, Task[]>(`/tasks/?${params.toString()}`)
  },
  
  getTask: (id: number) =>
    apiClient.get<any, Task>(`/tasks/${id}`),
  
  updateTaskStatus: (id: number, status: string, result?: any) =>
    apiClient.patch(`/tasks/${id}/status?status=${status}`, result ? { result } : {}),
  
  deleteTask: (id: number) =>
    apiClient.delete(`/tasks/${id}`),
}

