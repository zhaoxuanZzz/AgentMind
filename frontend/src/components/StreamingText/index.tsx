/**
 * 流式文本组件
 * 显示打字机光标效果
 */

import React, { useEffect, useState } from 'react'
import { MarkdownRenderer } from '../MarkdownRenderer'
import './index.css'

export interface StreamingTextProps {
  /** 文本内容 */
  content: string
  /** 是否正在流式传输 */
  isStreaming?: boolean
  /** 是否渲染为 Markdown */
  markdown?: boolean
  /** 自定义类名 */
  className?: string
}

/**
 * 流式文本组件
 */
export const StreamingText: React.FC<StreamingTextProps> = ({
  content,
  isStreaming = false,
  markdown = true,
  className = '',
}) => {
  const [showCursor, setShowCursor] = useState(isStreaming)

  // 光标闪烁效果
  useEffect(() => {
    if (!isStreaming) {
      setShowCursor(false)
      return
    }

    setShowCursor(true)
    const interval = setInterval(() => {
      setShowCursor(prev => !prev)
    }, 530) // 光标闪烁间隔

    return () => clearInterval(interval)
  }, [isStreaming])

  if (!content && !isStreaming) {
    return null
  }

  return (
    <div className={`streaming-text ${className}`}>
      {markdown ? (
        <MarkdownRenderer content={content} />
      ) : (
        <span className="streaming-text-plain">{content}</span>
      )}
      {isStreaming && (
        <span className={`streaming-cursor ${showCursor ? 'visible' : ''}`}>
          ▋
        </span>
      )}
    </div>
  )
}
