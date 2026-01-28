/**
 * 响应式断点检测 Hook
 * 基于 Ant Design 断点系统
 */

import { useState, useEffect } from 'react'
import { debounce } from '../utils/debounce'

/** 断点定义 */
export const breakpoints = {
  xs: 0,    // < 576px
  sm: 576,  // >= 576px
  md: 768,  // >= 768px
  lg: 992,  // >= 992px
  xl: 1200, // >= 1200px
  xxl: 1600, // >= 1600px
} as const

export type Breakpoint = keyof typeof breakpoints

/** 响应式状态 */
export interface ResponsiveState {
  /** 当前断点 */
  current: Breakpoint
  /** 是否为移动端 (< 768px) */
  isMobile: boolean
  /** 是否为平板 (768px - 992px) */
  isTablet: boolean
  /** 是否为桌面 (>= 992px) */
  isDesktop: boolean
  /** 屏幕宽度 */
  width: number
  /** 屏幕高度 */
  height: number
}

/**
 * 根据宽度获取当前断点
 */
function getCurrentBreakpoint(width: number): Breakpoint {
  if (width >= breakpoints.xxl) return 'xxl'
  if (width >= breakpoints.xl) return 'xl'
  if (width >= breakpoints.lg) return 'lg'
  if (width >= breakpoints.md) return 'md'
  if (width >= breakpoints.sm) return 'sm'
  return 'xs'
}

/**
 * 响应式断点检测 Hook
 */
export function useResponsive(): ResponsiveState {
  const [state, setState] = useState<ResponsiveState>(() => {
    const width = typeof window !== 'undefined' ? window.innerWidth : 1920
    const height = typeof window !== 'undefined' ? window.innerHeight : 1080
    const current = getCurrentBreakpoint(width)

    return {
      current,
      isMobile: width < breakpoints.md,
      isTablet: width >= breakpoints.md && width < breakpoints.lg,
      isDesktop: width >= breakpoints.lg,
      width,
      height,
    }
  })

  useEffect(() => {
    const handleResize = () => {
      const width = window.innerWidth
      const height = window.innerHeight
      const current = getCurrentBreakpoint(width)

      setState({
        current,
        isMobile: width < breakpoints.md,
        isTablet: width >= breakpoints.md && width < breakpoints.lg,
        isDesktop: width >= breakpoints.lg,
        width,
        height,
      })
    }

    // 使用 debounce 优化 resize 处理
    const debouncedHandleResize = debounce(handleResize, 100)

    // 使用 ResizeObserver 提供更好的性能
    let resizeObserver: ResizeObserver | null = null

    if (typeof window !== 'undefined') {
      if ('ResizeObserver' in window) {
        resizeObserver = new ResizeObserver((_entries) => {
          // 使用 requestAnimationFrame 避免 "ResizeObserver loop limit exceeded" 错误
          window.requestAnimationFrame(() => {
             debouncedHandleResize()
          })
        })
        resizeObserver.observe(document.documentElement)
      } else {
        // 降级到 resize 事件
        (window as Window).addEventListener('resize', debouncedHandleResize)
      }
    }

    return () => {
      if (resizeObserver) {
        resizeObserver.disconnect()
      } else if (typeof window !== 'undefined') {
        (window as Window).removeEventListener('resize', debouncedHandleResize)
      }
    }
  }, [])

  return state
}


/**
 * 检查是否匹配指定断点或更大
 */
export function useBreakpoint(breakpoint: Breakpoint): boolean {
  const { width } = useResponsive()
  return width >= breakpoints[breakpoint]
}
