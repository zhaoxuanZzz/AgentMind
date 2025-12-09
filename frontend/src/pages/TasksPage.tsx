import { useState, useEffect } from 'react'
import {
  Card,
  Button,
  Modal,
  Form,
  Input,
  List,
  message,
  Tag,
  Space,
  Popconfirm,
  Timeline,
  Empty,
  Tabs,
  Select,
} from 'antd'
import {
  PlusOutlined,
  DeleteOutlined,
  ThunderboltOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined,
  RobotOutlined,
} from '@ant-design/icons'
import { taskApi, chatApi } from '../api/services'
import type { Task, TaskStep, LLMProvider, LLMConfig } from '../api/types'
import './TasksPage.css'

const { TextArea } = Input

const TasksPage = () => {
  const [tasks, setTasks] = useState<Task[]>([])
  const [selectedTask, setSelectedTask] = useState<Task | null>(null)
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [planModalVisible, setPlanModalVisible] = useState(false)
  const [form] = Form.useForm()
  const [planForm] = Form.useForm()
  const [llmProviders, setLlmProviders] = useState<LLMProvider[]>([])
  const [selectedProvider, setSelectedProvider] = useState<string | undefined>()
  const [selectedModel, setSelectedModel] = useState<string | undefined>()
  const [availableModels, setAvailableModels] = useState<Array<{id: string, name: string}>>([])

  useEffect(() => {
    loadTasks()
    loadLLMProviders()
  }, [])

  const loadTasks = async () => {
    setLoading(true)
    try {
      const data = await taskApi.getTasks()
      setTasks(data)
    } catch (error) {
      message.error('加载任务失败')
    } finally {
      setLoading(false)
    }
  }

  const loadLLMProviders = async () => {
    try {
      const data = await chatApi.getLLMProviders()
      setLlmProviders(data.providers)
      // 设置默认值
      if (data.default.provider) {
        setSelectedProvider(data.default.provider)
        const provider = data.providers.find(p => p.id === data.default.provider)
        if (provider) {
          setAvailableModels(provider.models)
          setSelectedModel(data.default.model || provider.models[0]?.id)
        }
      }
    } catch (error) {
      console.error('Failed to load LLM providers:', error)
    }
  }

  const handleProviderChange = (providerId: string) => {
    setSelectedProvider(providerId)
    const provider = llmProviders.find(p => p.id === providerId)
    if (provider) {
      setAvailableModels(provider.models)
      setSelectedModel(provider.models[0]?.id)
    }
  }

  const handleCreateTask = async (values: any) => {
    try {
      await taskApi.createTask(values)
      message.success('任务创建成功')
      setModalVisible(false)
      form.resetFields()
      loadTasks()
    } catch (error) {
      message.error('创建任务失败')
    }
  }

  const handlePlanTask = async (taskId: number) => {
    setLoading(true)
    try {
      const updatedTask = await taskApi.planExistingTask(taskId)
      message.success('任务规划已生成')
      setSelectedTask(updatedTask)
      loadTasks()
    } catch (error) {
      message.error('生成任务规划失败')
    } finally {
      setLoading(false)
    }
  }

  const handleQuickPlan = async (values: any) => {
    setLoading(true)
    try {
      const llmConfig: LLMConfig = {
        provider: selectedProvider,
        model: selectedModel,
      }
      
      const response = await taskApi.planTask({
        description: values.description,
        llm_config: llmConfig,
      })
      
      if (response.success) {
        Modal.info({
          title: '任务规划',
          width: 700,
          content: (
            <div>
              <div style={{ marginBottom: 16, whiteSpace: 'pre-wrap' }}>
                {response.plan}
              </div>
              {response.steps.length > 0 && (
                <Timeline
                  items={response.steps.map((step, idx) => ({
                    children: step.description,
                    color: 'blue',
                  }))}
                />
              )}
            </div>
          ),
        })
      }
      setPlanModalVisible(false)
      planForm.resetFields()
    } catch (error) {
      message.error('生成规划失败')
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteTask = async (id: number) => {
    try {
      await taskApi.deleteTask(id)
      message.success('任务已删除')
      if (selectedTask?.id === id) {
        setSelectedTask(null)
      }
      loadTasks()
    } catch (error) {
      message.error('删除任务失败')
    }
  }

  const handleUpdateStatus = async (taskId: number, status: string) => {
    try {
      await taskApi.updateTaskStatus(taskId, status)
      message.success('状态已更新')
      loadTasks()
      if (selectedTask?.id === taskId) {
        const updatedTask = await taskApi.getTask(taskId)
        setSelectedTask(updatedTask)
      }
    } catch (error) {
      message.error('更新状态失败')
    }
  }

  const getStatusTag = (status: string) => {
    const statusConfig: Record<string, { color: string; icon: any; text: string }> = {
      pending: { color: 'default', icon: <ClockCircleOutlined />, text: '待处理' },
      planned: { color: 'blue', icon: <ThunderboltOutlined />, text: '已规划' },
      in_progress: { color: 'processing', icon: <ThunderboltOutlined />, text: '进行中' },
      completed: { color: 'success', icon: <CheckCircleOutlined />, text: '已完成' },
      failed: { color: 'error', icon: <ExclamationCircleOutlined />, text: '失败' },
    }
    const config = statusConfig[status] || statusConfig.pending
    return (
      <Tag icon={config.icon} color={config.color}>
        {config.text}
      </Tag>
    )
  }

  return (
    <div className="tasks-container">
      <div className="tasks-header">
        <h2>任务规划与管理</h2>
        <Space>
          <Button
            type="default"
            icon={<ThunderboltOutlined />}
            onClick={() => setPlanModalVisible(true)}
          >
            快速规划
          </Button>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setModalVisible(true)}
          >
            创建任务
          </Button>
        </Space>
      </div>

      <div className="tasks-content">
        <div className="tasks-list">
          <h3>任务列表</h3>
          <List
            loading={loading}
            dataSource={tasks}
            locale={{ emptyText: <Empty description="暂无任务" /> }}
            renderItem={(task) => (
              <List.Item
                className={selectedTask?.id === task.id ? 'task-item-selected' : 'task-item'}
                onClick={() => setSelectedTask(task)}
              >
                <List.Item.Meta
                  title={
                    <Space>
                      {task.title}
                      {getStatusTag(task.status)}
                    </Space>
                  }
                  description={task.description.substring(0, 60) + '...'}
                />
                <Space>
                  {task.status === 'pending' && (
                    <Button
                      size="small"
                      icon={<ThunderboltOutlined />}
                      onClick={(e) => {
                        e.stopPropagation()
                        handlePlanTask(task.id)
                      }}
                    >
                      生成规划
                    </Button>
                  )}
                  <Popconfirm
                    title="确定要删除这个任务吗？"
                    onConfirm={(e) => {
                      e?.stopPropagation()
                      handleDeleteTask(task.id)
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
                </Space>
              </List.Item>
            )}
          />
        </div>

        <div className="task-details">
          {selectedTask ? (
            <Card
              title={
                <Space>
                  {selectedTask.title}
                  {getStatusTag(selectedTask.status)}
                </Space>
              }
              extra={
                <Space>
                  {selectedTask.status !== 'completed' && (
                    <Button
                      type="primary"
                      size="small"
                      icon={<CheckCircleOutlined />}
                      onClick={() => handleUpdateStatus(selectedTask.id, 'completed')}
                    >
                      标记完成
                    </Button>
                  )}
                </Space>
              }
            >
              <Tabs
                items={[
                  {
                    key: 'description',
                    label: '任务描述',
                    children: (
                      <div className="task-description">{selectedTask.description}</div>
                    ),
                  },
                  {
                    key: 'plan',
                    label: '执行计划',
                    children: selectedTask.plan ? (
                      <div>
                        <div className="plan-text">{selectedTask.plan.plan_text}</div>
                        {selectedTask.plan.steps && selectedTask.plan.steps.length > 0 && (
                          <div style={{ marginTop: 20 }}>
                            <h4>执行步骤:</h4>
                            <Timeline
                              items={selectedTask.plan.steps.map((step: TaskStep, idx: number) => ({
                                children: (
                                  <div>
                                    <div>{step.description}</div>
                                    <Tag
                                      color={step.status === 'completed' ? 'success' : 'default'}
                                      style={{ marginTop: 8 }}
                                    >
                                      {step.status}
                                    </Tag>
                                  </div>
                                ),
                                color: step.status === 'completed' ? 'green' : 'blue',
                              }))}
                            />
                          </div>
                        )}
                      </div>
                    ) : (
                      <Empty
                        description="暂无执行计划"
                        image={Empty.PRESENTED_IMAGE_SIMPLE}
                      >
                        <Button
                          type="primary"
                          icon={<ThunderboltOutlined />}
                          onClick={() => handlePlanTask(selectedTask.id)}
                          loading={loading}
                        >
                          生成执行计划
                        </Button>
                      </Empty>
                    ),
                  },
                ]}
              />
            </Card>
          ) : (
            <Empty description="请选择一个任务" image={Empty.PRESENTED_IMAGE_SIMPLE} />
          )}
        </div>
      </div>

      {/* 创建任务Modal */}
      <Modal
        title="创建任务"
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
      >
        <Form form={form} onFinish={handleCreateTask} layout="vertical">
          <Form.Item
            name="title"
            label="任务标题"
            rules={[{ required: true, message: '请输入任务标题' }]}
          >
            <Input placeholder="例如: 开发用户登录功能" />
          </Form.Item>
          <Form.Item
            name="description"
            label="任务描述"
            rules={[{ required: true, message: '请输入任务描述' }]}
          >
            <TextArea rows={5} placeholder="详细描述任务的需求和目标..." />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                创建
              </Button>
              <Button onClick={() => setModalVisible(false)}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 快速规划Modal */}
      <Modal
        title="快速任务规划"
        open={planModalVisible}
        onCancel={() => setPlanModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form form={planForm} onFinish={handleQuickPlan} layout="vertical">
          <Form.Item label="选择AI模型">
            <Space.Compact style={{ width: '100%' }}>
              <Select
                style={{ width: '50%' }}
                placeholder="选择AI提供商"
                value={selectedProvider}
                onChange={handleProviderChange}
                suffixIcon={<RobotOutlined />}
                options={llmProviders.map((provider) => ({
                  label: provider.name,
                  value: provider.id,
                }))}
              />
              {selectedProvider && availableModels.length > 0 && (
                <Select
                  style={{ width: '50%' }}
                  placeholder="选择模型版本"
                  value={selectedModel}
                  onChange={setSelectedModel}
                  options={availableModels.map((model) => ({
                    label: model.name,
                    value: model.id,
                  }))}
                />
              )}
            </Space.Compact>
          </Form.Item>
          <Form.Item
            name="description"
            label="任务描述"
            rules={[{ required: true, message: '请输入任务描述' }]}
          >
            <TextArea
              rows={6}
              placeholder="详细描述你想要完成的任务，AI将为你生成执行计划..."
            />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={loading}>
                生成规划
              </Button>
              <Button onClick={() => setPlanModalVisible(false)}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default TasksPage

