import React, { useCallback, useMemo, useEffect } from 'react'
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType,
  Position,
} from 'reactflow'
import 'reactflow/dist/style.css'
import dagre from 'dagre'
import { Card, Tag, Tooltip } from 'antd'
import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  CloseCircleOutlined,
  SyncOutlined,
} from '@ant-design/icons'
import type { PlanningTaskStep, TaskDependencyEdge } from '../api/types'

interface TaskDependencyGraphProps {
  tasks: PlanningTaskStep[]
  dependencies: TaskDependencyEdge[]
  onTaskClick?: (taskId: string) => void
}

const nodeWidth = 220
const nodeHeight = 120

const getLayoutedElements = (nodes: Node[], edges: Edge[]) => {
  const dagreGraph = new dagre.graphlib.Graph()
  dagreGraph.setDefaultEdgeLabel(() => ({}))
  dagreGraph.setGraph({ rankdir: 'TB', nodesep: 50, ranksep: 100 })

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: nodeWidth, height: nodeHeight })
  })

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target)
  })

  dagre.layout(dagreGraph)

  nodes.forEach((node) => {
    const nodeWithPosition = dagreGraph.node(node.id)
    node.targetPosition = Position.Top
    node.sourcePosition = Position.Bottom
    node.position = {
      x: nodeWithPosition.x - nodeWidth / 2,
      y: nodeWithPosition.y - nodeHeight / 2,
    }
  })

  return { nodes, edges }
}

const TaskDependencyGraph: React.FC<TaskDependencyGraphProps> = ({
  tasks,
  dependencies,
  onTaskClick,
}) => {
  // 节点配置
  const initialNodes: Node[] = useMemo(() => {
    return tasks.map((task) => {
      const statusConfig = {
        pending: { color: '#d9d9d9', icon: <ClockCircleOutlined />, label: '待执行' },
        in_progress: { color: '#1890ff', icon: <SyncOutlined spin />, label: '执行中' },
        completed: { color: '#52c41a', icon: <CheckCircleOutlined />, label: '已完成' },
        failed: { color: '#ff4d4f', icon: <CloseCircleOutlined />, label: '失败' },
      }[task.status] || { color: '#d9d9d9', icon: <ClockCircleOutlined />, label: '待执行' }

      return {
        id: task.step_id,
        type: 'default',
        position: { x: 0, y: 0 }, // 将由布局算法计算
        data: {
          label: (
            <Card
              size="small"
              style={{
                width: nodeWidth - 20,
                borderColor: statusConfig.color,
                borderWidth: 2,
                cursor: 'pointer',
              }}
              onClick={() => onTaskClick?.(task.step_id)}
            >
              <div style={{ marginBottom: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Tag color={statusConfig.color} icon={statusConfig.icon}>
                  {statusConfig.label}
                </Tag>
                {task.priority && (
                  <Tag color={task.priority === 'high' ? 'red' : task.priority === 'medium' ? 'orange' : 'default'}>
                    {task.priority === 'high' ? '高' : task.priority === 'medium' ? '中' : '低'}
                  </Tag>
                )}
              </div>
              <div style={{ fontSize: 12, color: '#666', marginBottom: 4, minHeight: 40 }}>
                {task.description}
              </div>
              {task.estimated_time && (
                <div style={{ fontSize: 11, color: '#999', marginTop: 4 }}>
                  预估: {task.estimated_time}
                </div>
              )}
            </Card>
          ),
        },
        style: {
          border: `2px solid ${statusConfig.color}`,
          borderRadius: 8,
        },
      }
    })
  }, [tasks, onTaskClick])

  // 边配置
  const initialEdges: Edge[] = useMemo(() => {
    return dependencies.map((dep) => ({
      id: `${dep.source}-${dep.target}`,
      source: dep.source,
      target: dep.target,
      type: 'smoothstep',
      animated: tasks.find((t) => t.step_id === dep.target)?.status === 'in_progress',
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: '#1890ff',
      },
      style: {
        strokeWidth: 2,
        stroke: '#1890ff',
      },
    }))
  }, [dependencies, tasks])

  // 布局算法
  const { nodes: layoutedNodes, edges: layoutedEdges } = useMemo(
    () => getLayoutedElements(initialNodes, initialEdges),
    [initialNodes, initialEdges]
  )

  const [nodes, setNodes, onNodesChange] = useNodesState(layoutedNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(layoutedEdges)

  useEffect(() => {
    const { nodes: newNodes, edges: newEdges } = getLayoutedElements(initialNodes, initialEdges)
    setNodes(newNodes)
    setEdges(newEdges)
  }, [initialNodes, initialEdges, setNodes, setEdges])

  return (
    <div style={{ width: '100%', height: '600px', border: '1px solid #d9d9d9', borderRadius: 8 }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={(event, node) => {
          onTaskClick?.(node.id)
        }}
        fitView
        fitViewOptions={{ padding: 0.2 }}
      >
        <Background />
        <Controls />
        <MiniMap />
      </ReactFlow>
    </div>
  )
}

export default TaskDependencyGraph

