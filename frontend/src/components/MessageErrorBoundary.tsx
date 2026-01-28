/**
 * 前端错误边界组件
 */
import { Component, ErrorInfo, ReactNode } from 'react'
import { Alert } from 'antd'

interface Props {
  children: ReactNode
  fallback?: ReactNode
  onError?: (error: Error, errorInfo: ErrorInfo) => void
}

interface State {
  hasError: boolean
  error: Error | null
}

/**
 * 错误边界组件
 * 捕获子组件渲染错误，防止整个应用崩溃
 */
export class MessageErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = {
      hasError: false,
      error: null
    }
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error
    }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('MessageRenderer Error:', error, errorInfo)
    this.props.onError?.(error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <Alert
          type="error"
          message="消息渲染错误"
          description={
            <div>
              <div>无法正确渲染此消息，请刷新页面重试</div>
              {process.env.NODE_ENV === 'development' && this.state.error && (
                <details style={{ marginTop: 8 }}>
                  <summary style={{ cursor: 'pointer' }}>错误详情</summary>
                  <pre style={{ 
                    marginTop: 8, 
                    padding: 8, 
                    background: '#f5f5f5', 
                    borderRadius: 4,
                    fontSize: 12,
                    overflow: 'auto'
                  }}>
                    {this.state.error.message}
                    {'\n'}
                    {this.state.error.stack}
                  </pre>
                </details>
              )}
            </div>
          }
          style={{ margin: '8px 0' }}
        />
      )
    }

    return this.props.children
  }
}
