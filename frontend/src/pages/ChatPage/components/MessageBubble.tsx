import React from 'react'
import { Bubble } from '@ant-design/x'
import { UserOutlined, CopyOutlined, SyncOutlined } from '@ant-design/icons'
import { Button, Tooltip, App, Avatar } from 'antd'
import { MarkdownRenderer } from '../../../components/MarkdownRenderer'
import { StreamingText } from '../../../components/StreamingText'
import ThinkingSection from './ThinkingSection'
import ToolCallsDisplay from './ToolCallsDisplay'
import type { Message } from '../../../types/api'
import type { StreamingMessage } from '../../../types/stream'
import { motion } from 'framer-motion'
import { fadeInUp } from '../../../utils/animations'
import { formatTime } from '../../../utils/format'
import { useResponsive } from '../../../hooks/useResponsive'

interface MessageBubbleProps {
  message: Message | StreamingMessage
  isStreaming?: boolean
}

export const MessageBubble: React.FC<MessageBubbleProps> = React.memo(({
  message,
  isStreaming = false,
}) => {
  const { message: antdMessage } = App.useApp()
  const { isMobile } = useResponsive()
  
  const isUser = message.role === 'user'
  
  // 复制内容
  const handleCopy = () => {
    navigator.clipboard.writeText(message.content)
    antdMessage.success('已复制到剪贴板')
  }

  // 渲染头像
  const renderAvatar = () => {
    if (isUser) {
      return (
        <Avatar 
          icon={<UserOutlined />} 
          style={{ backgroundColor: '#87d068' }}
        />
      )
    }
    return (
      <Avatar 
        src="/logo.png" 
        alt="AI"
        style={{ backgroundColor: '#1677ff' }}
      >
        AI
      </Avatar>
    )
  }

  // 渲染 Content
  const renderContent = () => {
    if (isUser) {
      return <MarkdownRenderer content={message.content || ''} />
    }

    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8, minWidth: 200 }}>
        {/* Thinking Process */}
        {message.thinking && (
           <ThinkingSection 
             content={message.thinking} 
             isStreaming={isStreaming && !message.content && !message.intermediate_steps?.length} 
           />
        )}

        {/* Tool Calls */}
        {message.intermediate_steps && message.intermediate_steps.length > 0 && (
           <ToolCallsDisplay toolCalls={message.intermediate_steps} />
        )}

        {/* Main Content */}
        {(message.content || isStreaming) && (
           <div className={isStreaming ? 'streaming-content' : ''}>
             {isStreaming ? (
                <StreamingText content={message.content || ''} />
             ) : (
                <MarkdownRenderer content={message.content || ''} />
             )}
           </div>
        )}
      </div>
    )
  }

  // 渲染页脚
  const renderFooter = () => (
    <div style={{ 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: isUser ? 'flex-end' : 'flex-start',
      gap: 8, 
      marginTop: 4, 
      color: 'rgba(0, 0, 0, 0.45)', 
      fontSize: 12 
    }}>
      {isStreaming && <SyncOutlined spin />}
      <span>{isUser ? 'You' : 'Assistant'}</span>
      <span>{formatTime('created_at' in message ? message.created_at : new Date().toISOString())}</span>
      {!isStreaming && (
        <Tooltip title="复制">
          <Button 
            type="text" 
            size="small" 
            icon={<CopyOutlined />} 
            onClick={handleCopy}
            style={{ padding: 0, height: 'auto', color: 'inherit' }}
          />
        </Tooltip>
      )}
    </div>
  )

  return (
    <motion.div
      initial="initial"
      animate="animate"
      variants={fadeInUp}
      style={{
        marginBottom: 16,
        maxWidth: isMobile ? '95%' : '85%',
        alignSelf: isUser ? 'flex-end' : 'flex-start',
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        width: '100%',
      }}
    >
      <Bubble
        content={renderContent()}
        placement={isUser ? 'end' : 'start'}
        avatar={renderAvatar()}
        loading={isStreaming && !message.content && !message.thinking && (!message.intermediate_steps || message.intermediate_steps.length === 0)}
        variant={isUser ? 'shadow' : 'filled'}
        footer={renderFooter()}
        styles={{
          content: {
            borderRadius: 12,
            maxWidth: '100%',
            backgroundColor: isUser ? '#e6f4ff' : '#ffffff',
            boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
          }
        }}
        style={{
          maxWidth: '100%',
        }}
      />
    </motion.div>
  )
})
