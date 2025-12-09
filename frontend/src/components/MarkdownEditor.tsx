import React, { useState, useEffect, useRef } from 'react'
import { Input, Button, Tooltip, Divider } from 'antd'
import {
  BoldOutlined,
  ItalicOutlined,
  StrikethroughOutlined,
  CodeOutlined,
  LinkOutlined,
  PictureOutlined,
  UnorderedListOutlined,
  OrderedListOutlined,
  FileTextOutlined,
  MinusOutlined,
  TableOutlined,
  FontSizeOutlined,
} from '@ant-design/icons'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'
import './MarkdownEditor.css'

const { TextArea } = Input

interface MarkdownEditorProps {
  value?: string
  onChange?: (value: string) => void
  placeholder?: string
  rows?: number
}

const MarkdownEditor = ({ value = '', onChange, placeholder, rows = 10 }: MarkdownEditorProps) => {
  const [content, setContent] = useState(value || '')
  const textareaRef = useRef<any>(null)

  useEffect(() => {
    if (value !== undefined) {
      setContent(value)
    }
  }, [value])

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = e.target.value
    setContent(newValue)
    onChange?.(newValue)
  }

  // 插入文本到光标位置
  const insertText = (before: string, after: string = '', placeholder: string = '') => {
    // 获取textarea元素
    let textarea: HTMLTextAreaElement | null = null
    if (textareaRef.current) {
      // Ant Design TextArea的结构
      if (textareaRef.current.resizableTextArea?.textArea) {
        textarea = textareaRef.current.resizableTextArea.textArea
      } else if (textareaRef.current instanceof HTMLTextAreaElement) {
        textarea = textareaRef.current
      }
    }

    if (!textarea) {
      // 如果无法获取textarea，直接插入到内容末尾
      const textToInsert = placeholder
      const newContent = content + before + textToInsert + after
      setContent(newContent)
      onChange?.(newContent)
      return
    }

    const start = textarea.selectionStart
    const end = textarea.selectionEnd
    const selectedText = content.substring(start, end)
    const textToInsert = selectedText || placeholder

    const newContent = 
      content.substring(0, start) + 
      before + textToInsert + after + 
      content.substring(end)

    setContent(newContent)
    onChange?.(newContent)

    // 设置光标位置
    setTimeout(() => {
      const newCursorPos = start + before.length + textToInsert.length + after.length
      textarea?.focus()
      textarea?.setSelectionRange(newCursorPos, newCursorPos)
    }, 0)
  }

  // 插入标题
  const insertHeading = (level: number) => {
    const prefix = '#'.repeat(level) + ' '
    insertText(prefix, '', '标题')
  }

  // 插入加粗
  const insertBold = () => {
    insertText('**', '**', '加粗文本')
  }

  // 插入斜体
  const insertItalic = () => {
    insertText('*', '*', '斜体文本')
  }

  // 插入删除线
  const insertStrikethrough = () => {
    insertText('~~', '~~', '删除文本')
  }

  // 插入行内代码
  const insertInlineCode = () => {
    insertText('`', '`', '代码')
  }

  // 插入代码块
  const insertCodeBlock = () => {
    const textarea = textareaRef.current?.resizableTextArea?.textArea || textareaRef.current
    if (!textarea) {
      const newContent = content + '\n```\n代码块\n```\n'
      setContent(newContent)
      onChange?.(newContent)
      return
    }
    
    const start = textarea.selectionStart
    const end = textarea.selectionEnd
    const beforeText = content.substring(0, start)
    const afterText = content.substring(end)
    const needsNewlineBefore = beforeText.length > 0 && !beforeText.endsWith('\n')
    const needsNewlineAfter = afterText.length > 0 && !afterText.startsWith('\n')
    
    const newContent = 
      beforeText + 
      (needsNewlineBefore ? '\n' : '') +
      '```\n代码块\n```' +
      (needsNewlineAfter ? '\n' : '') +
      afterText

    setContent(newContent)
    onChange?.(newContent)

    setTimeout(() => {
      const newCursorPos = start + (needsNewlineBefore ? 1 : 0) + 4 // 4 = ```\n的长度
      textarea.focus()
      textarea.setSelectionRange(newCursorPos, newCursorPos + 3) // 选中"代码块"
    }, 0)
  }

  // 插入链接
  const insertLink = () => {
    insertText('[', '](url)', '链接文本')
  }

  // 插入图片
  const insertImage = () => {
    insertText('![', '](url)', '图片描述')
  }

  // 插入无序列表
  const insertUnorderedList = () => {
    const textarea = textareaRef.current?.resizableTextArea?.textArea || textareaRef.current
    if (!textarea) {
      insertText('- ', '', '列表项')
      return
    }
    
    const start = textarea.selectionStart
    const end = textarea.selectionEnd
    const beforeText = content.substring(0, start)
    const needsNewlineBefore = beforeText.length > 0 && !beforeText.endsWith('\n')
    
    insertText((needsNewlineBefore ? '\n' : '') + '- ', '', '列表项')
  }

  // 插入有序列表
  const insertOrderedList = () => {
    const textarea = textareaRef.current?.resizableTextArea?.textArea || textareaRef.current
    if (!textarea) {
      insertText('1. ', '', '列表项')
      return
    }
    
    const start = textarea.selectionStart
    const beforeText = content.substring(0, start)
    const needsNewlineBefore = beforeText.length > 0 && !beforeText.endsWith('\n')
    
    insertText((needsNewlineBefore ? '\n' : '') + '1. ', '', '列表项')
  }

  // 插入引用
  const insertQuote = () => {
    const textarea = textareaRef.current?.resizableTextArea?.textArea || textareaRef.current
    if (!textarea) {
      insertText('> ', '', '引用内容')
      return
    }
    
    const start = textarea.selectionStart
    const beforeText = content.substring(0, start)
    const needsNewlineBefore = beforeText.length > 0 && !beforeText.endsWith('\n')
    
    insertText((needsNewlineBefore ? '\n' : '') + '> ', '', '引用内容')
  }

  // 插入分隔线
  const insertHorizontalRule = () => {
    const textarea = textareaRef.current?.resizableTextArea?.textArea || textareaRef.current
    if (!textarea) {
      const newContent = content + '\n---\n'
      setContent(newContent)
      onChange?.(newContent)
      return
    }
    
    const start = textarea.selectionStart
    const end = textarea.selectionEnd
    const beforeText = content.substring(0, start)
    const afterText = content.substring(end)
    const needsNewlineBefore = beforeText.length > 0 && !beforeText.endsWith('\n')
    const needsNewlineAfter = afterText.length > 0 && !afterText.startsWith('\n')
    
    const newContent = 
      beforeText + 
      (needsNewlineBefore ? '\n' : '') +
      '---' +
      (needsNewlineAfter ? '\n' : '') +
      afterText

    setContent(newContent)
    onChange?.(newContent)

    setTimeout(() => {
      const newCursorPos = start + (needsNewlineBefore ? 1 : 0) + 3 + (needsNewlineAfter ? 1 : 0)
      textarea.focus()
      textarea.setSelectionRange(newCursorPos, newCursorPos)
    }, 0)
  }

  // 插入表格
  const insertTable = () => {
    const textarea = textareaRef.current?.resizableTextArea?.textArea || textareaRef.current
    if (!textarea) {
      const tableText = '\n| 列1 | 列2 | 列3 |\n| --- | --- | --- |\n| 内容1 | 内容2 | 内容3 |\n'
      const newContent = content + tableText
      setContent(newContent)
      onChange?.(newContent)
      return
    }
    
    const start = textarea.selectionStart
    const end = textarea.selectionEnd
    const beforeText = content.substring(0, start)
    const afterText = content.substring(end)
    const needsNewlineBefore = beforeText.length > 0 && !beforeText.endsWith('\n')
    
    const tableText = (needsNewlineBefore ? '\n' : '') + 
      '| 列1 | 列2 | 列3 |\n' +
      '| --- | --- | --- |\n' +
      '| 内容1 | 内容2 | 内容3 |\n'
    
    const newContent = beforeText + tableText + afterText
    setContent(newContent)
    onChange?.(newContent)

    setTimeout(() => {
      const newCursorPos = start + (needsNewlineBefore ? 1 : 0) + 2 // 定位到第一行末尾
      textarea.focus()
      textarea.setSelectionRange(newCursorPos, newCursorPos)
    }, 0)
  }

  // 配置 markdown-it（使用useMemo优化性能）
  const md = React.useMemo(() => {
    return new MarkdownIt({
      html: true,
      linkify: true,
      typographer: true,
      highlight: function (str, lang) {
        if (lang && hljs.getLanguage(lang)) {
          try {
            return hljs.highlight(str, { language: lang }).value
          } catch (__) {}
        }
        return ''
      }
    })
  }, [])

  const htmlContent = React.useMemo(() => {
    return md.render(content || '')
  }, [content, md])

  return (
    <div className="markdown-editor-wrapper">
      {/* 工具栏 */}
      <div className="markdown-toolbar">
        <div className="toolbar-group">
          <Tooltip title="标题1">
            <Button 
              type="text" 
              icon={<FontSizeOutlined />} 
              onClick={() => insertHeading(1)}
              className="toolbar-btn"
            >
              H1
            </Button>
          </Tooltip>
          <Tooltip title="标题2">
            <Button 
              type="text" 
              icon={<FontSizeOutlined />} 
              onClick={() => insertHeading(2)}
              className="toolbar-btn"
            >
              H2
            </Button>
          </Tooltip>
          <Tooltip title="标题3">
            <Button 
              type="text" 
              icon={<FontSizeOutlined />} 
              onClick={() => insertHeading(3)}
              className="toolbar-btn"
            >
              H3
            </Button>
          </Tooltip>
        </div>

        <Divider type="vertical" style={{ height: '24px', margin: '0 4px' }} />

        <div className="toolbar-group">
          <Tooltip title="加粗">
            <Button 
              type="text" 
              icon={<BoldOutlined />} 
              onClick={insertBold}
              className="toolbar-btn"
            />
          </Tooltip>
          <Tooltip title="斜体">
            <Button 
              type="text" 
              icon={<ItalicOutlined />} 
              onClick={insertItalic}
              className="toolbar-btn"
            />
          </Tooltip>
          <Tooltip title="删除线">
            <Button 
              type="text" 
              icon={<StrikethroughOutlined />} 
              onClick={insertStrikethrough}
              className="toolbar-btn"
            />
          </Tooltip>
        </div>

        <Divider type="vertical" style={{ height: '24px', margin: '0 4px' }} />

        <div className="toolbar-group">
          <Tooltip title="行内代码">
            <Button 
              type="text" 
              icon={<CodeOutlined />} 
              onClick={insertInlineCode}
              className="toolbar-btn"
            />
          </Tooltip>
          <Tooltip title="代码块">
            <Button 
              type="text" 
              onClick={insertCodeBlock}
              className="toolbar-btn"
            >
              ```
            </Button>
          </Tooltip>
        </div>

        <Divider type="vertical" style={{ height: '24px', margin: '0 4px' }} />

        <div className="toolbar-group">
          <Tooltip title="链接">
            <Button 
              type="text" 
              icon={<LinkOutlined />} 
              onClick={insertLink}
              className="toolbar-btn"
            />
          </Tooltip>
          <Tooltip title="图片">
            <Button 
              type="text" 
              icon={<PictureOutlined />} 
              onClick={insertImage}
              className="toolbar-btn"
            />
          </Tooltip>
        </div>

        <Divider type="vertical" style={{ height: '24px', margin: '0 4px' }} />

        <div className="toolbar-group">
          <Tooltip title="无序列表">
            <Button 
              type="text" 
              icon={<UnorderedListOutlined />} 
              onClick={insertUnorderedList}
              className="toolbar-btn"
            />
          </Tooltip>
          <Tooltip title="有序列表">
            <Button 
              type="text" 
              icon={<OrderedListOutlined />} 
              onClick={insertOrderedList}
              className="toolbar-btn"
            />
          </Tooltip>
          <Tooltip title="引用">
            <Button 
              type="text" 
              icon={<FileTextOutlined />} 
              onClick={insertQuote}
              className="toolbar-btn"
            />
          </Tooltip>
        </div>

        <Divider type="vertical" style={{ height: '24px', margin: '0 4px' }} />

        <div className="toolbar-group">
          <Tooltip title="分隔线">
            <Button 
              type="text" 
              icon={<MinusOutlined />} 
              onClick={insertHorizontalRule}
              className="toolbar-btn"
            />
          </Tooltip>
          <Tooltip title="表格">
            <Button 
              type="text" 
              icon={<TableOutlined />} 
              onClick={insertTable}
              className="toolbar-btn"
            />
          </Tooltip>
        </div>
      </div>

      <div className="markdown-editor-container">
        <div className="markdown-editor-left">
          <TextArea
            ref={textareaRef}
            value={content}
            onChange={handleChange}
            placeholder={placeholder}
            rows={rows}
            className="markdown-textarea"
          />
        </div>
      <div className="markdown-editor-right">
        {content.trim() ? (
          <div 
            className="markdown-preview"
            dangerouslySetInnerHTML={{ __html: htmlContent }}
          />
        ) : (
          <div className="markdown-preview-empty">
            <div style={{ color: '#bfbfbf', textAlign: 'center', padding: '40px 20px' }}>
              <div style={{ fontSize: '48px', marginBottom: '16px' }}>📝</div>
              <div>Markdown预览将在这里显示</div>
            </div>
          </div>
        )}
      </div>
      </div>
    </div>
  )
}

export default MarkdownEditor

