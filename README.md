# AgentMind - 智能助手系统

一个功能完整的AI Agent系统，支持知识库检索、智能问答和任务规划。

## 📋 功能特性

- 🤖 **AI对话**: 基于LangChain的智能对话，支持多轮对话和上下文理解
- 📚 **知识库检索**: 使用ChromaDB向量数据库，支持语义搜索
- 📝 **角色预设**: 创建、编辑、管理和应用AI角色预设，快速获得专业响应
- 🎯 **任务规划**: AI自动分解任务，生成执行计划
- 🔧 **工具集成**: 内置搜索、计算、网页抓取等工具，支持扩展
- 🌐 **联网搜索**: 集成Tavily搜索引擎，可实时获取网络信息
- 💾 **持久化存储**: PostgreSQL存储对话和任务，Redis缓存
- 🐳 **一键部署**: 基于Docker Compose，支持快速部署
- 🎨 **精美界面**: 三栏布局，渐变动画，现代化设计

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                     前端 (React + TS)                    │
│              Ant Design UI + Vite                        │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                  后端 API (FastAPI)                      │
│           LangChain + OpenAI + 工具链                    │
└─────────────────────────────────────────────────────────┘
                            ↓
┌──────────────┬──────────────┬──────────────────────────┐
│  PostgreSQL  │    Redis     │    ChromaDB              │
│  (主数据库)  │   (缓存)     │   (向量数据库)           │
└──────────────┴──────────────┴──────────────────────────┘
```

## 🚀 快速开始

### 前置要求

- Docker 20.10+
- Docker Compose 2.0+
- 阿里百炼 API Key（必填）- 从 [阿里云百炼控制台](https://dashscope.console.aliyun.com/) 获取
- OpenAI API Key（可选）- 如需切换使用OpenAI模型

### 一键部署

#### Linux/macOS

```bash
# 1. 克隆项目
git clone <repository-url>
cd AgentMind

# 2. 配置环境变量（推荐使用配置向导）
chmod +x setup-env.sh
./setup-env.sh
# 或手动配置: cp env.template .env && nano .env

# 3. 运行部署脚本
chmod +x deploy.sh
./deploy.sh
```

#### Windows

```cmd
# 1. 克隆项目
git clone <repository-url>
cd AgentMind

# 2. 配置环境变量（推荐使用配置向导）
setup-env.bat
# 或手动配置: copy env.template .env && notepad .env

# 3. 运行部署脚本
deploy.bat
```

💡 **配置向导**: 运行 `setup-env.bat` (Windows) 或 `setup-env.sh` (Linux/macOS) 可自动创建配置文件

### 手动部署

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 2. 构建并启动服务
docker-compose build
docker-compose up -d

# 3. 查看服务状态
docker-compose ps

# 4. 查看日志
docker-compose logs -f
```

## 🌐 访问服务

部署成功后，可以通过以下地址访问：

- **前端界面**: http://localhost:8080
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs (Swagger UI)

## 📁 项目结构

```
AgentMind/
├── backend/                 # 后端服务
│   ├── app/
│   │   ├── api/            # API路由
│   │   │   ├── routes/     # 路由模块
│   │   │   └── schemas.py  # 数据模型
│   │   ├── core/           # 核心配置
│   │   ├── db/             # 数据库模型
│   │   ├── services/       # 业务逻辑
│   │   │   ├── agent_service.py      # Agent服务
│   │   │   └── knowledge_service.py  # 知识库服务
│   │   └── main.py         # 应用入口
│   ├── requirements.txt    # Python依赖
│   └── Dockerfile
├── frontend/               # 前端应用
│   ├── src/
│   │   ├── api/           # API客户端
│   │   ├── components/    # 组件
│   │   ├── pages/         # 页面
│   │   │   ├── ChatPage.tsx      # 对话页面
│   │   │   ├── KnowledgePage.tsx # 知识库页面
│   │   │   └── TasksPage.tsx     # 任务页面
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml      # Docker编排配置
├── deploy.sh              # Linux/macOS部署脚本
├── deploy.bat             # Windows部署脚本
├── .env.example           # 环境变量模板
└── README.md
```

## 🔧 配置说明

### 环境变量配置

#### 方法1：创建 `.env` 文件（推荐）

在项目根目录创建 `.env` 文件，配置以下参数：

```bash
# ============================================
# LLM提供商配置
# ============================================

# LLM提供商选择: dashscope 或 openai
LLM_PROVIDER=dashscope

# 阿里百炼API配置（必填）
DASHSCOPE_API_KEY=sk-your-dashscope-api-key-here
DASHSCOPE_MODEL=qwen-max
DASHSCOPE_EMBEDDING_MODEL=text-embedding-v3
USE_DASHSCOPE_EMBEDDING=true

# OpenAI API配置（可选 - 用于多模型切换）
OPENAI_API_KEY=
OPENAI_API_BASE=https://api.openai.com/v1
MODEL_NAME=gpt-3.5-turbo

# ============================================
# 工具配置
# ============================================

# Tavily搜索工具（联网搜索 - 可选）
# 获取地址: https://tavily.com/
TAVILY_API_KEY=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

# ============================================
# 安全配置
# ============================================

# 安全密钥（建议修改）
SECRET_KEY=your-secret-key-change-this-in-production
```

#### 方法2：从模板文件复制

```bash
# 复制模板文件
cp env.template .env

# 编辑 .env 文件，填入您的API Key
# Linux/macOS
nano .env

# Windows
notepad .env
```

#### 配置说明

**必填配置：**
- `DASHSCOPE_API_KEY`: 阿里百炼API密钥（必需）
  - 获取地址: https://dashscope.console.aliyun.com/

**可选配置：**
- `TAVILY_API_KEY`: 联网搜索功能
  - 已提供测试Key: `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`
  - 或在 https://tavily.com/ 获取自己的Key
- `OPENAI_API_KEY`: 如需使用OpenAI模型

**其他配置：**
- 数据库、Redis等配置由 docker-compose 自动管理
- 无需手动配置

### 获取阿里百炼API Key

1. 访问 [阿里云百炼控制台](https://dashscope.console.aliyun.com/)
2. 登录或注册阿里云账号
3. 在控制台中获取 API Key

💡 **提示**：阿里百炼对新用户有免费额度，特别适合中文场景！

### 可选配置OpenAI

如需在UI中切换使用OpenAI模型，在 `.env` 中填入 `OPENAI_API_KEY`。
如果使用国内代理服务，修改 `OPENAI_API_BASE`。

## 📖 使用指南

### 1. AI对话

1. 访问 http://localhost:8080
2. 在对话界面输入问题
3. 可选择知识库进行RAG检索增强
4. AI会自动调用工具完成复杂任务
5. 支持切换 `qwen3-max` 和 `qwen3-vl-plus` 模型

**三栏式布局：**
- **左侧栏**：对话历史记录，快速切换会话
- **中间栏**：主对话区域，发送消息和查看回复
- **右侧栏**：角色预设配置，管理AI角色

**工具调用可视化：**
- Agent调用工具时，自动展示调用过程
- 点击"使用了X个工具"查看详细步骤
- 时间线展示工具调用顺序
- 显示每个工具的输入和输出
- 支持的工具图标：
  - 🔍 联网搜索（Tavily）
  - 🌐 网页抓取
  - 📄 PDF解析
  - 📚 知识库检索
  - 🔢 计算器

### 2. 角色预设管理

1. 在右侧栏点击"新建"按钮
2. 填写角色预设信息：
   - **标题**：简短名称（如：项目管理助手）
   - **内容**：详细的AI行为描述
   - **分类**：商业/技术/分析/创意
   - **标签**：多个标签用逗号分隔
3. 点击"保存"创建角色预设
4. 在对话中选择角色预设，AI将以该角色回答
5. 支持编辑和删除已有角色预设

**使用场景：**
- 项目管理咨询
- 代码审查指导
- 数据分析建议
- 营销文案创作

详细指南请查看 [角色预设管理指南](./PROMPT_CARD_GUIDE.md)

### 3. 知识库管理

1. 进入"知识库"页面
2. 创建知识库（例如：产品文档、FAQ）
3. 添加文档内容
4. 系统自动向量化并建立索引
5. 在"搜索测试"中验证检索效果

### 4. 任务规划

1. 进入"任务规划"页面
2. 创建任务并描述需求
3. 点击"生成规划"，AI自动分解任务
4. 查看详细的执行步骤
5. 管理任务状态

## 🛠️ 常用命令

```bash
# 查看所有容器状态
docker-compose ps

# 查看实时日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend

# 重启服务
docker-compose restart

# 停止服务
docker-compose stop

# 启动服务
docker-compose start

# 完全删除（包括数据）
docker-compose down -v

# 仅删除容器（保留数据）
docker-compose down
```

## 🔍 故障排查

### 快速诊断

#### 1. 查询天气/新闻没有反应？

```bash
# 检查服务状态
docker-compose ps

# 查看后端日志
docker-compose logs backend

# 运行诊断脚本
python test_tavily.py
```

**常见原因**:
- 后端服务未运行 → 运行 `docker-compose up -d`
- 环境变量未配置 → 运行 `setup-env.bat` 或 `setup-env.sh`
- TAVILY_API_KEY未设置 → 检查 `.env` 文件

📚 **详细排查步骤**: 查看 [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

### 2. 服务无法启动

```bash
# 查看详细日志
docker-compose logs

# 检查端口占用
# Linux/macOS
netstat -tulpn | grep -E '(8000|8080|5432|6379)'
# Windows
netstat -ano | findstr "8000 8080 5432 6379"
```

### 3. API连接失败

- 检查 `.env` 中的 `DASHSCOPE_API_KEY` 是否正确
- 检查网络是否可以访问API地址
- 查看后端日志: `docker-compose logs backend`

### 4. 向量数据库错误

```bash
# 重启ChromaDB
docker-compose restart chromadb

# 查看ChromaDB日志
docker-compose logs chromadb
```

### 5. 前端无法访问

- 确认后端服务已启动: `curl http://localhost:8000/health`
- 检查nginx配置: `docker-compose logs frontend`

## 🎨 自定义开发

### PyCharm 配置

如果使用 PyCharm 开发，需要正确配置项目结构以识别导入路径：

```bash
# 运行配置助手
python setup_pycharm.py
```

**快速配置步骤：**
1. 右键点击 `backend` 文件夹
2. 选择 `Mark Directory as` → `Sources Root`
3. `File` → `Invalidate Caches` → `Invalidate and Restart`

📚 **详细配置**: 查看 [PYCHARM_SETUP.md](./PYCHARM_SETUP.md)

### 后端开发

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 运行开发服务器
python -m app.main
```

### 前端开发

```bash
cd frontend

# 安装依赖
npm install

# 运行开发服务器
npm run dev

# 构建生产版本
npm run build
```

### 添加新工具

在 `backend/app/services/agent_service.py` 中添加新工具：

```python
def your_custom_tool(input: str) -> str:
    """工具描述"""
    # 实现工具逻辑
    return result

tools.append(Tool(
    name="tool_name",
    func=your_custom_tool,
    description="工具使用说明"
))
```

## 📊 技术栈

### 后端
- **FastAPI**: 现代、高性能的Python Web框架
- **LangChain**: LLM应用开发框架
- **ChromaDB**: 向量数据库
- **PostgreSQL**: 关系型数据库
- **Redis**: 缓存和会话管理
- **SQLAlchemy**: ORM
- **Pydantic**: 数据验证

### 前端
- **React 18**: UI框架
- **TypeScript**: 类型安全
- **Ant Design**: UI组件库
- **Vite**: 构建工具
- **Axios**: HTTP客户端

### 部署
- **Docker**: 容器化
- **Docker Compose**: 服务编排
- **Nginx**: Web服务器

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## 📮 联系方式

如有问题或建议，请提交Issue或联系开发团队。

---

**开始使用吧！祝您使用愉快！** 🎉

