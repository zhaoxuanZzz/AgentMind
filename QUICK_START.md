# Agent System 快速开始指南

5分钟快速部署和使用Agent System！使用阿里百炼平台，特别适合中文场景！

## 🚀 快速部署（3步搞定）

### 第1步：准备环境

确保已安装：
- Docker 20.10+
- Docker Compose 2.0+

### 第2步：获取阿里百炼API密钥

1. 访问 [阿里云百炼控制台](https://dashscope.console.aliyun.com/)
2. 登录或注册阿里云账号
3. 在控制台中创建/获取 API Key

💡 新用户有免费额度！

### 第3步：配置环境变量

#### 方法1：使用配置向导（推荐）

**Windows:**
```bash
# 克隆项目
git clone <repository-url>
cd agentSys

# 运行配置向导
setup-env.bat
```

**Linux/macOS:**
```bash
# 克隆项目
git clone <repository-url>
cd agentSys

# 运行配置向导
chmod +x setup-env.sh
./setup-env.sh
```

配置向导会自动创建 `.env` 文件，包含所有必要的配置。

#### 方法2：手动配置

```bash
# 创建配置文件
cp env.template .env

# 编辑.env文件
# Windows: notepad .env
# Linux/Mac: nano .env
```

在`.env`文件中设置：
```bash
# ============================================
# 必填项
# ============================================

# 阿里百炼API密钥
DASHSCOPE_API_KEY=sk-你的阿里百炼API-Key
DASHSCOPE_MODEL=qwen-max
LLM_PROVIDER=dashscope

# ============================================
# 可选项（已有默认值）
# ============================================

# Tavily联网搜索（已提供测试Key，可直接使用）
TAVILY_API_KEY=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

# OpenAI（如需使用OpenAI模型）
OPENAI_API_KEY=
```

💡 **配置说明：**
- **DASHSCOPE_API_KEY**: 必填，从阿里百炼获取
- **TAVILY_API_KEY**: 已提供测试Key，可直接使用联网搜索功能
- **OPENAI_API_KEY**: 可选，用于多模型切换

📚 **详细配置指南**: 查看 [ENV_CONFIG_GUIDE.md](./ENV_CONFIG_GUIDE.md)

### 第4步：一键部署

**Linux/macOS:**
```bash
chmod +x deploy.sh
./deploy.sh
```

**Windows:**
```cmd
deploy.bat
```

等待2-3分钟，部署完成！

## 🌐 访问系统

部署成功后：

- **前端界面**: http://localhost:8080
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

## 💡 快速体验

### 1. AI对话 (30秒)

1. 打开 http://localhost:8080
2. 在输入框输入："你好，请介绍一下你自己"
3. 点击发送
4. ✅ 完成！AI会回复你

### 2. 创建知识库 (2分钟)

1. 点击左侧"知识库"菜单
2. 点击"创建知识库"
   - 名称：测试知识库
   - 描述：我的第一个知识库
3. 点击新创建的知识库
4. 点击"添加文档"
   - 标题：Docker简介
   - 内容：Docker是一个开源的容器化平台...
5. 切换到"搜索测试"
   - 输入：什么是Docker？
6. ✅ 查看搜索结果

### 3. 任务规划 (1分钟)

1. 点击左侧"任务规划"菜单
2. 点击"快速规划"
3. 输入：开发一个简单的博客系统
4. 点击"生成规划"
5. ✅ AI会自动生成详细的执行计划

## 🎯 常用命令

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 停止服务
docker-compose stop

# 启动服务
docker-compose start

# 完全删除（包括数据）
docker-compose down -v
```

## 🛠️ 使用Makefile（推荐）

如果系统支持make命令：

```bash
make help          # 查看所有命令
make setup         # 初始化配置
make up            # 启动服务
make logs          # 查看日志
make ps            # 查看状态
make down          # 停止服务
make backup        # 备份数据
```

## 📱 核心功能速览

### AI对话
- ✅ 多轮对话
- ✅ 上下文记忆
- ✅ 知识库检索
- ✅ 工具调用（计算、搜索等）

### 知识库
- ✅ 创建多个知识库
- ✅ 添加文档
- ✅ 语义搜索
- ✅ 相似度评分

### 任务规划
- ✅ 任务创建
- ✅ 自动生成执行计划
- ✅ 步骤分解
- ✅ 状态管理

## ❓ 遇到问题？

### 端口被占用
```bash
# 修改docker-compose.yml中的端口映射
# 例如将8080改为3000
ports:
  - "3000:80"  # 前端
```

### API密钥错误
```bash
# 检查.env文件中的OPENAI_API_KEY
# 确保没有多余的空格或引号
OPENAI_API_KEY=sk-xxxxx
```

### 服务启动失败
```bash
# 查看详细日志
docker-compose logs backend

# 重新构建
docker-compose build --no-cache
docker-compose up -d
```

### 健康检查
```bash
# Linux/macOS
./scripts/health-check.sh

# 或手动检查
curl http://localhost:8000/health
curl http://localhost:8080
```

## 📚 深入学习

- **完整文档**: 查看 [README.md](README.md)
- **部署指南**: 查看 [DEPLOYMENT.md](DEPLOYMENT.md)
- **用户手册**: 查看 [USER_GUIDE.md](USER_GUIDE.md)

## 🎉 下一步

恭喜！你已经成功部署了Agent System。

现在可以：

1. 📖 创建自己的专属知识库
2. 💬 和AI进行深度对话
3. 📋 使用AI规划你的项目任务
4. 🔧 根据需求自定义系统

## 💪 进阶使用

### 连接到现有数据库

编辑`.env`:
```bash
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

### 使用国内API代理

编辑`.env`:
```bash
OPENAI_API_BASE=https://your-proxy.com/v1
```

### 自定义模型

编辑`.env`:
```bash
MODEL_NAME=gpt-4  # 或其他模型
```

## 🤝 需要帮助？

- 📖 查看文档
- 🐛 提交Issue
- 💬 加入讨论

---

**开始你的AI之旅吧！** 🚀

