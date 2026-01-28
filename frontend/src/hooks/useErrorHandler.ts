import { useEffect, useCallback } from 'react'
import { App } from 'antd'

interface ErrorHandlerOptions {
  preventDefault?: boolean
  logError?: boolean
}

export const useErrorHandler = (options: ErrorHandlerOptions = {}) => {
  const { notification } = App.useApp()
  const { preventDefault = false, logError = true } = options

  const handleError = useCallback((error: Error | string | unknown) => {
    const errorMsg = error instanceof Error ? error.message : String(error)
    
    if (logError) {
      console.error('Global Error Caught:', error)
    }

    // 区分严重程度，这里简单处理
    notification.error({
      message: '发生错误',
      description: errorMsg,
      placement: 'bottomRight'
    })
  }, [logError, notification])

  useEffect(() => {
    const handleRejection = (event: PromiseRejectionEvent) => {
      if (preventDefault) {
        event.preventDefault()
      }
      handleError(event.reason)
    }

    const handleErrorEvent = (event: ErrorEvent) => {
      if (preventDefault) {
        event.preventDefault()
      }
      handleError(event.error || event.message)
    }

    window.addEventListener('unhandledrejection', handleRejection)
    window.addEventListener('error', handleErrorEvent)

    return () => {
      window.removeEventListener('unhandledrejection', handleRejection)
      window.removeEventListener('error', handleErrorEvent)
    }
  }, [handleError, preventDefault])

  return {
    handleError
  }
}
