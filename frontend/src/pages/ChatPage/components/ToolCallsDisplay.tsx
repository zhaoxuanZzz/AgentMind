import React from 'react';
import { ThoughtChain } from '@ant-design/x';
import { theme } from 'antd';
import type { ToolInfo } from '../../../types/api';

interface ToolCallsDisplayProps {
  toolCalls: ToolInfo[];
  loading?: boolean;
}

const ToolCallsDisplay: React.FC<ToolCallsDisplayProps> = ({ toolCalls }) => {
  const { token } = theme.useToken();

  if (!toolCalls || toolCalls.length === 0) return null;

  const items = toolCalls.map((tool) => {
    // 简单的反序列化尝试，使得 JSON input/output 更易读
    let inputDisplay = tool.input;
    let outputDisplay = tool.output;
    
    try {
        // 如果是 JSON 字符串，尝试 parse 之后展示（可选优化，可以先不做）
    } catch(e) {}

    return {
      title: `Tool Usage: ${tool.tool}`,
      description: (
        <div style={{ fontSize: '13px', marginTop: 4 }}>
          <div style={{ 
            marginBottom: 4, 
            padding: '4px 8px', 
            backgroundColor: token.colorFillQuaternary,
            borderRadius: 4,
            fontFamily: 'monospace'
          }}>
            <span style={{ color: token.colorTextSecondary }}>Input: </span>
            <span>{inputDisplay}</span>
          </div>
          {outputDisplay && (
            <div style={{ 
              padding: '4px 8px', 
              backgroundColor: token.colorFillQuaternary,
              borderRadius: 4,
              fontFamily: 'monospace'
            }}>
              <span style={{ color: token.colorTextSecondary }}>Output: </span>
              <span>{outputDisplay}</span>
            </div>
          )}
        </div>
      ),
      status: 'success' as const,
    };
  });

  return (
    <div style={{ marginTop: 8, marginBottom: 8 }}>
      <ThoughtChain items={items} />
    </div>
  );
};

export default ToolCallsDisplay;
