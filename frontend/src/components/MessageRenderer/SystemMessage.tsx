/**
 * 系统消息渲染组件
 */
import React from 'react';
import { Alert } from 'antd';
import type { SystemChunk } from '../../types/messageTypes';

interface SystemMessageProps {
  chunk: SystemChunk;
}

const SystemMessage: React.FC<SystemMessageProps> = ({ chunk }) => {
  const getAlertType = (level: string): 'info' | 'warning' | 'error' => {
    switch (level) {
      case 'warning':
        return 'warning';
      case 'error':
        return 'error';
      default:
        return 'info';
    }
  };

  return (
    <div style={{ margin: '8px 0' }}>
      <Alert
        message={chunk.content}
        type={getAlertType(chunk.level)}
        showIcon
        style={{ fontSize: '13px' }}
      />
    </div>
  );
};

export default SystemMessage;
