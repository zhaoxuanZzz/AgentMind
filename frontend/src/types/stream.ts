/**
 * 流式响应相关类型定义
 * 对应后端 SSE 流式输出格式
 */

import { ToolInfo } from './api'

/** 流式数据块类型 */
export type StreamChunkType = 
  | 'conversation_id'  // 会话创建通知
  | 'thinking'         // AI 思考过程
  | 'tool'             // 工具调用信息（兼容旧格式）
  | 'tool_call'        // 工具调用开始
  | 'tool_result'      // 工具调用结果
  | 'content'          // 消息内容片段（旧格式）
  | 'text'             // 消息内容片段（新格式）
  | 'done'             // 流式响应完成
  | 'error'            // 错误信息

/** SSE 数据块（后端流式响应格式） */
export interface SSEChunk {
  /** 数据块类型 */
  type: StreamChunkType
  
  /** 数据负载（后端统一包裹在 data 字段中） */
  data?: {
    /** conversation_id 类型的数据 */
    conversation_id?: number
    /** thinking 类型的数据 */
    thinking?: string
    /** content 类型的数据 */
    content?: string
    /** tool_call 类型的数据 */
    tool_name?: string
    tool_input?: string | Record<string, any>
    /** tool_result 类型的数据 */
    tool_output?: string
    /** error 类型的数据 */
    message?: string
    code?: string
  }
  
  /** 时间戳 */
  timestamp?: string
  
  // 兼容旧格式的字段
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

/** 临时流式消息（UI 状态） */
export interface StreamingMessage {
  conversation_id?: number
  role: 'assistant'
  /** 累积的内容 */
  content: string
  /** 累积的思考过程 */
  thinking: string
  /** 累积的工具调用 (alias: intermediate_steps) */
  intermediate_steps: ToolInfo[]
  /** 是否完成 */
  is_complete: boolean
}

/** 流式请求状态 */
export type StreamStatus = 'idle' | 'streaming' | 'completed' | 'error'

/** 流式错误 */
export interface StreamError {
  message: string
  code?: string
  timestamp: string
}
