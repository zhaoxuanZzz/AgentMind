/**
 * 数据模型类型定义
 * 包括角色预设、知识库等
 */

/** 角色预设 */
export interface RolePreset {
  id: number
  name: string
  description: string
  system_prompt: string
  icon?: string
  created_at: string
  updated_at: string
}

/** 知识库 */
export interface KnowledgeBase {
  id: number
  name: string
  description?: string
  type: 'document' | 'qa' | 'custom'
  source?: string
  metadata?: Record<string, unknown>
  created_at: string
  updated_at: string
}

/** 知识卡片 */
export interface KnowledgeCard {
  id: number
  knowledge_base_id: number
  title: string
  content: string
  tags?: string[]
  metadata?: Record<string, unknown>
  created_at: string
  updated_at: string
}

/** LLM 提供商 */
export interface LLMProvider {
  id: string
  name: string
  models: LLMModel[]
  requires_api_key: boolean
}

/** LLM 模型 */
export interface LLMModel {
  id: string
  name: string
  description?: string
  max_tokens?: number
  supports_streaming?: boolean
  supports_function_calling?: boolean
}
