/**
 * API 相关类型定义
 * 对应后端 API 接口
 */

/** 消息角色 */
export type MessageRole = 'user' | 'assistant' | 'system'

/** 工具调用信息 */
export interface ToolInfo {
  /** 工具名称（如 'web_search'、'knowledge_retrieval'） */
  tool: string
  /** 工具输入参数 */
  input: string
  /** 工具输出结果 */
  output: string
  /** 调用时间戳 */
  timestamp?: string
}

/** 消息对象 */
export interface Message {
  id: number
  conversation_id: number
  role: MessageRole
  content: string
  /** AI 的思考过程 */
  thinking?: string
  /** 工具调用列表 */
  intermediate_steps?: ToolInfo[]
  /** 新格式：消息块列表 */
  chunks?: any[]  // AnyMessageChunk[] from messageTypes.ts
  created_at: string
  updated_at?: string
}

/** 会话对象 */
export interface Conversation {
  id: number
  title: string
  created_at: string
  updated_at: string
  message_count?: number
}

/** 会话创建请求 */
export interface ConversationCreate {
  title: string
}

/** LLM 配置 */
export interface LLMConfig {
  /** 提供商（如 'dashscope'、'openai'） */
  provider?: string
  /** 模型（如 'qwen-max'） */
  model?: string
  /** 温度参数（0-2） */
  temperature?: number
  /** 最大 token 数 */
  max_tokens?: number
}

/** 聊天请求 */
export interface ChatRequest {
  message: string
  conversation_id?: number
  llm_config?: LLMConfig
  plan_mode?: boolean  // 计划模式
  role_id?: string  // 角色ID
  use_knowledge_base?: string
  search_provider?: string
  role_preset_id?: string
  deep_reasoning?: boolean
}

/** 获取会话列表请求 */
export interface GetConversationsRequest {
  skip?: number
  limit?: number
}

/** 获取会话列表响应 */
export interface GetConversationsResponse {
  conversations: Conversation[]
  total?: number
}

/** 获取会话详情响应 */
export interface GetConversationResponse {
  conversation: Conversation
  messages: Message[]
}

/** API 响应通用结构 */
export interface ApiResponse<T = unknown> {
  success: boolean
  data?: T
  message?: string
  error?: string
}
