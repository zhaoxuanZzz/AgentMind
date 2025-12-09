# 🔧 环境变量配置指南

## 📋 配置步骤

### 1. 创建 `.env` 文件

在项目根目录创建 `.env` 文件（与 `docker-compose.yml` 同级）：

```bash
# Windows
type nul > .env

# Linux/macOS
touch .env
```

### 2. 填写配置内容

将以下内容复制到 `.env` 文件中：

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

# OpenAI API配置（可选）
OPENAI_API_KEY=
OPENAI_API_BASE=https://api.openai.com/v1
MODEL_NAME=gpt-3.5-turbo

# ============================================
# 工具配置
# ============================================

# Tavily搜索工具（联网搜索）
TAVILY_API_KEY=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

# ============================================
# 安全配置
# ============================================

SECRET_KEY=change-this-to-a-random-secret-key-in-production
```

### 3. 替换API Key

**必填项：**
- 将 `sk-your-dashscope-api-key-here` 替换为您的阿里百炼 API Key

**可选项：**
- `TAVILY_API_KEY` 已提供测试Key，可直接使用
- 如需使用OpenAI，填写 `OPENAI_API_KEY`

### 4. 启动服务

```bash
docker-compose up -d
```

## 📝 环境变量说明

### LLM配置

| 变量名 | 说明 | 默认值 | 必填 |
|--------|------|--------|------|
| `LLM_PROVIDER` | LLM提供商 | `dashscope` | 是 |
| `DASHSCOPE_API_KEY` | 阿里百炼API密钥 | - | **是** |
| `DASHSCOPE_MODEL` | 使用的模型 | `qwen-max` | 否 |
| `DASHSCOPE_EMBEDDING_MODEL` | 向量化模型 | `text-embedding-v3` | 否 |
| `USE_DASHSCOPE_EMBEDDING` | 是否使用百炼向量化 | `true` | 否 |

### 可选配置

| 变量名 | 说明 | 默认值 | 必填 |
|--------|------|--------|------|
| `TAVILY_API_KEY` | 联网搜索API | 已提供测试Key | 否 |
| `OPENAI_API_KEY` | OpenAI API密钥 | - | 否 |
| `OPENAI_API_BASE` | OpenAI API地址 | `https://api.openai.com/v1` | 否 |
| `MODEL_NAME` | OpenAI模型名称 | `gpt-3.5-turbo` | 否 |

### 安全配置

| 变量名 | 说明 | 默认值 | 必填 |
|--------|------|--------|------|
| `SECRET_KEY` | JWT密钥 | - | 是 |

## 🔑 获取API Key

### 阿里百炼 API Key（必需）

1. 访问 [阿里云百炼控制台](https://dashscope.console.aliyun.com/)
2. 登录或注册阿里云账号
3. 在控制台中获取 API Key
4. 复制API Key到 `.env` 文件的 `DASHSCOPE_API_KEY`

💡 **新用户福利**: 阿里百炼对新用户提供免费额度

### Tavily API Key（可选）

**已提供测试Key**: `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`

如需自己的Key:
1. 访问 [Tavily官网](https://tavily.com/)
2. 注册账号
3. 获取API Key
4. 替换 `.env` 文件中的 `TAVILY_API_KEY`

### OpenAI API Key（可选）

1. 访问 [OpenAI平台](https://platform.openai.com/)
2. 登录或注册账号
3. 创建API Key
4. 填写到 `.env` 文件的 `OPENAI_API_KEY`

如使用国内代理:
- 修改 `OPENAI_API_BASE` 为代理地址

## 🎯 配置模板

### 最小配置（仅阿里百炼）

```bash
LLM_PROVIDER=dashscope
DASHSCOPE_API_KEY=sk-your-api-key-here
SECRET_KEY=random-secret-key-here
```

### 完整配置（所有功能）

```bash
# LLM配置
LLM_PROVIDER=dashscope
DASHSCOPE_API_KEY=sk-your-dashscope-key
DASHSCOPE_MODEL=qwen-max
DASHSCOPE_EMBEDDING_MODEL=text-embedding-v3
USE_DASHSCOPE_EMBEDDING=true

# OpenAI（多模型切换）
OPENAI_API_KEY=sk-your-openai-key
OPENAI_API_BASE=https://api.openai.com/v1
MODEL_NAME=gpt-3.5-turbo

# Tavily（联网搜索）
TAVILY_API_KEY=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

# 安全
SECRET_KEY=your-random-secret-key
```

## 🐛 常见问题

### Q: 如何验证配置是否正确？

**A**: 启动后检查日志:

```bash
docker-compose logs backend | grep "API"
```

看到类似输出说明配置成功:
```
INFO: DASHSCOPE_API_KEY configured
INFO: TAVILY_API_KEY configured
```

### Q: 启动时报错 "DASHSCOPE_API_KEY not set"

**A**: 检查步骤:
1. 确认 `.env` 文件存在于项目根目录
2. 检查文件内容是否正确
3. 重启服务: `docker-compose restart backend`

### Q: Tavily搜索不可用

**A**: 检查步骤:
1. 确认 `TAVILY_API_KEY` 已配置
2. 检查Key是否有效
3. 查看后端日志: `docker-compose logs backend`

### Q: 如何切换到OpenAI模型？

**A**: 步骤:
1. 在 `.env` 中添加 `OPENAI_API_KEY`
2. 重启服务
3. 在前端界面选择OpenAI提供商

### Q: 环境变量修改后不生效

**A**: 需要重启服务:
```bash
docker-compose down
docker-compose up -d
```

## 🔒 安全提示

1. **不要提交 `.env` 文件到Git**
   - `.env` 已在 `.gitignore` 中
   - 检查: `git status` 不应显示 `.env`

2. **定期更换密钥**
   - 特别是生产环境
   - 使用强随机字符串作为 `SECRET_KEY`

3. **保护API Key**
   - 不要在代码中硬编码
   - 不要分享给他人
   - 发现泄露立即更换

## 📚 相关文档

- [快速开始指南](./QUICK_START.md)
- [部署文档](./DEPLOYMENT.md)
- [用户手册](./USER_GUIDE.md)
- [提示词管理](./PROMPT_CARD_GUIDE.md)

---

**配置完成后，运行 `docker-compose up -d` 启动服务！** 🚀

