/**
 * 工具调用消息渲染组件
 */
import React, { useState } from 'react';
import { Collapse, Tag } from 'antd';
import { ToolOutlined } from '@ant-design/icons';
import type { ToolChunk } from '../../types/messageTypes';

const { Panel } = Collapse;

interface ToolMessageProps {
  chunk: ToolChunk;
}

const ToolMessage: React.FC<ToolMessageProps> = ({ chunk }) => {
  const [activeKey, setActiveKey] = useState<string | string[]>([]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      case 'running':
        return 'processing';
      default:
        return 'default';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed':
        return '已完成';
      case 'failed':
        return '失败';
      case 'running':
        return '执行中';
      case 'pending':
        return '等待中';
      default:
        return status;
    }
  };

  return (
    <div style={{ margin: '8px 0' }}>
      <Collapse
        activeKey={activeKey}
        onChange={setActiveKey}
        bordered={false}
        style={{
          backgroundColor: '#fafafa',
          border: '1px solid #e8e8e8',
          borderRadius: '4px',
        }}
      >
        <Panel
          header={
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <ToolOutlined style={{ color: '#52c41a' }} />
              <span style={{ fontWeight: 500 }}>
                工具调用：{chunk.tool_name}
              </span>
              <Tag color={getStatusColor(chunk.status)}>
                {getStatusText(chunk.status)}
              </Tag>
            </div>
          }
          key="1"
        >
          <div style={{ padding: '8px 0' }}>
            <div style={{ marginBottom: '12px' }}>
              <div style={{ 
                fontWeight: 500, 
                marginBottom: '4px',
                color: '#666',
                fontSize: '13px'
              }}>
                输入参数：
              </div>
              <pre style={{
                backgroundColor: '#f5f5f5',
                padding: '8px 12px',
                borderRadius: '4px',
                margin: 0,
                fontSize: '12px',
                overflow: 'auto',
              }}>
                {JSON.stringify(chunk.tool_input, null, 2)}
              </pre>
            </div>

            {chunk.tool_output && (
              <div>
                <div style={{ 
                  fontWeight: 500, 
                  marginBottom: '4px',
                  color: '#666',
                  fontSize: '13px'
                }}>
                  输出结果：
                </div>
                <div style={{
                  backgroundColor: '#f5f5f5',
                  padding: '8px 12px',
                  borderRadius: '4px',
                  fontSize: '13px',
                  lineHeight: '1.6',
                  whiteSpace: 'pre-wrap',
                }}>
                  {chunk.tool_output}
                </div>
              </div>
            )}

            {chunk.error && (
              <div style={{ marginTop: '12px' }}>
                <div style={{ 
                  fontWeight: 500, 
                  marginBottom: '4px',
                  color: '#ff4d4f',
                  fontSize: '13px'
                }}>
                  错误信息：
                </div>
                <div style={{
                  backgroundColor: '#fff2f0',
                  padding: '8px 12px',
                  borderRadius: '4px',
                  color: '#ff4d4f',
                  fontSize: '13px',
                }}>
                  {chunk.error}
                </div>
              </div>
            )}
          </div>
        </Panel>
      </Collapse>
    </div>
  );
};

export default ToolMessage;
