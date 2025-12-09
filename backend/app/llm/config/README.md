# LLM模型配置

## 📋 说明

本目录存放LLM模型配置文件，用于管理所有可用的LLM提供商和模型。

## 📁 文件说明

### models.json

LLM模型配置文件，包含：

- **providers**: 所有LLM提供商配置
  - `openai`: OpenAI模型列表
  - `dashscope`: 阿里百炼模型列表
  
- **defaults**: 默认配置
  - `provider`: 默认提供商
  - `openai_model`: OpenAI默认模型
  - `dashscope_model`: DashScope默认模型

## 🔧 使用方法

### 添加新模型

编辑 `models.json`，在对应提供商的 `models` 数组中添加：

```json
{
  "id": "model-id",
  "name": "模型显示名称",
  "description": "模型描述"
}
```

### 添加新提供商

在 `providers` 对象中添加新的提供商配置：

```json
{
  "providers": {
    "new_provider": {
      "id": "new_provider",
      "name": "新提供商",
      "models": [...]
    }
  }
}
```

然后在 `llm_factory.py` 中添加对应的创建逻辑。

## 📝 注意事项

1. JSON文件必须使用UTF-8编码
2. 修改后需要重启服务才能生效
3. 配置文件加载失败时会使用默认配置

## 🔗 相关文件

- `app/services/llm_factory.py` - LLM工厂，使用此配置
- `app/core/config.py` - 应用配置，包含API密钥等

