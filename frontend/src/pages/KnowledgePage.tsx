import { useState, useEffect } from 'react'
import {
  Card,
  Button,
  Modal,
  Form,
  Input,
  List,
  message,
  Tabs,
  Space,
  Popconfirm,
  Tag,
  Empty,
  Table,
  Statistic,
  Select,
} from 'antd'
import {
  PlusOutlined,
  DeleteOutlined,
  FileTextOutlined,
  SearchOutlined,
  ThunderboltOutlined,
  EditOutlined,
  DiffOutlined,
  SendOutlined,
} from '@ant-design/icons'
import { knowledgeApi } from '../api/services'
import type { KnowledgeBase, Document, SearchResult, RolePreset } from '../api/types'
import MarkdownEditor from '../components/MarkdownEditor'
import './KnowledgePage.css'

const { TextArea } = Input
const { Option } = Select

const KnowledgePage = () => {
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([])
  const [selectedKB, setSelectedKB] = useState<KnowledgeBase | null>(null)
  const [documents, setDocuments] = useState<Document[]>([])
  const [searchResults, setSearchResults] = useState<SearchResult[]>([])
  const [rolePresets, setRolePresets] = useState<RolePreset[]>([])
  const [filteredPresets, setFilteredPresets] = useState<RolePreset[]>([])
  const [loading, setLoading] = useState(false)
  
  const [kbModalVisible, setKbModalVisible] = useState(false)
  const [docModalVisible, setDocModalVisible] = useState(false)
  const [presetDetailModalVisible, setPresetDetailModalVisible] = useState(false)
  const [presetEditModalVisible, setPresetEditModalVisible] = useState(false)
  const [presetCreateModalVisible, setPresetCreateModalVisible] = useState(false)
  const [selectedPreset, setSelectedPreset] = useState<RolePreset | null>(null)
  
  // AI功能状态
  const [aiGenerating, setAiGenerating] = useState(false)
  const [aiOptimizing, setAiOptimizing] = useState(false)
  const [originalContent, setOriginalContent] = useState<string>('')
  const [optimizedContent, setOptimizedContent] = useState<string>('')
  const [compareModalVisible, setCompareModalVisible] = useState(false)
  const [aiGenerateModalVisible, setAiGenerateModalVisible] = useState(false)
  const [generateRequirement, setGenerateRequirement] = useState<string>('')
  const [aiOptimizeModalVisible, setAiOptimizeModalVisible] = useState(false)
  const [optimizeRequirement, setOptimizeRequirement] = useState<string>('')
  
  const [categoryFilter, setCategoryFilter] = useState<string>('all')
  const [searchText, setSearchText] = useState<string>('')
  
  // 条件查询状态
  const [filterCategory, setFilterCategory] = useState<string>('')
  const [filterTags, setFilterTags] = useState<string>('')
  const [filterTitle, setFilterTitle] = useState<string>('')
  
  const [kbForm] = Form.useForm()
  const [docForm] = Form.useForm()
  const [searchForm] = Form.useForm()
  const [presetForm] = Form.useForm()

  useEffect(() => {
    loadKnowledgeBases()
    loadRolePresets(true) // 首次加载显示消息
  }, [])

  useEffect(() => {
    if (selectedKB) {
      loadDocuments(selectedKB.id)
    }
  }, [selectedKB])

  // 筛选预设
  useEffect(() => {
    let filtered = rolePresets

    // 按分类筛选
    if (categoryFilter !== 'all') {
      filtered = filtered.filter(preset => preset.category === categoryFilter)
    }

    // 按搜索文本筛选
    if (searchText.trim()) {
      const searchLower = searchText.toLowerCase()
      filtered = filtered.filter(preset => 
        preset.title.toLowerCase().includes(searchLower) ||
        preset.content.toLowerCase().includes(searchLower) ||
        (preset.tags && preset.tags.some(tag => tag.toLowerCase().includes(searchLower)))
      )
    }

    setFilteredPresets(filtered)
  }, [rolePresets, categoryFilter, searchText])

  const loadKnowledgeBases = async () => {
    setLoading(true)
    try {
      const data = await knowledgeApi.getKnowledgeBases()
      setKnowledgeBases(data)
    } catch (error) {
      message.error('加载知识库失败')
    } finally {
      setLoading(false)
    }
  }

  const loadDocuments = async (kbId: number) => {
    setLoading(true)
    try {
      const data = await knowledgeApi.getDocuments(kbId)
      setDocuments(data)
    } catch (error) {
      message.error('加载文档失败')
    } finally {
      setLoading(false)
    }
  }

  const loadRolePresets = async (showMessage = false) => {
    setLoading(true)
    try {
      const params: any = { limit: 1000 }
      if (filterCategory) params.category = filterCategory
      if (filterTags) params.tags = filterTags
      if (filterTitle) params.title = filterTitle
      
      const data = await knowledgeApi.getRolePresets(params)
      console.log('加载的预设数据:', data)
      setRolePresets(data || [])
      if (showMessage && data && data.length > 0) {
        message.success(`成功加载 ${data.length} 个角色预设`)
      } else if (showMessage && (!data || data.length === 0)) {
        message.info('暂无角色预设数据')
      }
    } catch (error) {
      console.error('加载提示词卡片失败:', error)
      message.error('加载提示词卡片失败')
    } finally {
      setLoading(false)
    }
  }

  const handleCreatePreset = async (values: any) => {
    try {
      const tags = values.tags ? values.tags.split(',').map((t: string) => t.trim()).filter(Boolean) : []
      await knowledgeApi.createRolePreset({
        title: values.title,
        prompt_content: values.content,
        category: values.category || 'general',
        tags: tags
      })
      message.success('角色预设创建成功')
      setPresetCreateModalVisible(false)
      presetForm.resetFields()
      setOriginalContent('')
      setOptimizedContent('')
      setOptimizeRequirement('')
      loadRolePresets()
    } catch (error: any) {
      console.error('创建失败:', error)
      message.error(error?.response?.data?.detail || '创建角色预设失败')
    }
  }

  // 打开AI帮写需求输入对话框
  const handleAiGenerateClick = () => {
    const title = presetForm.getFieldValue('title')
    
    if (!title) {
      message.warning('请先输入卡片标题')
      return
    }
    
    setGenerateRequirement('')
    setAiGenerateModalVisible(true)
  }

  // AI帮写提示词
  const handleAiGenerate = async () => {
    if (!generateRequirement.trim()) {
      message.warning('请输入提示词需求')
      return
    }
    
    const title = presetForm.getFieldValue('title')
    const category = presetForm.getFieldValue('category')
    
    setAiGenerateModalVisible(false)
    setAiGenerating(true)
    
    try {
      const prompt = `请帮我生成一个专业的提示词（Prompt），用于角色预设。

基本信息：
- 标题：${title}
- 分类：${category || '通用'}
- 用户需求：${generateRequirement}

要求：
1. 根据用户需求生成详细、专业的提示词
2. 提示词应该结构清晰，包含以下部分：
   - 角色定义：明确AI的角色和定位
   - 核心能力：列出主要功能和能力
   - 工具调用策略：说明如何使用各种工具（如web_search、knowledge_base_search等）
   - 推理规划流程：展示思考过程
   - 输出要求：明确输出格式和质量要求
3. 使用Markdown格式，包含适当的标题和列表
4. 确保提示词详细、专业、易于理解

请直接输出提示词内容，不要包含其他解释。`
      
      const response = await knowledgeApi.generatePrompt({
        prompt: prompt,
        llm_config: {
          provider: 'dashscope',
          model: 'qwen3-max'
        }
      })
      
      console.log('AI生成响应:', response)
      
      if (response && response.success && response.content) {
        const generatedContent = response.content.trim()
        if (generatedContent) {
          presetForm.setFieldsValue({ content: generatedContent })
          setGenerateRequirement('')
          message.success('AI帮写完成')
        } else {
          console.error('AI生成的内容为空')
          message.error('AI生成的内容为空，请重试')
        }
      } else {
        console.error('AI生成失败，响应:', response)
        const errorMsg = response?.error || 'AI生成失败，请检查网络连接和API配置'
        message.error(errorMsg)
      }
    } catch (error: any) {
      console.error('AI生成异常:', error)
      console.error('错误详情:', {
        message: error?.message,
        response: error?.response?.data,
        status: error?.response?.status
      })
      
      let errorMessage = 'AI生成失败'
      if (error?.response?.data?.detail) {
        errorMessage = error.response.data.detail
      } else if (error?.response?.data?.message) {
        errorMessage = error.response.data.message
      } else if (error?.message) {
        errorMessage = error.message
      }
      
      message.error(errorMessage)
    } finally {
      setAiGenerating(false)
    }
  }

  // 打开AI优化需求输入对话框
  const handleAiOptimizeClick = () => {
    const currentContent = presetForm.getFieldValue('content')
    
    if (!currentContent || !currentContent.trim()) {
      message.warning('请先输入提示词内容')
      return
    }
    
    setOptimizeRequirement('')
    setAiOptimizeModalVisible(true)
  }

  // AI优化提示词
  const handleAiOptimize = async () => {
    const currentContent = presetForm.getFieldValue('content')
    
    if (!currentContent || !currentContent.trim()) {
      message.warning('请先输入提示词内容')
      return
    }
    
    // 构建优化提示词
    let optimizePrompt = `请优化以下提示词，使其更加专业、清晰、有效。

原提示词：
${currentContent}

优化要求：`
    
    // 如果用户输入了优化需求，添加到提示词中
    if (optimizeRequirement && optimizeRequirement.trim()) {
      optimizePrompt += `\n\n用户特别要求：${optimizeRequirement}\n\n`
    }
    
    optimizePrompt += `
1. 保持原意不变，但使表达更加清晰专业
2. 优化结构和格式，使其更易读
3. 补充缺失的重要信息
4. 确保逻辑清晰、条理分明
5. 使用Markdown格式，包含适当的标题和列表`

    if (optimizeRequirement && optimizeRequirement.trim()) {
      optimizePrompt += `\n6. 特别关注用户的要求：${optimizeRequirement}`
    }
    
    optimizePrompt += `\n\n请直接输出优化后的提示词内容，不要包含其他解释。`
    
    setAiOptimizeModalVisible(false)
    setAiOptimizing(true)
    try {
      const response = await knowledgeApi.generatePrompt({
        prompt: optimizePrompt,
        llm_config: {
          provider: 'dashscope',
          model: 'qwen3-max'
        }
      })
      
      console.log('AI优化响应:', response)
      
      if (response && response.success && response.content) {
        const optimized = response.content.trim()
        if (optimized) {
          setOriginalContent(currentContent)
          setOptimizedContent(optimized)
          setOptimizeRequirement('')
          setCompareModalVisible(true)
          message.success('AI优化完成，请查看对比')
        } else {
          console.error('AI优化的内容为空')
          message.error('AI优化的内容为空，请重试')
        }
      } else {
        console.error('AI优化失败，响应:', response)
        const errorMsg = response?.error || 'AI优化失败，请检查网络连接和API配置'
        message.error(errorMsg)
      }
    } catch (error: any) {
      console.error('AI优化异常:', error)
      console.error('错误详情:', {
        message: error?.message,
        response: error?.response?.data,
        status: error?.response?.status
      })
      
      let errorMessage = 'AI优化失败'
      if (error?.response?.data?.detail) {
        errorMessage = error.response.data.detail
      } else if (error?.response?.data?.message) {
        errorMessage = error.response.data.message
      } else if (error?.message) {
        errorMessage = error.message
      }
      
      message.error(errorMessage)
    } finally {
      setAiOptimizing(false)
    }
  }

  // 应用优化后的内容
  const handleApplyOptimized = () => {
    presetForm.setFieldsValue({ content: optimizedContent })
    setCompareModalVisible(false)
    message.success('已应用优化后的内容')
  }

  const handleEditPreset = async (values: any) => {
    if (!selectedPreset?.id) {
      message.error('预设ID不存在，无法更新')
      return
    }
    
    try {
      const tags = values.tags ? values.tags.split(',').map((t: string) => t.trim()).filter(Boolean) : []
      await knowledgeApi.updateRolePreset(selectedPreset.id, {
        title: values.title,
        prompt_content: values.content,
        category: values.category,
        tags: tags
      })
      message.success('角色预设更新成功')
      setPresetEditModalVisible(false)
      setSelectedPreset(null)
      presetForm.resetFields()
      setOriginalContent('')
      setOptimizedContent('')
      setOptimizeRequirement('')
      loadRolePresets()
    } catch (error: any) {
      console.error('更新失败:', error)
      message.error(error?.response?.data?.detail || '更新角色预设失败')
    }
  }

  const handleDeletePreset = async (preset: RolePreset) => {
    if (!preset.id) {
      message.error('预设ID不存在，无法删除')
      return
    }
    
    try {
      await knowledgeApi.deleteRolePreset(preset.id)
      message.success('角色预设已删除')
      loadRolePresets()
    } catch (error: any) {
      console.error('删除失败:', error)
      message.error(error?.response?.data?.detail || '删除角色预设失败')
    }
  }

  const handleViewPreset = (preset: RolePreset) => {
    setSelectedPreset(preset)
    setPresetDetailModalVisible(true)
  }

  const handleEditPresetClick = (preset: RolePreset) => {
    if (!preset.id) {
      message.error('预设ID不存在，无法编辑')
      return
    }
    console.log('编辑预设:', preset)
    setSelectedPreset(preset)
    presetForm.setFieldsValue({
      title: preset.title,
      content: preset.content,
      category: preset.category,
      tags: preset.tags?.join(', ') || ''
    })
    setPresetEditModalVisible(true)
  }

  const handleFilter = () => {
    loadRolePresets()
  }

  const handleResetFilter = () => {
    setFilterCategory('')
    setFilterTags('')
    setFilterTitle('')
    setTimeout(() => {
      loadRolePresets()
    }, 100)
  }

  const handleCreateKB = async (values: any) => {
    try {
      await knowledgeApi.createKnowledgeBase(values)
      message.success('知识库创建成功')
      setKbModalVisible(false)
      kbForm.resetFields()
      loadKnowledgeBases()
    } catch (error) {
      message.error('创建知识库失败')
    }
  }

  const handleDeleteKB = async (id: number) => {
    try {
      await knowledgeApi.deleteKnowledgeBase(id)
      message.success('知识库已删除')
      if (selectedKB?.id === id) {
        setSelectedKB(null)
        setDocuments([])
      }
      loadKnowledgeBases()
    } catch (error) {
      message.error('删除知识库失败')
    }
  }

  const handleAddDocument = async (values: any) => {
    if (!selectedKB) return
    
    try {
      await knowledgeApi.addDocument(selectedKB.id, values)
      message.success('文档添加成功')
      setDocModalVisible(false)
      docForm.resetFields()
      loadDocuments(selectedKB.id)
    } catch (error) {
      message.error('添加文档失败')
    }
  }

  const handleSearch = async (values: any) => {
    if (!selectedKB) return
    
    setLoading(true)
    try {
      const response = await knowledgeApi.searchKnowledge(selectedKB.id, {
        query: values.query,
        top_k: 5,
      })
      setSearchResults(response.results)
      message.success(`找到 ${response.results.length} 条相关结果`)
    } catch (error) {
      message.error('搜索失败')
    } finally {
      setLoading(false)
    }
  }

  const getCategoryColor = (category: string) => {
    const colorMap: Record<string, string> = {
      tech: 'blue',
      business: 'green',
      analysis: 'purple',
      creative: 'orange',
      general: 'default',
    }
    return colorMap[category] || 'default'
  }

  const getCategoryName = (category: string) => {
    const nameMap: Record<string, string> = {
      tech: '技术',
      business: '商业',
      analysis: '分析',
      creative: '创意',
      general: '通用',
    }
    return nameMap[category] || category
  }

  return (
    <div className="knowledge-container">
      <div className="knowledge-header">
        <h2>知识库管理</h2>
      </div>

      <Tabs
        defaultActiveKey="knowledgebases"
        items={[
          {
            key: 'knowledgebases',
            label: '📚 知识库',
            children: (
              <div className="knowledge-content">
                <div className="kb-list">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                    <h3>知识库列表</h3>
                    <Button
                      type="primary"
                      icon={<PlusOutlined />}
                      onClick={() => setKbModalVisible(true)}
                    >
                      创建知识库
                    </Button>
                  </div>
                  <List
                    loading={loading}
                    dataSource={knowledgeBases}
                    locale={{ emptyText: <Empty description="暂无知识库" /> }}
                    renderItem={(kb) => (
                      <List.Item
                        className={selectedKB?.id === kb.id ? 'kb-item-selected' : 'kb-item'}
                        onClick={() => setSelectedKB(kb)}
                      >
                        <List.Item.Meta
                          title={kb.name}
                          description={kb.description || '暂无描述'}
                        />
                        <Popconfirm
                          title="确定要删除这个知识库吗？"
                          onConfirm={(e) => {
                            e?.stopPropagation()
                            handleDeleteKB(kb.id)
                          }}
                          okText="确定"
                          cancelText="取消"
                        >
                          <Button
                            danger
                            size="small"
                            icon={<DeleteOutlined />}
                            onClick={(e) => e.stopPropagation()}
                          />
                        </Popconfirm>
                      </List.Item>
                    )}
                  />
                </div>

                <div className="kb-details">
                  {selectedKB ? (
                    <Tabs
                      items={[
                {
                  key: 'documents',
                  label: (
                    <span>
                      <FileTextOutlined />
                      文档列表
                    </span>
                  ),
                  children: (
                    <div>
                      <div className="tab-header">
                        <Button
                          type="primary"
                          icon={<PlusOutlined />}
                          onClick={() => setDocModalVisible(true)}
                        >
                          添加文档
                        </Button>
                      </div>
                      <List
                        loading={loading}
                        dataSource={documents}
                        locale={{ emptyText: <Empty description="暂无文档" /> }}
                        renderItem={(doc) => (
                          <List.Item>
                            <List.Item.Meta
                              title={doc.title}
                              description={
                                <div>
                                  <div className="doc-content">
                                    {doc.content.substring(0, 150)}...
                                  </div>
                                  {doc.source && (
                                    <Tag color="blue" style={{ marginTop: 8 }}>
                                      来源: {doc.source}
                                    </Tag>
                                  )}
                                </div>
                              }
                            />
                          </List.Item>
                        )}
                      />
                    </div>
                  ),
                },
                {
                  key: 'search',
                  label: (
                    <span>
                      <SearchOutlined />
                      搜索测试
                    </span>
                  ),
                  children: (
                    <div>
                      <Form form={searchForm} onFinish={handleSearch}>
                        <Space.Compact style={{ width: '100%' }}>
                          <Form.Item
                            name="query"
                            style={{ flex: 1, marginBottom: 0 }}
                            rules={[{ required: true, message: '请输入搜索内容' }]}
                          >
                            <Input placeholder="输入搜索内容..." />
                          </Form.Item>
                          <Button
                            type="primary"
                            htmlType="submit"
                            icon={<SearchOutlined />}
                            loading={loading}
                          >
                            搜索
                          </Button>
                        </Space.Compact>
                      </Form>

                      <List
                        style={{ marginTop: 20 }}
                        dataSource={searchResults}
                        locale={{ emptyText: <Empty description="暂无搜索结果" /> }}
                        renderItem={(result, index) => (
                          <List.Item>
                            <Card size="small" style={{ width: '100%' }}>
                              <div className="search-result-header">
                                <span>结果 {index + 1}</span>
                                <Tag color="green">
                                  相似度: {(result.score * 100).toFixed(1)}%
                                </Tag>
                              </div>
                              <div className="search-result-content">
                                {result.content}
                              </div>
                            </Card>
                          </List.Item>
                        )}
                      />
                    </div>
                  ),
                },
              ]}
                    />
                  ) : (
                    <Empty description="请选择一个知识库" image={Empty.PRESENTED_IMAGE_SIMPLE} />
                  )}
                </div>
              </div>
            ),
          },
          {
            key: 'prompttemplates',
            label: '📝 角色预设库',
            children: (
              <div className="prompt-cards-container">
                {/* 顶部工具栏 */}
                <div className="cards-toolbar">
                  <div className="toolbar-left">
                    <h3>
                      <span>📚 角色预设库</span>
                      <Tag color={filteredPresets.length > 0 ? 'success' : 'default'} style={{ marginLeft: 8, fontSize: '12px' }}>
                        {filteredPresets.length}/{rolePresets.length}
                      </Tag>
                    </h3>
                  </div>
                  <div className="toolbar-right">
                    <Space size="small">
                      <Input.Search
                        placeholder="搜索预设..."
                        allowClear
                        size="small"
                        style={{ width: 200 }}
                        onChange={(e) => setSearchText(e.target.value)}
                        value={searchText}
                      />
                      <Button
                        size="small"
                        onClick={() => loadRolePresets()}
                        loading={loading}
                      >
                        刷新
                      </Button>
                    </Space>
                  </div>
                </div>

                {/* 分类筛选器 - 紧凑设计 */}
                <div className="category-filter">
                  <Space wrap size="small">
                    <Tag 
                      color={categoryFilter === 'all' ? 'blue' : 'default'} 
                      style={{ cursor: 'pointer', padding: '2px 10px', fontSize: '12px', borderRadius: '12px' }}
                      onClick={() => setCategoryFilter('all')}
                    >
                      全部 {rolePresets.length}
                    </Tag>
                    <Tag 
                      color={categoryFilter === 'tech' ? 'blue' : 'default'} 
                      style={{ cursor: 'pointer', padding: '2px 10px', fontSize: '12px', borderRadius: '12px' }}
                      onClick={() => setCategoryFilter('tech')}
                    >
                      💻 技术 {rolePresets.filter(p => p.category === 'tech').length}
                    </Tag>
                    <Tag 
                      color={categoryFilter === 'business' ? 'green' : 'default'} 
                      style={{ cursor: 'pointer', padding: '2px 10px', fontSize: '12px', borderRadius: '12px' }}
                      onClick={() => setCategoryFilter('business')}
                    >
                      📊 商业 {rolePresets.filter(p => p.category === 'business').length}
                    </Tag>
                    <Tag 
                      color={categoryFilter === 'analysis' ? 'purple' : 'default'} 
                      style={{ cursor: 'pointer', padding: '2px 10px', fontSize: '12px', borderRadius: '12px' }}
                      onClick={() => setCategoryFilter('analysis')}
                    >
                      🔍 分析 {rolePresets.filter(p => p.category === 'analysis').length}
                    </Tag>
                    <Tag 
                      color={categoryFilter === 'creative' ? 'orange' : 'default'} 
                      style={{ cursor: 'pointer', padding: '2px 10px', fontSize: '12px', borderRadius: '12px' }}
                      onClick={() => setCategoryFilter('creative')}
                    >
                      🎨 创意 {rolePresets.filter(p => p.category === 'creative').length}
                    </Tag>
                  </Space>
                </div>
                
                {/* 卡片列表 */}
                {loading && rolePresets.length === 0 ? (
                  <div style={{ textAlign: 'center', padding: '100px 0' }}>
                    <Empty description="正在加载角色预设..." />
                  </div>
                ) : rolePresets.length === 0 ? (
                  <div style={{ textAlign: 'center', padding: '100px 0' }}>
                    <Empty 
                      description={
                        <div>
                          <p>暂无角色预设</p>
                          <p style={{ color: '#999', fontSize: '14px', marginTop: '8px' }}>
                            请运行: <code style={{ padding: '2px 6px', background: 'rgba(255,255,255,0.1)', borderRadius: '4px', color: 'var(--agent-primary-color)' }}>cd backend && python create_knowledge_cards.py</code>
                          </p>
                        </div>
                      }
                    />
                  </div>
                ) : filteredPresets.length === 0 ? (
                  <div style={{ textAlign: 'center', padding: '100px 0' }}>
                    <Empty description="没有符合条件的预设" />
                  </div>
                ) : (
                  <List
                    className="cards-grid"
                    dataSource={filteredPresets}
                    grid={{ gutter: 16, xs: 1, sm: 2, md: 2, lg: 3, xl: 4, xxl: 4 }}
                    renderItem={(preset) => (
                      <List.Item>
                        <Card
                          className="prompt-card"
                          hoverable
                          onClick={() => handleViewPreset(preset)}
                        >
                          <div className="card-header">
                            <h4 className="card-title">{preset.title}</h4>
                            <Tag color={getCategoryColor(preset.category)}>
                              {getCategoryName(preset.category)}
                            </Tag>
                          </div>
                          
                          {preset.tags && preset.tags.length > 0 && (
                            <div className="card-tags">
                              <Space wrap size="small">
                                {preset.tags.slice(0, 3).map((tag, idx) => (
                                  <Tag key={idx} color="cyan" style={{ fontSize: '12px' }}>{tag}</Tag>
                                ))}
                                {preset.tags.length > 3 && (
                                  <Tag color="default" style={{ fontSize: '12px' }}>+{preset.tags.length - 3}</Tag>
                                )}
                              </Space>
                            </div>
                          )}
                          
                          <div className="card-content">
                            {preset.content.substring(0, 150)}
                            {preset.content.length > 150 && '...'}
                          </div>
                          
                          <div className="card-footer">
                            <Button type="link" size="small" onClick={(e) => {
                              e.stopPropagation()
                              handleViewPreset(preset)
                            }}>
                              查看详情 →
                            </Button>
                          </div>
                        </Card>
                      </List.Item>
                    )}
                  />
                )}
              </div>
            ),
          },
          {
            key: 'promptcards',
            label: '🎯 角色预设管理',
            children: (
              <div style={{ padding: '20px', minHeight: '500px' }}>
                <div style={{ marginBottom: 24 }}>
                  <h3 style={{ marginBottom: 16 }}>📊 角色预设统计</h3>
                  <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
                    <Card style={{ flex: 1, minWidth: '200px' }}>
                      <Statistic title="总预设数" value={rolePresets.length} />
                    </Card>
                    <Card style={{ flex: 1, minWidth: '200px' }}>
                      <Statistic title="技术类" value={rolePresets.filter(p => p.category === 'tech').length} />
                    </Card>
                    <Card style={{ flex: 1, minWidth: '200px' }}>
                      <Statistic title="商业类" value={rolePresets.filter(p => p.category === 'business').length} />
                    </Card>
                    <Card style={{ flex: 1, minWidth: '200px' }}>
                      <Statistic title="分析类" value={rolePresets.filter(p => p.category === 'analysis').length} />
                    </Card>
                    <Card style={{ flex: 1, minWidth: '200px' }}>
                      <Statistic title="创意类" value={rolePresets.filter(p => p.category === 'creative').length} />
                    </Card>
                  </div>
                </div>
                
                {/* 条件查询表单 */}
                <Card style={{ marginBottom: 16 }}>
                  <Form layout="inline" onFinish={handleFilter}>
                    <Form.Item label="标题">
                      <Input
                        placeholder="搜索标题"
                        value={filterTitle}
                        onChange={(e) => setFilterTitle(e.target.value)}
                        style={{ width: 200 }}
                        allowClear
                      />
                    </Form.Item>
                    <Form.Item label="分类">
                      <Select
                        placeholder="选择分类"
                        value={filterCategory || undefined}
                        onChange={(value) => setFilterCategory(value || '')}
                        style={{ width: 150 }}
                        allowClear
                      >
                        <Option value="tech">技术</Option>
                        <Option value="business">商业</Option>
                        <Option value="analysis">分析</Option>
                        <Option value="creative">创意</Option>
                        <Option value="general">通用</Option>
                      </Select>
                    </Form.Item>
                    <Form.Item label="标签">
                      <Input
                        placeholder="多个标签用逗号分隔"
                        value={filterTags}
                        onChange={(e) => setFilterTags(e.target.value)}
                        style={{ width: 200 }}
                        allowClear
                      />
                    </Form.Item>
                    <Form.Item>
                      <Space>
                        <Button type="primary" htmlType="submit" icon={<SearchOutlined />}>
                          查询
                        </Button>
                        <Button onClick={handleResetFilter}>
                          重置
                        </Button>
                      </Space>
                    </Form.Item>
                  </Form>
                </Card>
                
                <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h3 style={{ margin: 0 }}>预设管理</h3>
                  <Space>
                    <Button onClick={() => loadRolePresets()} loading={loading}>
                      刷新列表
                    </Button>
                    <Button
                      type="primary"
                      icon={<PlusOutlined />}
                      onClick={() => {
                        setSelectedPreset(null)
                        presetForm.resetFields()
                        setPresetCreateModalVisible(true)
                      }}
                    >
                      创建预设
                    </Button>
                  </Space>
                </div>
                
                <Table
                  loading={loading}
                  dataSource={rolePresets}
                  rowKey={(record) => record.id || record.title}
                  columns={[
                    {
                      title: '序号',
                      dataIndex: 'index',
                      key: 'index',
                      width: 60,
                      render: (_: any, __: any, index: number) => index + 1,
                    },
                    {
                      title: '标题',
                      dataIndex: 'title',
                      key: 'title',
                      ellipsis: true,
                    },
                    {
                      title: '分类',
                      dataIndex: 'category',
                      key: 'category',
                      width: 100,
                      render: (category: string) => {
                        const colorMap: Record<string, string> = {
                          tech: 'blue',
                          business: 'green',
                          analysis: 'purple',
                          creative: 'orange',
                          general: 'default',
                        }
                        const nameMap: Record<string, string> = {
                          tech: '技术',
                          business: '商业',
                          analysis: '分析',
                          creative: '创意',
                          general: '通用',
                        }
                        return <Tag color={colorMap[category] || 'default'}>{nameMap[category] || category}</Tag>
                      },
                    },
                    {
                      title: '标签',
                      dataIndex: 'tags',
                      key: 'tags',
                      width: 200,
                      ellipsis: true,
                      render: (tags: string[]) => (
                        <Space wrap size="small">
                          {tags && tags.slice(0, 3).map((tag, idx) => (
                            <Tag key={idx} color="cyan">{tag}</Tag>
                          ))}
                          {tags && tags.length > 3 && <span>+{tags.length - 3}</span>}
                        </Space>
                      ),
                    },
                    {
                      title: '内容预览',
                      dataIndex: 'content',
                      key: 'content',
                      ellipsis: true,
                      render: (content: string) => content?.substring(0, 50) + '...',
                    },
                    {
                      title: '操作',
                      key: 'action',
                      width: 200,
                      fixed: 'right',
                      render: (_: any, record: RolePreset) => (
                        <Space size="small">
                          <Button 
                            type="link" 
                            size="small"
                            onClick={() => handleViewPreset(record)}
                          >
                            查看
                          </Button>
                          <Button 
                            type="link" 
                            size="small"
                            onClick={() => handleEditPresetClick(record)}
                          >
                            编辑
                          </Button>
                          <Popconfirm
                            title="确定要删除这个预设吗？"
                            onConfirm={() => handleDeletePreset(record)}
                            okText="确定"
                            cancelText="取消"
                          >
                            <Button type="link" size="small" danger>
                              删除
                            </Button>
                          </Popconfirm>
                        </Space>
                      ),
                    },
                  ]}
                  pagination={{
                    pageSize: 10,
                    showSizeChanger: true,
                    showTotal: (total) => `共 ${total} 张卡片`,
                  }}
                />
              </div>
            ),
          },
        ]}
      />

      {/* 创建知识库Modal */}
      <Modal
        title="创建知识库"
        open={kbModalVisible}
        onCancel={() => setKbModalVisible(false)}
        footer={null}
      >
        <Form form={kbForm} onFinish={handleCreateKB} layout="vertical">
          <Form.Item
            name="name"
            label="知识库名称"
            rules={[{ required: true, message: '请输入知识库名称' }]}
          >
            <Input placeholder="例如: 产品文档" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <TextArea rows={3} placeholder="知识库的用途和内容说明" />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                创建
              </Button>
              <Button onClick={() => setKbModalVisible(false)}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 添加文档Modal */}
      <Modal
        title="添加文档"
        open={docModalVisible}
        onCancel={() => setDocModalVisible(false)}
        footer={null}
        width={700}
      >
        <Form form={docForm} onFinish={handleAddDocument} layout="vertical">
          <Form.Item
            name="title"
            label="文档标题"
            rules={[{ required: true, message: '请输入文档标题' }]}
          >
            <Input placeholder="文档标题" />
          </Form.Item>
          <Form.Item
            name="content"
            label="文档内容"
            rules={[{ required: true, message: '请输入文档内容' }]}
          >
            <TextArea rows={10} placeholder="输入文档内容..." />
          </Form.Item>
          <Form.Item name="source" label="来源">
            <Input placeholder="例如: https://example.com/doc" />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                添加
              </Button>
              <Button onClick={() => setDocModalVisible(false)}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 预设详情Modal */}
      <Modal
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span>{selectedPreset?.title}</span>
            {selectedPreset && (
              <Tag color={getCategoryColor(selectedPreset.category)}>
                {getCategoryName(selectedPreset.category)}
              </Tag>
            )}
          </div>
        }
        open={presetDetailModalVisible}
        onCancel={() => {
          setPresetDetailModalVisible(false)
          setSelectedPreset(null)
        }}
        width={800}
        footer={[
          <Button key="close" onClick={() => setPresetDetailModalVisible(false)}>
            关闭
          </Button>,
          <Button 
            key="copy" 
            type="primary"
            onClick={() => {
              if (selectedPreset) {
                navigator.clipboard.writeText(selectedPreset.content)
                message.success('已复制到剪贴板')
              }
            }}
          >
            复制内容
          </Button>,
        ]}
      >
        {selectedPreset && (
          <div className="card-detail-content">
            {/* 标签 */}
            {selectedPreset.tags && selectedPreset.tags.length > 0 && (
              <div style={{ marginBottom: 16 }}>
                <div style={{ fontWeight: 600, marginBottom: 8, color: '#666' }}>标签：</div>
                <Space wrap>
                  {selectedPreset.tags.map((tag, idx) => (
                    <Tag key={idx} color="cyan">{tag}</Tag>
                  ))}
                </Space>
              </div>
            )}
            
            {/* 内容 */}
            <div style={{ marginTop: 20 }}>
              <div style={{ fontWeight: 600, marginBottom: 12, color: '#666' }}>提示词内容：</div>
              <div style={{ 
                background: 'rgba(0, 0, 0, 0.3)', 
                padding: '16px', 
                borderRadius: '8px',
                whiteSpace: 'pre-wrap',
                lineHeight: '1.8',
                fontSize: '14px',
                maxHeight: '500px',
                overflow: 'auto',
                border: '1px solid var(--agent-glass-border)',
                color: 'var(--agent-text-color)'
              }}>
                {selectedPreset.content}
              </div>
            </div>
          </div>
        )}
      </Modal>

      {/* 创建预设Modal */}
      <Modal
        title="创建角色预设"
        open={presetCreateModalVisible}
        onCancel={() => {
          setPresetCreateModalVisible(false)
          presetForm.resetFields()
          setOriginalContent('')
          setOptimizedContent('')
          setOptimizeRequirement('')
        }}
        footer={null}
        width={1200}
      >
        <Form form={presetForm} onFinish={handleCreatePreset} layout="vertical">
          <Form.Item
            name="title"
            label="预设标题"
            rules={[{ required: true, message: '请输入预设标题' }]}
          >
            <Input placeholder="例如: 项目管理助手" />
          </Form.Item>
          <Form.Item
            name="content"
            label={
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
                <span>提示词内容（支持Markdown）</span>
                <Space>
                  <Button
                    type="default"
                    size="small"
                    icon={<ThunderboltOutlined />}
                    loading={aiGenerating}
                    onClick={handleAiGenerateClick}
                  >
                    AI帮写
                  </Button>
                  <Button
                    type="default"
                    size="small"
                    icon={<EditOutlined />}
                    loading={aiOptimizing}
                    onClick={handleAiOptimizeClick}
                  >
                    AI优化
                  </Button>
                </Space>
              </div>
            }
            rules={[{ required: true, message: '请输入提示词内容' }]}
          >
            <MarkdownEditor 
              placeholder="输入详细的提示词内容，或使用AI帮写/优化功能..." 
              rows={15}
            />
          </Form.Item>
          <Form.Item
            name="category"
            label="分类"
            rules={[{ required: true, message: '请选择分类' }]}
          >
            <Select placeholder="选择分类">
              <Option value="tech">技术</Option>
              <Option value="business">商业</Option>
              <Option value="analysis">分析</Option>
              <Option value="creative">创意</Option>
              <Option value="general">通用</Option>
            </Select>
          </Form.Item>
          <Form.Item
            name="tags"
            label="标签"
            help="多个标签用逗号分隔"
          >
            <Input placeholder="例如: 管理, 计划, 项目" />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                创建
              </Button>
              <Button onClick={() => {
                setCardCreateModalVisible(false)
                cardForm.resetFields()
                setOriginalContent('')
                setOptimizedContent('')
                setOptimizeRequirement('')
              }}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 优化对比Modal */}
      <Modal
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <DiffOutlined />
            <span>优化前后对比</span>
          </div>
        }
        open={compareModalVisible}
        onCancel={() => setCompareModalVisible(false)}
        width={1000}
        footer={[
          <Button key="cancel" onClick={() => setCompareModalVisible(false)}>
            取消
          </Button>,
          <Button key="apply" type="primary" onClick={handleApplyOptimized}>
            应用优化后的内容
          </Button>
        ]}
      >
        <div style={{ display: 'flex', gap: 16, height: '60vh' }}>
          {/* 优化前 */}
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
            <div style={{ 
              padding: '8px 12px', 
              background: 'rgba(250, 173, 20, 0.1)', 
              border: '1px solid rgba(250, 173, 20, 0.3)',
              borderRadius: '4px 4px 0 0',
              fontWeight: 500,
              color: '#ffc069'
            }}>
              优化前
            </div>
            <div style={{
              flex: 1,
              padding: '16px',
              background: 'rgba(0, 0, 0, 0.2)',
              border: '1px solid var(--agent-glass-border)',
              borderTop: 'none',
              borderRadius: '0 0 4px 4px',
              overflow: 'auto',
              whiteSpace: 'pre-wrap',
              lineHeight: 1.8,
              fontSize: 14,
              color: 'var(--agent-text-secondary)'
            }}>
              {originalContent}
            </div>
          </div>
          
          {/* 优化后 */}
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
            <div style={{ 
              padding: '8px 12px', 
              background: 'rgba(82, 196, 26, 0.1)', 
              border: '1px solid rgba(82, 196, 26, 0.3)',
              borderRadius: '4px 4px 0 0',
              fontWeight: 500,
              color: '#95de64'
            }}>
              优化后
            </div>
            <div style={{
              flex: 1,
              padding: '16px',
              background: 'rgba(0, 0, 0, 0.2)',
              border: '1px solid var(--agent-glass-border)',
              borderTop: 'none',
              borderRadius: '0 0 4px 4px',
              overflow: 'auto',
              whiteSpace: 'pre-wrap',
              lineHeight: 1.8,
              fontSize: 14,
              color: 'var(--agent-text-secondary)'
            }}>
              {optimizedContent}
            </div>
          </div>
        </div>
      </Modal>

      {/* AI帮写需求输入Modal */}
      <Modal
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <ThunderboltOutlined style={{ color: '#1890ff' }} />
            <span>AI帮写提示词</span>
          </div>
        }
        open={aiGenerateModalVisible}
        onOk={handleAiGenerate}
        onCancel={() => {
          setAiGenerateModalVisible(false)
          setGenerateRequirement('')
        }}
        okText="生成"
        cancelText="取消"
        confirmLoading={aiGenerating}
        width={600}
      >
        <div style={{ marginBottom: 16 }}>
          <div style={{ marginBottom: 8, color: '#666', fontSize: 13 }}>
            请描述您希望生成的提示词需求，AI将根据您的描述生成专业的提示词内容。
          </div>
          <div style={{ marginBottom: 8, color: '#999', fontSize: 12 }}>
            例如：需要创建一个项目管理助手，能够帮助制定计划、分配任务、跟踪进度等。
          </div>
        </div>
        <TextArea
          rows={6}
          placeholder="请输入您的提示词需求，描述越详细，生成的内容越符合您的期望..."
          value={generateRequirement}
          onChange={(e) => setGenerateRequirement(e.target.value)}
          autoFocus
        />
        <div style={{ marginTop: 12, padding: '8px 12px', background: '#f5f5f5', borderRadius: 4, fontSize: 12, color: '#666' }}>
          💡 提示：您可以描述AI的角色、功能、使用场景等，AI会根据您的描述生成完整的提示词。
        </div>
      </Modal>

      {/* AI优化需求输入Modal */}
      <Modal
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <EditOutlined style={{ color: '#52c41a' }} />
            <span>AI优化提示词</span>
          </div>
        }
        open={aiOptimizeModalVisible}
        onCancel={() => {
          setAiOptimizeModalVisible(false)
          setOptimizeRequirement('')
        }}
        footer={null}
        width={600}
      >
        <div style={{ marginBottom: 16 }}>
          <div style={{ marginBottom: 8, color: '#666', fontSize: 13 }}>
            请描述您希望如何优化提示词，AI将根据您的需求进行针对性优化。
          </div>
          <div style={{ marginBottom: 8, color: '#999', fontSize: 12 }}>
            例如：让表达更简洁、增加更多示例、优化结构层次等。如果不填写，将进行通用优化。
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
          <Input.TextArea
            rows={4}
            placeholder="需要我帮你怎么优化呢？"
            value={optimizeRequirement}
            onChange={(e) => setOptimizeRequirement(e.target.value)}
            onPressEnter={(e) => {
              if (e.shiftKey) {
                // Shift+Enter 换行
                return
              }
              // Enter 发送
              e.preventDefault()
              handleAiOptimize()
            }}
            autoFocus
            style={{ flex: 1 }}
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleAiOptimize}
            loading={aiOptimizing}
            style={{ height: 'auto', paddingTop: 8, paddingBottom: 8 }}
          >
            发送
          </Button>
        </div>
        <div style={{ marginTop: 12, padding: '8px 12px', background: '#f5f5f5', borderRadius: 4, fontSize: 12, color: '#666' }}>
          💡 提示：您可以描述具体的优化方向，如"更简洁"、"增加示例"、"优化结构"等。按Enter发送，Shift+Enter换行。
        </div>
      </Modal>

      {/* 编辑卡片Modal */}
      <Modal
        title="编辑角色预设"
        open={presetEditModalVisible}
        onCancel={() => {
          setPresetEditModalVisible(false)
          setSelectedPreset(null)
          presetForm.resetFields()
          setOriginalContent('')
          setOptimizedContent('')
          setOptimizeRequirement('')
        }}
        footer={null}
        width={1200}
      >
        <Form form={presetForm} onFinish={handleEditPreset} layout="vertical">
          <Form.Item
            name="title"
            label="预设标题"
            rules={[{ required: true, message: '请输入预设标题' }]}
          >
            <Input placeholder="例如: 项目管理助手" />
          </Form.Item>
          <Form.Item
            name="content"
            label={
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
                <span>提示词内容（支持Markdown）</span>
                <Space>
                  <Button
                    type="default"
                    size="small"
                    icon={<ThunderboltOutlined />}
                    loading={aiGenerating}
                    onClick={handleAiGenerateClick}
                  >
                    AI帮写
                  </Button>
                  <Button
                    type="default"
                    size="small"
                    icon={<EditOutlined />}
                    loading={aiOptimizing}
                    onClick={handleAiOptimizeClick}
                  >
                    AI优化
                  </Button>
                </Space>
              </div>
            }
            rules={[{ required: true, message: '请输入提示词内容' }]}
          >
            <MarkdownEditor 
              placeholder="输入详细的提示词内容，或使用AI帮写/优化功能..." 
              rows={15}
            />
          </Form.Item>
          <Form.Item
            name="category"
            label="分类"
            rules={[{ required: true, message: '请选择分类' }]}
          >
            <Select placeholder="选择分类">
              <Option value="tech">技术</Option>
              <Option value="business">商业</Option>
              <Option value="analysis">分析</Option>
              <Option value="creative">创意</Option>
              <Option value="general">通用</Option>
            </Select>
          </Form.Item>
          <Form.Item
            name="tags"
            label="标签"
            help="多个标签用逗号分隔"
          >
            <Input placeholder="例如: 管理, 计划, 项目" />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                保存
              </Button>
              <Button onClick={() => {
                setCardEditModalVisible(false)
                setSelectedCard(null)
                cardForm.resetFields()
                setOriginalContent('')
                setOptimizedContent('')
                setOptimizeRequirement('')
              }}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default KnowledgePage

