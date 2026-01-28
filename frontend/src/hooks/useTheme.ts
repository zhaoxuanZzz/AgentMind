/**
 * 主题 Hook
 * 管理应用主题状态（目前仅支持浅色主题）
 */

import { useState, useEffect, useCallback } from 'react'
import { useLocalStorage } from './useLocalStorage'

export type ThemeMode = 'light'

/** 主题状态 */
export interface ThemeState {
  /** 当前主题模式 */
  mode: ThemeMode
  /** 切换主题（当前版本固定为浅色） */
  toggle: () => void
  /** 设置主题 */
  setMode: (mode: ThemeMode) => void
}

/**
 * 主题 Hook
 * 注意：当前版本仅支持浅色主题，暗色主题延后实现
 */
export function useTheme(): ThemeState {
  const [mode, setMode] = useLocalStorage<ThemeMode>('theme-mode', 'light')
  const [, setInternalMode] = useState<ThemeMode>('light')

  // 应用主题到 DOM
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', mode)
    setInternalMode(mode)
  }, [mode])

  // 切换主题（当前固定为浅色）
  const toggle = useCallback(() => {
    // 暗色主题延后实现，目前保持浅色
    console.info('暗色主题将在后续版本实现')
  }, [])

  // 设置主题（当前固定为浅色）
  const handleSetMode = useCallback((newMode: ThemeMode) => {
    if (newMode !== 'light') {
      console.warn('当前版本仅支持浅色主题')
      return
    }
    setMode(newMode)
  }, [setMode])

  return {
    mode,
    toggle,
    setMode: handleSetMode,
  }
}
