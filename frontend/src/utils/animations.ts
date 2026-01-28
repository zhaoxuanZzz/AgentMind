/**
 * 动画配置 (Framer Motion)
 */
import { Variants } from 'framer-motion'

/** 基础过渡配置 */
export const transition = {
  type: 'spring',
  damping: 20,
  stiffness: 100,
} as const

/** 渐入向上动画 */
export const fadeInUp: Variants = {
  initial: {
    opacity: 0,
    y: 20,
  },
  animate: {
    opacity: 1,
    y: 0,
    transition: transition,
  },
  exit: {
    opacity: 0,
    y: -20,
    transition: { duration: 0.2 },
  },
}

/** 渐入动画 */
export const fadeIn: Variants = {
  initial: { opacity: 0 },
  animate: { 
    opacity: 1, 
    transition: { duration: 0.3 } 
  },
  exit: { 
    opacity: 0, 
    transition: { duration: 0.2 } 
  },
}

/** 容器动画（子元素交错） */
export const staggerContainer: Variants = {
  animate: {
    transition: {
      staggerChildren: 0.1,
    },
  },
}

/** 左侧滑入 */
export const slideInLeft: Variants = {
  initial: { x: -20, opacity: 0 },
  animate: { 
    x: 0, 
    opacity: 1, 
    transition: transition 
  },
  exit: { 
    x: -20, 
    opacity: 0, 
    transition: { duration: 0.2 } 
  },
}

/** 思考过程展开动画 */
export const accordion: Variants = {
  initial: { height: 0, opacity: 0 },
  animate: { 
    height: 'auto', 
    opacity: 1,
    transition: {
      height: {
        type: 'spring',
        damping: 30,
        stiffness: 200,
      },
      opacity: { duration: 0.2, delay: 0.1 }
    }
  },
  exit: { 
    height: 0, 
    opacity: 0,
    transition: { 
      height: { duration: 0.2 },
      opacity: { duration: 0.1 } 
    }
  },
}
