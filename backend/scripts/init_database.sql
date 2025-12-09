-- ============================================
-- Agent System 数据库初始化脚本
-- ============================================
-- 说明：本脚本用于初始化PostgreSQL数据库表结构和初始数据
-- 数据库：agentsys
-- 用户：agentsys
-- ============================================

-- 设置时区
SET timezone = 'UTC';

-- ============================================
-- 1. 删除现有表（如果存在，用于重新初始化）
-- ============================================
-- 注意：生产环境请谨慎使用，会删除所有数据！

DROP TABLE IF EXISTS messages CASCADE;
DROP TABLE IF EXISTS conversations CASCADE;
DROP TABLE IF EXISTS documents CASCADE;
DROP TABLE IF EXISTS knowledge_bases CASCADE;
DROP TABLE IF EXISTS tasks CASCADE;

-- ============================================
-- 2. 创建表结构
-- ============================================

-- 2.1 对话会话表
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_conversations_created_at ON conversations(created_at DESC);
CREATE INDEX idx_conversations_updated_at ON conversations(updated_at DESC);

COMMENT ON TABLE conversations IS '对话会话表，存储用户与AI的对话会话';
COMMENT ON COLUMN conversations.id IS '会话ID，主键';
COMMENT ON COLUMN conversations.title IS '会话标题';
COMMENT ON COLUMN conversations.created_at IS '创建时间';
COMMENT ON COLUMN conversations.updated_at IS '更新时间';

-- 2.2 消息表
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    meta_info JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_messages_conversation 
        FOREIGN KEY (conversation_id) 
        REFERENCES conversations(id) 
        ON DELETE CASCADE
);

-- 创建索引
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_created_at ON messages(created_at DESC);
CREATE INDEX idx_messages_role ON messages(role);

COMMENT ON TABLE messages IS '消息表，存储对话中的每条消息';
COMMENT ON COLUMN messages.id IS '消息ID，主键';
COMMENT ON COLUMN messages.conversation_id IS '所属会话ID，外键';
COMMENT ON COLUMN messages.role IS '消息角色：user, assistant, system';
COMMENT ON COLUMN messages.content IS '消息内容';
COMMENT ON COLUMN messages.meta_info IS '元信息，JSON格式，存储额外信息如检索的知识等';
COMMENT ON COLUMN messages.created_at IS '创建时间';

-- 2.3 知识库表
CREATE TABLE knowledge_bases (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL UNIQUE,
    description TEXT,
    collection_name VARCHAR(200) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_knowledge_bases_name ON knowledge_bases(name);
CREATE INDEX idx_knowledge_bases_collection_name ON knowledge_bases(collection_name);
CREATE INDEX idx_knowledge_bases_created_at ON knowledge_bases(created_at DESC);

COMMENT ON TABLE knowledge_bases IS '知识库表，存储知识库元信息';
COMMENT ON COLUMN knowledge_bases.id IS '知识库ID，主键';
COMMENT ON COLUMN knowledge_bases.name IS '知识库名称，唯一';
COMMENT ON COLUMN knowledge_bases.description IS '知识库描述';
COMMENT ON COLUMN knowledge_bases.collection_name IS 'ChromaDB集合名称';
COMMENT ON COLUMN knowledge_bases.created_at IS '创建时间';
COMMENT ON COLUMN knowledge_bases.updated_at IS '更新时间';

-- 2.4 文档表
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    knowledge_base_id INTEGER NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    source VARCHAR(500),
    meta_info JSONB,
    vector_id VARCHAR(100),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_documents_knowledge_base 
        FOREIGN KEY (knowledge_base_id) 
        REFERENCES knowledge_bases(id) 
        ON DELETE CASCADE
);

-- 创建索引
CREATE INDEX idx_documents_knowledge_base_id ON documents(knowledge_base_id);
CREATE INDEX idx_documents_vector_id ON documents(vector_id);
CREATE INDEX idx_documents_created_at ON documents(created_at DESC);
CREATE INDEX idx_documents_title ON documents(title);

COMMENT ON TABLE documents IS '文档表，存储知识库中的文档元信息';
COMMENT ON COLUMN documents.id IS '文档ID，主键';
COMMENT ON COLUMN documents.knowledge_base_id IS '所属知识库ID，外键';
COMMENT ON COLUMN documents.title IS '文档标题';
COMMENT ON COLUMN documents.content IS '文档内容';
COMMENT ON COLUMN documents.source IS '文档来源URL或路径';
COMMENT ON COLUMN documents.meta_info IS '元信息，JSON格式';
COMMENT ON COLUMN documents.vector_id IS 'ChromaDB中的向量ID';
COMMENT ON COLUMN documents.created_at IS '创建时间';

-- 2.5 任务表
CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    plan JSONB,
    result JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_created_at ON tasks(created_at DESC);
CREATE INDEX idx_tasks_updated_at ON tasks(updated_at DESC);

COMMENT ON TABLE tasks IS '任务表，存储AI任务规划信息';
COMMENT ON COLUMN tasks.id IS '任务ID，主键';
COMMENT ON COLUMN tasks.title IS '任务标题';
COMMENT ON COLUMN tasks.description IS '任务描述';
COMMENT ON COLUMN tasks.status IS '任务状态：pending, planned, in_progress, completed, failed';
COMMENT ON COLUMN tasks.plan IS '任务计划，JSON格式，存储规划的步骤';
COMMENT ON COLUMN tasks.result IS '任务结果，JSON格式，存储执行结果';
COMMENT ON COLUMN tasks.created_at IS '创建时间';
COMMENT ON COLUMN tasks.updated_at IS '更新时间';

-- ============================================
-- 3. 创建更新时间触发器函数
-- ============================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为需要自动更新updated_at的表创建触发器
CREATE TRIGGER update_conversations_updated_at 
    BEFORE UPDATE ON conversations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_knowledge_bases_updated_at 
    BEFORE UPDATE ON knowledge_bases 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at 
    BEFORE UPDATE ON tasks 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 4. 插入初始数据（可选，生产环境请注释掉）
-- ============================================

-- 注意：以下初始数据仅用于开发和测试环境
-- 生产环境部署时请注释掉或删除这部分

-- 4.1 创建示例知识库（开发环境）
-- INSERT INTO knowledge_bases (name, description, collection_name) 
-- VALUES 
--     ('默认知识库', '系统默认知识库，用于存储通用知识', 'kb_default'),
--     ('产品文档', '产品相关文档和说明', 'kb_product'),
--     ('技术文档', '技术规范和API文档', 'kb_tech');

-- 4.2 创建示例对话（开发环境）
-- INSERT INTO conversations (title) 
-- VALUES 
--     ('欢迎对话'),
--     ('项目规划讨论');

-- 4.3 创建示例任务（开发环境）
-- INSERT INTO tasks (title, description, status) 
-- VALUES 
--     ('示例任务', '这是一个示例任务，用于演示任务规划功能', 'pending');

-- ============================================
-- 5. 权限设置（如果需要）
-- ============================================

-- 授予应用用户所有权限
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO agentsys;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO agentsys;

-- ============================================
-- 初始化完成
-- ============================================

-- 显示表信息
SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'public' 
    AND table_type = 'BASE TABLE'
ORDER BY table_name;

