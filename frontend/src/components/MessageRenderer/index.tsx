/**
 * 消息渲染器主组件
 * 根据消息类型分发到不同的渲染组件
 */
import React from 'react';
import { Bubble } from '@ant-design/x';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { MessageType, type AnyMessageChunk } from '../../types/messageTypes';
import { MessageErrorBoundary } from '../MessageErrorBoundary';
import ThinkingMessage from './ThinkingMessage';
import ToolMessage from './ToolMessage';
import PlanMessage from './PlanMessage';
import SystemMessage from './SystemMessage';

interface MessageRendererProps {
  chunks: AnyMessageChunk[];
  role: 'user' | 'assistant';
}

const MessageRenderer: React.FC<MessageRendererProps> = ({ chunks, role }) => {
  if (!chunks || chunks.length === 0) {
    return null;
  }

  // 按类型分组渲染
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
      {chunks.map((chunk, index) => (
        <MessageErrorBoundary
          key={`${chunk.type}-${index}`}
          fallback={
            <div style={{
              padding: 12,
              background: '#fff1f0',
              border: '1px solid #ffa39e',
              borderRadius: 4,
              color: '#cf1322'
            }}>
              <strong>⚠️ 消息渲染错误</strong>
              <div style={{ fontSize: 12, marginTop: 4, color: '#8c8c8c' }}>
                类型: {chunk.type}
              </div>
            </div>
          }
        >
          {renderChunkContent(chunk, index, role)}
        </MessageErrorBoundary>
      ))}
    </div>
  );
};

// 分离渲染逻辑以便ErrorBoundary捕获错误
function renderChunkContent(chunk: AnyMessageChunk, index: number, role: 'user' | 'assistant'): React.ReactNode {
  try {
    switch (chunk.type) {
          case MessageType.THINKING:
            return <ThinkingMessage key={index} chunk={chunk} />;

          case MessageType.TOOL:
            return <ToolMessage key={index} chunk={chunk} />;

          case MessageType.PLAN:
            return <PlanMessage key={index} chunk={chunk} />;

          case MessageType.SYSTEM:
            return <SystemMessage key={index} chunk={chunk} />;

          case MessageType.TEXT:
            return (
              <Bubble
                key={index}
                content=""
                variant="filled"
                styles={{
                  content: {
                    backgroundColor: role === 'user' ? '#1890ff' : '#f5f5f5',
                    color: role === 'user' ? '#fff' : '#000',
                  },
                }}
              >
                <div style={{ fontSize: '14px', lineHeight: '1.6' }}>
                  <ReactMarkdown
                    components={{
                      code(props) {
                        const { className, children } = props;
                        const match = /language-(\w+)/.exec(className || '');
                        const isInline = !match;
                        
                        if (isInline) {
                          return (
                            <code className={className} style={{ 
                              backgroundColor: '#f5f5f5',
                              padding: '2px 6px',
                              borderRadius: '3px'
                            }}>
                              {children}
                            </code>
                          );
                        }
                        
                        return (
                          <SyntaxHighlighter
                            style={tomorrow as any}
                            language={match[1]}
                            PreTag="div"
                          >
                            {String(children).replace(/\n$/, '')}
                          </SyntaxHighlighter>
                        );
                      },
                    }}
                  >
                    {chunk.content}
                  </ReactMarkdown>
                </div>
              </Bubble>
            );

          default:
            // 未知类型，以默认方式渲染（降级处理）
            console.warn('Unknown message chunk type:', chunk.type);
            return (
              <div style={{ 
                padding: '8px 12px',
                backgroundColor: '#fafafa',
                border: '1px dashed #d9d9d9',
                borderRadius: '4px',
                fontSize: '13px'
              }}>
                <div style={{ color: '#8c8c8c', marginBottom: '4px' }}>
                  未知消息类型: {chunk.type}
                </div>
                <pre style={{ margin: 0, fontSize: '12px', whiteSpace: 'pre-wrap' }}>
                  {JSON.stringify(chunk, null, 2)}
                </pre>
              </div>
            );
        }
      } catch (error) {
        console.error('Error rendering message chunk:', error, chunk);
        // 错误降级渲染
        return (
          <div style={{
            padding: 12,
            background: '#fff1f0',
            border: '1px solid #ffa39e',
            borderRadius: 4
          }}>
            <strong style={{ color: '#cf1322' }}>⚠️ 渲染错误</strong>
            <div style={{ fontSize: 12, marginTop: 4, color: '#595959' }}>
              {error instanceof Error ? error.message : '未知错误'}
            </div>
          </div>
        );
      }
}

export default MessageRenderer;
