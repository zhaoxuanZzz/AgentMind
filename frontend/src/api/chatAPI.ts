/**
 * 聊天 API 客户端
 * 处理会话管理和消息获取
 */

import apiClient from './client'
import type {
  Conversation,
  Message,
  GetConversationsRequest,
  GetConversationsResponse,
  GetConversationResponse,
  ConversationCreate,
  ApiResponse,
} from '../types/api'

/** 后端返回的会话详情（包含messages） */
interface ConversationResponse {
  id: number
  title: string
  created_at: string
  updated_at: string
  messages: Message[]
}

/**
 * 聊天 API 类
 */
export class ChatAPI {
  /**
   * 获取会话列表
   */
  static async getConversations(
    params?: GetConversationsRequest
  ): Promise<GetConversationsResponse> {
    const conversations = await apiClient.get('/chat/conversations', { params }) as Conversation[]
    return { conversations }
  }

  /**
   * 获取会话详情
   */
  static async getConversation(
    conversationId: number
  ): Promise<GetConversationResponse> {
    const data = await apiClient.get(`/chat/conversations/${conversationId}`) as ConversationResponse
    // 后端返回的 ConversationResponse 包含 messages，需要转换为前端期望的格式
    return {
      conversation: {
        id: data.id,
        title: data.title,
        created_at: data.created_at,
        updated_at: data.updated_at,
      },
      messages: data.messages || [],
    }
  }

  /**
   * 创建新会话
   */
  static async createConversation(
    data: ConversationCreate
  ): Promise<Conversation> {
    return apiClient.post('/chat/conversations', data)
  }

  /**
   * 删除会话
   */
  static async deleteConversation(
    conversationId: number
  ): Promise<ApiResponse> {
    return apiClient.delete(`/chat/conversations/${conversationId}`)
  }

  /**
   * 更新会话标题
   */
  static async updateConversationTitle(
    conversationId: number,
    title: string
  ): Promise<Conversation> {
    return apiClient.patch(`/chat/conversations/${conversationId}`, { title })
  }

  /**
   * 获取会话的消息列表
   */
  static async getMessages(conversationId: number): Promise<Message[]> {
    const response = await this.getConversation(conversationId)
    return response.messages
  }
}
