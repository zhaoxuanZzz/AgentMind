import React, { useEffect, useRef } from 'react'
import { Prompts } from '@ant-design/x'
import { RocketOutlined, BuildOutlined, BulbOutlined } from '@ant-design/icons'
import { MessageBubble } from './MessageBubble'
import MessageRenderer from '../../../components/MessageRenderer'
import type { Message } from '../../../types/api'
import type { StreamingMessage } from '../../../types/stream'
import type { AnyMessageChunk } from '../../../types/messageTypes'
import styles from '../styles/index.module.css'

interface MessageListProps {
  messages: Message[]
  streamingMessage: StreamingMessage | null
  isStreaming?: boolean
  className?: string
  onSelectPrompt?: (message: string) => void
}

export const MessageList: React.FC<MessageListProps> = ({
  messages,
  streamingMessage,
  isStreaming = false,
  className = '',
  onSelectPrompt
}) => {
  const bottomRef = useRef<HTMLDivElement>(null)
  
  // 自动滚动到底部
  const scrollToBottom = (behavior: ScrollBehavior = 'smooth') => {
    bottomRef.current?.scrollIntoView({ behavior })
  }

  // 当消息列表更新时滚动
  useEffect(() => {
    scrollToBottom()
  }, [messages.length, streamingMessage])

  // 初始加载时立即滚动
  useEffect(() => {
    scrollToBottom('auto')
  }, [])
  
  // 空状态提示
  if (messages.length === 0 && !streamingMessage) {
    return (
      <div className={`${styles.messageListContainer} ${className}`} style={{ justifyContent: 'center', alignItems: 'center' }}>
        <div style={{ maxWidth: 800, width: '100%', padding: 24 }}>
          <Prompts
            title="欢迎使用 AgentSystem"
            style={{
              '--prompts-item-color': '#1f1f1f',
              '--prompts-description-color': '#666666',
            } as React.CSSProperties}
            items={[
              {
                key: '1',
                icon: <RocketOutlined style={{ color: '#1677ff' }} />,
                label: '写一个 React 倒计时组件',
                description: '包含开始、暂停、重置功能',
              },
              {
                key: '2',
                icon: <BuildOutlined style={{ color: '#1677ff' }} />,
                label: '解释深拷贝和浅拷贝的区别',
                description: '使用 JavaScript 示例代码说明',
              },
              {
                key: '3',
                icon: <BulbOutlined style={{ color: '#1677ff' }} />,
                label: '分析一下当前 AI 发展的趋势',
                description: '从模型能力和应用场景两个角度',
              },
            ]}
            onItemClick={(info) => {
              if (onSelectPrompt) {
                onSelectPrompt(info.data.label as string)
              }
            }}
          />
        </div>
      </div>
    )
  }

  return (
    <div className={`${styles.messageListContainer} ${className}`}>
      {messages.map((msg) => {
        // 如果消息有chunks字段，使用MessageRenderer；否则使用旧的MessageBubble
        const hasChunks = msg.chunks && Array.isArray(msg.chunks) && msg.chunks.length > 0
        
        if (hasChunks) {
          return (
            <div key={msg.id} style={{ marginBottom: 16 }}>
              <div style={{ 
                fontSize: 12, 
                color: '#999', 
                marginBottom: 8,
                textAlign: msg.role === 'user' ? 'right' : 'left'
              }}>
                {msg.role === 'user' ? '你' : 'AI'}
              </div>
              <MessageRenderer 
                chunks={msg.chunks as AnyMessageChunk[]} 
                role={msg.role as 'user' | 'assistant'}
              />
            </div>
          )
        } else {
          return <MessageBubble key={msg.id} message={msg} />
        }
      })}
      
      {streamingMessage && (
        <MessageBubble 
          key="streaming" 
          message={streamingMessage} 
          isStreaming={isStreaming} 
        />
      )}
      
      <div ref={bottomRef} style={{ height: 1 }} />
    </div>
  )
}
