# Tasks: 前端重构 - 基于 @ant-design/x

**分支**: `001-frontend-refactor` | **日期**: 2026-01-25
**输入**: `/specs/001-frontend-refactor/` 中的设计文档
**前置条件**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

---

## 任务格式说明

每个任务遵循格式：`- [ ] [TaskID] [P?] [Story?] Description with file path`

- **[P]** = 可并行（不同文件，无依赖）
- **[Story]** = 所属用户故事（US1, US2, US3...）
- 文件路径采用 Web 应用结构：`frontend/src/...`

---

## 总览

| 阶段 | 任务数 | 说明 |
|------|--------|------|
| Phase 1: Setup | 8 | 项目配置、依赖安装 |
| Phase 2: Foundational | 12 | 基础组件、Hooks、类型定义 |
| Phase 3: US1 - 流式对话核心 | 15 | XRequest 集成、消息展示 |
| Phase 4: US2 - 思考过程可视化 | 8 | 展示 AI 推理和工具调用 |
| Phase 5: US3 - 响应式布局 | 10 | 移动端、平板适配 |
| Phase 6: US4 - 页面动画 | 7 | 流畅过渡效果 |
| Phase 7: Polish | 10 | 性能优化、错误处理 |
| **总计** | **70** | |

---

## Phase 1: Setup（项目基础设施）

**目的**: 配置开发环境和安装依赖

### 依赖管理

- [X] T001 安装核心依赖 framer-motion react-markdown react-syntax-highlighter lodash-es
- [X] T002 [P] 安装类型定义 @types/lodash-es @types/react-syntax-highlighter
- [X] T003 验证 antd@6.x 和 @ant-design/x@2.x 已正确安装

### 目录结构

- [X] T004 [P] 创建全局组件目录 frontend/src/components/
- [X] T005 [P] 创建全局 Hooks 目录 frontend/src/hooks/
- [X] T006 [P] 创建类型定义目录 frontend/src/types/
- [X] T007 [P] 创建工具函数目录 frontend/src/utils/

### 主题配置

- [X] T008 创建主题变量文件 frontend/src/styles/theme.css 并定义 CSS 变量（清新淡雅配色）
  - **仅定义浅色主题变量**，但结构支持未来扩展（如预留 `--color-bg-base`、`--color-text-base` 等语义化变量名）
  - 使用 CSS 变量而非硬编码值，便于主题切换
  - 示例结构：
    ```css
    :root {
      /* 浅色主题（默认） */
      --color-primary: #1677ff;
      --color-bg-base: #ffffff;
      --color-bg-secondary: #f5f8fc;
      /* 未来可扩展为 [data-theme="dark"] { ... } */
    }
    ```
- [X] T008-1 验证主题配色符合清新淡雅标准 frontend/src/styles/theme.css
  - 检查项：主色 #1677ff、背景 #ffffff、次背景 #f5f8fc
  - 使用 [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/) 验证对比度
  - 验收标准：
    - #1d2129 on #ffffff >= 4.5:1 ✅
    - #4e5969 on #ffffff >= 4.5:1 ✅
    - #1677ff on #ffffff >= 4.5:1 ✅
  - 在浏览器中手动测试所有组件的可见性（按钮、文本、边框）

---

## Phase 2: Foundational（基础层）

**目的**: 构建可复用的基础设施，供所有用户故事使用

**隐式用户故事覆盖**: 此阶段通过模块化设计和清晰的组件结构隐式满足用户故事 "作为开发者，我希望组件结构清晰，便于后续功能扩展"
- ✅ T009-T020 建立的类型定义、Hooks 和工具函数为后续组件提供清晰接口
- ✅ Phase 3-6 的组件拆分（T021-T070）遵循单一职责原则，每个组件可独立测试

### 类型定义

- [X] T009 [P] 定义 API 类型 frontend/src/types/api.ts（Message, Conversation, LLMProvider）
- [X] T010 [P] 定义流式类型 frontend/src/types/stream.ts（SSEChunk, StreamChunkType, ToolInfo）
- [X] T011 [P] 定义数据模型类型 frontend/src/types/models.ts（RolePreset, KnowledgeBase）

### 全局样式

- [X] T012 创建全局样式文件 frontend/src/styles/global.css
- [X] T013 更新 App.tsx 配置 ConfigProvider 主题

### API 客户端

- [X] T014 [P] 实现 ChatAPI 客户端类 frontend/src/api/chatAPI.ts
- [X] T015 [P] 实现流式 API 辅助函数 frontend/src/api/streamAPI.ts（基于 contracts/stream-api.md）

### 基础 Hooks

- [X] T016 [P] 实现 useLocalStorage Hook frontend/src/hooks/useLocalStorage.ts
- [X] T017 [P] 实现 useResponsive Hook frontend/src/hooks/useResponsive.ts（断点检测）
- [X] T018 [P] 实现 useTheme Hook frontend/src/hooks/useTheme.ts

### 工具函数

- [X] T019 [P] 实现 Markdown 处理工具 frontend/src/utils/markdown.ts
- [X] T020 [P] 实现格式化工具 frontend/src/utils/format.ts（时间戳、文本清理）

---

## Phase 3: US1 - 流式对话核心功能

**用户故事**: 作为用户，我希望消息流式响应更流畅，能清楚看到 AI 的思考过程

**验收标准**:
- ✅ 流式消息实时显示（桌面端）
- ✅ 支持取消正在进行的请求
- ✅ 错误处理清晰（超时、网络错误）
- ✅ 流式内容支持 Markdown 渲染
- ⚠️ 移动端适配将在 Phase 5 US3 完成

### Hooks 层

- [X] T021 [US1] 实现 useStreamChat Hook frontend/src/hooks/useStreamChat.ts（XRequest 集成）
- [X] T022 [US1] 实现 useConversations Hook frontend/src/hooks/useConversations.ts
- [X] T023 [US1] 实现 useConversationMessages Hook frontend/src/hooks/useConversationMessages.ts

### 全局组件

- [X] T024 [P] [US1] 创建 Markdown 渲染组件 frontend/src/components/MarkdownRenderer/index.tsx
- [X] T025 [P] [US1] 创建流式文本组件 frontend/src/components/StreamingText/index.tsx（打字机光标）

### ChatPage 基础结构

- [X] T026 [US1] 创建 ChatPage 容器 frontend/src/pages/ChatPage/index.tsx
- [X] T027 [US1] 创建 ChatPage 样式 frontend/src/pages/ChatPage/styles/index.module.css

### 消息展示组件（使用 @ant-design/x）

- [X] T028 [P] [US1] 创建 MessageBubble 组件 frontend/src/pages/ChatPage/components/MessageBubble.tsx（基于 Bubble）
- [X] T029 [US1] 创建 MessageList 组件 frontend/src/pages/ChatPage/components/MessageList.tsx（基于 Conversations）
- [X] T030 [US1] 实现 MessageList 自动滚动到底部逻辑

### 输入区域（使用 @ant-design/x）

- [X] T031 [P] [US1] 创建 ChatSender 组件 frontend/src/pages/ChatPage/components/ChatSender.tsx（基于 Sender）
- [X] T032 [US1] 实现输入验证和提交逻辑

### 会话管理

- [X] T033 [P] [US1] 创建 ConversationSidebar 组件 frontend/src/pages/ChatPage/components/ConversationSidebar/index.tsx
- [X] T034 [P] [US1] 创建 ConversationItem 组件 frontend/src/pages/ChatPage/components/ConversationSidebar/ConversationItem.tsx
- [X] T035 [US1] 实现新建、删除、切换会话功能
- [X] T035-1 [P] [US1] 在 ChatSender 中添加知识库选择器组件 frontend/src/pages/ChatPage/components/KnowledgeSelector.tsx
  - 从知识库 API 获取可用知识库列表
  - 提供下拉选择器UI(Ant Design Select)
  - 在发送消息时附加选中的知识库ID
  - 验收标准: 选中知识库后,对话请求包含 knowledge_base_id 参数

---

## Phase 4: US2 - 思考过程和工具调用可视化

**用户故事**: 作为用户，我希望看到 AI 的思考过程和工具调用，了解 AI 如何得出答案

**验收标准**:
- ✅ 显示 AI 的推理步骤
- ✅ 展示工具调用的输入输出
- ✅ 支持折叠/展开思考过程
- ✅ 时间线样式展示

### 思考过程组件

- [X] T036 [P] [US2] 创建 ThinkingSection 组件 frontend/src/pages/ChatPage/components/ThinkingSection.tsx
- [X] T037 [P] [US2] 添加折叠/展开交互

### 工具调用组件（使用 @ant-design/x ThoughtChain）

- [X] T038 [P] [US2] 创建 ToolCallsDisplay 组件 frontend/src/pages/ChatPage/components/ToolCallsDisplay.tsx（基于 ThoughtChain）
- [X] T039 [P] [US2] 创建 ToolCallStep 组件显示单个工具调用

### 集成到消息组件

- [X] T040 [US2] 在 MessageBubble 中集成思考过程展示（footer）
- [X] T041 [US2] 在 MessageBubble 中集成工具调用展示

### 流式数据处理

- [X] T042 [US2] 扩展 useStreamChat Hook 处理 thinking 和 tool 类型的流式数据
- [X] T043 [US2] 实现流式思考过程和工具调用的累积逻辑

---

## Phase 5: US3 - 响应式布局

**用户故事**: 作为用户，我希望在移动设备上也能流畅使用对话功能

**验收标准**:
- ✅ 移动端（<576px）正常显示和交互
- ✅ 平板（577-992px）布局适配
- ✅ 桌面（>992px）完整功能
- ✅ 侧边栏在移动端改为 Drawer

### 响应式 Hook 增强

- [X] T044 [P] [US3] 扩展 useResponsive Hook 支持断点检测

### 移动端适配

- [X] T045 [US3] 实现移动端会话侧边栏 Drawer frontend/src/pages/ChatPage/index.tsx
- [X] T046 [US3] 添加移动端头部操作栏（打开侧边栏、设置）

### 响应式样式

- [X] T047 [P] [US3] 添加响应式 CSS 媒体查询 frontend/src/pages/ChatPage/styles/responsive.module.css
- [X] T048 [P] [US3] 调整消息气泡在移动端的样式（缩小内边距、字体）
- [X] T049 [P] [US3] 调整输入框在移动端的布局

### 触摸优化

- [X] T050 [US3] 增大移动端按钮触控区域（最小 44x44px）
- [X] T051 [US3] 优化移动端滚动性能（-webkit-overflow-scrolling）

### 测试

- [X] T052 [US3] 在移动端浏览器测试对话功能
- [X] T053 [US3] 在平板尺寸测试布局适配

---

## Phase 6: US4 - 流畅的页面过渡动画

**用户故事**: 作为用户，我希望界面过渡流畅自然，提升使用体验

**验收标准**:
- ✅ 页面切换有淡入淡出效果
- ✅ 消息入场有 stagger 动画
- ✅ 动画保持 60 FPS
- ✅ 尊重用户的减少动画偏好

### 动画配置

- [X] T054 [P] [US4] 创建动画变体配置 frontend/src/utils/animations.ts

### 页面过渡动画

- [X] T055 [US4] 在 App.tsx 中添加 AnimatePresence 和路由过渡动画
- [X] T056 [US4] 实现页面淡入淡出效果（framer-motion）

### 消息动画

- [X] T057 [P] [US4] 为 MessageList 添加 stagger 入场动画
- [X] T058 [P] [US4] 为 MessageBubble 添加淡入动画

### 性能优化

- [X] T059 [US4] 使用 GPU 加速属性（transform, opacity）
- [X] T060 [US4] 添加 useReducedMotion Hook 支持用户偏好

---

## Phase 7: Polish & 优化

**目的**: 性能优化、错误处理、细节完善

### 性能优化

- [X] T061 [P] 为关键组件添加 React.memo（MessageBubble, ConversationItem）
- [X] T062 [P] 实现防抖工具函数并应用到输入框和滚动监听
- [X] T063 [P] 添加代码分割（React.lazy）到 ChatPage、KnowledgePage、TasksPage
- [X] T064 测试长消息列表性能（100+ 消息），确认无卡顿
  - 验收标准：
    - 渲染 100 条消息耗时 < 2s
    - 滚动帧率 >= 55 FPS（使用 Chrome DevTools FPS Meter）
    - 内存占用 < 150MB（使用 Performance Monitor）
  - 测试工具：Chrome DevTools Performance 面板

### 错误处理

- [X] T065 [P] 创建错误边界组件 frontend/src/components/ErrorBoundary.tsx
- [X] T066 [P] 实现全局错误处理 Hook frontend/src/hooks/useErrorHandler.ts
- [X] T067 完善流式请求错误处理（超时、网络中断、取消）

### 细节完善

- [X] T068 [P] 添加加载状态指示器（Skeleton、Spin）
- [X] T069 [P] 添加空状态提示（无消息时显示 Prompts 组件）
- [X] T070 测试所有核心功能，确保无 Bug

### 可访问性验证

- [ ] T070-1 [P] 验证键盘导航支持
  - Tab 键正确遍历所有可交互元素（按钮、输入框、链接）
  - Enter/Space 键激活按钮和链接
  - Esc 键关闭模态框和 Drawer
  - 焦点顺序符合逻辑（从上到下、从左到右）
  
- [ ] T070-2 [P] 验证 ARIA 标签和屏幕阅读器兼容性
  - 使用 Chrome DevTools Accessibility 面板检查 ARIA 属性
  - 使用 axe DevTools 扫描可访问性问题
  - 测试屏幕阅读器 (NVDA/JAWS on Windows, VoiceOver on Mac)
  - 验收标准：
    - 所有交互元素有正确的 aria-label 或 aria-labelledby
    - 表单输入有关联的 label 元素
    - 动态内容变化使用 aria-live 通知
    - 无 axe 报告的 Critical/Serious 级别错误

---

## 依赖关系图

```
Phase 1 (Setup)
    ↓
Phase 2 (Foundational) ← 必须先完成
    ↓
    ├─→ Phase 3 (US1) ← 核心功能，优先级最高
    │       ↓
    │   Phase 4 (US2) ← 依赖 US1 的消息组件
    │
    ├─→ Phase 5 (US3) ← 可与 US2 并行
    │
    └─→ Phase 6 (US4) ← 可与 US2、US3 并行
            ↓
        Phase 7 (Polish) ← 最后阶段
```

### 并行执行建议

**Week 1**:
- Phase 1 (Setup) - 全员
- Phase 2 (Foundational) - 全员

**Week 2**:
- Phase 3 (US1) - 核心团队（2-3 人）

**Week 3**:
- Phase 4 (US2) - 1 人
- Phase 5 (US3) - 1 人（可并行）

**Week 4**:
- Phase 6 (US4) - 1 人
- Phase 7 (Polish) - 全员

---

## MVP 范围

**最小可交付产品** (仅 US1 核心功能):

✅ **包含**:
- Phase 1: Setup (T001-T008)
- Phase 2: Foundational (T009-T020)
- Phase 3: US1 核心对话 (T021-T035)

✅ **功能**:
- 流式对话显示
- 消息历史记录
- 会话管理
- Markdown 渲染

⏳ **延后到后续迭代**:
- US2: 思考过程可视化
- US3: 响应式布局
- US4: 页面动画
- Phase 7: 性能优化

---

## 实施策略

### 增量交付

1. **Sprint 1**: MVP (US1) - 基本可用
2. **Sprint 2**: US2 + US3 - 功能增强
3. **Sprint 3**: US4 + Polish - 体验优化

### 质量保证

- 每完成一个 Phase，在本地测试功能
- 确保 TypeScript 无错误（strict mode）
- 遵循 ESLint 规则
- 关键组件添加基础测试（可选）

### 代码审查检查点

- Phase 2 完成后 - 审查基础架构
- Phase 3 完成后 - 审查核心功能（MVP 交付点）
- Phase 7 完成后 - 最终审查

---

## 宪章合规性检查

每个 Phase 完成后验证：

- ✅ **模块化设计**: 组件单一职责，可独立测试
- ✅ **类型安全**: TypeScript 严格模式，无 any 类型
- ⚠️ **API 优先**: 前端消费现有 API，TypeScript 接口作为契约
- ✅ **可观测性**: 关键交互点有 console 日志（XRequest callbacks）

---

**任务总数**: 70  
**预计工期**: 4 周（按 4 个 Sprint 执行）  
**MVP 交付**: Week 2 结束  
**完整交付**: Week 4 结束  

**下一步**: 开始执行 Phase 1 Setup 任务（T001-T008）
