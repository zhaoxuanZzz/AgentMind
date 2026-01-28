/**
 * 角色预设状态管理 Hook
 */
import { useState, useEffect, useCallback } from 'react'
import { roleApi, configApi } from '../api/services'
import type { RolePresetV2 } from '../api/types'

export interface UseRolePresetOptions {
  /** 会话ID（用于获取会话级配置） */
  conversationId?: number | null
  /** 自动加载 */
  autoLoad?: boolean
}

export interface UseRolePresetReturn {
  /** 可用角色列表 */
  roles: RolePresetV2[]
  /** 当前选中的角色ID */
  currentRoleId: string | null
  /** 全局默认角色ID */
  globalDefaultRoleId: string | null
  /** 是否加载中 */
  loading: boolean
  /** 错误信息 */
  error: string | null
  /** 设置当前角色 */
  setRole: (roleId: string) => Promise<void>
  /** 设置全局默认角色 */
  setGlobalDefaultRole: (roleId: string) => Promise<void>
  /** 重新加载角色列表 */
  reload: () => Promise<void>
}

/**
 * 角色预设状态管理Hook
 * 
 * 功能：
 * 1. 加载可用角色列表
 * 2. 管理当前选中角色（会话级）
 * 3. 管理全局默认角色
 * 4. 持久化到后端（会话配置/全局设置）
 * 
 * 优先级：会话配置 > 全局默认
 * 
 * @example
 * ```tsx
 * const { roles, currentRoleId, setRole, loading } = useRolePreset({
 *   conversationId: currentConversationId
 * })
 * 
 * return (
 *   <RoleSelector 
 *     roles={roles} 
 *     value={currentRoleId} 
 *     onChange={setRole}
 *     loading={loading}
 *   />
 * )
 * ```
 */
export const useRolePreset = (options: UseRolePresetOptions = {}): UseRolePresetReturn => {
  const { conversationId = null, autoLoad = true } = options
  
  const [roles, setRoles] = useState<RolePresetV2[]>([])
  const [currentRoleId, setCurrentRoleId] = useState<string | null>(null)
  const [globalDefaultRoleId, setGlobalDefaultRoleId] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // 加载角色列表和配置
  const reload = useCallback(async () => {
    setLoading(true)
    setError(null)
    
    try {
      // 1. 加载角色列表
      const rolesData = await roleApi.getRoles()
      setRoles(rolesData)
      
      // 2. 加载全局默认设置
      const globalSettings = await configApi.getGlobalSettings()
      const globalDefault = globalSettings.default_role_id
      setGlobalDefaultRoleId(globalDefault)
      
      // 3. 如果有会话ID，尝试加载会话配置
      let conversationRoleId: string | null = null
      if (conversationId) {
        try {
          const convConfig = await configApi.getConversationConfig(conversationId)
          conversationRoleId = convConfig.role_id || null
        } catch (err) {
          // 会话配置可能不存在，使用全局默认
          console.debug('No conversation config found, using global default')
        }
      }
      
      // 4. 确定当前角色：会话配置 > 全局默认
      const effectiveRoleId = conversationRoleId || globalDefault
      setCurrentRoleId(effectiveRoleId)
      
    } catch (err: any) {
      const errorMsg = err.message || '加载角色失败'
      setError(errorMsg)
      console.error('Failed to load roles:', err)
    } finally {
      setLoading(false)
    }
  }, [conversationId])
  
  // 设置当前角色（会话级）
  const setRole = useCallback(async (roleId: string) => {
    try {
      // 如果有会话ID，保存到会话配置；否则只更新状态
      if (conversationId) {
        await configApi.updateConversationConfig(conversationId, {
          role_id: roleId
        })
      }
      
      setCurrentRoleId(roleId)
    } catch (err: any) {
      const errorMsg = err.message || '设置角色失败'
      setError(errorMsg)
      console.error('Failed to set role:', err)
      throw err
    }
  }, [conversationId])
  
  // 设置全局默认角色
  const setGlobalDefaultRole = useCallback(async (roleId: string) => {
    try {
      await configApi.updateGlobalSettings({
        default_role_id: roleId
      })
      
      setGlobalDefaultRoleId(roleId)
      
      // 如果当前没有会话特定角色，也更新当前角色
      if (!conversationId) {
        setCurrentRoleId(roleId)
      }
    } catch (err: any) {
      const errorMsg = err.message || '设置全局默认角色失败'
      setError(errorMsg)
      console.error('Failed to set global default role:', err)
      throw err
    }
  }, [conversationId])
  
  // 初始加载
  useEffect(() => {
    if (autoLoad) {
      reload()
    }
  }, [autoLoad, reload])
  
  // 当会话ID变化时重新加载
  useEffect(() => {
    if (conversationId && autoLoad) {
      reload()
    }
  }, [conversationId, autoLoad, reload])
  
  return {
    roles,
    currentRoleId,
    globalDefaultRoleId,
    loading,
    error,
    setRole,
    setGlobalDefaultRole,
    reload
  }
}
