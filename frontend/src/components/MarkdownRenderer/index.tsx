/**
 * Markdown 渲染组件
 * 支持代码高亮、表格、列表等
 */

import React from 'react'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism'
import type { Components } from 'react-markdown'
import './index.css'

export interface MarkdownRendererProps {
  /** Markdown 内容 */
  content: string
  /** 自定义类名 */
  className?: string
}

/**
 * Markdown 渲染组件
 */
export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({
  content,
  className = '',
}) => {
  const components: Components = {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    code({ className, children, ref, ...props }) {
      const match = /language-(\w+)/.exec(className || '')
      const language = match ? match[1] : ''
      const isInline = !language

      return !isInline && language ? (
        <SyntaxHighlighter
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          style={oneLight as any}
          language={language}
          PreTag="div"
          {...props}
        >
          {String(children).replace(/\n$/, '')}
        </SyntaxHighlighter>
      ) : (
        <code className={className} {...props}>
          {children}
        </code>
      )
    },
  }

  return (
    <div className={`markdown-renderer ${className}`}>
      <ReactMarkdown components={components}>{content}</ReactMarkdown>
    </div>
  )
}
