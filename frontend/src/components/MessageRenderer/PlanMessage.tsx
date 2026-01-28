/**
 * 计划步骤消息渲染组件
 */
import React from 'react';
import { Tag } from 'antd';
import { 
  ClockCircleOutlined, 
  CheckCircleOutlined, 
  CloseCircleOutlined,
  SyncOutlined
} from '@ant-design/icons';
import type { PlanChunk } from '../../types/messageTypes';

interface PlanMessageProps {
  chunk: PlanChunk;
}

const PlanMessage: React.FC<PlanMessageProps> = ({ chunk }) => {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'failed':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
      case 'in_progress':
        return <SyncOutlined spin style={{ color: '#1890ff' }} />;
      default:
        return <ClockCircleOutlined style={{ color: '#d9d9d9' }} />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return '#52c41a';
      case 'failed':
        return '#ff4d4f';
      case 'in_progress':
        return '#1890ff';
      default:
        return '#d9d9d9';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed':
        return '已完成';
      case 'failed':
        return '失败';
      case 'in_progress':
        return '进行中';
      case 'pending':
        return '等待中';
      default:
        return status;
    }
  };

  return (
    <div style={{ margin: '12px 0' }}>
      <div style={{ 
        backgroundColor: '#f0f5ff',
        borderLeft: '3px solid #1890ff',
        padding: '12px 16px',
        borderRadius: '4px',
      }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
          <span style={{ fontSize: '18px' }}>📋</span>
          <div style={{ flex: 1 }}>
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '8px',
              marginBottom: '8px'
            }}>
              <span style={{ 
                fontWeight: 600, 
                color: '#1890ff',
                fontSize: '14px'
              }}>
                Step {chunk.step_number}
              </span>
              <Tag color={getStatusColor(chunk.status)}>
                {getStatusIcon(chunk.status)}
                <span style={{ marginLeft: '4px' }}>
                  {getStatusText(chunk.status)}
                </span>
              </Tag>
            </div>

            <div style={{ 
              fontSize: '14px',
              lineHeight: '1.6',
              marginBottom: chunk.result || chunk.substeps ? '12px' : 0
            }}>
              {chunk.description}
            </div>

            {chunk.substeps && chunk.substeps.length > 0 && (
              <div style={{ marginTop: '8px' }}>
                <div style={{ 
                  fontSize: '12px', 
                  color: '#666',
                  marginBottom: '4px'
                }}>
                  子步骤：
                </div>
                <ul style={{ 
                  margin: 0, 
                  paddingLeft: '20px',
                  fontSize: '13px',
                  color: '#666'
                }}>
                  {chunk.substeps.map((substep, index) => (
                    <li key={index} style={{ marginBottom: '4px' }}>
                      {substep}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {chunk.result && (
              <div style={{ 
                marginTop: '8px',
                paddingTop: '8px',
                borderTop: '1px solid #d9d9d9'
              }}>
                <div style={{ 
                  fontSize: '12px', 
                  color: '#666',
                  marginBottom: '4px'
                }}>
                  执行结果：
                </div>
                <div style={{ 
                  fontSize: '13px',
                  color: '#333',
                  lineHeight: '1.6',
                  whiteSpace: 'pre-wrap'
                }}>
                  {chunk.result}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PlanMessage;
