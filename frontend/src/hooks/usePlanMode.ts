/**
 * 计划模式状态管理 Hook
 */
import { useState, useEffect, useCallback } from 'react'

export interface UsePlanModeOptions {
  /** 默认是否启用（如果localStorage没有值） */
  defaultEnabled?: boolean
  /** localStorage的key */
  storageKey?: string
}

export interface UsePlanModeReturn {
  /** 当前是否启用计划模式 */
  enabled: boolean
  /** 设置计划模式状态 */
  setEnabled: (enabled: boolean) => void
  /** 切换计划模式状态 */
  toggle: () => void
}

/**
 * 计划模式状态管理Hook
 * 
 * 功能：
 * 1. 管理计划模式的启用/禁用状态
 * 2. 使用localStorage持久化状态
 * 3. 提供便捷的toggle方法
 * 
 * @example
 * ```tsx
 * const { enabled, setEnabled, toggle } = usePlanMode()
 * 
 * return (
 *   <PlanModeToggle enabled={enabled} onChange={setEnabled} />
 * )
 * ```
 */
export const usePlanMode = (options: UsePlanModeOptions = {}): UsePlanModeReturn => {
  const {
    defaultEnabled = false,
    storageKey = 'agentmind_plan_mode_enabled'
  } = options
  
  // 从localStorage读取初始值
  const getInitialValue = useCallback((): boolean => {
    try {
      const stored = localStorage.getItem(storageKey)
      if (stored !== null) {
        return JSON.parse(stored)
      }
    } catch (error) {
      console.error('Failed to read plan mode from localStorage:', error)
    }
    return defaultEnabled
  }, [defaultEnabled, storageKey])
  
  const [enabled, setEnabledState] = useState<boolean>(getInitialValue)
  
  // 设置状态并持久化到localStorage
  const setEnabled = useCallback((newEnabled: boolean) => {
    try {
      setEnabledState(newEnabled)
      localStorage.setItem(storageKey, JSON.stringify(newEnabled))
    } catch (error) {
      console.error('Failed to save plan mode to localStorage:', error)
    }
  }, [storageKey])
  
  // 切换状态
  const toggle = useCallback(() => {
    setEnabled(!enabled)
  }, [enabled, setEnabled])
  
  // 监听其他标签页的变化
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === storageKey && e.newValue !== null) {
        try {
          const newValue = JSON.parse(e.newValue)
          setEnabledState(newValue)
        } catch (error) {
          console.error('Failed to parse plan mode from storage event:', error)
        }
      }
    }
    
    window.addEventListener('storage', handleStorageChange)
    return () => window.removeEventListener('storage', handleStorageChange)
  }, [storageKey])
  
  return {
    enabled,
    setEnabled,
    toggle
  }
}
