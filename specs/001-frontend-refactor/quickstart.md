# 前端重构快速开始指南

**特性**：001-frontend-refactor  
**日期**：2026-01-24  

---

## 前提条件

- Node.js 18+ 和 npm
- 对 React 18、TypeScript、Ant Design 的基本了解
- 已安装依赖：`@ant-design/x-sdk`

---

## 安装新依赖

```bash
cd frontend

# 安装核心依赖
npm install framer-motion react-markdown react-syntax-highlighter lodash-es

# 安装类型定义
npm install -D @types/lodash-es @types/react-syntax-highlighter
```

---

## Phase 1: 基础架构（Week 1）

### 1.1 配置主题系统

创建 `src/styles/theme.css`:
```css
:root {
  --primary-color: #1677ff;
  --bg-primary: #ffffff;
  --bg-secondary: #f5f8fc;
  /* ... 其他变量 */
}
```

### 1.2 更新 App.tsx

```typescript
import { ConfigProvider } from 'antd'

const theme = {
  token: {
    colorPrimary: '#1677ff',
    colorBgContainer: '#ffffff',
    /* ... */
  }
}

function App() {
  return (
    <ConfigProvider theme={theme}>
      {/* 应用内容 */}
    </ConfigProvider>
  )
}
```

### 1.3 创建基础目录结构

```bash
mkdir -p src/{components,hooks,types,utils}/
mkdir -p src/pages/ChatPage/components
mkdir -p src/pages/ChatPage/hooks
```

---

## Phase 2: 聊天页面重构（Week 2）

### 2.1 创建 StreamAPI Hook

`src/hooks/useStreamChat.ts` - 参考 `contracts/stream-api.md`

### 2.2 拆分 ChatPage 组件

按照 `research.md` R4 的组件层级拆分

### 2.3 实现 XRequest 集成

参考 `contracts/stream-api.md` 的示例代码

---

## 关键文档

- [研究报告](./research.md) - 技术调研结果
- [数据模型](./data-model.md) - 前端数据结构
- [API 契约](./contracts/) - 接口定义
- [实施计划](./plan.md) - 完整计划

---

**下一步**：运行 `/speckit.tasks` 生成详细任务列表
