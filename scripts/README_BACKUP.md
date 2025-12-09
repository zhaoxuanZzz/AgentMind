# 数据库备份命令说明

## 快速使用

### Linux/macOS

```bash
# Docker方式（推荐）
USE_DOCKER=true ./scripts/backup_database.sh

# 本地PostgreSQL方式
DB_HOST=localhost DB_USER=agentsys DB_NAME=agentsys ./scripts/backup_database.sh

# 自定义备份目录
BACKUP_DIR=/path/to/backups ./scripts/backup_database.sh
```

### Windows

```cmd
REM Docker方式（推荐）
set USE_DOCKER=true
scripts\backup_database.bat

REM 本地PostgreSQL方式
set DB_HOST=localhost
set DB_USER=agentsys
set DB_NAME=agentsys
scripts\backup_database.bat

REM 自定义备份目录
set BACKUP_DIR=D:\backups
scripts\backup_database.bat
```

## 手动备份命令

### 使用 pg_dump (Docker方式)

```bash
# 完整备份（SQL格式，压缩）
docker exec agentsys-postgres pg_dump -U agentsys agentsys | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# 完整备份（自定义格式，支持并行恢复）
docker exec agentsys-postgres pg_dump -U agentsys -F c agentsys -f /tmp/backup.dump
docker cp agentsys-postgres:/tmp/backup.dump ./backup_$(date +%Y%m%d_%H%M%S).dump

# 仅备份表结构
docker exec agentsys-postgres pg_dump -U agentsys -s agentsys > schema_$(date +%Y%m%d_%H%M%S).sql

# 仅备份数据
docker exec agentsys-postgres pg_dump -U agentsys -a agentsys > data_$(date +%Y%m%d_%H%M%S).sql
```

### 使用 pg_dump (本地PostgreSQL)

```bash
# 完整备份（SQL格式，压缩）
pg_dump -h localhost -p 5432 -U agentsys agentsys | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# 完整备份（自定义格式）
pg_dump -h localhost -p 5432 -U agentsys -F c agentsys -f backup_$(date +%Y%m%d_%H%M%S).dump

# 仅备份表结构
pg_dump -h localhost -p 5432 -U agentsys -s agentsys > schema_$(date +%Y%m%d_%H%M%S).sql

# 仅备份数据
pg_dump -h localhost -p 5432 -U agentsys -a agentsys > data_$(date +%Y%m%d_%H%M%S).sql
```

### Windows PowerShell

```powershell
# Docker方式
docker exec agentsys-postgres pg_dump -U agentsys agentsys | Out-File -Encoding UTF8 backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').sql.gz

# 本地PostgreSQL方式
$env:PGPASSWORD="your_password"
pg_dump -h localhost -p 5432 -U agentsys agentsys | Out-File -Encoding UTF8 backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').sql
```

## 环境变量说明

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `DB_NAME` | `agentsys` | 数据库名称 |
| `DB_USER` | `agentsys` | 数据库用户名 |
| `DB_HOST` | `localhost` | 数据库主机地址 |
| `DB_PORT` | `5432` | 数据库端口 |
| `BACKUP_DIR` | `./backups` | 备份文件保存目录 |
| `USE_DOCKER` | `false` | 是否使用Docker容器 |
| `DOCKER_CONTAINER` | `agentsys-postgres` | Docker容器名称 |
| `PGPASSWORD` | - | PostgreSQL密码（本地方式需要） |

## 备份文件格式

### SQL格式 (.sql)
- **优点**: 可读性强，可以直接编辑
- **缺点**: 文件较大，恢复较慢
- **适用场景**: 小数据库，需要查看或编辑SQL

### 自定义格式 (.dump)
- **优点**: 文件较小，支持并行恢复，可以选择性恢复
- **缺点**: 不可读，需要pg_restore恢复
- **适用场景**: 生产环境，大数据库

### 压缩格式 (.sql.gz)
- **优点**: 文件最小
- **缺点**: 需要解压后才能使用
- **适用场景**: 长期存储，节省空间

## 定时备份

### Linux (crontab)

```bash
# 编辑crontab
crontab -e

# 每天凌晨2点备份
0 2 * * * cd /path/to/agentSys && USE_DOCKER=true ./scripts/backup_database.sh

# 每小时备份
0 * * * * cd /path/to/agentSys && USE_DOCKER=true ./scripts/backup_database.sh
```

### Windows (任务计划程序)

1. 打开"任务计划程序"
2. 创建基本任务
3. 触发器：每天/每小时
4. 操作：启动程序
   - 程序：`cmd.exe`
   - 参数：`/c cd /d D:\code\agentSys && set USE_DOCKER=true && scripts\backup_database.bat`

## 恢复数据库

### 从SQL文件恢复

```bash
# Docker方式
gunzip < backup.sql.gz | docker exec -i agentsys-postgres psql -U agentsys agentsys

# 本地方式
gunzip < backup.sql.gz | psql -h localhost -p 5432 -U agentsys agentsys
```

### 从自定义格式恢复

```bash
# Docker方式
docker cp backup.dump agentsys-postgres:/tmp/backup.dump
docker exec agentsys-postgres pg_restore -U agentsys -d agentsys -c /tmp/backup.dump

# 本地方式
pg_restore -h localhost -p 5432 -U agentsys -d agentsys -c backup.dump
```

## 注意事项

1. **密码设置**: 本地PostgreSQL方式需要设置`PGPASSWORD`环境变量或使用`.pgpass`文件
2. **权限检查**: 确保备份用户有足够的权限访问数据库
3. **磁盘空间**: 备份前检查磁盘空间是否充足
4. **备份验证**: 定期验证备份文件的完整性
5. **清理旧备份**: 建议设置自动清理策略，避免占用过多磁盘空间

## 故障排查

### 问题：找不到pg_dump命令
**解决**: 安装PostgreSQL客户端工具
- Ubuntu/Debian: `sudo apt-get install postgresql-client`
- CentOS/RHEL: `sudo yum install postgresql`
- Windows: 下载PostgreSQL安装包，选择安装客户端工具

### 问题：Docker容器未运行
**解决**: 检查容器状态
```bash
docker ps | grep agentsys-postgres
```

### 问题：权限不足
**解决**: 检查数据库用户权限
```sql
-- 在PostgreSQL中执行
GRANT ALL PRIVILEGES ON DATABASE agentsys TO agentsys;
```

