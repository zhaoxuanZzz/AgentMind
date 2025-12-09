# Agent System 项目结构说明

本文档详细说明项目的目录结构和文件组织。

## 📁 项目总览

```
agentSys/
├── backend/              # 后端服务
├── frontend/             # 前端应用
├── scripts/              # 工具脚本
├── docker-compose.yml    # Docker编排配置
├── deploy.sh            # Linux/macOS部署脚本
├── deploy.bat           # Windows部署脚本
├── Makefile             # Make命令定义
├── env.template         # 环境变量模板
└── 文档文件
```

## 🔧 后端服务 (backend/)

```
backend/
├── app/                       # 应用主目录
│   ├── api/                   # API层
│   │   ├── routes/            # 路由模块
│   │   │   ├── __init__.py
│   │   │   ├── chat.py        # 对话路由
│   │   │   ├── knowledge.py   # 知识库路由
│   │   │   └── tasks.py       # 任务路由
│   │   ├── __init__.py
│   │   └── schemas.py         # Pydantic数据模型
│   │
│   ├── core/                  # 核心配置
│   │   ├── __init__.py
│   │   └── config.py          # 应用配置
│   │
│   ├── db/                    # 数据库层
│   │   ├── __init__.py
│   │   ├── database.py        # 数据库连接
│   │   └── models.py          # SQLAlchemy模型
│   │
│   ├── llm/                   # LLM模块
│   │   ├── __init__.py
│   │   └── config/            # LLM配置
│   │       ├── __init__.py
│   │       └── models.json    # 模型配置文件
│   │
│   ├── services/              # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── agent_service.py   # Agent服务
│   │   ├── knowledge_service.py # 知识库服务
│   │   ├── llm_factory.py      # LLM工厂
│   │   └── tools/             # 工具模块
│   │       ├── __init__.py
│   │       ├── baidu_tool.py  # 百度搜索工具
│   │       ├── knowledge_tool.py # 知识库工具
│   │       ├── tavily_tool.py # Tavily搜索工具
│   │       ├── web_scraper_tool.py # 网页抓取工具
│   │       └── web_search_tool.py # 网页搜索工具
│   │
│   ├── __init__.py
│   └── main.py                # 应用入口
│
├── scripts/                   # 工具脚本目录
│   ├── init_database.sql     # 数据库初始化脚本
│   ├── README.md             # 脚本说明文档
│   └── create_knowledge_cards.py # 创建知识卡片脚本（可选移动）
│
├── requirements.txt           # Python依赖
├── Dockerfile                 # Docker镜像定义
├── run-backend.bat           # Windows启动脚本
├── run-backend.sh            # Linux/macOS启动脚本
└── .dockerignore             # Docker忽略文件
```

### 主要模块说明

#### app/main.py
- FastAPI应用主入口
- 配置CORS、日志
- 注册路由
- 生命周期管理

#### app/core/config.py
- 环境变量配置
- 应用设置
- 使用pydantic-settings管理

#### app/db/models.py
定义的数据模型：
- `Conversation`: 对话会话
- `Message`: 消息
- `KnowledgeBase`: 知识库
- `Document`: 文档
- `Task`: 任务

#### app/services/agent_service.py
Agent服务功能：
- 创建LangChain Agent
- 配置工具（搜索、计算、规划）
- 处理对话
- 任务规划

#### app/services/knowledge_service.py
知识库服务功能：
- ChromaDB集成
- 文档向量化
- 语义搜索
- 集合管理

#### app/services/llm_factory.py
LLM工厂功能：
- 支持多LLM提供商（OpenAI、DashScope）
- 动态创建LLM实例
- 从配置文件加载模型列表
- 提供默认配置

#### app/llm/config/models.json
LLM模型配置文件：
- 定义所有可用的LLM提供商
- 配置每个提供商的模型列表
- 设置默认模型
- 模型描述信息

#### app/api/routes/
API路由定义：
- `chat.py`: 对话相关API
- `knowledge.py`: 知识库管理API
- `tasks.py`: 任务管理API

#### backend/scripts/
工具脚本：
- `init_database.sql`: 数据库初始化脚本（创建表结构、索引、触发器）
- `create_knowledge_cards.py`: 创建知识卡片脚本

## 🎨 前端应用 (frontend/)

```
frontend/
├── src/
│   ├── api/                   # API客户端
│   │   ├── client.ts          # Axios配置
│   │   ├── services.ts        # API方法
│   │   └── types.ts           # TypeScript类型
│   │
│   ├── components/            # 组件
│   │   └── Layout.tsx         # 主布局组件
│   │
│   ├── pages/                 # 页面
│   │   ├── ChatPage.tsx       # 对话页面
│   │   ├── ChatPage.css
│   │   ├── KnowledgePage.tsx  # 知识库页面
│   │   ├── KnowledgePage.css
│   │   ├── TasksPage.tsx      # 任务页面
│   │   └── TasksPage.css
│   │
│   ├── App.tsx                # 应用根组件
│   ├── App.css
│   ├── main.tsx               # 应用入口
│   └── index.css              # 全局样式
│
├── public/                    # 静态资源
├── index.html                 # HTML模板
├── package.json               # Node.js依赖
├── tsconfig.json              # TypeScript配置
├── tsconfig.node.json
├── vite.config.ts             # Vite配置
├── Dockerfile                 # Docker镜像定义
├── nginx.conf                 # Nginx配置
└── .dockerignore             # Docker忽略文件
```

### 主要模块说明

#### src/api/
- `client.ts`: 配置axios实例，请求/响应拦截器
- `services.ts`: 封装所有API调用方法
- `types.ts`: 定义TypeScript接口

#### src/components/
- `Layout.tsx`: 主布局，包含侧边栏和导航

#### src/pages/
三个核心页面：
- `ChatPage.tsx`: AI对话界面
- `KnowledgePage.tsx`: 知识库管理界面
- `TasksPage.tsx`: 任务规划界面

## 🛠️ 工具脚本 (scripts/)

```
scripts/
├── health-check.sh    # 健康检查脚本
├── backup.sh          # 数据备份脚本
└── restore.sh         # 数据恢复脚本
```

### 脚本说明

- **health-check.sh**: 检查所有服务状态
- **backup.sh**: 备份PostgreSQL、ChromaDB和Redis数据
- **restore.sh**: 从备份恢复数据

## 🐳 Docker配置

### docker-compose.yml

定义的服务：
```yaml
services:
  postgres:     # PostgreSQL数据库
  redis:        # Redis缓存
  chromadb:     # ChromaDB向量数据库
  backend:      # 后端API服务
  frontend:     # 前端Web服务
```

数据卷：
```yaml
volumes:
  postgres_data:  # PostgreSQL数据持久化
  redis_data:     # Redis数据持久化
  chroma_data:    # ChromaDB数据持久化
```

网络：
```yaml
networks:
  agentsys-network:  # 服务间通信网络
```

### Dockerfile

- **backend/Dockerfile**: 
  - 基于python:3.11-slim
  - 安装系统依赖
  - 安装Python包
  - 暴露8000端口

- **frontend/Dockerfile**:
  - 多阶段构建
  - 第一阶段：构建React应用
  - 第二阶段：Nginx服务静态文件

## 📄 配置文件

### 环境变量

- **env.template**: 环境变量模板
- **.env**: 实际配置（不提交到Git）

必需配置：
```bash
OPENAI_API_KEY       # OpenAI API密钥
OPENAI_API_BASE      # API基础URL
MODEL_NAME           # 使用的模型
SECRET_KEY           # 应用密钥
```

### 其他配置

- **Makefile**: 定义常用命令快捷方式
- **.gitignore**: Git忽略文件列表
- **deploy.sh/bat**: 自动化部署脚本

## 📚 文档文件

```
├── README.md              # 项目总览和快速开始
├── QUICK_START.md         # 5分钟快速开始指南
├── DEPLOYMENT.md          # 详细部署文档
├── USER_GUIDE.md          # 用户操作手册
├── PROJECT_STRUCTURE.md   # 项目结构说明（本文件）
└── CHANGELOG.md           # 版本更新日志
```

## 🔄 数据流

### 对话流程

```
用户输入 → Frontend → Backend API → Agent Service
                                         ↓
                                   LangChain Agent
                                   ├─ 知识库搜索
                                   ├─ 工具调用
                                   └─ LLM推理
                                         ↓
保存对话 ← PostgreSQL ← Backend ← 返回结果
```

### 知识库流程

```
添加文档 → Frontend → Backend API → Knowledge Service
                                         ↓
                                   文本分割
                                         ↓
                                   向量化
                                         ↓
                                   存储到ChromaDB
                                         ↓
                                   保存元数据到PostgreSQL
```

### 任务规划流程

```
创建任务 → Frontend → Backend API → Agent Service
                                         ↓
                                   LangChain Agent
                                         ↓
                                   任务分析
                                         ↓
                                   生成执行计划
                                         ↓
保存到PostgreSQL ← Backend ← 返回计划
```

## 🔐 安全考虑

### 环境变量
- 所有敏感信息存储在`.env`
- `.env`不提交到版本控制
- 使用`env.template`作为模板

### API安全
- CORS配置
- 输入验证（Pydantic）
- SQL注入防护（SQLAlchemy ORM）

### 数据库安全
- 配置强密码
- 网络隔离（Docker网络）
- 定期备份

## 📊 技术栈总结

### 后端
- **Web框架**: FastAPI
- **ORM**: SQLAlchemy
- **AI框架**: LangChain
- **向量数据库**: ChromaDB
- **关系数据库**: PostgreSQL
- **缓存**: Redis

### 前端
- **框架**: React 18
- **语言**: TypeScript
- **UI库**: Ant Design
- **构建工具**: Vite
- **HTTP客户端**: Axios

### 部署
- **容器化**: Docker
- **编排**: Docker Compose
- **Web服务器**: Nginx

## 🎯 扩展指南

### 添加新的API端点

1. 在`backend/app/api/schemas.py`定义数据模型
2. 在`backend/app/api/routes/`创建或修改路由文件
3. 在`backend/app/main.py`注册路由

### 添加新的前端页面

1. 在`frontend/src/pages/`创建页面组件
2. 在`frontend/src/App.tsx`添加路由
3. 在`frontend/src/components/Layout.tsx`添加菜单项

### 添加新的Agent工具

1. 在`backend/app/services/agent_service.py`的`_create_tools`方法中添加工具
2. 定义工具函数
3. 使用`Tool`类包装

### 自定义Embedding模型

1. 修改`backend/app/services/knowledge_service.py`
2. 更改`HuggingFaceEmbeddings`或使用`OpenAIEmbeddings`
3. 更新`.env`中的`EMBEDDING_MODEL`

## 📞 技术支持

如果对项目结构有疑问：
- 查看相关文档
- 提交GitHub Issue
- 查看代码注释

---

**项目结构清晰，易于维护和扩展！** 🎉

