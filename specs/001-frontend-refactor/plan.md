# 实现计划：前端重构 - 基于 @ant-design/x-sdk

**分支**：`001-frontend-refactor` | **日期**：2026-01-24 | **规范**：[spec.md](./spec.md)
**输入**：来自 `/specs/001-frontend-refactor/spec.md` 的特性规范

**注意**：此模板由 `/speckit.plan` 命令填充。详见 `.specify/templates/commands/plan.md` 以了解执行工作流程。

## 摘要

重构 AgentMind 前端应用，采用 `@ant-design/x-sdk` 作为核心 AI 对话流处理库。主要改进包括：
1. 使用 XRequest 替代 EventSource 处理流式响应
2. 采用清新淡雅浅色主题（白色+浅蓝色）
3. 组件化重构，将 1298 行的 ChatPage.tsx 拆分为中等粒度的功能模块
4. 新增思考过程和工具调用可视化
5. 实现流畅的动画效果和响应式设计
6. 分阶段性能优化（基础优化优先，虚拟滚动 Phase 4）

## 技术背景

**语言/版本**：TypeScript 5.2+、ECMAScript 2022  
**主要依赖**：
  - React 18.2+（前端框架）
  - Ant Design 5.11+（UI 组件库）
  - @ant-design/x-sdk 2.1+（AI 对话流处理 - 已安装）
  - framer-motion 11.x（动画库 - 需安装）
  - react-markdown + highlight.js（Markdown 渲染 - highlight.js 已安装）
  
**存储**：浏览器 LocalStorage（会话持久化）、SessionStorage（临时状态）  
**测试**：Vitest + React Testing Library（需配置）  
**目标平台**：现代浏览器（Chrome 90+、Firefox 88+、Safari 14+、Edge 90+）、移动端（375px+）  
**项目类型**：Web 应用 - 前端重构（后端 FastAPI 保持不变）  
**性能目标**：
  - 首屏加载 < 2s（3G 网络）
  - 流式响应延迟 < 100ms
  - 动画帧率 60 FPS
  - 支持 1000+ 消息列表（Phase 4 虚拟滚动）
  
**约束**：
  - 必须兼容现有后端 API（/api/chat/stream）
  - TypeScript 严格模式
  - 仅浅色主题（暗色主题延后）
  - 移动端适配（响应式断点：576px、768px、992px）
  
**规模/范围**：
  - 3 个主要页面（聊天、知识库、任务）
  - ~15-20 个可复用组件
  - ~8-10 个自定义 Hooks
  - 预计代码量：~3000-4000 行 TypeScript/TSX

## 宪章检查

*门控：必须在第 0 阶段研究之前通过。在第 1 阶段设计后重新检查。*

验证是否符合 AgentMind 宪章（v1.0.0）：

- [x] **模块化服务设计**：✅ 前端组件采用中等粒度拆分，每个组件单一职责（UserMessage、AIMessage、ThinkingProcess 等），可独立测试
- [⚠️] **API 优先开发**：⚠️ 部分适用 - 前端消费现有后端 API，但需定义流式数据格式接口（StreamChunk）作为契约
- [N/A] **依赖管理**：N/A - 前端使用 npm/package.json，不适用 uv（后端工具）
- [x] **类型安全**：✅ TypeScript 严格模式，所有组件和 Hooks 使用完整类型定义
- [⚠️] **可观测性**：⚠️ 部分适用 - 前端使用浏览器 console 日志，关键交互点（XRequest callbacks、错误边界）包含日志

**违规项（如有）**：

| 项目 | 状态 | 说明 |
|------|------|------|
| API 优先开发 | 部分适用 | 前端作为 API 消费者，需定义 TypeScript 接口作为前端契约。后端契约由 FastAPI Pydantic 模型定义 |
| 依赖管理（uv） | 不适用 | uv 是 Python 工具，前端使用 npm。npm 已是前端标准实践 |
| 可观测性（Loguru） | 部分适用 | 浏览器环境使用 console API。考虑引入前端日志库（如 loglevel）用于结构化日志 |

## Project Structure

### Documentation (this feature)

```text
specs/001-frontend-refactor/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output - 技术调研和决策
├── data-model.md        # Phase 1 output - 前端数据模型和状态管理
├── quickstart.md        # Phase 1 output - 快速开始指南
├── contracts/           # Phase 1 output - API 接口定义
│   ├── stream-api.ts    # 流式响应接口
│   ├── chat-api.ts      # 聊天 API 接口
│   └── knowledge-api.ts # 知识库 API 接口
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── components/          # 全局共享组件
│   │   ├── MessageBubble/   # 消息气泡组件
│   │   │   ├── index.tsx
│   │   │   ├── UserMessage.tsx
│   │   │   ├── AIMessage.tsx
│   │   │   ├── ThinkingProcess.tsx
│   │   │   ├── ToolCallDisplay.tsx
│   │   │   └── styles.module.css
│   │   ├── StreamingText/   # 流式文本显示
│   │   │   ├── index.tsx
│   │   │   └── styles.module.css
│   │   ├── MarkdownRenderer/ # Markdown 渲染器
│   │   │   ├── index.tsx
│   │   │   └── styles.module.css
│   │   └── Layout/          # 布局组件
│   │       ├── AppLayout.tsx
│   │       └── styles.module.css
│   ├── pages/
│   │   ├── ChatPage/        # 对话页面（重构重点）
│   │   │   ├── index.tsx
│   │   │   ├── components/
│   │   │   │   ├── ConversationSidebar/
│   │   │   │   │   ├── index.tsx
│   │   │   │   │   ├── ConversationItem.tsx
│   │   │   │   │   └── NewChatButton.tsx
│   │   │   │   ├── MessageList/
│   │   │   │   │   ├── index.tsx
│   │   │   │   │   └── MessageItem.tsx
│   │   │   │   ├── InputArea/
│   │   │   │   │   ├── index.tsx
│   │   │   │   │   ├── MessageInput.tsx
│   │   │   │   │   └── Toolbar.tsx
│   │   │   │   └── SettingsPanel/
│   │   │   │       ├── index.tsx
│   │   │   │       ├── ModelSelector.tsx
│   │   │   │       └── OptionsToggle.tsx
│   │   │   ├── hooks/
│   │   │   │   ├── useStreamChat.ts
│   │   │   │   └── useConversationManager.ts
│   │   │   └── styles/
│   │   │       └── index.module.css
│   │   ├── KnowledgePage/   # 知识库页面
│   │   │   ├── index.tsx
│   │   │   ├── components/
│   │   │   │   ├── KnowledgeBaseTab/
│   │   │   │   ├── DocumentTab/
│   │   │   │   └── RolePresetTab/
│   │   │   └── styles/
│   │   └── TasksPage/       # 任务页面（保持现状）
│   │       └── ...
│   ├── hooks/               # 全局共享 Hooks
│   │   ├── useXRequest.ts   # XRequest 封装
│   │   ├── useTheme.ts      # 主题管理
│   │   └── useResponsive.ts # 响应式工具
│   ├── styles/              # 全局样式
│   │   ├── theme.css        # 主题变量
│   │   ├── global.css       # 全局样式
│   │   └── variables.css    # CSS 变量定义
│   ├── types/               # TypeScript 类型定义
│   │   ├── api.ts           # API 类型
│   │   ├── stream.ts        # 流式响应类型
│   │   └── models.ts        # 数据模型
│   ├── utils/               # 工具函数
│   │   ├── markdown.ts      # Markdown 处理
│   │   └── format.ts        # 格式化工具
│   ├── api/                 # API 客户端（已存在）
│   │   ├── client.ts
│   │   ├── services.ts
│   │   └── types.ts
│   ├── App.tsx
│   ├── main.tsx
│   ├── App.css
│   └── index.css
└── package.json

backend/                     # 保持不变（仅在需要时调整 API）
└── ...
```

**Structure Decision**: 

选择 **Web 应用结构（Option 2 变体）**，因为：
1. AgentMind 是前后端分离的 Web 应用
2. 前端重构不影响后端代码（除非需要调整流式 API 格式）
3. 采用页面级组件拆分（pages/）+ 共享组件（components/）的标准 React 架构
4. 使用 CSS Modules 实现样式隔离
5. Hooks 和 Utils 按作用域分层（全局 vs 页面私有）

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| 依赖管理（uv） | 前端项目使用 npm 作为包管理器 | uv 是 Python 专用工具，npm 是 JavaScript/TypeScript 生态的标准，无替代方案 |
| 可观测性（Loguru） | 浏览器环境使用 console API | Loguru 是 Python 库，浏览器环境使用原生 console 或前端日志库（如 loglevel） |

**说明**：前端项目与后端 Python 项目使用不同的工具链，这是技术栈本质决定的，不是架构缺陷。前端遵循等效原则（npm = uv，console/loglevel = Loguru）。

---

## Phase 0: Outline & Research

### 研究任务列表

基于技术背景中的"需要澄清"项和技术选型，需要进行以下研究：

#### R1: @ant-design/x-sdk 流式处理最佳实践 ✅
- **目标**：深入理解 XRequest API，确定如何处理不同类型的流式数据块
- **输出**：流式处理最佳实践文档

#### R2: 流式数据格式设计 ✅
- **目标**：定义前后端统一的流式响应格式
- **输出**：StreamChunk TypeScript 接口定义

#### R3: framer-motion 动画模式 ✅
- **目标**：确定页面和组件的动画策略
- **输出**：动画配置和变体定义

#### R4: 组件拆分策略 ✅
- **目标**：将 1298 行 ChatPage.tsx 拆分为可维护的模块
- **输出**：组件层级图和接口定义

#### R5: 响应式设计实现 ✅
- **目标**：确定移动端适配策略
- **输出**：响应式设计规范

#### R6: 性能优化技术 ✅
- **目标**：确定第一阶段的性能优化方案
- **输出**：性能优化清单

### 研究成果

✅ **所有研究任务已完成** - 详见 [research.md](./research.md)

**关键决策**：
- 使用 XRequest 处理流式响应（完整 TS 支持、内置取消、超时控制）
- 保持后端 SSE 格式，前端适配（成本低、格式合理）
- 渐进式引入 framer-motion 动画（Phase 2-4 分阶段）
- 中等粒度组件拆分（15-20 个组件，平衡维护性）
- 移动优先响应式设计（Ant Design Grid + 自定义 Hook）
- 基础性能优化优先（Memo、防抖、代码分割），虚拟滚动 Phase 4

---

## Phase 1: Design & Contracts

### 数据模型设计

**目标**：定义前端核心数据结构和状态管理模式

**输出文件**：`data-model.md`

**内容包括**：
1. 前端数据模型（Message、Conversation、RolePreset 等）
2. 状态管理策略（全局状态 vs 组件状态）
3. LocalStorage 持久化策略
4. 数据流图（用户操作 → 状态变更 → UI 更新）

### API 契约定义

**目标**：定义前端使用的 API TypeScript 接口

**输出文件**：`contracts/` ✅
- `stream-api.md` - 流式聊天 API（XRequest 集成）
- `chat-api.md` - 聊天管理 API（Axios 客户端）

**内容包括**：
- 请求/响应类型定义
- 流式数据块类型（SSEChunk）
- 错误类型定义和处理
- API 客户端封装（ChatAPI 类）
- React Hooks（useStreamChat、useConversations 等）
- 完整的使用示例

### 快速开始指南

**目标**：提供开发者快速上手指南

**输出文件**：`quickstart.md` ✅

**内容包括**：
- 依赖安装步骤
- Phase 1-4 核心任务概览
- 关键文档索引

---

## Phase 2: 任务分解（由 /speckit.tasks 命令生成）

**说明**：Phase 1 计划完成后，运行 `/speckit.tasks` 命令生成详细的任务分解文件 `tasks.md`

**任务文件将包含**：
- Setup 阶段任务（依赖安装、目录创建）
- Foundational 阶段任务（基础组件、Hooks）
- Feature 阶段任务（按用户故事组织）
- 优化阶段任务（性能、测试）

---

## 总结与下一步

### Phase 0 & 1 完成情况

✅ **Phase 0 - Research**：
- 所有研究任务完成（R1-R6）
- 技术决策已确定
- 详见 [research.md](./research.md)

✅ **Phase 1 - Design & Contracts**：
- 数据模型设计完成 [data-model.md](./data-model.md)
- API 契约定义完成 [contracts/](./contracts/)
- 快速开始指南完成 [quickstart.md](./quickstart.md)

### 交付物清单

| 文件 | 状态 | 说明 |
|------|------|------|
| plan.md | ✅ | 本文件 - 实施计划 |
| research.md | ✅ | 技术调研报告（6 个研究任务） |
| data-model.md | ✅ | 前端数据模型和状态管理 |
| contracts/stream-api.md | ✅ | 流式 API 契约（XRequest） |
| contracts/chat-api.md | ✅ | 聊天 API 契约（Axios） |
| quickstart.md | ✅ | 快速开始指南 |
| tasks.md | ⏳ | 待生成（运行 /speckit.tasks） |

### 关键决策总结

| 决策领域 | 选择 | 理由 |
|----------|------|------|
| 流式处理 | XRequest | TypeScript 支持、取消机制、超时控制 |
| 数据格式 | 保持后端 SSE 格式 | 前端适配成本低、格式合理 |
| 动画库 | framer-motion | React 集成好、性能优秀 |
| 组件粒度 | 中等（15-20 个） | 平衡维护性和复杂度 |
| 状态管理 | React Hooks | 项目规模适中，无需 Redux |
| 响应式 | Ant Design Grid | 统一技术栈 |
| 性能策略 | 基础优化优先 | 虚拟滚动延后 Phase 4 |

### 技术栈清单

**现有依赖**：
- React 18.2、TypeScript 5.2、Ant Design 5.11
- @ant-design/x-sdk 2.1.3 ✅
- highlight.js 11.9.0 ✅

**需要安装**：
```json
{
  "framer-motion": "^11.0.0",
  "react-markdown": "^9.0.0",
  "react-syntax-highlighter": "^15.5.0",
  "lodash-es": "^4.17.21"
}
```

### 风险与缓解

| 风险 | 等级 | 缓解措施 |
|------|------|----------|
| XRequest 稳定性 | 中 | 详细错误处理、超时配置、充分测试 |
| 动画性能影响 | 低 | GPU 属性优先、监控 FPS、渐进引入 |
| 组件拆分过度 | 低 | 遵循中等粒度原则、避免过度抽象 |

### 下一步行动

1. ✅ **Phase 0-1 完成** - 规划和设计阶段
2. **运行命令**：`/speckit.tasks` - 生成详细任务列表
3. **Phase 2-4 实施** - 按照任务列表执行开发
4. **持续迭代** - 每周交付一个可用版本

---

**规划完成时间**：2026-01-24  
**分支**：001-frontend-refactor  
**规划状态**：✅ 完成，准备进入任务分解阶段
