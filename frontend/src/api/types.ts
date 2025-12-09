// LLM配置相关类型
export interface LLMConfig {
  provider?: string  // 'openai' 或 'dashscope'
  model?: string
}

export interface LLMModel {
  id: string
  name: string
}

export interface LLMProvider {
  id: string
  name: string
  models: LLMModel[]
}

export interface LLMProvidersResponse {
  providers: LLMProvider[]
  default: LLMConfig
}

// 工具调用步骤
export interface ToolStep {
  tool: string
  input: string
  output: string
  log?: string
}

// 对话相关类型
export interface Message {
  id: number
  conversation_id: number
  role: 'user' | 'assistant' | 'system'
  content: string
  metadata?: any
  created_at: string
  intermediate_steps?: ToolStep[]
  thinking?: string  // 推理过程
}

export interface Conversation {
  id: number
  title: string
  created_at: string
  updated_at: string
  messages: Message[]
}

export interface ChatRequest {
  message: string
  conversation_id?: number
  use_knowledge_base?: string
  llm_config?: LLMConfig
  search_provider?: string  // 搜索提供商: 'tavily' 或 'baidu'
  role_preset_id?: string  // 指定的角色预设ID，如果指定则直接使用该预设，不再检索
  deep_reasoning?: boolean  // 深度推理模式
}

export interface ChatResponse {
  success: boolean
  response: string
  conversation_id: number
  intermediate_steps: any[]
}

// 知识库相关类型
export interface KnowledgeBase {
  id: number
  name: string
  description?: string
  collection_name: string
  created_at: string
  updated_at: string
}

export interface Document {
  id: number
  knowledge_base_id: number
  title: string
  content: string
  source?: string
  metadata?: any
  created_at: string
}

export interface SearchRequest {
  query: string
  top_k?: number
}

export interface SearchResult {
  content: string
  metadata: any
  score: number
}

export interface SearchResponse {
  results: SearchResult[]
  query: string
}

// 角色预设相关类型
export interface RolePreset {
  id?: string
  title: string
  content: string
  category: string
  tags: string[]
  score?: number
}

// 任务相关类型
export interface Task {
  id: number
  title: string
  description: string
  status: 'pending' | 'planned' | 'in_progress' | 'completed' | 'failed'
  plan?: {
    plan_text: string
    steps: TaskStep[]
  }
  result?: any
  created_at: string
  updated_at: string
}

export interface TaskStep {
  description: string
  status: 'pending' | 'in_progress' | 'completed' | 'failed'
}

export interface TaskPlanRequest {
  description: string
  llm_config?: LLMConfig
}

export interface TaskPlanResponse {
  success: boolean
  plan: string
  steps: TaskStep[]
}

