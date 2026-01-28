/**
 * 思考过程消息渲染组件
 */
import React from 'react';
import { Bubble } from '@ant-design/x';
import type { ThinkingChunk } from '../../types/messageTypes';

interface ThinkingMessageProps {
  chunk: ThinkingChunk;
}

const ThinkingMessage: React.FC<ThinkingMessageProps> = ({ chunk }) => {
  return (
    <Bubble
      content=""
      variant="shadow"
      styles={{
        content: {
          backgroundColor: '#f5f5f5',
          borderLeft: '3px solid #1890ff',
          padding: '12px 16px',
        },
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
        <span style={{ fontSize: '18px' }}>💭</span>
        <div style={{ flex: 1 }}>
          <div style={{ 
            fontWeight: 500, 
            marginBottom: '4px', 
            color: '#1890ff',
            fontSize: '13px'
          }}>
            思考过程
            {chunk.reasoning_step && ` - 步骤 ${chunk.reasoning_step}`}
          </div>
          <div style={{ 
            color: '#666',
            lineHeight: '1.6',
            fontSize: '14px',
            whiteSpace: 'pre-wrap'
          }}>
            {chunk.content}
          </div>
        </div>
      </div>
    </Bubble>
  );
};

export default ThinkingMessage;
