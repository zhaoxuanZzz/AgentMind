# LangChain 文档和版本信息

## 📦 当前版本

项目已更新到最新的 LangChain 版本：

- **langchain**: `>=1.2.0` (最新: 1.2.0, 发布于 2025-12-15)
- **langchain-community**: `>=0.4.1` (最新: 0.4.1, 发布于 2025-10-27)
- **langchain-openai**: `>=1.1.6` (最新: 1.1.6, 发布于 2025-12-19)
- **langchain-tavily**: `>=0.2.15` (最新: 0.2.15)

## 📚 官方文档链接

### 主要文档站点

1. **LangChain 官方文档（英文）**
   - 主页: https://docs.langchain.com/
   - Python 文档: https://docs.langchain.com/oss/python/langchain/overview
   - API 参考: https://reference.langchain.com/python/langchain/langchain/

2. **LangChain 中文文档**
   - 中文文档: https://docs.langchain.org.cn/
   - 中文 API 参考: https://python.langchain.com.cn/

3. **LangChain 参考文档（英文）**
   - Python API 参考: https://reference.langchain.com/python/
   - LangChain Core: https://reference.langchain.com/python/langchain_core/
   - 集成包: https://reference.langchain.com/python/integrations/

### 特定包的文档

- **langchain-community**: https://reference.langchain.com/python/integrations/langchain_community/
- **langchain-openai**: 
  - API 参考: https://reference.langchain.com/python/integrations/langchain_openai/
  - 使用指南: https://docs.langchain.com/oss/python/integrations/providers/openai
- **langchain-tavily**: https://reference.langchain.com/python/integrations/langchain_tavily/

## 🔄 版本更新说明

### LangChain 1.x 版本主要变化

LangChain 1.2.0 是当前最新版本，主要特点：

1. **架构改进**
   - 基于 LangGraph 构建的代理架构
   - 更好的流式处理支持
   - 改进的中间件系统

2. **API 变化**
   - 使用 Pydantic 2.x
   - 新的消息类型系统
   - 改进的工具接口

3. **性能优化**
   - 更快的依赖解析
   - 更好的内存管理
   - 优化的向量存储

### 迁移指南

如果从旧版本升级，请参考：

- **LangChain v0.3 迁移指南**: https://changelog.langchain.ac.cn/announcements/langchain-v0-3-migrating-to-pydantic-2-for-python-peer-dependencies-for-javascript
- **版本策略**: https://docs.langchain.com/oss/python/release-policy
- **版本控制**: https://docs.langchain.com/oss/python/versioning

## 🚀 快速开始

### 安装最新版本

使用 uv（推荐）:
```bash
cd backend
uv sync
```

使用 pip:
```bash
pip install --upgrade langchain langchain-community langchain-openai langchain-tavily
```

### 验证安装

```python
import langchain
print(f"LangChain version: {langchain.__version__}")
```

## 📖 学习资源

### 官方资源

1. **教程和指南**
   - 入门教程: https://docs.langchain.com/oss/python/get_started/introduction
   - 概念指南: https://docs.langchain.com/oss/python/concepts/
   - 示例代码: https://github.com/langchain-ai/langchain/tree/master/templates

2. **社区资源**
   - GitHub: https://github.com/langchain-ai/langchain
   - Slack 社区: https://www.langchain.com/join-community
   - Twitter: https://twitter.com/LangChainAI
   - Reddit: https://www.reddit.com/r/LangChain/

3. **发布说明**
   - GitHub Releases: https://github.com/langchain-ai/langchain/releases
   - 变更日志: https://changelog.langchain.ac.cn/

### 核心概念

- **Agents（代理）**: https://docs.langchain.com/oss/python/langchain/agents
- **Models（模型）**: https://docs.langchain.com/oss/python/langchain/models
- **Tools（工具）**: https://docs.langchain.com/oss/python/langchain/tools
- **Embeddings（嵌入）**: https://docs.langchain.com/oss/python/langchain/embeddings
- **Vector Stores（向量存储）**: https://docs.langchain.com/oss/python/langchain/vectorstores

## 🔧 项目中的使用

### 主要使用场景

1. **AI 对话服务** (`app/services/agent_service.py`)
   - 使用 LangChain 代理进行多轮对话
   - 集成知识库检索
   - 工具调用（搜索、计算等）

2. **知识库服务** (`app/services/knowledge_service.py`)
   - 使用 ChromaDB 作为向量存储
   - 文档嵌入和检索
   - 语义搜索

3. **工具集成**
   - Tavily 搜索工具 (`app/services/tools/tavily_tool.py`)
   - Web 搜索工具 (`app/services/tools/web_search_tool.py`)
   - 知识库工具 (`app/services/tools/knowledge_tool.py`)

## ⚠️ 注意事项

1. **版本兼容性**
   - LangChain 1.x 需要 Python >= 3.10
   - 项目使用 Python 3.11，完全兼容
   - 确保所有相关包版本兼容

2. **API 变化**
   - LangChain 1.x 相比 0.x 有重大 API 变化
   - 如果遇到兼容性问题，请查看迁移指南
   - 建议逐步迁移，充分测试

3. **依赖管理**
   - 使用 `uv sync` 可以自动解决依赖冲突
   - 定期更新依赖以获取安全补丁和新功能

## 📝 更新日志

### 2025-12-26
- 更新 langchain 从 `>=0.3.0` 到 `>=1.2.0`
- 更新 langchain-community 从 `>=0.3.0` 到 `>=0.4.1`
- 更新 langchain-openai 从 `>=0.2.0` 到 `>=1.1.6`
- 更新 langchain-tavily 从 `>=0.1.0` 到 `>=0.2.15`

## 🔗 相关链接

- [LangChain GitHub](https://github.com/langchain-ai/langchain)
- [LangChain PyPI](https://pypi.org/project/langchain/)
- [LangSmith](https://smith.langchain.com/) - 用于构建、测试和监控 LLM 应用
- [LangGraph](https://docs.langchain.com/oss/python/langgraph/overview) - 低级别的代理编排框架

