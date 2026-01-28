import React from 'react'
import { Button, Empty, Skeleton } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import { ConversationItem } from './ConversationItem'
import type { Conversation } from '../../../../types/api'
import styles from '../../styles/index.module.css'

interface ConversationSidebarProps {
  conversations: Conversation[]
  currentId: number | null
  loading?: boolean
  onSelect: (id: number) => void
  onCreate: () => void
  onDelete: (id: number) => void
  onRename: (id: number, title: string) => void
  className?: string
}

export const ConversationSidebar: React.FC<ConversationSidebarProps> = ({
  conversations,
  currentId,
  loading = false,
  onSelect,
  onCreate,
  onDelete,
  onRename,
  className = '',
}) => {
  return (
    <div className={`${styles.sidebar} ${className}`}>
      <div style={{ padding: '16px 12px' }}>
        <Button 
          type="primary" 
          icon={<PlusOutlined />} 
          block 
          onClick={onCreate}
          style={{ height: 40, borderRadius: 8 }}
        >
          新建对话
        </Button>
      </div>
      
      <div style={{ flex: 1, overflowY: 'auto', padding: '0 12px 12px' }}>
        {loading && conversations.length === 0 ? (
          <div style={{ padding: '0 8px' }}>
            <Skeleton active paragraph={{ rows: 2 }} title={false} style={{ marginBottom: 16 }} />
            <Skeleton active paragraph={{ rows: 2 }} title={false} style={{ marginBottom: 16 }} />
            <Skeleton active paragraph={{ rows: 2 }} title={false} style={{ marginBottom: 16 }} />
          </div>
        ) : conversations.length === 0 ? (
          <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无历史对话" />
        ) : (
          conversations.map(conv => (
            <ConversationItem
              key={conv.id}
              conversation={conv}
              active={conv.id === currentId}
              onClick={() => onSelect(conv.id)}
              onDelete={onDelete}
              onRename={onRename}
            />
          ))
        )}
      </div>
    </div>
  )
}
