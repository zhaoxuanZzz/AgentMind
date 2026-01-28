import React, { useState } from 'react'
import { Button, Drawer } from 'antd'
import { MenuOutlined } from '@ant-design/icons'
import { motion } from 'framer-motion'
import { MessageList } from './components/MessageList'
import { ChatSender } from './components/ChatSender'
import { ConversationSidebar } from './components/ConversationSidebar'
import { PlanModeToggle } from '../../components/PlanModeToggle'
import { RoleSelector } from '../../components/RoleSelector'
import { useConversations } from '../../hooks/useConversations'
import { useConversationMessages } from '../../hooks/useConversationMessages'
import { useStreamChat } from '../../hooks/useStreamChat'
import { useResponsive } from '../../hooks/useResponsive'
import { usePlanMode } from '../../hooks/usePlanMode'
import { useRolePreset } from '../../hooks/useRolePreset'
import { fadeIn } from '../../utils/animations'
import type { Message } from '../../types/api'
import styles from './styles/index.module.css'

const ChatPage: React.FC = () => {
  const { isMobile } = useResponsive()
  const [drawerVisible, setDrawerVisible] = useState(false)
  
  // 计划模式状态
  const { enabled: planModeEnabled, setEnabled: setPlanModeEnabled } = usePlanMode()
  
  // 会话列表管理
  const { 
    conversations, 
    currentConversationId, 
    loading: loadingConversations,
    createConversation, 
    deleteConversation, 
    switchConversation,
    updateConversationTitle,
    refreshConversation
  } = useConversations()

  // 角色预设状态（在currentConversationId之后使用）
  const { 
    roles, 
    currentRoleId, 
    setRole,
    loading: rolesLoading 
  } = useRolePreset({ 
    conversationId: currentConversationId 
  })

  // 消息列表管理
  const { 
    messages, 
    loadMessages, 
    addMessage, 
    // loading: loadingMessages // 暂时未使用，可用于 Loading 状态展示
  } = useConversationMessages(currentConversationId)

  // 流式对话管理
  const { 
    streamingMessage, 
    isStreaming, 
    sendMessage,
    clearStreamingMessage 
  } = useStreamChat({
    onComplete: async () => {
      // 对话完成后刷新消息列表以获取持久化的消息
      if (currentConversationId) {
        await loadMessages(currentConversationId)
        refreshConversation(currentConversationId)
        // loadMessages 完成后立即清空流式消息，因为服务器消息已经包含完整数据
        clearStreamingMessage()
      }
    }
  })

  // 处理发送消息
  const handleSend = async (content: string) => {
    let conversationId = currentConversationId

    // 1. 如果没有当前会话，先创建一个
    if (!conversationId) {
      // 使用消息前10个字符作为标题
      const title = content.slice(0, 20) || '新对话'
      const newConv = await createConversation(title)
      if (newConv) {
        conversationId = newConv.id
      } else {
        return // 创建失败
      }
    }

    // 2. 乐观更新：立即将用户消息添加到列表
    const optimisticUserMessage: Message = {
      id: Date.now(), // 临时 ID
      conversation_id: conversationId,
      role: 'user',
      content: content,
      created_at: new Date().toISOString()
    }
    addMessage(optimisticUserMessage)

    // 3. 发送请求，包含plan_mode和role_id参数
    await sendMessage({
      message: content,
      conversation_id: conversationId,
      plan_mode: planModeEnabled,  // 传递计划模式状态
      role_id: currentRoleId || undefined  // 传递角色ID
    })
  }

  // 处理新建会话
  const handleCreateConversation = () => {
    switchConversation(null)
    if (isMobile) {
      setDrawerVisible(false)
    }
  }

  // 处理选择会话
  const handleSelectConversation = (id: number) => {
    switchConversation(id)
    if (isMobile) {
      setDrawerVisible(false)
    }
  }

  // 侧边栏内容
  const sidebarContent = (
    <ConversationSidebar
      conversations={conversations}
      currentId={currentConversationId}
      loading={loadingConversations}
      onSelect={handleSelectConversation}
      onCreate={handleCreateConversation}
      onDelete={deleteConversation}
      onRename={updateConversationTitle}
    />
  )

  return (
    <motion.div 
      className={styles.container}
      initial="initial"
      animate="animate"
      exit="exit"
      variants={fadeIn}
    >
      {/* 桌面端侧边栏 */}
      {!isMobile && sidebarContent}

      {/* 移动端侧边栏 Drawer */}
      <Drawer
        placement="left"
        onClose={() => setDrawerVisible(false)}
        open={drawerVisible}
        styles={{ body: { padding: 0 } }}
        width={280}
      >
        {sidebarContent}
      </Drawer>

      {/* 主聊天区域 */}
      <div className={styles.main}>
        {/* 移动端头部 Toggle */}
        {isMobile && (
          <div style={{ 
            padding: '12px 16px', 
            borderBottom: '1px solid var(--border-color)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            backgroundColor: 'var(--bg-primary)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <Button 
                type="text" 
                icon={<MenuOutlined />} 
                onClick={() => setDrawerVisible(true)} 
              />
              <span style={{ marginLeft: 12, fontWeight: 500 }}>
                {currentConversationId 
                  ? conversations.find(c => c.id === currentConversationId)?.title 
                  : '新对话'}
              </span>
            </div>
            <PlanModeToggle 
              enabled={planModeEnabled}
              onChange={setPlanModeEnabled}
            />
          </div>
        )}

        {/* 消息列表 */}
        <MessageList 
          messages={messages} 
          streamingMessage={streamingMessage} 
          isStreaming={isStreaming}
          onSelectPrompt={handleSend}
        />

        {/* 输入区域 */}
        <div>
          {/* 桌面端计划模式切换 */}
          {!isMobile && (
            <div style={{ 
              padding: '8px 16px',
              borderTop: '1px solid var(--border-color)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <RoleSelector 
                roles={roles}
                value={currentRoleId || undefined}
                onChange={setRole}
                loading={rolesLoading}
              />
              <PlanModeToggle 
                enabled={planModeEnabled}
                onChange={setPlanModeEnabled}
              />
            </div>
          )}
          <ChatSender 
            onSend={handleSend} 
            loading={isStreaming} 
          />
        </div>
      </div>
    </motion.div>
  )
}

export default ChatPage
