import React, { useState } from 'react'
import { Sender } from '@ant-design/x'
import { App } from 'antd'
import styles from '../styles/index.module.css'

interface ChatSenderProps {
  onSend: (message: string) => void
  disabled?: boolean
  loading?: boolean
  className?: string
}

export const ChatSender: React.FC<ChatSenderProps> = ({
  onSend,
  disabled = false,
  loading = false,
  className = '',
}) => {
  const { message } = App.useApp()
  const [value, setValue] = useState('')

  const handleSubmit = () => {
    const trimmedValue = value.trim()
    
    if (!trimmedValue) {
      message.warning('请输入消息内容')
      return
    }

    onSend(trimmedValue)
    setValue('')
  }

  return (
    <div className={`${styles.senderContainer} ${className}`}>
      <div className={styles.senderWrapper}>
        <Sender
          value={value}
          onChange={(v) => setValue(v)}
          onSubmit={handleSubmit}
          loading={loading}
          disabled={disabled}
          placeholder="输入消息，Shift + Enter 换行，Enter 发送"
          style={{ width: '100%' }}
        />
      </div>
    </div>
  )
}
