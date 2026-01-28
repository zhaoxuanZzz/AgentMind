/**
 * 会话消息管理 Hook
 */

import { useState, useEffect, useCallback } from 'react'
import { ChatAPI } from '../api/chatAPI'
import type { Message } from '../types/api'

/** 会话消息状态 */
export interface UseConversationMessagesState {
  /** 消息列表 */
  messages: Message[]
  /** 是否正在加载 */
  loading: boolean
  /** 错误信息 */
  error: string | null
}

/** 会话消息操作 */
export interface UseConversationMessagesActions {
  /** 加载消息列表 */
  loadMessages: (conversationId: number) => Promise<void>
  /** 添加消息到列表 */
  addMessage: (message: Message) => void
  /** 更新消息 */
  updateMessage: (messageId: number, updates: Partial<Message>) => void
  /** 清空消息列表 */
  clearMessages: () => void
}

/** 会话消息 Hook 返回值 */
export type UseConversationMessagesReturn = UseConversationMessagesState &
  UseConversationMessagesActions

/**
 * 会话消息管理 Hook
 * 
 * @param conversationId - 会话 ID
 */
export function useConversationMessages(
  conversationId: number | null
): UseConversationMessagesReturn {
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastLoadedConversationId, setLastLoadedConversationId] = useState<number | null>(null)

  /**
   * 加载消息列表
   */
  const loadMessages = useCallback(async (convId: number) => {
    setLoading(true)
    setError(null)

    try {
      const response = await ChatAPI.getConversation(convId)
      const serverMessages = response.messages || []
      
      // 直接使用服务器返回的消息，覆盖本地所有消息
      // 因为服务器消息是权威数据源，包含完整的 chunks 等信息
      setMessages(serverMessages)
      setLastLoadedConversationId(convId)
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : '加载消息失败'
      setError(errorMsg)
      console.error('Failed to load messages:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  /**
   * 添加消息到列表
   */
  const addMessage = useCallback((message: Message) => {
    setMessages(prev => [...prev, message])
  }, [])

  /**
   * 更新消息
   */
  const updateMessage = useCallback(
    (messageId: number, updates: Partial<Message>) => {
      setMessages(prev =>
        prev.map(msg => (msg.id === messageId ? { ...msg, ...updates } : msg))
      )
    },
    []
  )

  /**
   * 清空消息列表
   */
  const clearMessages = useCallback(() => {
    setMessages([])
    setError(null)
  }, [])

  // 当会话 ID 变化时，加载消息
  useEffect(() => {
    if (conversationId === null) {
      // 切换到空会话，清空消息
      clearMessages()
      setLastLoadedConversationId(null)
    } else if (conversationId !== lastLoadedConversationId) {
      // 切换到不同的会话，直接加载消息
      loadMessages(conversationId)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [conversationId]) // 只依赖 conversationId

  return {
    messages,
    loading,
    error,
    loadMessages,
    addMessage,
    updateMessage,
    clearMessages,
  }
}
