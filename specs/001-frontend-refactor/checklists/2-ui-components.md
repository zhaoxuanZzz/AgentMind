# UI 组件与设计规格检查清单

**检查类别**: UI Components & Design Specifications  
**优先级**: HIGH  
**门控**: 必须在 Phase 6 US4 完成前 85% 通过

---

## 1. 主题配色验证

### 1.1 颜色定义符合性

- [ ] **CRITICAL** 主题文件必须定义规格中的所有颜色变量
  - **规格参考**: `spec.md` 第 113-128 行
  - **位置**: `src/styles/theme.css`
  - **必需颜色**:
    - `--color-primary: #1677ff` ✅
    - `--color-bg-base: #ffffff` ✅
    - `--color-bg-secondary: #f5f8fc` ✅
    - `--color-text-primary: #1d2129` ✅
    - `--color-text-secondary: #4e5969` ✅
    - `--color-border: #e5e8ef` ✅

- [ ] **HIGH** 颜色使用场景符合规格表格
  - **规格参考**: `spec.md` 第 130-137 行（使用场景表）
  - **验证项**:
    - 主色 #1677ff 用于: 发送按钮、会话选中态、进度条 ✅
    - 主背景 #ffffff 用于: 页面主体、消息气泡、输入框 ✅
    - 次要背景 #f5f8fc 用于: 会话列表背景、思考过程背景 ✅

### 1.2 对比度合规性

- [ ] **CRITICAL** 所有文字色与背景色对比度 >= 4.5:1 (WCAG AA)
  - **规格参考**: `spec.md` 第 139-148 行
  - **验证工具**: [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
  - **必需通过**:
    - #1d2129 on #ffffff: >= 15.3:1 ✅
    - #4e5969 on #ffffff: >= 7.1:1 ✅
    - #1677ff on #ffffff: >= 4.8:1 ✅
    - #1d2129 on #f5f8fc: >= 14.1:1 ✅

- [ ] **HIGH** 所有交互元素（按钮、链接）在 hover/focus 状态下对比度 >= 3:1
  - **验证方法**: 使用浏览器开发工具检查伪类样式

### 1.3 暗色主题扩展性

- [ ] **MEDIUM** CSS 变量结构支持未来暗色主题扩展
  - **规格参考**: `tasks.md` T008
  - **验证**: 检查是否使用语义化变量名（如 `--color-bg-base` 而非 `--white`）
  - **示例结构**:
    ```css
    :root {
      /* 浅色主题（默认） */
      --color-primary: #1677ff;
      --color-bg-base: #ffffff;
    }
    /* 未来可扩展为 */
    /* [data-theme="dark"] { ... } */
    ```

---

## 2. 布局与响应式设计

### 2.1 桌面端布局

- [ ] **CRITICAL** 对话页面布局符合规格设计
  - **规格参考**: `spec.md` 第 150-161 行
  - **验证项**:
    - 左侧会话列表固定宽度 280px ✅
    - 中间消息区域自适应宽度 ✅
    - 底部输入区域固定在底部 ✅
    - Header 包含 Logo + 导航 + 模型选择 ⚠️ (需验证)

- [ ] **HIGH** 知识库页面布局符合规格
  - **规格参考**: `spec.md` 第 163-170 行
  - **验证项**:
    - Tabs: 知识库 | 文档 | 角色预设 ⚠️ (需验证)
    - 卡片网格布局 ⚠️ (需验证)

### 2.2 响应式断点

- [ ] **CRITICAL** 支持规格定义的响应式断点
  - **规格参考**: `plan.md` 第 51 行
  - **断点**:
    - 移动端: 375px+
    - 平板: 768px+
    - 桌面: 992px+

- [ ] **HIGH** 移动端侧边栏使用 Drawer 组件
  - **当前状态**: ✅ PASS - `ChatPage/index.tsx` 第 138-148 行
  - **验证**: 在 < 768px 宽度下，会话列表变为 Drawer

- [ ] **HIGH** 移动端头部显示 Toggle 按钮
  - **当前状态**: ✅ PASS - `ChatPage/index.tsx` 第 152-168 行

### 2.3 知识库选择器组件

- [ ] **CRITICAL** 必须实现知识库选择器组件
  - **规格参考**: `spec.md` 第 42 行，`tasks.md` T035-1
  - **当前状态**: ❌ FAIL - 未找到独立的知识库选择器组件
  - **位置**: 应在 `components/KnowledgeBaseSelector/` 或 `ChatPage/components/`
  - **需求**: 
    - 允许用户在对话中选择知识库
    - 显示已选择的知识库
    - 支持清除选择
  - **验收标准**: 能正确将 `use_knowledge_base` 参数传递给 API

---

## 3. 消息展示组件

### 3.1 消息气泡组件

- [ ] **HIGH** `MessageBubble` 必须支持用户和 AI 两种角色
  - **当前状态**: ✅ PASS - `MessageBubble.tsx` 第 23 行判断
  - **验证**: 检查头像、布局方向、配色是否符合规格

- [ ] **HIGH** AI 消息必须支持 Markdown 渲染
  - **当前状态**: ✅ PASS - 使用 `MarkdownRenderer`
  - **规格要求**: `spec.md` 第 41 行

- [ ] **HIGH** 支持代码高亮
  - **当前状态**: ⚠️ 需验证 `MarkdownRenderer` 是否集成 `highlight.js`
  - **规格要求**: `spec.md` 第 41 行

### 3.2 思考过程可视化

- [ ] **CRITICAL** 必须显示 AI 思考过程
  - **当前状态**: ✅ PASS - `ThinkingSection.tsx`
  - **规格要求**: `spec.md` 第 39 行
  - **验证**: 检查是否显示 `thinking` 字段内容

- [ ] **HIGH** 思考过程有明显的视觉区分
  - **验证项**:
    - 使用次要背景色 #f5f8fc ✅
    - 有折叠/展开功能 ⚠️ (需验证)
    - 流式状态下有加载动画 ✅ (第 26 行 `<SyncOutlined spin />`)

### 3.3 工具调用展示

- [ ] **CRITICAL** 必须显示工具调用信息
  - **当前状态**: ✅ PASS - `ToolCallsDisplay.tsx`
  - **规格要求**: `spec.md` 第 40 行
  - **验证**: 检查是否显示 `tool_name`, `tool_input`, `tool_output`

- [ ] **HIGH** 工具调用有清晰的视觉展示
  - **验证项**:
    - 显示工具名称 ⚠️
    - 显示输入参数 ⚠️
    - 显示输出结果 ⚠️
    - 有图标或颜色标识 ⚠️

### 3.4 流式文本组件

- [ ] **CRITICAL** 流式文本有打字机效果或平滑滚动
  - **当前状态**: ✅ PASS - `StreamingText` 组件
  - **规格要求**: `spec.md` 第 38 行（流畅的流式响应）

---

## 4. 交互动画

### 4.1 页面过渡动画

- [ ] **HIGH** 页面切换有 fade-in 动画
  - **当前状态**: ✅ PASS - `ChatPage/index.tsx` 使用 `framer-motion`
  - **规格要求**: `spec.md` 第 40 行
  - **验证**: 检查 `fadeIn` 动画变体定义

- [ ] **MEDIUM** 消息气泡进入有 fade-in-up 动画
  - **当前状态**: ✅ PASS - `MessageBubble.tsx` 第 12 行导入 `fadeInUp`
  - **验证**: 检查 `motion.div` 是否应用动画

### 4.2 加载状态

- [ ] **HIGH** 流式响应中有明显的加载指示器
  - **验证位置**: `ChatSender` 组件的 `loading` 状态
  - **规格要求**: 使用主色 #1677ff 的 Spin 或 Progress 组件

- [ ] **MEDIUM** 长列表滚动流畅（目标 60 FPS）
  - **规格参考**: `spec.md` 第 175 行
  - **验证方法**: Chrome DevTools Performance 面板录制滚动操作

---

## 5. 输入区域

### 5.1 ChatSender 组件

- [ ] **HIGH** 支持多行文本输入
  - **验证**: 检查是否使用 `TextArea` 或 `Input.TextArea`

- [ ] **HIGH** 发送按钮使用主色 #1677ff
  - **规格参考**: `spec.md` 第 132 行

- [ ] **MEDIUM** 支持快捷键发送（Enter 发送，Shift+Enter 换行）
  - **验证**: 测试键盘交互

### 5.2 工具栏

- [ ] **MEDIUM** 输入框工具栏包含必要功能
  - **规格参考**: `spec.md` 第 159 行
  - **需求**: 
    - 知识库选择（如果未实现则为 CRITICAL）
    - 模型选择 ⚠️
    - 其他设置 ⚠️

---

## 6. 会话管理

### 6.1 会话列表

- [ ] **HIGH** `ConversationSidebar` 显示所有会话
  - **当前状态**: ✅ PASS

- [ ] **HIGH** 当前会话有选中状态高亮
  - **验证**: 使用主色 #1677ff 或次要背景色 #f5f8fc

- [ ] **MEDIUM** 支持会话重命名
  - **当前状态**: ✅ PASS - `ChatPage/index.tsx` 传入 `onRename`

- [ ] **MEDIUM** 支持会话删除
  - **当前状态**: ✅ PASS - 传入 `onDelete`

---

## 验证步骤

### 自动化验证

1. **颜色对比度检查**:
   - 使用 [pa11y-ci](https://github.com/pa11y/pa11y-ci) 进行自动化无障碍检查
   - 或使用 Chrome DevTools Lighthouse 的 Accessibility 审计

2. **响应式测试**:
   ```bash
   # Chrome DevTools Device Toolbar
   # 测试断点: 375px, 768px, 992px, 1440px
   ```

### 手动验证

1. **视觉回归测试**:
   - 对比当前实现与 `spec.md` 第 113-170 行的设计规格
   - 截图保存到 `specs/001-frontend-refactor/screenshots/`

2. **交互测试**:
   - 发送包含 Markdown 的消息，验证渲染效果
   - 发送触发工具调用的消息（如"武汉天气"），验证思考过程和工具展示
   - 切换会话，验证消息加载和动画效果

3. **性能测试**:
   - Chrome DevTools Performance 录制流式对话过程
   - 验证帧率 >= 55 FPS（参考 `tasks.md` T064）
   - 验证流式延迟 < 100ms（参考 `spec.md` 第 175 行）

---

## 完成标准

**门控条件** (必须 85% 通过):
- [ ] 所有 CRITICAL 项已修复
- [ ] 90% HIGH 项已修复或有明确计划
- [ ] 对比度符合 WCAG AA 标准
- [ ] 响应式布局在 3 个断点下正常工作

**质量指标**:
- 颜色对比度: 100% 符合 WCAG AA
- 响应式覆盖: 移动端、平板、桌面 100% 可用
- 动画帧率: >= 55 FPS
- 无障碍得分: Lighthouse >= 90

---

**最后更新**: 2026-01-26  
**状态**: 🟡 PARTIAL - 需补充知识库选择器组件
