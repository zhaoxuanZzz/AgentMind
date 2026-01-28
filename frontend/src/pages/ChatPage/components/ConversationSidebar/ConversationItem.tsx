import React, { useState, useRef, useEffect } from 'react'
import { Button, Input, Dropdown, Modal, Typography, type MenuProps } from 'antd'
import { 
  MessageOutlined, 
  MoreOutlined, 
  EditOutlined, 
  DeleteOutlined,
  CheckOutlined,
  CloseOutlined 
} from '@ant-design/icons'
import type { Conversation } from '../../../../types/api'

interface ConversationItemProps {
  conversation: Conversation
  active: boolean
  onClick: () => void
  onDelete: (id: number) => void
  onRename: (id: number, title: string) => void
}

export const ConversationItem: React.FC<ConversationItemProps> = React.memo(({
  conversation,
  active,
  onClick,
  onDelete,
  onRename,
}) => {
  const [isEditing, setIsEditing] = useState(false)
  const [editTitle, setEditTitle] = useState(conversation.title)
  const inputRef = useRef<any>(null)

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus()
    }
  }, [isEditing])

  useEffect(() => {
    setEditTitle(conversation.title)
  }, [conversation.title])

  const handleSave = (e: React.MouseEvent | React.KeyboardEvent) => {
    e.stopPropagation()
    const newTitle = editTitle.trim()
    if (newTitle && newTitle !== conversation.title) {
      onRename(conversation.id, newTitle)
    } else {
      setEditTitle(conversation.title)
    }
    setIsEditing(false)
  }

  const handleCancel = (e: React.MouseEvent | React.KeyboardEvent) => {
    e.stopPropagation()
    setEditTitle(conversation.title)
    setIsEditing(false)
  }

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation()
    // 使用 Modal 确认
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个会话吗？此操作不可恢复。',
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: () => onDelete(conversation.id),
    })
  }

  const menuItems: MenuProps['items'] = [
    {
      key: 'rename',
      label: '重命名',
      icon: <EditOutlined />,
      onClick: ({ domEvent }) => {
        domEvent.stopPropagation()
        setIsEditing(true)
      }
    },
    {
      key: 'delete',
      label: '删除',
      icon: <DeleteOutlined />,
      danger: true,
      onClick: ({ domEvent }) => handleDelete(domEvent as unknown as React.MouseEvent)
    }
  ]

  return (
    <div
      onClick={onClick}
      style={{
        display: 'flex',
        alignItems: 'center',
        padding: '10px 12px',
        cursor: 'pointer',
        borderRadius: 8,
        backgroundColor: active ? 'var(--primary-color-light)' : 'transparent',
        color: active ? 'var(--primary-color)' : 'var(--text-primary)',
        marginBottom: 4,
        transition: 'all 0.2s',
      }}
      className="conversation-item"
    >
      <MessageOutlined style={{ marginRight: 12, flexShrink: 0 }} />
      
      {isEditing ? (
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 4 }}>
          <Input
            ref={inputRef}
            size="small"
            value={editTitle}
            onChange={(e) => setEditTitle(e.target.value)}
            onPressEnter={handleSave}
            onClick={(e) => e.stopPropagation()}
          />
          <Button 
            size="small" 
            type="text" 
            icon={<CheckOutlined />} 
            onClick={handleSave} 
            style={{ color: 'var(--success-color)' }}
          />
          <Button 
            size="small" 
            type="text" 
            icon={<CloseOutlined />} 
            onClick={handleCancel} 
            style={{ color: 'var(--text-tertiary)' }}
          />
        </div>
      ) : (
        <>
          <Typography.Text 
            ellipsis 
            style={{ 
              flex: 1, 
              color: 'inherit',
              fontSize: 14 
            }}
          >
            {conversation.title}
          </Typography.Text>
          
          <div className="actions" onClick={e => e.stopPropagation()}>
            <Dropdown menu={{ items: menuItems }} trigger={['click']}>
              <Button 
                type="text" 
                size="small" 
                icon={<MoreOutlined />} 
                style={{ 
                  color: 'inherit',
                  opacity: active ? 1 : 0.6 
                }}
              />
            </Dropdown>
          </div>
        </>
      )}
    </div>
  )
})
