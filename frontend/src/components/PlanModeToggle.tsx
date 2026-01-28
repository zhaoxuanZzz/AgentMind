/**
 * 计划模式切换组件
 */
import React from 'react'
import { Switch, Tooltip } from 'antd'
import { ThunderboltOutlined } from '@ant-design/icons'

export interface PlanModeToggleProps {
  /** 是否启用计划模式 */
  enabled: boolean
  /** 状态变化回调 */
  onChange: (enabled: boolean) => void
  /** 是否禁用 */
  disabled?: boolean
  /** 自定义样式 */
  style?: React.CSSProperties
  /** 自定义类名 */
  className?: string
}

/**
 * 计划模式切换组件
 * 
 * 用于控制AI是否在处理复杂任务时先生成执行计划
 */
export const PlanModeToggle: React.FC<PlanModeToggleProps> = ({
  enabled,
  onChange,
  disabled = false,
  style,
  className
}) => {
  return (
    <div 
      style={{ 
        display: 'inline-flex', 
        alignItems: 'center', 
        gap: 8,
        ...style 
      }}
      className={className}
    >
      <Tooltip 
        title={
          enabled 
            ? "计划模式已启用：AI会为复杂任务先制定执行计划" 
            : "计划模式已禁用：AI直接执行任务"
        }
      >
        <span style={{ 
          fontSize: 14, 
          color: enabled ? '#1677ff' : '#666',
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          cursor: 'pointer',
          userSelect: 'none'
        }}>
          <ThunderboltOutlined />
          计划模式
        </span>
      </Tooltip>
      
      <Switch
        checked={enabled}
        onChange={onChange}
        disabled={disabled}
        size="small"
      />
    </div>
  )
}
