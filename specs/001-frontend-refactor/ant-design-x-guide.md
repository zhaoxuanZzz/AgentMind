# @ant-design/x 组件使用指南

**日期**：2026-01-25  
**版本**：@ant-design/x 2.1.3  
**目的**：说明如何在前端重构中使用 Ant Design X AI 组件库

---

## 组件概览

`@ant-design/x` 提供了专门为 AI 应用设计的高质量 React 组件，与 `@ant-design/x-sdk` 配合使用可以快速构建 AI 对话界面。

### 核心组件

| 组件 | 用途 | 替代原有组件 |
|------|------|-------------|
| `Bubble` | AI/用户消息气泡 | MessageBubble |
| `Conversations` | 对话列表容器 | MessageList |
| `Sender` | 消息输入框 | MessageInput |
| `Prompts` | 快捷提示词 | 新增功能 |
| `ThoughtChain` | 思考链展示 | ThinkingProcess |
| `Attachment` | 附件上传 | 新增功能 |

---

## 1. Bubble - 消息气泡组件

### 基础用法

```typescript
import { Bubble } from '@ant-design/x'

// AI 消息
<Bubble
  content="这是 AI 的回复内容"
  avatar={{ src: '/ai-avatar.png', alt: 'AI' }}
  placement="start"  // 左侧显示
  variant="filled"   // 填充样式
/>

// 用户消息
<Bubble
  content="用户的问题"
  avatar={{ src: '/user-avatar.png', alt: 'User' }}
  placement="end"    // 右侧显示
  variant="outlined" // 轮廓样式
/>
```

### 流式打字效果

```typescript
<Bubble
  content={streamingContent}
  typing={isStreaming}  // 显示打字机光标
  avatar={{ src: '/ai-avatar.png' }}
  placement="start"
/>
```

### Markdown 渲染

```typescript
import ReactMarkdown from 'react-markdown'

<Bubble
  content="支持 **Markdown** 格式"
  avatar={{ src: '/ai-avatar.png' }}
  messageRender={(content) => (
    <ReactMarkdown>{content}</ReactMarkdown>
  )}
/>
```

### 加载状态

```typescript
<Bubble
  content=""
  loading={true}
  avatar={{ src: '/ai-avatar.png' }}
  loadingRender={() => <Spin size="small" />}
/>
```

### 完整示例

```typescript
import { Bubble } from '@ant-design/x'
import ReactMarkdown from 'react-markdown'
import { Spin } from 'antd'

interface MessageBubbleProps {
  message: Message
  isStreaming?: boolean
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ 
  message, 
  isStreaming 
}) => {
  const isUser = message.role === 'user'
  
  return (
    <Bubble
      content={message.content}
      avatar={{
        src: isUser ? '/user-avatar.png' : '/ai-avatar.png',
        alt: isUser ? 'User' : 'AI'
      }}
      placement={isUser ? 'end' : 'start'}
      variant={isUser ? 'outlined' : 'filled'}
      typing={isStreaming}
      messageRender={(content) => (
        <ReactMarkdown>{content}</ReactMarkdown>
      )}
      footer={
        message.thinking && (
          <ThinkingSection content={message.thinking} />
        )
      }
    />
  )
}
```

---

## 2. Conversations - 对话列表组件

### 基础用法

```typescript
import { Conversations } from '@ant-design/x'

<Conversations
  items={messages}
  renderItem={(message) => (
    <MessageBubble 
      message={message} 
      isStreaming={isStreaming && message.id === streamingMessageId}
    />
  )}
/>
```

### 虚拟滚动（大量消息）

```typescript
<Conversations
  items={messages}
  virtual  // 启用虚拟滚动
  height={600}  // 容器高度
  renderItem={(message) => (
    <MessageBubble message={message} />
  )}
/>
```

### 自动滚动到底部

```typescript
import { useEffect, useRef } from 'react'
import { Conversations } from '@ant-design/x'

const MessageList = ({ messages, isStreaming }) => {
  const conversationsRef = useRef(null)
  
  useEffect(() => {
    if (isStreaming) {
      conversationsRef.current?.scrollToBottom()
    }
  }, [isStreaming, messages])
  
  return (
    <Conversations
      ref={conversationsRef}
      items={messages}
      renderItem={(message) => <MessageBubble message={message} />}
    />
  )
}
```

### 分组显示（按日期）

```typescript
<Conversations
  items={messages}
  groupBy={(message) => {
    const date = new Date(message.created_at)
    return date.toLocaleDateString('zh-CN')
  }}
  renderGroupHeader={(date) => (
    <div className="date-divider">{date}</div>
  )}
  renderItem={(message) => <MessageBubble message={message} />}
/>
```

---

## 3. Sender - 消息输入组件

### 基础用法

```typescript
import { Sender } from '@ant-design/x'

<Sender
  placeholder="输入消息..."
  onSubmit={(message) => handleSendMessage(message)}
  loading={isStreaming}
  disabled={!conversationId}
/>
```

### 自定义操作按钮

```typescript
import { FileOutlined, SettingOutlined, AudioOutlined } from '@ant-design/icons'

<Sender
  placeholder="输入消息..."
  onSubmit={handleSendMessage}
  actions={[
    {
      icon: <FileOutlined />,
      tooltip: '上传文件',
      onClick: handleFileUpload
    },
    {
      icon: <AudioOutlined />,
      tooltip: '语音输入',
      onClick: handleVoiceInput
    },
    {
      icon: <SettingOutlined />,
      tooltip: '设置',
      onClick: openSettings
    }
  ]}
/>
```

### 多行输入

```typescript
<Sender
  placeholder="输入消息..."
  onSubmit={handleSendMessage}
  autoSize={{ minRows: 1, maxRows: 6 }}  // 自动调整高度
/>
```

### 提交前验证

```typescript
<Sender
  placeholder="输入消息..."
  onSubmit={(message) => {
    if (!message.trim()) {
      antdMessage.warning('请输入消息内容')
      return false  // 阻止提交
    }
    handleSendMessage(message)
    return true
  }}
/>
```

### 完整示例

```typescript
import { Sender } from '@ant-design/x'
import { FileOutlined, SettingOutlined } from '@ant-design/icons'
import { message as antdMessage } from 'antd'

interface ChatInputProps {
  onSend: (message: string) => void
  isStreaming: boolean
  disabled?: boolean
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSend,
  isStreaming,
  disabled
}) => {
  return (
    <Sender
      placeholder="输入消息，Shift+Enter 换行，Enter 发送"
      onSubmit={(message) => {
        if (!message.trim()) {
          antdMessage.warning('请输入消息内容')
          return false
        }
        onSend(message)
        return true
      }}
      loading={isStreaming}
      disabled={disabled}
      autoSize={{ minRows: 1, maxRows: 4 }}
      actions={[
        {
          icon: <FileOutlined />,
          tooltip: '上传文件',
          onClick: () => antdMessage.info('文件上传功能开发中')
        },
        {
          icon: <SettingOutlined />,
          tooltip: '高级设置',
          onClick: () => antdMessage.info('设置面板开发中')
        }
      ]}
    />
  )
}
```

---

## 4. Prompts - 快捷提示词组件

### 基础用法

```typescript
import { Prompts } from '@ant-design/x'

<Prompts
  items={[
    { key: '1', label: '总结这篇文章', icon: <FileTextOutlined /> },
    { key: '2', label: '解释这个概念', icon: <QuestionCircleOutlined /> },
    { key: '3', label: '生成代码示例', icon: <CodeOutlined /> }
  ]}
  onItemClick={(item) => handleSendMessage(item.label)}
/>
```

### 分类提示词

```typescript
<Prompts
  title="选择一个提示词开始对话"
  items={[
    {
      key: 'code',
      label: '编程助手',
      description: '帮助你编写和优化代码',
      children: [
        { key: 'code-1', label: '生成 React 组件' },
        { key: 'code-2', label: '优化性能' },
        { key: 'code-3', label: '修复 Bug' }
      ]
    },
    {
      key: 'writing',
      label: '写作助手',
      description: '帮助你撰写各类文档',
      children: [
        { key: 'writing-1', label: '写邮件' },
        { key: 'writing-2', label: '写报告' }
      ]
    }
  ]}
  onItemClick={(item) => handleSendMessage(item.label)}
/>
```

### 与角色预设集成

```typescript
import { Prompts } from '@ant-design/x'
import type { RolePreset } from '../types'

interface RolePresetPromptsProps {
  rolePresets: RolePreset[]
  onSelect: (preset: RolePreset) => void
}

export const RolePresetPrompts: React.FC<RolePresetPromptsProps> = ({
  rolePresets,
  onSelect
}) => {
  const items = rolePresets.map(preset => ({
    key: preset.id,
    label: preset.title,
    description: preset.content.slice(0, 50) + '...',
    tags: preset.tags
  }))
  
  return (
    <Prompts
      title="选择角色预设"
      items={items}
      onItemClick={(item) => {
        const preset = rolePresets.find(p => p.id === item.key)
        if (preset) onSelect(preset)
      }}
    />
  )
}
```

---

## 5. ThoughtChain - 思考链组件

展示 AI 的推理过程和工具调用。

```typescript
import { ThoughtChain } from '@ant-design/x'

<ThoughtChain
  items={[
    {
      title: '分析问题',
      description: '用户想要了解...',
      status: 'finish'
    },
    {
      title: '搜索相关信息',
      description: '正在使用 web_search 工具...',
      status: 'process'
    },
    {
      title: '生成回复',
      description: '',
      status: 'wait'
    }
  ]}
/>
```

### 集成工具调用

```typescript
import { ThoughtChain } from '@ant-design/x'
import type { ToolInfo } from '../types'

interface ToolCallsDisplayProps {
  toolCalls: ToolInfo[]
}

export const ToolCallsDisplay: React.FC<ToolCallsDisplayProps> = ({ 
  toolCalls 
}) => {
  const items = toolCalls.map((tool, index) => ({
    title: `工具调用: ${tool.tool}`,
    description: (
      <div>
        <div><strong>输入:</strong> {tool.input}</div>
        <div><strong>输出:</strong> {tool.output}</div>
      </div>
    ),
    status: 'finish' as const,
    timestamp: tool.timestamp
  }))
  
  return <ThoughtChain items={items} />
}
```

---

## 6. 完整聊天页面示例

结合所有组件构建完整的聊天界面。

```typescript
import { useState } from 'react'
import { Conversations, Sender, Bubble, Prompts } from '@ant-design/x'
import { useStreamChat } from '../hooks/useStreamChat'
import type { Message } from '../types'

export const ChatPage = () => {
  const [messages, setMessages] = useState<Message[]>([])
  const { 
    isStreaming, 
    streamingContent, 
    sendMessage 
  } = useStreamChat()
  
  // 合并历史消息和流式消息
  const displayMessages = [
    ...messages,
    ...(isStreaming ? [{
      id: -1,
      role: 'assistant' as const,
      content: streamingContent,
      conversation_id: 0,
      created_at: new Date().toISOString()
    }] : [])
  ]
  
  return (
    <div className="chat-page">
      {/* 消息列表 */}
      <div className="messages-container">
        {messages.length === 0 ? (
          <Prompts
            title="开始对话"
            items={[
              { key: '1', label: '介绍一下你自己' },
              { key: '2', label: '帮我写一段代码' },
              { key: '3', label: '总结一下今天的新闻' }
            ]}
            onItemClick={(item) => sendMessage(item.label)}
          />
        ) : (
          <Conversations
            items={displayMessages}
            renderItem={(message) => (
              <Bubble
                key={message.id}
                content={message.content}
                avatar={{
                  src: message.role === 'user' 
                    ? '/user-avatar.png' 
                    : '/ai-avatar.png'
                }}
                placement={message.role === 'user' ? 'end' : 'start'}
                typing={isStreaming && message.id === -1}
              />
            )}
          />
        )}
      </div>
      
      {/* 输入框 */}
      <div className="input-container">
        <Sender
          placeholder="输入消息..."
          onSubmit={sendMessage}
          loading={isStreaming}
        />
      </div>
    </div>
  )
}
```

---

## 7. 主题定制

### ConfigProvider 配置

```typescript
import { ConfigProvider } from 'antd'
import { XProvider } from '@ant-design/x'

const theme = {
  token: {
    colorPrimary: '#1677ff',
    colorBgContainer: '#ffffff',
    borderRadius: 8
  },
  components: {
    // Ant Design X 组件主题
    Bubble: {
      colorBgUser: '#1677ff',
      colorTextUser: '#ffffff',
      colorBgAssistant: '#f5f8fc',
      colorTextAssistant: '#1d2129'
    }
  }
}

function App() {
  return (
    <ConfigProvider theme={theme}>
      <XProvider>
        {/* 应用内容 */}
      </XProvider>
    </ConfigProvider>
  )
}
```

---

## 8. 最佳实践

### 1. 性能优化

```typescript
import { memo } from 'react'
import { Bubble } from '@ant-design/x'

// 使用 memo 避免不必要的重渲染
export const MessageBubble = memo<MessageBubbleProps>(
  ({ message, isStreaming }) => (
    <Bubble
      content={message.content}
      typing={isStreaming}
      // ...
    />
  ),
  (prev, next) => 
    prev.message.id === next.message.id &&
    prev.isStreaming === next.isStreaming
)
```

### 2. 错误处理

```typescript
<Bubble
  content={message.content}
  status={message.error ? 'error' : 'success'}
  footer={
    message.error && (
      <Alert 
        type="error" 
        message={message.error} 
        showIcon 
      />
    )
  }
/>
```

### 3. 可访问性

```typescript
<Bubble
  content={message.content}
  avatar={{
    src: '/ai-avatar.png',
    alt: 'AI Assistant'  // 提供 alt 文本
  }}
  aria-label={`${message.role} 消息: ${message.content}`}
/>
```

---

## 总结

使用 `@ant-design/x` 的优势：

✅ **开箱即用** - 专门为 AI 应用设计的组件  
✅ **完美集成** - 与 Ant Design 6.x 无缝配合  
✅ **减少开发量** - 内置打字机、流式渲染等功能  
✅ **统一体验** - 提供一致的 AI 交互模式  
✅ **易于定制** - 支持主题配置和自定义渲染  

**下一步**：
1. 在 ChatPage 中使用 Bubble 和 Conversations 替代自定义组件
2. 使用 Sender 替代当前的 MessageInput
3. 添加 Prompts 组件提供快捷提示词功能
4. 使用 ThoughtChain 展示 AI 推理过程

---

**文档版本**: v1.0.0  
**最后更新**: 2026-01-25  
**相关链接**: https://x.ant.design/
