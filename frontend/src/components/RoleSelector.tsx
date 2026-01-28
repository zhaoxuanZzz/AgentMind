/**
 * 角色预设选择组件
 */
import React from 'react'
import { Select, Tooltip } from 'antd'
import { UserOutlined } from '@ant-design/icons'
import type { RolePresetV2 } from '../api/types'

export interface RoleSelectorProps {
  /** 当前选中的角色ID */
  value?: string
  /** 可用角色列表 */
  roles: RolePresetV2[]
  /** 角色变化回调 */
  onChange: (roleId: string) => void
  /** 是否禁用 */
  disabled?: boolean
  /** 是否加载中 */
  loading?: boolean
  /** 自定义样式 */
  style?: React.CSSProperties
  /** 自定义类名 */
  className?: string
  /** 占位符 */
  placeholder?: string
}

/**
 * 角色预设选择组件
 * 
 * 允许用户从预设角色列表中选择AI的行为模式
 */
export const RoleSelector: React.FC<RoleSelectorProps> = ({
  value,
  roles,
  onChange,
  disabled = false,
  loading = false,
  style,
  className,
  placeholder = "选择AI角色"
}) => {
  // 过滤出激活的角色
  const activeRoles = roles.filter(role => role.is_active)
  
  // 构建选项
  const options = activeRoles.map(role => ({
    value: role.id,
    label: (
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        {role.icon && <span>{role.icon}</span>}
        <div>
          <div style={{ fontWeight: 500 }}>{role.name}</div>
          {role.description && (
            <div style={{ fontSize: 12, color: '#999' }}>{role.description}</div>
          )}
        </div>
      </div>
    ),
    role
  }))
  
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
      <Tooltip title="选择AI的专业领域和对话风格">
        <span style={{ 
          fontSize: 14, 
          color: '#666',
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          userSelect: 'none'
        }}>
          <UserOutlined />
          角色
        </span>
      </Tooltip>
      
      <Select
        value={value}
        onChange={onChange}
        options={options}
        disabled={disabled}
        loading={loading}
        placeholder={placeholder}
        style={{ minWidth: 150 }}
        optionLabelProp="label"
        optionRender={(option) => (
          <div style={{ padding: '4px 0' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
              {option.data.role.icon && <span style={{ fontSize: 16 }}>{option.data.role.icon}</span>}
              <span style={{ fontWeight: 500 }}>{option.data.role.name}</span>
            </div>
            {option.data.role.description && (
              <div style={{ fontSize: 12, color: '#999', paddingLeft: 24 }}>
                {option.data.role.description}
              </div>
            )}
          </div>
        )}
      />
    </div>
  )
}
