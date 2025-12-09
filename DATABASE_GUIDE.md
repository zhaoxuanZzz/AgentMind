# 📊 数据库和知识库说明文档

## 📋 概述

Agent System使用两种数据存储方式：
- **PostgreSQL** - 关系型数据库，存储结构化数据（对话、任务、知识库元信息）
- **ChromaDB** - 向量数据库，存储文档向量和语义搜索数据

## 🗄️ PostgreSQL数据库结构

### 数据库信息

- **数据库名**: `agentsys`
- **用户名**: `agentsys`
- **端口**: `5432`
- **字符集**: UTF-8
- **时区**: UTC

### 表结构说明

#### 1. conversations（对话会话表）

存储用户与AI的对话会话信息。

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | INTEGER | 会话ID | PRIMARY KEY, AUTO_INCREMENT |
| title | VARCHAR(200) | 会话标题 | NOT NULL |
| created_at | TIMESTAMP | 创建时间 | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | 更新时间 | NOT NULL, DEFAULT CURRENT_TIMESTAMP |

**索引：**
- `idx_conversations_created_at` - 按创建时间降序
- `idx_conversations_updated_at` - 按更新时间降序

**关系：**
- 一对多关联 `messages` 表

**示例数据：**
```sql
id | title        | created_at          | updated_at
---|--------------|---------------------|---------------------
1  | 项目规划讨论 | 2024-10-26 10:00:00 | 2024-10-26 10:30:00
```

---

#### 2. messages（消息表）

存储对话中的每条消息。

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | INTEGER | 消息ID | PRIMARY KEY, AUTO_INCREMENT |
| conversation_id | INTEGER | 所属会话ID | NOT NULL, FOREIGN KEY |
| role | VARCHAR(20) | 消息角色 | NOT NULL (user/assistant/system) |
| content | TEXT | 消息内容 | NOT NULL |
| meta_info | JSONB | 元信息 | NULLABLE |
| created_at | TIMESTAMP | 创建时间 | NOT NULL, DEFAULT CURRENT_TIMESTAMP |

**索引：**
- `idx_messages_conversation_id` - 会话ID索引
- `idx_messages_created_at` - 创建时间索引
- `idx_messages_role` - 角色索引

**关系：**
- 多对一关联 `conversations` 表

**meta_info字段说明：**
```json
{
  "intermediate_steps": [...],  // 工具调用步骤
  "retrieved_knowledge": [...], // 检索到的知识
  "tokens_used": 150            // 使用的token数
}
```

**示例数据：**
```sql
id | conversation_id | role      | content           | created_at
---|-----------------|-----------|-------------------|---------------------
1  | 1               | user      | 你好              | 2024-10-26 10:00:00
2  | 1               | assistant | 你好！有什么...   | 2024-10-26 10:00:05
```

---

#### 3. knowledge_bases（知识库表）

存储知识库的元信息。实际文档向量存储在ChromaDB中。

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | INTEGER | 知识库ID | PRIMARY KEY, AUTO_INCREMENT |
| name | VARCHAR(200) | 知识库名称 | NOT NULL, UNIQUE |
| description | TEXT | 知识库描述 | NULLABLE |
| collection_name | VARCHAR(200) | ChromaDB集合名称 | NOT NULL |
| created_at | TIMESTAMP | 创建时间 | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | 更新时间 | NOT NULL, DEFAULT CURRENT_TIMESTAMP |

**索引：**
- `idx_knowledge_bases_name` - 名称索引（唯一）
- `idx_knowledge_bases_collection_name` - 集合名称索引
- `idx_knowledge_bases_created_at` - 创建时间索引

**关系：**
- 一对多关联 `documents` 表

**collection_name说明：**
- 对应ChromaDB中的collection名称
- 格式：`kb_{name}`（小写，空格替换为下划线）

**示例数据：**
```sql
id | name      | description | collection_name | created_at
---|-----------|-------------|-----------------|---------------------
1  | 产品文档  | 产品相关... | kb_product      | 2024-10-26 09:00:00
```

---

#### 4. documents（文档表）

存储知识库中文档的元信息。文档内容向量存储在ChromaDB中。

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | INTEGER | 文档ID | PRIMARY KEY, AUTO_INCREMENT |
| knowledge_base_id | INTEGER | 所属知识库ID | NOT NULL, FOREIGN KEY |
| title | VARCHAR(200) | 文档标题 | NOT NULL |
| content | TEXT | 文档内容 | NOT NULL |
| source | VARCHAR(500) | 文档来源 | NULLABLE |
| meta_info | JSONB | 元信息 | NULLABLE |
| vector_id | VARCHAR(100) | ChromaDB向量ID | NULLABLE |
| created_at | TIMESTAMP | 创建时间 | NOT NULL, DEFAULT CURRENT_TIMESTAMP |

**索引：**
- `idx_documents_knowledge_base_id` - 知识库ID索引
- `idx_documents_vector_id` - 向量ID索引
- `idx_documents_created_at` - 创建时间索引
- `idx_documents_title` - 标题索引

**关系：**
- 多对一关联 `knowledge_bases` 表

**vector_id说明：**
- 对应ChromaDB中存储的文档向量ID
- 用于关联PostgreSQL元数据和ChromaDB向量数据

**示例数据：**
```sql
id | knowledge_base_id | title    | content | vector_id | created_at
---|-------------------|----------|---------|-----------|---------------------
1  | 1                 | API文档  | ...     | uuid-123  | 2024-10-26 09:05:00
```

---

#### 5. tasks（任务表）

存储AI任务规划信息。

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | INTEGER | 任务ID | PRIMARY KEY, AUTO_INCREMENT |
| title | VARCHAR(200) | 任务标题 | NOT NULL |
| description | TEXT | 任务描述 | NOT NULL |
| status | VARCHAR(20) | 任务状态 | NOT NULL, DEFAULT 'pending' |
| plan | JSONB | 任务计划 | NULLABLE |
| result | JSONB | 任务结果 | NULLABLE |
| created_at | TIMESTAMP | 创建时间 | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | 更新时间 | NOT NULL, DEFAULT CURRENT_TIMESTAMP |

**索引：**
- `idx_tasks_status` - 状态索引
- `idx_tasks_created_at` - 创建时间索引
- `idx_tasks_updated_at` - 更新时间索引

**status状态值：**
- `pending` - 待处理
- `planned` - 已规划
- `in_progress` - 进行中
- `completed` - 已完成
- `failed` - 失败

**plan字段结构：**
```json
{
  "plan_text": "任务计划文本描述",
  "steps": [
    {
      "description": "步骤1描述",
      "status": "pending"
    }
  ]
}
```

**result字段结构：**
```json
{
  "success": true,
  "output": "执行结果",
  "steps_completed": 3,
  "total_steps": 5
}
```

**示例数据：**
```sql
id | title      | description | status    | created_at
---|------------|-------------|-----------|---------------------
1  | 项目规划   | 制定项目... | completed | 2024-10-26 11:00:00
```

---

## 🔍 ChromaDB向量数据库

### 概述

ChromaDB用于存储文档的向量表示，支持语义搜索。

### 集合（Collections）

每个知识库对应一个ChromaDB集合（Collection）。

**命名规则：**
- 格式：`kb_{knowledge_base_name}`
- 示例：`kb_product`、`kb_default`

**特殊集合：**
- `prompts` - 存储提示词卡片（Prompt Cards）

### 数据结构

**文档向量存储：**
```json
{
  "id": "uuid-123",
  "document": "文档文本内容",
  "metadata": {
    "title": "文档标题",
    "source": "文档来源",
    "doc_index": 0,
    "chunk_index": 0,
    "total_chunks": 5
  },
  "embedding": [0.1, 0.2, ...]  // 向量表示
}
```

**提示词卡片存储：**
```json
{
  "id": "uuid-456",
  "document": "提示词内容",
  "metadata": {
    "title": "卡片标题",
    "type": "prompt_card",
    "category": "tech",
    "tags": "代码,审查,安全"
  },
  "embedding": [0.3, 0.4, ...]
}
```

### 数据流程

```
添加文档
  ↓
文本分割（chunks）
  ↓
向量化（Embedding）
  ↓
存储到ChromaDB
  ↓
保存元数据到PostgreSQL
```

---

## 🔗 数据关联关系

### ER图

```
conversations (1) ──< (N) messages
knowledge_bases (1) ──< (N) documents
tasks (独立表)
```

### 跨数据库关联

```
PostgreSQL (元数据)          ChromaDB (向量数据)
─────────────────          ──────────────────
knowledge_bases             Collection: kb_xxx
  └─ collection_name ──────> Collection Name
documents                   Document Vector
  └─ vector_id ────────────> Document ID
```

---

## 📝 数据库初始化

### 方法1：使用SQL脚本（推荐）

**位置：** `backend/scripts/init_database.sql`

```bash
# 使用psql命令行
psql -U agentsys -d agentsys -f backend/scripts/init_database.sql

# 或使用Docker
docker exec -i agentsys-postgres psql -U agentsys agentsys < backend/scripts/init_database.sql
```

**脚本功能：**
- ✅ 创建所有表结构
- ✅ 创建索引优化性能
- ✅ 创建触发器自动更新时间戳
- ✅ 添加表和字段注释
- ⚠️ 会删除现有表（开发环境安全，生产环境需谨慎）

### 方法2：使用SQLAlchemy自动创建

应用启动时会自动创建表结构（如果不存在）：

```python
# app/main.py
Base.metadata.create_all(bind=engine)
```

**注意：** 自动创建不会添加索引和注释，建议使用SQL脚本。

### 方法3：使用Docker Compose

```bash
# 启动服务，数据库会自动初始化
docker-compose up -d postgres

# 然后执行初始化脚本
docker exec -i agentsys-postgres psql -U agentsys agentsys < backend/scripts/init_database.sql
```

---

## 🔧 常用SQL查询

### 查询对话及其消息

```sql
SELECT 
    c.id,
    c.title,
    COUNT(m.id) as message_count,
    MAX(m.created_at) as last_message_time
FROM conversations c
LEFT JOIN messages m ON c.id = m.conversation_id
GROUP BY c.id
ORDER BY last_message_time DESC;
```

### 查询知识库及其文档数量

```sql
SELECT 
    kb.id,
    kb.name,
    kb.collection_name,
    COUNT(d.id) as document_count
FROM knowledge_bases kb
LEFT JOIN documents d ON kb.id = d.knowledge_base_id
GROUP BY kb.id;
```

### 查询任务统计

```sql
SELECT 
    status,
    COUNT(*) as count
FROM tasks
GROUP BY status;
```

### 查询最近的消息

```sql
SELECT 
    m.id,
    m.role,
    LEFT(m.content, 100) as content_preview,
    c.title as conversation_title,
    m.created_at
FROM messages m
JOIN conversations c ON m.conversation_id = c.id
ORDER BY m.created_at DESC
LIMIT 20;
```

---

## 🛠️ 维护操作

### 备份数据库

```bash
# 使用pg_dump
pg_dump -U agentsys agentsys > backup_$(date +%Y%m%d).sql

# 或使用Docker
docker exec agentsys-postgres pg_dump -U agentsys agentsys > backup.sql
```

### 恢复数据库

```bash
# 使用psql
psql -U agentsys -d agentsys < backup.sql

# 或使用Docker
docker exec -i agentsys-postgres psql -U agentsys agentsys < backup.sql
```

### 清理旧数据

```sql
-- 删除30天前的对话
DELETE FROM conversations 
WHERE updated_at < NOW() - INTERVAL '30 days';

-- 删除已完成的任务
DELETE FROM tasks 
WHERE status = 'completed' 
  AND updated_at < NOW() - INTERVAL '7 days';
```

### 优化数据库

```sql
-- 更新统计信息
ANALYZE;

-- 重建索引
REINDEX DATABASE agentsys;

-- 清理空间
VACUUM FULL;
```

---

## 📊 数据统计查询

### 系统概览

```sql
SELECT 
    (SELECT COUNT(*) FROM conversations) as total_conversations,
    (SELECT COUNT(*) FROM messages) as total_messages,
    (SELECT COUNT(*) FROM knowledge_bases) as total_knowledge_bases,
    (SELECT COUNT(*) FROM documents) as total_documents,
    (SELECT COUNT(*) FROM tasks) as total_tasks;
```

### 活跃度统计

```sql
-- 每日消息数
SELECT 
    DATE(created_at) as date,
    COUNT(*) as message_count
FROM messages
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

---

## 🔐 安全建议

1. **定期备份**
   - 建议每天备份一次
   - 保留至少7天的备份

2. **访问控制**
   - 使用强密码
   - 限制数据库访问IP
   - 使用SSL连接（生产环境）

3. **数据清理**
   - 定期清理旧数据
   - 归档重要数据

4. **监控**
   - 监控数据库性能
   - 监控存储空间
   - 设置告警

---

## 📚 相关文档

- [部署文档](DEPLOYMENT.md) - 数据库部署说明
- [项目结构](PROJECT_STRUCTURE.md) - 项目整体结构
- [环境配置](ENV_CONFIG_GUIDE.md) - 环境变量配置

---

**最后更新：** 2024年10月26日

