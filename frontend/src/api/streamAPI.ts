/**
 * 流式 API 辅助函数
 * 基于 @ant-design/x-sdk XRequest
 */

import type { SSEChunk, StreamingMessage } from '../types/stream'
import type { ChatRequest } from '../types/api'

/**
 * 解析 SSE 数据行
 */
export function parseSSEChunk(line: string): SSEChunk | null {
  if (!line.startsWith('data: ')) {
    return null
  }
  
  const dataStr = line.slice(6).trim()
  
  if (dataStr === '[DONE]') {
    return {
      type: 'done',
    }
  }
  
  try {
    return JSON.parse(dataStr) as SSEChunk
  } catch (error) {
    console.error('Failed to parse SSE chunk:', dataStr, error)
    return null
  }
}

/**
 * 创建空的流式消息
 */
export function createEmptyStreamingMessage(): StreamingMessage {
  return {
    role: 'assistant',
    content: '',
    thinking: '',
    intermediate_steps: [],
    is_complete: false,
  }
}

/**
 * 累积流式数据块到消息对象
 */
export function accumulateStreamChunk(
  message: StreamingMessage,
  chunk: SSEChunk
): StreamingMessage {
  console.log('accumulateStreamChunk called with chunk:', chunk)
  const updated = { ...message }

  switch (chunk.type) {
    case 'conversation_id':
      // 后端格式: { type, data: { conversation_id }, timestamp }
      const convId = chunk.data?.conversation_id ?? chunk.conversation_id
      if (convId !== undefined) {
        updated.conversation_id = convId
        console.log('Updated conversation_id:', convId)
      }
      break

    case 'thinking':
      // 后端格式: { type, data: { thinking }, timestamp }
      const thinking = chunk.data?.thinking ?? chunk.content
      if (thinking !== undefined) {
        updated.thinking += thinking
        console.log('Updated thinking, new length:', updated.thinking.length)
      }
      break

    case 'content':
    case 'text':
      // 后端格式: { type, content, timestamp } 或 { type, data: { content }, timestamp }
      const content = chunk.content ?? chunk.data?.content
      if (content !== undefined) {
        updated.content += content
        console.log('Updated content:', updated.content)
      }
      break

    case 'tool_call':
      // 后端格式: { type, data: { tool_name, tool_input }, timestamp }
      if (chunk.data) {
        const toolInput = chunk.data.tool_input
        updated.intermediate_steps.push({
          tool: chunk.data.tool_name || '',
          input: typeof toolInput === 'string' ? toolInput : JSON.stringify(toolInput || ''),
          output: '',
          timestamp: chunk.timestamp || new Date().toISOString(),
        })
      } else if (chunk.tool_info) {
        updated.intermediate_steps.push(chunk.tool_info)
      }
      break

    case 'tool_result':
      // 后端格式: { type, data: { tool_name, tool_output }, timestamp }
      if (chunk.data) {
        // 更新对应工具的输出
        const stepIndex = updated.intermediate_steps.findIndex(
          step => step.tool === chunk.data!.tool_name
        )
        if (stepIndex !== -1) {
          updated.intermediate_steps[stepIndex].output = chunk.data.tool_output || ''
        }
      }
      break

    case 'tool':
      // 兼容旧格式
      if (chunk.tool_info) {
        updated.intermediate_steps.push(chunk.tool_info)
      }
      break

    case 'done':
      updated.is_complete = true
      // 后端格式: { type, data: { conversation_id }, timestamp }
      const doneConvId = chunk.data?.conversation_id ?? chunk.conversation_id
      if (doneConvId !== undefined) {
        updated.conversation_id = doneConvId
      }
      break

    case 'error':
      // 错误处理由调用方处理
      break

    default:
      console.warn('Unknown chunk type:', chunk)
  }

  return updated
}

/**
 * 构建流式聊天请求体（v2 格式）
 */
export function buildChatStreamRequest(request: ChatRequest): any {
  return {
    message: request.message.trim(),
    conversation_id: request.conversation_id 
      ? Number(request.conversation_id) 
      : undefined,
    llm_config: request.llm_config,
    role_id: request.role_id || request.role_preset_id,  // 兼容旧字段名
    plan_mode: request.plan_mode,
    use_knowledge_base: request.use_knowledge_base,
    search_provider: request.search_provider,
    deep_reasoning: request.deep_reasoning,
  }
}

/**
 * 获取流式 API 端点 URL
 */
export function getStreamAPIUrl(): string {
  // 使用相对路径，避免硬编码域名
  return '/api/chat/stream-v2'
}
