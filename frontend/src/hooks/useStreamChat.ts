/**
 * 流式聊天 Hook
 * 集成 @ant-design/x-sdk XRequest
 */

import { useState, useCallback, useRef } from 'react'
import type { ChatRequest } from '../types/api'
import type { StreamingMessage, StreamStatus, StreamError } from '../types/stream'
import {
  createEmptyStreamingMessage,
  accumulateStreamChunk,
  buildChatStreamRequest,
  getStreamAPIUrl,
} from '../api/streamAPI'

/** 流式聊天状态 */
export interface UseStreamChatState {
  /** 当前流式消息 */
  streamingMessage: StreamingMessage | null
  /** 流式状态 */
  status: StreamStatus
  /** 错误信息 */
  error: StreamError | null
  /** 是否正在流式传输 */
  isStreaming: boolean
}

/** 流式聊天回调 */
export interface UseStreamChatCallbacks {
  /** 发送消息并开始流式响应 */
  sendMessage: (request: ChatRequest) => Promise<void>
  /** 取消当前流式请求 */
  cancelStream: () => void
  /** 重置状态 */
  reset: () => void
  /** 清空流式消息 */
  clearStreamingMessage: () => void
}

/** 流式聊天 Hook 返回值 */
export type UseStreamChatReturn = UseStreamChatState & UseStreamChatCallbacks

/**
 * 流式聊天 Hook
 * 
 * @param onChunkUpdate - 每次收到数据块时的回调
 * @param onComplete - 流式完成时的回调
 * @param onError - 错误时的回调
 */
export function useStreamChat(options?: {
  onChunkUpdate?: (message: StreamingMessage) => void
  onComplete?: (message: StreamingMessage) => void
  onError?: (error: StreamError) => void
}): UseStreamChatReturn {
  const { onChunkUpdate, onComplete, onError: onErrorCallback } = options || {}

  const [streamingMessage, setStreamingMessage] = useState<StreamingMessage | null>(null)
  const [status, setStatus] = useState<StreamStatus>('idle')
  const [error, setError] = useState<StreamError | null>(null)

  // 使用 ref 存储累积的消息
  const accumulatedMessageRef = useRef<StreamingMessage>(createEmptyStreamingMessage())

  /**
   * 发送消息并开始流式响应
   */
  const sendMessage = useCallback(
    async (request: ChatRequest & { plan_mode?: boolean }) => {
      try {
        // 重置状态
        setError(null)
        setStatus('streaming')

        // 创建空的流式消息
        const initialMessage = createEmptyStreamingMessage()
        accumulatedMessageRef.current = initialMessage
        setStreamingMessage(initialMessage)

        // 构建请求
        const requestBody = buildChatStreamRequest(request)

        console.log('Sending fetch request to:', getStreamAPIUrl(), 'body:', requestBody)
        
        // 使用原生 fetch 发送请求
        const response = await fetch(getStreamAPIUrl(), {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(requestBody),
        })

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
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
              console.log('Stream reader done')
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
                    const chunk = JSON.parse(jsonStr)
                    console.log('Parsed chunk:', chunk)
                    
                    // 累积数据
                    const accumulated = accumulateStreamChunk(
                      accumulatedMessageRef.current,
                      chunk
                    )
                    console.log('Accumulated message:', accumulated)
                    accumulatedMessageRef.current = accumulated
                    setStreamingMessage({ ...accumulated })
                    onChunkUpdate?.(accumulated)
                    
                    // 检查是否收到 done chunk
                    if (chunk.type === 'done') {
                      console.log('Stream completed with done chunk')
                      setStatus('completed')
                      // 调用 onComplete，让父组件加载新消息并决定何时清空流式消息
                      if (onComplete) {
                        await onComplete(accumulatedMessageRef.current)
                      }
                      return // 提前退出
                    }
                  }
                } catch (e) {
                  console.error('Failed to parse SSE data:', e, 'Line:', line)
                }
              }
            }
          }
        } finally {
          reader.releaseLock()
        }
      } catch (err) {
        console.error('Stream error:', err)
        const streamError: StreamError = {
          message: err instanceof Error ? err.message : '未知错误',
          code: 'REQUEST_ERROR',
          timestamp: new Date().toISOString(),
        }
        setError(streamError)
        setStatus('error')
        setStreamingMessage(null)  // 错误时也清空流式消息
        onErrorCallback?.(streamError)
      }
    },
    [onChunkUpdate, onComplete, onErrorCallback]
  )

  /**
   * 取消当前流式请求
   * 注意：XRequest 目前没有提供取消 API，此方法仅重置状态
   */
  const cancelStream = useCallback(() => {
    setStatus('idle')
    setStreamingMessage(null)
  }, [])

  /**
   * 重置状态
   */
  const reset = useCallback(() => {
    cancelStream()
    setError(null)
    setStreamingMessage(null)
    setStatus('idle')
  }, [cancelStream])

  /**
   * 清空流式消息
   */
  const clearStreamingMessage = useCallback(() => {
    setStreamingMessage(null)
  }, [])

  return {
    streamingMessage,
    status,
    error,
    isStreaming: status === 'streaming',
    sendMessage,
    cancelStream,
    reset,
    clearStreamingMessage,
  }
}
