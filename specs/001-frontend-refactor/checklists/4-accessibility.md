# 无障碍性检查清单

**检查类别**: Accessibility (a11y) & WCAG Compliance  
**优先级**: HIGH  
**门控**: 必须在 Phase 7 Polish 完成前 90% 通过

---

## 1. 键盘导航 (Keyboard Navigation)

### 1.1 焦点管理

- [ ] **CRITICAL** 所有交互元素可通过 Tab 键访问
  - **规格要求**: `spec.md` 第 181 行，`tasks.md` T070-1
  - **测试元素**:
    - 发送按钮 ⚠️
    - 会话列表项 ⚠️
    - 新建会话按钮 ⚠️
    - 删除会话按钮 ⚠️
    - 知识库选择器 ⚠️
    - 模型选择器 ⚠️
    - 输入框 ⚠️

- [ ] **CRITICAL** Tab 顺序符合逻辑（从上到下，从左到右）
  - **验证方法**: 按 Tab 键遍历页面，观察焦点顺序
  - **预期顺序**: 
    1. 会话列表
    2. 消息区域
    3. 输入框
    4. 发送按钮

- [ ] **HIGH** 焦点状态有明显的视觉指示
  - **规格要求**: 对比度 >= 3:1（WCAG 2.1 非文本对比度标准）
  - **验证**: 使用 WebAIM Contrast Checker 检查焦点边框颜色
  - **建议**: 使用 `outline: 2px solid #1677ff` 或 `box-shadow: 0 0 0 3px rgba(22,119,255,0.3)`

### 1.2 键盘快捷键

- [ ] **HIGH** Enter 键发送消息
  - **当前状态**: ⚠️ 需验证 `ChatSender` 组件

- [ ] **HIGH** Shift+Enter 键换行
  - **当前状态**: ⚠️ 需验证 `ChatSender` 组件

- [ ] **MEDIUM** Esc 键关闭 Drawer（移动端侧边栏）
  - **当前状态**: ✅ PASS - Ant Design Drawer 默认支持
  - **验证**: 在移动端打开侧边栏，按 Esc 关闭

- [ ] **MEDIUM** 上/下箭头键切换会话
  - **当前状态**: ❌ FAIL - 未实现
  - **优先级**: MEDIUM（可延后到 v2.1）

---

## 2. 屏幕阅读器支持 (Screen Reader)

### 2.1 语义化 HTML

- [ ] **CRITICAL** 使用正确的 HTML 语义标签
  - **验证项**:
    - `<header>` 用于页面头部 ⚠️
    - `<nav>` 用于导航区域 ⚠️
    - `<main>` 用于主内容区域 ⚠️
    - `<article>` 或 `<section>` 用于消息列表 ⚠️
    - `<button>` 用于所有按钮（而非 `<div onClick>`) ⚠️

- [ ] **HIGH** 列表使用 `<ul>` 和 `<li>` 标签
  - **验证**: 会话列表、消息列表

### 2.2 ARIA 标签

- [ ] **CRITICAL** 所有交互元素有 `aria-label` 或可见文本
  - **规格要求**: `tasks.md` T070-2
  - **验证项**:
    | 元素 | ARIA 标签 | 状态 |
    |------|-----------|------|
    | 发送按钮 | `aria-label="发送消息"` | ⚠️ |
    | 新建会话按钮 | `aria-label="新建对话"` | ⚠️ |
    | 删除会话按钮 | `aria-label="删除对话"` | ⚠️ |
    | 会话列表 | `aria-label="对话列表"` | ⚠️ |
    | 消息列表 | `aria-label="消息列表"` | ⚠️ |
    | 知识库选择器 | `aria-label="选择知识库"` | ⚠️ |

- [ ] **HIGH** 动态内容更新使用 `aria-live` 区域
  - **规格要求**: 流式消息更新时通知屏幕阅读器
  - **实现建议**:
    ```tsx
    <div 
      role="log" 
      aria-live="polite" 
      aria-atomic="false"
      aria-relevant="additions"
    >
      {/* 流式消息内容 */}
    </div>
    ```

- [ ] **HIGH** 当前会话在会话列表中有 `aria-current="page"`
  - **验证**: 检查 `ConversationSidebar` 组件

- [ ] **MEDIUM** 折叠/展开组件使用 `aria-expanded`
  - **验证**: 检查思考过程折叠组件（如果有）

### 2.3 图像和图标

- [ ] **HIGH** 所有图标有 `aria-label` 或 `aria-hidden="true"`
  - **验证**: 检查 `<UserOutlined>`, `<CopyOutlined>`, `<SyncOutlined>` 等 Ant Design 图标

- [ ] **HIGH** 装饰性图标使用 `aria-hidden="true"`
  - **规则**: 如果图标旁边有文本说明，图标应隐藏

- [ ] **MEDIUM** 头像有 `alt` 属性
  - **验证**: `<Avatar>` 组件

---

## 3. 颜色对比度 (Color Contrast)

### 3.1 文本对比度

- [ ] **CRITICAL** 所有文本对比度 >= 4.5:1 (WCAG AA)
  - **当前状态**: ✅ PASS - 见 `spec.md` 第 139-148 行验证结果
  - **验证工具**: [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
  - **已验证**:
    - #1d2129 on #ffffff: 15.3:1 ✅
    - #4e5969 on #ffffff: 7.1:1 ✅
    - #1677ff on #ffffff: 4.8:1 ✅
    - #1d2129 on #f5f8fc: 14.1:1 ✅

- [ ] **HIGH** 大文本对比度 >= 3:1 (WCAG AA)
  - **定义**: 大文本 = 18px 及以上 或 14px 粗体
  - **验证**: 检查标题、按钮文本

### 3.2 非文本对比度

- [ ] **HIGH** UI 组件和边框对比度 >= 3:1 (WCAG 2.1)
  - **验证项**:
    | 元素 | 背景色 | 前景色 | 对比度 | 状态 |
    |------|--------|--------|--------|------|
    | 输入框边框 | #ffffff | #e5e8ef | ⚠️ 需计算 | - |
    | 按钮边框 | #ffffff | #1677ff | 4.8:1 | ✅ |
    | 会话分隔线 | #f5f8fc | #e5e8ef | ⚠️ 需计算 | - |
    | 焦点指示器 | #ffffff | #1677ff | 4.8:1 | ✅ |

- [ ] **MEDIUM** 图表和图标对比度 >= 3:1
  - **验证**: 工具调用图标、状态图标

---

## 4. 表单和输入

### 4.1 表单标签

- [ ] **CRITICAL** 所有输入框有关联的 `<label>` 或 `aria-label`
  - **验证**: 
    - 消息输入框 ⚠️
    - 知识库选择器 ⚠️
    - 模型选择器 ⚠️

- [ ] **HIGH** 必填字段有 `aria-required="true"` 或 `required` 属性
  - **验证**: 消息输入框（发送空消息应被阻止）

### 4.2 错误提示

- [ ] **CRITICAL** 错误消息有 `aria-describedby` 关联
  - **示例**:
    ```tsx
    <Input
      aria-invalid="true"
      aria-describedby="error-message"
    />
    <span id="error-message" role="alert">
      请输入消息内容
    </span>
    ```

- [ ] **HIGH** 错误状态使用颜色 + 图标/文本（不仅依赖颜色）
  - **规则**: 不能仅通过红色表示错误，需配合文本或图标

---

## 5. 响应式与缩放

### 5.1 文本缩放

- [ ] **CRITICAL** 支持浏览器文本缩放至 200%
  - **测试方法**: 
    1. Chrome 设置 → 外观 → 字体大小 → 非常大
    2. 或使用 Ctrl/Cmd + Plus 放大
  - **验证**: 布局不破坏，内容可访问

- [ ] **HIGH** 使用相对单位（rem, em）而非固定像素
  - **验证**: 检查 CSS 文件是否大量使用 `px`
  - **建议**: 转换为 `rem` 或 `em`

### 5.2 移动端可访问性

- [ ] **HIGH** 触摸目标尺寸 >= 44x44 像素 (WCAG 2.1)
  - **验证**: 移动端按钮、链接、会话列表项

- [ ] **MEDIUM** 横竖屏旋转后布局正常
  - **测试**: Chrome DevTools Device Mode 切换方向

---

## 6. 自动化测试

### 6.1 axe DevTools 扫描

- [ ] **CRITICAL** 无 Critical 级别违规
  - **工具**: [axe DevTools](https://chrome.google.com/webstore/detail/axe-devtools-web-accessib/lhdoppojpmngadmnindnejefpokejbdd)
  - **规格要求**: `tasks.md` T070-2
  - **测试步骤**:
    1. 安装 axe DevTools Chrome 扩展
    2. 打开 AgentMind 应用
    3. 运行 axe 扫描
    4. 修复所有 Critical 和 Serious 问题

- [ ] **HIGH** 无 Serious 级别违规
  - **目标**: Serious 问题数量 = 0

- [ ] **MEDIUM** Moderate/Minor 问题 < 5 个
  - **优先级**: MEDIUM（可延后到 v2.1）

### 6.2 Lighthouse 无障碍审计

- [ ] **CRITICAL** Lighthouse Accessibility 得分 >= 90
  - **规格要求**: `checklists/2-ui-components.md` 完成标准
  - **测试步骤**:
    1. Chrome DevTools → Lighthouse
    2. 勾选 Accessibility
    3. 运行审计
  - **目标**: >= 90 分

- [ ] **HIGH** 修复所有自动检测的可访问性问题
  - **常见问题**:
    - 按钮无可访问名称
    - 图像无 alt 属性
    - 对比度不足
    - 表单元素无标签

---

## 7. 屏幕阅读器测试

### 7.1 NVDA/JAWS (Windows)

- [ ] **HIGH** 使用 NVDA 完整测试对话流程
  - **规格要求**: `tasks.md` T070-2
  - **测试步骤**:
    1. 安装 [NVDA](https://www.nvaccess.org/)
    2. 启动 NVDA
    3. 仅使用键盘导航
    4. 验证所有内容都能被朗读

- [ ] **MEDIUM** 使用 JAWS 测试关键功能
  - **优先级**: MEDIUM（NVDA 测试通过即可）

### 7.2 VoiceOver (Mac)

- [ ] **HIGH** 使用 VoiceOver 测试对话流程
  - **规格要求**: `tasks.md` T070-2
  - **测试步骤**:
    1. Cmd+F5 启动 VoiceOver
    2. 仅使用键盘导航（VoiceOver 快捷键）
    3. 验证所有内容都能被朗读

### 7.3 TalkBack (Android)

- [ ] **MEDIUM** 移动端使用 TalkBack 测试
  - **优先级**: MEDIUM（桌面端通过即可）
  - **测试**: 发送消息、切换会话

---

## 验证步骤

### 自动化验证

1. **axe DevTools 扫描**:
   ```bash
   # 在页面上运行 axe
   # 或使用 @axe-core/cli 进行 CI 集成
   npm install -g @axe-core/cli
   axe http://localhost:3000
   ```

2. **Lighthouse CI**:
   ```bash
   # 在 CI 中运行 Lighthouse
   npm install -g @lhci/cli
   lhci autorun --collect.url=http://localhost:3000
   ```

### 手动验证

1. **键盘导航测试** (T070-1):
   - 拔掉鼠标，仅使用键盘完成完整对话流程
   - 记录无法访问的元素

2. **屏幕阅读器测试** (T070-2):
   - 闭眼使用 NVDA/VoiceOver 测试
   - 记录朗读不清晰或遗漏的内容

3. **对比度测试**:
   - 使用 [Contrast Ratio Tool](https://contrast-ratio.com/)
   - 测试所有文本和UI元素

---

## 完成标准

**门控条件** (必须 90% 通过):
- [ ] 所有 CRITICAL 项已修复
- [ ] axe DevTools 无 Critical/Serious 违规
- [ ] Lighthouse Accessibility >= 90
- [ ] 键盘导航 100% 可用

**质量指标**:
- axe DevTools 得分: 100%（无违规）
- Lighthouse Accessibility: >= 90
- 键盘可访问性: 100%
- 屏幕阅读器兼容性: NVDA + VoiceOver 通过

---

**最后更新**: 2026-01-26  
**状态**: 🟡 UNKNOWN - 需执行测试确认状态
