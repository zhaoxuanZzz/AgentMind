/**
 * 会话列表管理 Hook
 */

import { useState, useEffect, useCallback } from 'react'
import { ChatAPI } from '../api/chatAPI'
import type { Conversation } from '../types/api'
import { useLocalStorage } from './useLocalStorage'

/** 会话列表状态 */
export interface UseConversationsState {
  /** 会话列表 */
  conversations: Conversation[]
  /** 当前选中的会话 ID */
  currentConversationId: number | null
  /** 是否正在加载 */
  loading: boolean
  /** 错误信息 */
  error: string | null
}

/** 会话列表操作 */
export interface UseConversationsActions {
  /** 加载会话列表 */
  loadConversations: () => Promise<void>
  /** 创建新会话 */
  createConversation: (title?: string) => Promise<Conversation | null>
  /** 删除会话 */
  deleteConversation: (id: number) => Promise<boolean>
  /** 切换会话 */
  switchConversation: (id: number | null) => void
  /** 更新会话标题 */
  updateConversationTitle: (id: number, title: string) => Promise<boolean>
  /** 刷新单个会话 */
  refreshConversation: (id: number) => Promise<void>
}

/** 会话列表 Hook 返回值 */
export type UseConversationsReturn = UseConversationsState & UseConversationsActions

/**
 * 会话列表管理 Hook
 */
export function useConversations(): UseConversationsReturn {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [currentConversationId, setCurrentConversationId] = useLocalStorage<number | null>(
    'current-conversation-id',
    null
  )
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  /**
   * 加载会话列表
   */
  const loadConversations = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await ChatAPI.getConversations()
      setConversations(response.conversations || [])
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : '加载会话列表失败'
      setError(errorMsg)
      console.error('Failed to load conversations:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  /**
   * 创建新会话
   */
  const createConversation = useCallback(
    async (title = '新对话'): Promise<Conversation | null> => {
      setError(null)

      try {
        const newConversation = await ChatAPI.createConversation({ title })
        setConversations(prev => [newConversation, ...prev])
        setCurrentConversationId(newConversation.id)
        return newConversation
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : '创建会话失败'
        setError(errorMsg)
        console.error('Failed to create conversation:', err)
        return null
      }
    },
    [setCurrentConversationId]
  )

  /**
   * 删除会话
   */
  const deleteConversation = useCallback(
    async (id: number): Promise<boolean> => {
      setError(null)

      try {
        await ChatAPI.deleteConversation(id)
        setConversations(prev => prev.filter(conv => conv.id !== id))

        // 如果删除的是当前会话，切换到第一个会话
        if (currentConversationId === id) {
          const remaining = conversations.filter(conv => conv.id !== id)
          setCurrentConversationId(remaining.length > 0 ? remaining[0].id : null)
        }

        return true
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : '删除会话失败'
        setError(errorMsg)
        console.error('Failed to delete conversation:', err)
        return false
      }
    },
    [conversations, currentConversationId, setCurrentConversationId]
  )

  /**
   * 切换会话
   */
  const switchConversation = useCallback(
    (id: number | null) => {
      setCurrentConversationId(id)
      setError(null)
    },
    [setCurrentConversationId]
  )

  /**
   * 更新会话标题
   */
  const updateConversationTitle = useCallback(
    async (id: number, title: string): Promise<boolean> => {
      setError(null)

      try {
        const updated = await ChatAPI.updateConversationTitle(id, title)
        setConversations(prev =>
          prev.map(conv => (conv.id === id ? updated : conv))
        )
        return true
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : '更新会话标题失败'
        setError(errorMsg)
        console.error('Failed to update conversation title:', err)
        return false
      }
    },
    []
  )

  /**
   * 刷新单个会话
   */
  const refreshConversation = useCallback(async (id: number) => {
    setError(null)

    try {
      const response = await ChatAPI.getConversation(id)
      setConversations(prev =>
        prev.map(conv => (conv.id === id ? response.conversation : conv))
      )
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : '刷新会话失败'
      setError(errorMsg)
      console.error('Failed to refresh conversation:', err)
    }
  }, [])

  // 组件挂载时加载会话列表
  useEffect(() => {
    loadConversations()
  }, [loadConversations])

  return {
    conversations,
    currentConversationId,
    loading,
    error,
    loadConversations,
    createConversation,
    deleteConversation,
    switchConversation,
    updateConversationTitle,
    refreshConversation,
  }
}
