import { useState, useEffect, useRef } from 'react'
import { Input, Button, Spin, message, Card, Avatar, Space, Select, Tooltip, Badge, List, Empty, Tag, Switch, Divider, Modal, Form, Collapse, Timeline } from 'antd'
import { SendOutlined, RobotOutlined, UserOutlined, ThunderboltFilled, PlusOutlined, DeleteOutlined, HistoryOutlined, BookOutlined, SettingOutlined, TagsOutlined, EditOutlined, ToolOutlined, CheckCircleOutlined, ClockCircleOutlined, SearchOutlined, GlobalOutlined, FileTextOutlined, DatabaseOutlined, CalculatorOutlined } from '@ant-design/icons'
import { chatApi, knowledgeApi } from '../api/services'
import type { Message, Conversation } from '../api/types'
import './ChatPage.css'

const { TextArea } = Input
const { Option } = Select
const { Panel } = Collapse

const ChatPage = () => {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [loading, setLoading] = useState(false)
  const [conversationId, setConversationId] = useState<number | undefined>()
  const [streamingThinking, setStreamingThinking] = useState<string>('')
  const [streamingContent, setStreamingContent] = useState<string>('')
  const [currentStreamingMessageId, setCurrentStreamingMessageId] = useState<number | null>(null)
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [selectedProvider, setSelectedProvider] = useState<string>(() => {
    // 从localStorage读取缓存的provider
    const saved = localStorage.getItem('llmProvider')
    return saved || 'dashscope'
  })
  const [selectedModel, setSelectedModel] = useState<string>(() => {
    // 从localStorage读取缓存的model
    const saved = localStorage.getItem('llmModel')
    return saved || 'qwen3-vl-plus'
  })
  const [providers, setProviders] = useState<any[]>([])
  const [rolePresets, setRolePresets] = useState<any[]>([])
  const [useKnowledge, setUseKnowledge] = useState(() => {
    // 从localStorage读取缓存状态
    const saved = localStorage.getItem('useKnowledge')
    return saved === 'true'
  })
  const [selectedSearchProvider, setSelectedSearchProvider] = useState<string>(() => {
    // 从localStorage读取缓存的搜索提供商
    const saved = localStorage.getItem('searchProvider')
    return saved || 'tavily'  // 默认使用Tavily
  })
  const [selectedCategories, setSelectedCategories] = useState<string[]>([])
  const [selectedRolePresetId, setSelectedRolePresetId] = useState<string | undefined>(undefined)
  const [deepReasoning, setDeepReasoning] = useState<boolean>(() => {
    const saved = localStorage.getItem('deepReasoning')
    return saved === 'true'
  })
  const [isPromptModalOpen, setIsPromptModalOpen] = useState(false)
  const [editingPrompt, setEditingPrompt] = useState<any>(null)
  const [viewingPrompt, setViewingPrompt] = useState<any>(null)
  const [isViewModalOpen, setIsViewModalOpen] = useState(false)
  const [promptForm] = Form.useForm()
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<any>(null)

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    loadProviders()
    loadConversations()
    loadRolePresets()
  }, [])

  const loadProviders = async () => {
    try {
      const data = await chatApi.getLLMProviders()
      setProviders(data.providers)
      
      // 如果localStorage中没有保存的值，使用默认值
      const savedProvider = localStorage.getItem('llmProvider')
      const savedModel = localStorage.getItem('llmModel')
      
      if (!savedProvider && data.default) {
        const defaultProvider = data.default.provider || 'dashscope'
        setSelectedProvider(defaultProvider)
        localStorage.setItem('llmProvider', defaultProvider)
      }
      
      if (!savedModel && data.default) {
        const defaultModel = data.default.model || 'qwen3-vl-plus'
        setSelectedModel(defaultModel)
        localStorage.setItem('llmModel', defaultModel)
      }
      
      // 验证当前选择的model是否属于当前provider
      const currentProvider = providers.find(p => p.id === selectedProvider)
      if (currentProvider) {
        const modelExists = currentProvider.models.some(m => m.id === selectedModel)
        if (!modelExists && currentProvider.models.length > 0) {
          // 如果当前model不在当前provider中，使用第一个model
          const firstModel = currentProvider.models[0].id
          setSelectedModel(firstModel)
          localStorage.setItem('llmModel', firstModel)
        }
      }
    } catch (error) {
      console.error('Failed to load providers:', error)
    }
  }
  
  // 当provider变化时，更新model
  useEffect(() => {
    if (providers.length > 0) {
      const provider = providers.find(p => p.id === selectedProvider)
      if (provider && provider.models.length > 0) {
        // 检查当前model是否属于新provider
        const modelExists = provider.models.some(m => m.id === selectedModel)
        if (!modelExists) {
          // 如果不存在，使用第一个model
          const firstModel = provider.models[0].id
          setSelectedModel(firstModel)
          localStorage.setItem('llmModel', firstModel)
        }
      }
    }
  }, [selectedProvider, providers])

  const loadConversations = async () => {
    try {
      const data = await chatApi.getConversations(0, 20)
      setConversations(data)
    } catch (error) {
      console.error('Failed to load conversations:', error)
    }
  }

  const loadRolePresets = async () => {
    try {
      // 从后端加载角色预设 - 使用getRolePresets直接获取所有预设
      const data = await knowledgeApi.getRolePresets({
        limit: 50
      })
      setRolePresets(data || [])
    } catch (error) {
      console.error('Failed to load role presets:', error)
      // 如果失败，使用示例数据
      setRolePresets([
        { 
          title: '项目管理助手', 
          content: '你是一个专业的项目管理助手，擅长制定计划、分配任务、跟踪进度。', 
          category: 'business', 
          tags: ['管理', '计划'],
          score: 1.0
        },
        { 
          title: '代码审查专家', 
          content: '你是一个资深的代码审查专家，关注代码质量、性能、安全性。', 
          category: 'tech', 
          tags: ['代码', '质量'],
          score: 1.0
        },
        { 
          title: '数据分析师', 
          content: '你是一个专业的数据分析师，擅长数据清洗、分析、可视化。', 
          category: 'analysis', 
          tags: ['数据', '分析'],
          score: 1.0
        },
      ])
    }
  }

  const handleCreatePrompt = () => {
    setEditingPrompt(null)
    promptForm.resetFields()
    setIsPromptModalOpen(true)
  }

  const handleEditPrompt = (prompt: any) => {
    setEditingPrompt(prompt)
    promptForm.setFieldsValue({
      title: prompt.title,
      content: prompt.content,
      category: prompt.category,
      tags: prompt.tags.join(', ')
    })
    setIsPromptModalOpen(true)
  }

  const handleDeletePrompt = async (prompt: any) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除提示词 "${prompt.title}" 吗？`,
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          // TODO: 实现删除 API
          message.success('删除成功')
          loadRolePresets()
        } catch (error) {
          message.error('删除失败')
        }
      }
    })
  }

  const handlePromptSubmit = async () => {
    try {
      const values = await promptForm.validateFields()
      const tags = values.tags ? values.tags.split(',').map((t: string) => t.trim()).filter(Boolean) : []
      
      if (editingPrompt) {
        // 编辑模式
        message.info('编辑功能开发中...')
        // TODO: 实现编辑 API
      } else {
        // 创建模式
        await knowledgeApi.createRolePreset({
          title: values.title,
          prompt_content: values.content,
          category: values.category,
          tags: tags
        })
        message.success('创建成功')
      }
      
      setIsPromptModalOpen(false)
      promptForm.resetFields()
      loadRolePresets()
    } catch (error: any) {
      console.error('Failed to save prompt:', error)
      message.error(error.response?.data?.detail || '保存失败')
    }
  }

  const handleApplyPrompt = (prompt: any) => {
    // 将提示词内容添加到输入框
    const currentValue = inputValue.trim()
    const newValue = currentValue 
      ? `${currentValue}\n\n[应用提示词: ${prompt.title}]\n${prompt.content}`
      : `[应用提示词: ${prompt.title}]\n${prompt.content}`
    setInputValue(newValue)
    inputRef.current?.focus()
    message.success(`已应用提示词: ${prompt.title}`)
  }

  const handleViewPrompt = (prompt: any) => {
    setViewingPrompt(prompt)
    setIsViewModalOpen(true)
  }

  const handleSelectConversation = async (convId: number) => {
    try {
      const conv = await chatApi.getConversation(convId)
      setConversationId(convId)
      // 从meta_info中提取thinking和intermediate_steps
      const processedMessages = (conv.messages || []).map((msg: any) => ({
        ...msg,
        thinking: msg.meta_info?.thinking || undefined,
        intermediate_steps: msg.meta_info?.intermediate_steps || msg.intermediate_steps || []
      }))
      setMessages(processedMessages)
    } catch (error) {
      message.error('加载对话失败')
    }
  }

  const handleDeleteConversation = async (convId: number) => {
    try {
      await chatApi.deleteConversation(convId)
      message.success('已删除')
      loadConversations()
      if (conversationId === convId) {
        handleNewChat()
      }
    } catch (error) {
      message.error('删除失败')
    }
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const handleSend = async () => {
    if (!inputValue.trim()) return

    const userMessage = inputValue.trim()
    setInputValue('')
    setLoading(true)
    setStreamingThinking('')
    setStreamingContent('')

    // 添加用户消息到界面
    const tempUserMsg: Message = {
      id: Date.now(),
      conversation_id: conversationId || 0,
      role: 'user',
      content: userMessage,
      created_at: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, tempUserMsg])

    // 创建临时助手消息用于流式更新
    const assistantMsgId = Date.now() + 1
    setCurrentStreamingMessageId(assistantMsgId)
    const tempAssistantMsg: Message = {
      id: assistantMsgId,
      conversation_id: conversationId || 0,
      role: 'assistant',
      content: '',
      created_at: new Date().toISOString(),
      intermediate_steps: [],
      thinking: ''  // 初始化推理过程字段
    }
    setMessages((prev) => [...prev, tempAssistantMsg])

    try {
      // 使用流式API
      await chatApi.sendMessageStream(
        {
          message: userMessage,
          conversation_id: conversationId,
          use_knowledge_base: (useKnowledge && !selectedRolePresetId) ? 'prompts' : undefined,
          search_provider: selectedSearchProvider,
          role_preset_id: selectedRolePresetId,
          deep_reasoning: deepReasoning,
          llm_config: {
            provider: selectedProvider,
            model: selectedModel
          }
        },
        (chunk) => {
          console.log('Received chunk:', chunk) // 调试日志
          if (chunk.type === 'conversation_id') {
            setConversationId(chunk.conversation_id)
          } else if (chunk.type === 'thinking') {
            // 更新推理过程 - 同时保存到消息中
            setStreamingThinking((prev) => {
              const newThinking = prev + (chunk.content || '')
              // 实时更新消息中的推理过程
              setMessages((prevMsgs) =>
                prevMsgs.map((msg) =>
                  msg.id === assistantMsgId
                    ? { ...msg, thinking: newThinking }
                    : msg
                )
              )
              return newThinking
            })
          } else if (chunk.type === 'content') {
            // 更新最终答案 - 使用函数式更新避免闭包问题
            setStreamingContent((prev) => {
              const newContent = prev + (chunk.content || '')
              // 实时更新消息内容
              setMessages((prevMsgs) =>
                prevMsgs.map((msg) =>
                  msg.id === assistantMsgId
                    ? { ...msg, content: newContent }
                    : msg
                )
              )
              return newContent
            })
          } else if (chunk.type === 'tool') {
            // 更新工具调用信息
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMsgId
                  ? {
                      ...msg,
                      intermediate_steps: [
                        ...(msg.intermediate_steps || []),
                        chunk.tool_info
                      ]
                    }
                  : msg
              )
            )
          } else if (chunk.type === 'done') {
            // 流式输出完成，更新最终消息
            // 使用函数式更新确保获取最新的streamingContent和streamingThinking
            setStreamingContent((prevContent) => {
              const finalContent = prevContent || ''
              setStreamingThinking((prevThinking) => {
                const finalThinking = prevThinking || ''
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMsgId
                      ? {
                          ...msg,
                          content: finalContent || msg.content,  // 使用累积的内容或消息内容
                          thinking: finalThinking || msg.thinking,  // 保存推理过程
                          conversation_id: chunk.conversation_id || conversationId || 0
                        }
                      : msg
                  )
                )
                return finalThinking
              })
              return finalContent
            })
            setStreamingThinking('')
            setStreamingContent('')
            setCurrentStreamingMessageId(null)
            loadConversations()
          } else if (chunk.type === 'error') {
            message.error(chunk.message || '请求失败')
            setMessages((prev) => prev.filter((msg) => msg.id !== assistantMsgId))
          }
        }
      )
    } catch (error: any) {
      console.error('Error:', error)
      message.error(error.message || '请求失败')
      // 移除失败的消息
      setMessages((prev) => prev.filter((msg) => msg.id !== assistantMsgId))
    } finally {
      setLoading(false)
      setStreamingThinking('')
      setStreamingContent('')
      setCurrentStreamingMessageId(null)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleNewChat = () => {
    setMessages([])
    setConversationId(undefined)
    inputRef.current?.focus()
    loadConversations()
  }

  // 获取工具配置（图标、名称、颜色主题）
  const getToolConfig = (toolName: string) => {
    const configMap: Record<string, {
      icon: React.ReactNode,
      name: string,
      color: string,
      bgColor: string,
      borderColor: string,
      iconBg: string
    }> = {
      'web_search': {
        icon: <SearchOutlined />,
        name: '联网搜索',
        color: '#1890ff',
        bgColor: 'rgba(24, 144, 255, 0.08)',
        borderColor: 'rgba(24, 144, 255, 0.3)',
        iconBg: 'linear-gradient(135deg, #1890ff 0%, #096dd9 100%)'
      },
      // 兼容旧的工具名称
      'tavily_web_search': {
        icon: <SearchOutlined />,
        name: '联网搜索',
        color: '#1890ff',
        bgColor: 'rgba(24, 144, 255, 0.08)',
        borderColor: 'rgba(24, 144, 255, 0.3)',
        iconBg: 'linear-gradient(135deg, #1890ff 0%, #096dd9 100%)'
      },
      'baidu_web_search': {
        icon: <SearchOutlined />,
        name: '联网搜索',
        color: '#1890ff',
        bgColor: 'rgba(24, 144, 255, 0.08)',
        borderColor: 'rgba(24, 144, 255, 0.3)',
        iconBg: 'linear-gradient(135deg, #1890ff 0%, #096dd9 100%)'
      },
      'web_content_fetcher': {
        icon: <GlobalOutlined />,
        name: '网页抓取',
        color: '#52c41a',
        bgColor: 'rgba(82, 196, 26, 0.08)',
        borderColor: 'rgba(82, 196, 26, 0.3)',
        iconBg: 'linear-gradient(135deg, #52c41a 0%, #389e0d 100%)'
      },
      'pdf_parser': {
        icon: <FileTextOutlined />,
        name: 'PDF解析',
        color: '#fa8c16',
        bgColor: 'rgba(250, 140, 22, 0.08)',
        borderColor: 'rgba(250, 140, 22, 0.3)',
        iconBg: 'linear-gradient(135deg, #fa8c16 0%, #d46b08 100%)'
      },
      'knowledge_base_search': {
        icon: <DatabaseOutlined />,
        name: '知识库检索',
        color: '#722ed1',
        bgColor: 'rgba(114, 46, 209, 0.08)',
        borderColor: 'rgba(114, 46, 209, 0.3)',
        iconBg: 'linear-gradient(135deg, #722ed1 0%, #531dab 100%)'
      },
      'calculator': {
        icon: <CalculatorOutlined />,
        name: '计算器',
        color: '#eb2f96',
        bgColor: 'rgba(235, 47, 150, 0.08)',
        borderColor: 'rgba(235, 47, 150, 0.3)',
        iconBg: 'linear-gradient(135deg, #eb2f96 0%, #c41d7f 100%)'
      }
    }
    return configMap[toolName] || {
      icon: <ToolOutlined />,
      name: toolName,
      color: '#666',
      bgColor: 'rgba(0, 0, 0, 0.04)',
      borderColor: 'rgba(0, 0, 0, 0.1)',
      iconBg: '#666'
    }
  }

  const getToolIcon = (toolName: string) => {
    const config = getToolConfig(toolName)
    return config.icon
  }

  const getToolDisplayName = (toolName: string) => {
    const config = getToolConfig(toolName)
    return config.name
  }

  const renderMessage = (msg: Message) => {
    const isUser = msg.role === 'user'
    const hasTools = !isUser && msg.intermediate_steps && msg.intermediate_steps.length > 0
    const isStreaming = !isUser && msg.id === currentStreamingMessageId
    const hasThinking = msg.thinking || (isStreaming && streamingThinking)
    const hasContent = msg.content || (isStreaming && streamingContent)
    
    // 如果是流式消息但还没有任何内容（推理、工具、内容），则不显示
    // 用户消息总是显示
    if (!isUser && !hasThinking && !hasTools && !hasContent) {
      return null
    }
    
    return (
      <div 
        key={msg.id} 
        className={`message-item ${isUser ? 'user-message' : 'assistant-message'}`}
      >
        <Avatar 
          size={32}
          icon={isUser ? <UserOutlined /> : <RobotOutlined />}
          style={{ 
            backgroundColor: isUser ? '#1677ff' : '#52c41a',
            flexShrink: 0
          }}
        />
        <div className="message-content">
          {/* 推理过程 - 显示保存的推理过程或流式推理过程 */}
          {(msg.thinking || (isStreaming && streamingThinking)) && (
            <div className="thinking-section">
              <div className="thinking-header">
                <span className="thinking-icon">💭</span>
                <span className="thinking-label">
                  {isStreaming && streamingThinking ? '推理中...' : '推理过程'}
                </span>
              </div>
              <div className="thinking-content">
                {isStreaming && streamingThinking ? streamingThinking : msg.thinking}
              </div>
            </div>
          )}
          
          {/* 工具调用过程 */}
          {hasTools && (
            <Collapse 
              ghost 
              size="small"
              style={{ marginBottom: 12 }}
              items={[
                {
                  key: '1',
                  label: (
                    <Space>
                      <ToolOutlined style={{ color: '#1890ff' }} />
                      <span style={{ color: '#666', fontSize: 13 }}>
                        使用了 {msg.intermediate_steps!.length} 个工具
                      </span>
                    </Space>
                  ),
                  children: (
                    <Timeline
                      items={msg.intermediate_steps!.map((step, idx) => {
                        const toolConfig = getToolConfig(step.tool)
                        return {
                          dot: (
                            <div 
                              style={{
                                width: 32,
                                height: 32,
                                borderRadius: '50%',
                                background: toolConfig.iconBg,
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                color: 'white',
                                fontSize: 14,
                                boxShadow: `0 2px 8px ${toolConfig.color}40`,
                                border: `2px solid white`
                              }}
                            >
                              {toolConfig.icon}
                            </div>
                          ),
                          color: toolConfig.color,
                          children: (
                            <div 
                              key={idx} 
                              style={{ 
                                paddingBottom: 12,
                                paddingLeft: 8
                              }}
                            >
                              {/* 工具名称卡片 */}
                              <div 
                                className="tool-name-tag"
                                style={{ 
                                  display: 'inline-flex',
                                  alignItems: 'center',
                                  gap: 8,
                                  padding: '6px 12px',
                                  borderRadius: 6,
                                  background: toolConfig.bgColor,
                                  border: `1px solid ${toolConfig.borderColor}`,
                                  marginBottom: 8,
                                  fontWeight: 500,
                                  color: toolConfig.color,
                                  fontSize: 13
                                }}
                              >
                                {toolConfig.icon}
                                <span>{toolConfig.name}</span>
                              </div>
                              
                              {/* 输入框 */}
                              <div 
                                className="tool-input-box"
                                style={{ 
                                  fontSize: 12, 
                                  color: '#666',
                                  background: '#f5f5f5',
                                  padding: '8px 12px',
                                  borderRadius: 6,
                                  marginBottom: 8,
                                  borderLeft: `3px solid ${toolConfig.color}`,
                                  fontFamily: 'monospace'
                                }}
                              >
                                <div style={{ 
                                  fontSize: 11, 
                                  color: '#999', 
                                  marginBottom: 4,
                                  fontWeight: 500,
                                  textTransform: 'uppercase',
                                  letterSpacing: 0.5
                                }}>
                                  输入
                                </div>
                                <div>{step.input}</div>
                              </div>
                              
                              {/* 输出框 */}
                              <div 
                                className="tool-output-box"
                                style={{ 
                                  fontSize: 12, 
                                  color: '#333',
                                  background: toolConfig.bgColor,
                                  padding: '8px 12px',
                                  borderRadius: 6,
                                  border: `1px solid ${toolConfig.borderColor}`,
                                  maxHeight: 200,
                                  overflow: 'auto',
                                  lineHeight: 1.6
                                }}
                              >
                                <div style={{ 
                                  fontSize: 11, 
                                  color: toolConfig.color, 
                                  marginBottom: 4,
                                  fontWeight: 500,
                                  textTransform: 'uppercase',
                                  letterSpacing: 0.5
                                }}>
                                  输出
                                </div>
                                <div style={{ whiteSpace: 'pre-wrap' }}>{step.output}</div>
                              </div>
                            </div>
                          )
                        }
                      })}
                    />
                  )
                }
              ]}
            />
          )}
          
          {/* 最终答案内容 */}
          <div className={`message-text ${isStreaming && (streamingContent || msg.content) ? 'streaming' : ''}`}>
            {isStreaming ? (streamingContent || msg.content) : msg.content}
            {isStreaming && (
              <span className="streaming-cursor">▋</span>
            )}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="chat-layout">
      {/* 左侧：对话历史 */}
      <div className="sidebar-left">
        <div className="sidebar-header">
          <HistoryOutlined style={{ fontSize: 18, marginRight: 8 }} />
          <span>对话历史</span>
        </div>
        <Button 
          type="primary" 
          icon={<PlusOutlined />} 
          onClick={handleNewChat}
          style={{ width: '100%', marginBottom: 12 }}
        >
          新建对话
        </Button>
        <div className="conversations-list">
          {conversations.length === 0 ? (
            <Empty 
              description="暂无对话" 
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          ) : (
            <List
              dataSource={conversations}
              renderItem={(conv) => (
                <List.Item
                  className={`conversation-item ${conversationId === conv.id ? 'active' : ''}`}
                  onClick={() => handleSelectConversation(conv.id)}
                  actions={[
                    <Button
                      type="text"
                      size="small"
                      danger
                      icon={<DeleteOutlined />}
                      onClick={(e) => {
                        e.stopPropagation()
                        handleDeleteConversation(conv.id)
                      }}
                    />
                  ]}
                >
                  <List.Item.Meta
                    avatar={<Avatar icon={<UserOutlined />} size="small" />}
                    title={conv.title}
                    description={new Date(conv.updated_at).toLocaleString('zh-CN', {
                      month: '2-digit',
                      day: '2-digit',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  />
                </List.Item>
              )}
            />
          )}
        </div>
      </div>

      {/* 中间：对话区域 */}
      <div className="chat-main">
        {/* Header */}
        <div className="chat-header">
          <div className="header-left">
            <div className="logo-wrapper">
              <RobotOutlined className="logo-icon" />
              <div className="logo-pulse"></div>
            </div>
            <span className="header-title">
              Agent System
              <Badge 
                count="AI" 
                style={{ 
                  backgroundColor: '#52c41a',
                  marginLeft: 8,
                  fontSize: 10
                }} 
              />
            </span>
          </div>
          <Space>
            <Tooltip title="选择联网搜索提供商">
              <Select
                value={selectedSearchProvider}
                onChange={(value) => {
                  setSelectedSearchProvider(value)
                  localStorage.setItem('searchProvider', value)
                }}
                style={{ width: 160 }}
                size="middle"
              >
                <Option value="tavily">
                  <Space>
                    <SearchOutlined style={{ color: '#1890ff' }} />
                    <span>Tavily</span>
                  </Space>
                </Option>
                <Option value="baidu">
                  <Space>
                    <GlobalOutlined style={{ color: '#52c41a' }} />
                    <span>百度</span>
                  </Space>
                </Option>
              </Select>
            </Tooltip>
            <Tooltip title="选择AI提供商">
              <Select
                value={selectedProvider}
                onChange={(value) => {
                  setSelectedProvider(value)
                  localStorage.setItem('llmProvider', value)
                  // 切换provider时，自动选择该provider的第一个model
                  const provider = providers.find(p => p.id === value)
                  if (provider && provider.models.length > 0) {
                    const firstModel = provider.models[0].id
                    setSelectedModel(firstModel)
                    localStorage.setItem('llmModel', firstModel)
                  }
                }}
                style={{ width: 140 }}
                size="middle"
              >
                {providers.map((provider: any) => (
                  <Option key={provider.id} value={provider.id}>
                    <Space>
                      <ThunderboltFilled style={{ color: '#faad14' }} />
                      {provider.name}
                    </Space>
                  </Option>
                ))}
              </Select>
            </Tooltip>
            <Tooltip title="选择AI模型">
              <Select
                value={selectedModel}
                onChange={(value) => {
                  setSelectedModel(value)
                  localStorage.setItem('llmModel', value)
                }}
                style={{ width: 200 }}
                size="middle"
                className="model-selector"
              >
                {providers.find(p => p.id === selectedProvider)?.models.map((model: any) => (
                  <Option key={model.id} value={model.id}>
                    <Space>
                      <ThunderboltFilled style={{ color: '#faad14' }} />
                      {model.name}
                    </Space>
                  </Option>
                ))}
              </Select>
            </Tooltip>
          </Space>
        </div>

        {/* Messages */}
        <div className="chat-messages">
          {messages.length === 0 ? (
            <div className="empty-state">
              <RobotOutlined style={{ fontSize: 48, color: '#d9d9d9' }} />
              <h2>你好！我是智能AI助手</h2>
              <p>我可以帮你搜索信息、分析问题、规划任务</p>
            </div>
          ) : (
            <>
              {messages.map(renderMessage).filter(Boolean)}
              {/* Loading指示器 - 显示在消息列表底部，当有loading但还没有内容时 */}
              {(loading || currentStreamingMessageId) && 
               !messages.some(msg => 
                 msg.id === currentStreamingMessageId && 
                 (msg.content || msg.thinking || msg.intermediate_steps?.length)
               ) && (
                <div className="message-loading-indicator">
                  <Spin size="small" />
                  <span>AI正在思考中...</span>
                </div>
              )}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Input */}
        <div className="chat-input-container">
          {/* 角色预设选择器和深度推理开关 */}
          {rolePresets.length > 0 && (
            <div className="prompt-card-selector-wrapper">
              <div style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                <div style={{ flex: 1 }}>
                  <Select
                    placeholder="选择角色预设"
                    value={selectedRolePresetId}
                    onChange={(value) => setSelectedRolePresetId(value)}
                    allowClear
                    className="prompt-card-selector"
                    size="middle"
                    showSearch
                    style={{ width: '100%', minWidth: '500px' }}
                    filterOption={(input, option) => {
                      const preset = rolePresets.find(c => c.id === option?.value)
                      if (!preset) return false
                      const searchText = input.toLowerCase()
                      return preset.title.toLowerCase().includes(searchText) ||
                             preset.content.toLowerCase().includes(searchText) ||
                             (preset.tags && preset.tags.some(tag => tag.toLowerCase().includes(searchText)))
                    }}
                  >
                    {rolePresets
                      .filter(preset => 
                        selectedCategories.length === 0 || 
                        selectedCategories.includes(preset.category)
                      )
                      .map((preset) => (
                        <Option key={preset.id} value={preset.id}>
                          <div className="prompt-card-option">
                            <span className="prompt-card-option-title">{preset.title}</span>
                            {selectedRolePresetId === preset.id && (
                              <Tag color="blue" className="prompt-card-selected-tag">已选</Tag>
                            )}
                          </div>
                        </Option>
                      ))}
                  </Select>
                </div>
                <Button
                  type={deepReasoning ? "primary" : "default"}
                  size="small"
                  onClick={() => {
                    const newValue = !deepReasoning
                    setDeepReasoning(newValue)
                    localStorage.setItem('deepReasoning', String(newValue))
                  }}
                  className="deep-reasoning-btn"
                  style={{
                    height: '32px',
                    padding: '0 12px',
                    whiteSpace: 'nowrap',
                    flexShrink: 0
                  }}
                >
                  <ThunderboltFilled style={{ marginRight: 4 }} />
                  深度推理
                </Button>
              </div>
              {selectedRolePresetId && (
                <div className="prompt-card-hint">
                  <CheckCircleOutlined />
                  <span>已选择角色预设，将直接使用</span>
                </div>
              )}
            </div>
          )}
          <div className="input-wrapper">
            <TextArea
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="输入消息... (Shift+Enter 换行)"
              autoSize={{ minRows: 1, maxRows: 3 }}
              disabled={loading}
              className="chat-input"
            />
            <Button
              type="primary"
              icon={<SendOutlined />}
              onClick={handleSend}
              loading={loading}
              disabled={!inputValue.trim()}
              className="send-button"
              size="small"
            />
          </div>
        </div>
      </div>

      {/* 右侧：角色预设配置 */}
      <div className="sidebar-right">
        <div className="sidebar-header">
          <BookOutlined style={{ fontSize: 18, marginRight: 8 }} />
          <span>角色预设</span>
        </div>
        
        <Card size="small" style={{ marginBottom: 12 }}>
          <Space direction="vertical" style={{ width: '100%' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>启用知识检索</span>
              <Switch 
                checked={useKnowledge} 
                onChange={(checked) => {
                  setUseKnowledge(checked)
                  // 保存到localStorage
                  localStorage.setItem('useKnowledge', String(checked))
                }} 
              />
            </div>
            <Divider style={{ margin: '8px 0' }} />
            <div>
              <SettingOutlined style={{ marginRight: 4 }} />
              <span style={{ fontSize: 12, color: '#888' }}>
                {useKnowledge ? '已启用，将从知识库检索相关信息' : '已禁用'}
              </span>
            </div>
          </Space>
        </Card>

        <div style={{ marginBottom: 12 }}>
          <div style={{ marginBottom: 8 }}>
            <div style={{ fontSize: 13, fontWeight: 500, color: '#666' }}>
              <TagsOutlined style={{ marginRight: 4 }} />
              角色预设分类
            </div>
          </div>
          <Space wrap>
            {['business', 'tech', 'analysis', 'creative'].map(cat => (
              <Tag
                key={cat}
                color={selectedCategories.includes(cat) ? 'blue' : 'default'}
                style={{ cursor: 'pointer' }}
                onClick={() => {
                  setSelectedCategories(prev =>
                    prev.includes(cat)
                      ? prev.filter(c => c !== cat)
                      : [...prev, cat]
                  )
                }}
              >
                {cat === 'business' && '商业'}
                {cat === 'tech' && '技术'}
                {cat === 'analysis' && '分析'}
                {cat === 'creative' && '创意'}
              </Tag>
            ))}
          </Space>
        </div>

        <div className="prompt-cards-list">
          <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 8, color: '#666' }}>
            推荐预设 ({rolePresets.filter(preset => 
              selectedCategories.length === 0 || 
              selectedCategories.includes(preset.category)
            ).length})
          </div>
          {rolePresets.length === 0 ? (
            <Empty 
              description="暂无角色预设" 
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              style={{ marginTop: 40 }}
            >
              <Button type="primary" icon={<PlusOutlined />} onClick={handleCreatePrompt}>
                创建第一个角色预设
              </Button>
            </Empty>
          ) : (
            rolePresets
              .filter(preset => 
                selectedCategories.length === 0 || 
                selectedCategories.includes(preset.category)
              )
              .slice(0, 10) // 只显示前10个预设
              .map((preset, index) => (
                <Card 
                  key={index}
                  size="small" 
                  hoverable
                  style={{ marginBottom: 8, cursor: 'pointer' }}
                  onClick={() => handleViewPrompt(preset)}
                >
                  <div style={{ fontSize: 14, fontWeight: 500, marginBottom: 6 }}>
                    {preset.title}
                  </div>
                  <div style={{ 
                    fontSize: 12, 
                    color: '#666', 
                    marginBottom: 8,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    display: '-webkit-box',
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: 'vertical'
                  }}>
                    {preset.content}
                  </div>
                  <div style={{ 
                    display: 'flex', 
                    flexWrap: 'wrap', 
                    gap: 4,
                    maxHeight: 28,
                    overflow: 'hidden',
                    alignItems: 'center'
                  }}>
                    <Tag color="default" style={{ fontSize: 11, margin: 0, flexShrink: 0 }}>
                      {preset.category === 'business' && '商业'}
                      {preset.category === 'tech' && '技术'}
                      {preset.category === 'analysis' && '分析'}
                      {preset.category === 'creative' && '创意'}
                    </Tag>
                    {preset.tags && preset.tags.length > 0 ? (
                      <Tooltip 
                        title={
                          <div style={{ maxWidth: 300 }}>
                            <div style={{ marginBottom: 4, fontSize: 12, color: '#fff' }}>全部标签：</div>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                              {preset.tags.map((tag: string) => (
                                <Tag key={tag} color="processing" style={{ margin: 0 }}>
                                  {tag}
                                </Tag>
                              ))}
                            </div>
                          </div>
                        }
                        placement="top"
                        overlayStyle={{ maxWidth: 350 }}
                      >
                        <div style={{ 
                          display: 'flex', 
                          flexWrap: 'wrap', 
                          gap: 4, 
                          flex: 1,
                          minWidth: 0,
                          overflow: 'hidden'
                        }}>
                          {preset.tags.slice(0, 3).map((tag: string) => (
                            <Tag key={tag} color="processing" style={{ fontSize: 11, margin: 0, flexShrink: 0 }}>
                              {tag}
                            </Tag>
                          ))}
                          {preset.tags.length > 3 && (
                            <Tag color="default" style={{ fontSize: 11, margin: 0, flexShrink: 0, cursor: 'help' }}>
                              +{preset.tags.length - 3}
                            </Tag>
                          )}
                        </div>
                      </Tooltip>
                    ) : null}
                  </div>
                </Card>
              ))
          )}
          
          {/* 显示"查看更多"提示 */}
          {rolePresets.filter(preset => 
            selectedCategories.length === 0 || 
            selectedCategories.includes(preset.category)
          ).length > 10 && (
            <div style={{ 
              textAlign: 'center', 
              marginTop: 12, 
              padding: '8px',
              background: 'rgba(22, 119, 255, 0.05)',
              borderRadius: '8px',
              fontSize: 12,
              color: '#666'
            }}>
              <BookOutlined style={{ marginRight: 4 }} />
              还有更多预设，点击顶部"知识库管理"查看全部 ({rolePresets.filter(preset => 
                selectedCategories.length === 0 || 
                selectedCategories.includes(preset.category)
              ).length - 10})
            </div>
          )}
        </div>
      </div>

      {/* 提示词编辑弹窗 */}
      <Modal
        title={editingPrompt ? '编辑提示词' : '新建提示词'}
        open={isPromptModalOpen}
        onOk={handlePromptSubmit}
        onCancel={() => {
          setIsPromptModalOpen(false)
          promptForm.resetFields()
        }}
        okText="保存"
        cancelText="取消"
        width={600}
      >
        <Form
          form={promptForm}
          layout="vertical"
          autoComplete="off"
        >
          <Form.Item
            label="标题"
            name="title"
            rules={[{ required: true, message: '请输入提示词标题' }]}
          >
            <Input placeholder="例如：项目管理助手" />
          </Form.Item>

          <Form.Item
            label="提示词内容"
            name="content"
            rules={[{ required: true, message: '请输入提示词内容' }]}
          >
            <TextArea
              rows={6}
              placeholder="输入详细的提示词内容，描述AI应该如何行为..."
            />
          </Form.Item>

          <Form.Item
            label="分类"
            name="category"
            rules={[{ required: true, message: '请选择分类' }]}
          >
            <Select placeholder="选择分类">
              <Option value="business">商业</Option>
              <Option value="tech">技术</Option>
              <Option value="analysis">分析</Option>
              <Option value="creative">创意</Option>
            </Select>
          </Form.Item>

          <Form.Item
            label="标签"
            name="tags"
            help="多个标签用逗号分隔"
          >
            <Input placeholder="例如：管理, 计划, 项目" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 查看详情弹窗 */}
      <Modal
        title="知识卡片详情"
        open={isViewModalOpen}
        onCancel={() => {
          setIsViewModalOpen(false)
          setViewingPrompt(null)
        }}
        footer={[
          <Button key="close" onClick={() => {
            setIsViewModalOpen(false)
            setViewingPrompt(null)
          }}>
            关闭
          </Button>
        ]}
        width={700}
      >
        {viewingPrompt && (
          <div>
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 16, fontWeight: 500, marginBottom: 8 }}>
                {viewingPrompt.title}
              </div>
              <Space size={8}>
                <Tag color="default">
                  {viewingPrompt.category === 'business' && '商业'}
                  {viewingPrompt.category === 'tech' && '技术'}
                  {viewingPrompt.category === 'analysis' && '分析'}
                  {viewingPrompt.category === 'creative' && '创意'}
                  {viewingPrompt.category === 'general' && '通用'}
                </Tag>
                {viewingPrompt.tags?.map((tag: string) => (
                  <Tag key={tag} color="processing">
                    {tag}
                  </Tag>
                ))}
              </Space>
            </div>
            <Divider />
            <div style={{ 
              fontSize: 14, 
              lineHeight: 1.8,
              whiteSpace: 'pre-wrap',
              maxHeight: 500,
              overflow: 'auto',
              padding: '12px',
              background: '#f5f5f5',
              borderRadius: 4
            }}>
              {viewingPrompt.content}
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}

export default ChatPage
