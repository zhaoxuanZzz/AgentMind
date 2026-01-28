-- 002: 添加角色预设和配置表
-- 创建日期: 2026-01-27
-- 用途: 支持角色预设、会话配置和全局设置功能
-- 数据库: PostgreSQL

-- 1. 添加会话配置表
CREATE TABLE IF NOT EXISTS conversation_configs (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER UNIQUE NOT NULL,
    role_id VARCHAR(100),
    plan_mode_enabled BOOLEAN,  -- true/false/null, null=使用全局默认
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_conversation_configs_conversation 
        FOREIGN KEY (conversation_id) 
        REFERENCES conversations(id) 
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_conversation_configs_conversation_id 
ON conversation_configs(conversation_id);

COMMENT ON TABLE conversation_configs IS '会话配置表，存储会话级别的角色和计划模式配置';
COMMENT ON COLUMN conversation_configs.conversation_id IS '所属会话ID，外键，唯一';
COMMENT ON COLUMN conversation_configs.role_id IS '角色预设ID（如software_engineer），NULL表示使用全局默认';
COMMENT ON COLUMN conversation_configs.plan_mode_enabled IS '计划模式是否启用，NULL表示使用全局默认';

-- 2. 添加全局设置表
CREATE TABLE IF NOT EXISTS global_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_global_settings_key 
ON global_settings(setting_key);

CREATE INDEX IF NOT EXISTS idx_global_settings_user_id 
ON global_settings(user_id);

COMMENT ON TABLE global_settings IS '全局设置表，存储用户级别的默认配置';
COMMENT ON COLUMN global_settings.setting_key IS '设置键名，唯一（如default_role_id、default_plan_mode）';
COMMENT ON COLUMN global_settings.setting_value IS '设置值，JSON格式存储';

-- 3. 为 messages 表添加新字段（向后兼容）
-- 检查字段是否存在，避免重复添加
DO $$ 
BEGIN
    -- 添加 chunks 字段用于存储结构化消息块
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='messages' AND column_name='chunks'
    ) THEN
        ALTER TABLE messages ADD COLUMN chunks JSONB;
        COMMENT ON COLUMN messages.chunks IS '结构化消息块（新格式），JSON数组';
    END IF;
    
    -- 添加 thinking 字段（向后兼容）
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='messages' AND column_name='thinking'
    ) THEN
        ALTER TABLE messages ADD COLUMN thinking TEXT;
        COMMENT ON COLUMN messages.thinking IS 'AI思考过程（向后兼容）';
    END IF;
    
    -- 添加 intermediate_steps 字段（向后兼容）
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='messages' AND column_name='intermediate_steps'
    ) THEN
        ALTER TABLE messages ADD COLUMN intermediate_steps JSONB;
        COMMENT ON COLUMN messages.intermediate_steps IS '工具调用中间步骤（向后兼容）';
    END IF;
END $$;

-- 4. 初始化默认全局设置
INSERT INTO global_settings (setting_key, setting_value) 
VALUES 
    ('default_role_id', '"software_engineer"'),
    ('default_plan_mode', 'false')
ON CONFLICT(setting_key) DO NOTHING;

-- 5. 创建或更新触发器函数（如果不存在）
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE 'plpgsql';

-- 为新表创建触发器
DROP TRIGGER IF EXISTS update_conversation_configs_updated_at ON conversation_configs;
CREATE TRIGGER update_conversation_configs_updated_at 
    BEFORE UPDATE ON conversation_configs 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_global_settings_updated_at ON global_settings;
CREATE TRIGGER update_global_settings_updated_at 
    BEFORE UPDATE ON global_settings 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
