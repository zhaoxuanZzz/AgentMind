# 📜 数据库脚本说明

## 📁 脚本文件

### init_database.sql

数据库初始化脚本，用于创建表结构和索引。

**功能：**
- 创建所有数据库表
- 创建索引优化查询性能
- 创建触发器自动更新updated_at字段
- 添加表注释和字段注释

**使用方法：**

```bash
# 方法1：使用psql命令行
psql -U agentsys -d agentsys -f backend/scripts/init_database.sql

# 方法2：使用Docker
docker exec -i agentsys-postgres psql -U agentsys agentsys < backend/scripts/init_database.sql

# 方法3：在Docker容器内执行
docker exec -it agentsys-postgres psql -U agentsys agentsys
\i /path/to/init_database.sql
```

**注意事项：**
- ⚠️ 脚本会删除现有表（如果存在），生产环境请谨慎使用
- ✅ 开发环境可以安全使用
- 📝 初始数据部分已注释，需要时可取消注释

## 🔧 其他脚本

### create_knowledge_cards.py

创建知识卡片脚本，用于初始化提示词卡片。

**使用方法：**
```bash
cd backend
python create_knowledge_cards.py
```

## 📚 相关文档

- [数据库说明文档](../../DATABASE_GUIDE.md)
- [部署文档](../../DEPLOYMENT.md)

