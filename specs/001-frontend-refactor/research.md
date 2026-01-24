# Phase 0 研究报告：前端重构技术调研

**日期**：2026-01-24  
**特性**：001-frontend-refactor  
**研究目标**：解决技术背景中的未知项，确定实施细节

---

## R1: @ant-design/x-sdk 流式处理最佳实践

### 1.1 核心 API

#### XRequest 接口签名
```typescript
function XRequest<Input = AnyObject, Output = SSEOutput>(
  baseURL: string, 
  options?: XRequestOptions<Input, Output>
): XRequestClass<Input, Output>

interface XRequestCallbacks<Output> {
  onSuccess: (chunks: Output[], responseHeaders: Headers) => void
  onError: (error: Error, errorInfo?: any) => void
  onUpdate?: (chunk: Output, responseHeaders: Headers) => void
}
```

### 1.2 关键能力

**✅ 支持特性**：
- SSE (Server-Sent Events) 自动解析
- 自定义流转换器（TransformStream）
- 内置 AbortController（请求取消）
- 双重超时机制（请求超时 + 流超时）
- 中间件系统（请求/响应拦截）
- 完整的 TypeScript 类型支持

**⚠️ 已知限制**：
- 仅支持 UTF-8 编码
- 需手动实现重试逻辑
- 无内置并发控制
- 无进度追踪 API

### 1.3 使用决策

**决定**：使用 XRequest 替代 EventSource

**理由**：
1. 更好的 TypeScript 支持（泛型类型）
2. 内置请求取消（用户停止生成）
3. 统一的错误处理（onError callback）
4. 支持超时控制（避免无限等待）
5. 可扩展性强（中间件、自定义转换器）

**实施要点**：
- 使用  处理请求超时（30s）
- 使用  检测流中断（5s 无数据）
- 在  中处理 AbortError（用户取消）
- 使用  批量更新 UI（防抖 100ms）

---

## R2: 流式数据格式设计

### 2.1 当前后端格式分析

**后端 SSE 响应格式**（`backend/app/api/routes/chat.py`）：

```python
# 对话 ID（首次）
yield f"data: {json.dumps({'type': 'conversation_id', 'conversation_id': 123})}\n\n"

# 推理过程
yield f"data: {json.dumps({'type': 'thinking', 'content': '思考内容'})}\n\n"

# 工具调用
yield f"data: {json.dumps({'type': 'tool', 'tool_info': {...}})}\n\n"

# 消息内容
yield f"data: {json.dumps({'type': 'content', 'content': '回复内容'})}\n\n"

# 完成标记
yield f"data: {json.dumps({'type': 'done', 'conversation_id': 123})}\n\n"

# 错误
yield f"data: {json.dumps({'type': 'error', 'message': '错误信息'})}\n\n"
```

### 2.2 统一的 TypeScript 接口

```typescript
// 基础流式块类型
type StreamChunkType = 
  | 'conversation_id'  // 会话创建
  | 'thinking'         // 思考过程
  | 'tool'             // 工具调用
  | 'content'          // 消息内容
  | 'done'             // 完成标记
  | 'error';           // 错误

// SSE 输出格式（后端返回）
interface SSEChunk {
  type: StreamChunkType
  content?: string          // thinking/content 使用
  conversation_id?: number  // conversation_id/done 使用
  tool_info?: ToolInfo      // tool 使用
  message?: string          // error 使用
}

// 工具调用信息
interface ToolInfo {
  tool: string              // 工具名称
  input: string             // 工具输入
  output: string            // 工具输出
  timestamp?: string        // 调用时间
}

// 前端消息模型（整合后的完整消息）
interface Message {
  id: number
  conversation_id: number
  role: 'user' | 'assistant'
  content: string
  thinking?: string                  // 推理过程
  intermediate_steps?: ToolInfo[]   // 工具调用列表
  created_at: string
}
```

### 2.3 实施决策

**决定**：保持后端格式不变，前端适配

**理由**：
1. 后端格式已经清晰合理
2. 前端改造成本低于后端
3. 避免影响其他已有功能
4. SSE 标准格式（ 字段）

**前端处理策略**：
```typescript
// XRequest 处理 SSE
XRequest<ChatRequest, SSEChunk>('/api/chat/stream', {
  params: { message, conversation_id },
  callbacks: {
    onUpdate: (chunk) => {
      switch (chunk.type) {
        case 'conversation_id':
          setConversationId(chunk.conversation_id!)
          break
        case 'thinking':
          setStreamingThinking(prev => prev + chunk.content!)
          break
        case 'tool':
          setToolCalls(prev => [...prev, chunk.tool_info!])
          break
        case 'content':
          setStreamingContent(prev => prev + chunk.content!)
          break
        case 'done':
          finalizeMessage()
          break
        case 'error':
          handleError(chunk.message!)
          break
      }
    }
  }
})
```

---

## R3: framer-motion 动画模式

### 3.1 核心动画变体

**消息入场动画（Stagger）**：
```typescript
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.2
    }
  }
}

const itemVariants = {
  hidden: { opacity: 0, y: 20, scale: 0.95 },
  visible: { 
    opacity: 1, 
    y: 0, 
    scale: 1,
    transition: { type: "spring", stiffness: 100, damping: 12 }
  }
}
```

**页面切换动画**：
```typescript
const pageVariants = {
  initial: { opacity: 0, x: -20, scale: 0.98 },
  in: { opacity: 1, x: 0, scale: 1 },
  out: { opacity: 0, x: 20, scale: 0.98 }
}

// 使用 AnimatePresence
<AnimatePresence mode="wait" initial={false}>
  <motion.div
    key={location.pathname}
    initial="initial"
    animate="in"
    exit="out"
    variants={pageVariants}
    transition={{ type: "tween", ease: "anticipate", duration: 0.4 }}
  >
    {children}
  </motion.div>
</AnimatePresence>
```

**流式文本效果**：
```typescript
// 打字机光标
<motion.span
  animate={{ opacity: [0, 1, 0] }}
  transition={{ 
    duration: 0.8, 
    repeat: Infinity,
    repeatType: "loop"
  }}
>
  ▊
</motion.span>
```

### 3.2 性能优化策略

**GPU 加速属性（优先使用）**：
- `opacity`
- `scale`
- `x`, `y`（translateX/Y）
- `rotate`

**避免的属性（触发重排）**：
- `width`, `height`
- `top`, `left`, `right`, `bottom`

**批量动画控制**：
```typescript
import { useAnimation } from 'framer-motion'

const controls = useAnimation()

useEffect(() => {
  controls.start(i => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.1 }
  }))
}, [messages])
```

### 3.3 实施决策

**决定**：渐进式引入动画

**阶段划分**：
1. **Phase 2**：基础入场动画（消息、卡片）
2. **Phase 3**：页面切换动画
3. **Phase 4**：复杂交互动画（拖拽、手势）

**性能目标**：
- 保持 60 FPS
- 使用  检测用户偏好
- 大量元素时禁用 stagger（>50 条消息）

---

## R4: 组件拆分策略

### 4.1 组件层级结构

```
ChatPage (容器)
├── ConversationSidebar
│   ├── ConversationList
│   └── ConversationItem
│
├── ChatMainArea
│   ├── ChatHeader
│   │   ├── ModelSelector
│   │   └── ProviderSelector
│   ├── MessageList
│   │   └── MessageItem
│   │       ├── ThinkingSection
│   │       ├── ToolCallsTimeline
│   │       └── MessageContent
│   └── ChatInputArea
│       ├── RolePresetSelector
│       └── MessageInput
│
└── RolePresetSidebar
    ├── KnowledgeToggle
    ├── CategoryFilter
    ├── RolePresetList
    └── RolePresetModal
```

### 4.2 状态管理策略

**提升到 ChatPage 的状态**（全局共享）：
```typescript
interface ChatPageState {
  // 会话相关
  messages: Message[]
  conversations: Conversation[]
  conversationId?: number
  loading: boolean
  
  // 流式输出
  streamingThinking: string
  streamingContent: string
  currentStreamingMessageId: number | null
  
  // LLM 配置（localStorage 持久化）
  selectedProvider: string
  selectedModel: string
  selectedSearchProvider: string
  providers: LLMProvider[]
  
  // 角色预设
  rolePresets: RolePreset[]
  selectedRolePresetId?: string
  useKnowledge: boolean
  deepReasoning: boolean
  
  // 输入
  inputValue: string
}
```

**保留在子组件的本地状态**：
- **RolePresetSidebar**： 、 、
- **MessageItem**： （折叠状态）
- **ChatInputArea**： （表单引用）

### 4.3 实施决策

**决定**：中等粒度拆分（~15-20 个组件）

**拆分优先级**：
1. **Phase 2**：ConversationSidebar、ChatMainArea、MessageItem
2. **Phase 2**：ToolCallsTimeline、ChatInputArea
3. **Phase 3**：RolePresetSidebar 细化
4. **Phase 4**：性能优化（虚拟滚动）

**组件职责原则**：
- 展示组件：仅负责 UI 渲染，接收 props
- 容器组件：管理状态和业务逻辑
- 平均代码量：100-200 行/组件

---

## R5: 响应式设计实现

### 5.1 断点定义

```css
/* 移动端 */
@media (max-width: 576px) {
  --sidebar-width: 0;  /* 隐藏，使用 Drawer */
  --font-size-base: 14px;
  --spacing-base: 12px;
}

/* 平板 */
@media (min-width: 577px) and (max-width: 992px) {
  --sidebar-width: 240px;
  --font-size-base: 14px;
  --spacing-base: 16px;
}

/* 桌面 */
@media (min-width: 993px) {
  --sidebar-width: 280px;
  --font-size-base: 14px;
  --spacing-base: 16px;
}
```

### 5.2 移动端适配策略

**布局调整**：
- 侧边栏 → Drawer（抽屉）
- 三列布局 → 单列布局
- 工具栏折叠 → 下拉菜单

**交互优化**：
- 点击 → 触摸优化（增大触控区域）
- 键盘快捷键 → 隐藏（移动端无效）
- Hover 效果 → Active 效果

### 5.3 实施决策

**决定**：移动优先，渐进增强

**Ant Design Grid 系统**：
```tsx
<Row gutter={[16, 16]}>
  <Col xs={24} sm={24} md={6} lg={5}>
    {/* 侧边栏 */}
  </Col>
  <Col xs={24} sm={24} md={18} lg={19}>
    {/* 主内容 */}
  </Col>
</Row>
```

**自定义 Hook**：
```typescript
const useResponsive = () => {
  const [breakpoint, setBreakpoint] = useState<'mobile' | 'tablet' | 'desktop'>('desktop')
  
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth <= 576) setBreakpoint('mobile')
      else if (window.innerWidth <= 992) setBreakpoint('tablet')
      else setBreakpoint('desktop')
    }
    
    handleResize()
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])
  
  return breakpoint
}
```

---

## R6: 性能优化技术

### 6.1 第一阶段优化（Phase 2-3）

**React.memo 优化**：
```typescript
// 消息组件（避免所有消息重新渲染）
export const MessageItem = React.memo<MessageItemProps>(({ message, isStreaming }) => {
  // ...
}, (prev, next) => {
  return prev.message.id === next.message.id &&
         prev.isStreaming === next.isStreaming
})

// 会话项（频繁更新时避免重渲染）
export const ConversationItem = React.memo<ConversationItemProps>(
  ({ conversation, isActive, onSelect }) => {
    // ...
  }
)
```

**防抖节流**：
```typescript
import { debounce } from 'lodash-es'

// 搜索框防抖（300ms）
const debouncedSearch = useMemo(
  () => debounce((value: string) => {
    fetchSearchResults(value)
  }, 300),
  []
)

// 滚动监听节流（100ms）
const throttledScroll = useMemo(
  () => throttle(() => {
    checkScrollPosition()
  }, 100),
  []
)
```

**代码分割**：
```typescript
// 路由级别代码分割
const ChatPage = lazy(() => import('./pages/ChatPage'))
const KnowledgePage = lazy(() => import('./pages/KnowledgePage'))
const TasksPage = lazy(() => import('./pages/TasksPage'))

// Suspense 包裹
<Suspense fallback={<Spin size="large" />}>
  <Routes>
    <Route path="/chat" element={<ChatPage />} />
    <Route path="/knowledge" element={<KnowledgePage />} />
    <Route path="/tasks" element={<TasksPage />} />
  </Routes>
</Suspense>
```

### 6.2 第四阶段优化（Phase 4）

**虚拟滚动**（1000+ 消息时）：
```typescript
import { FixedSizeList as List } from 'react-window'

<List
  height={600}
  itemCount={messages.length}
  itemSize={120}
  width="100%"
>
  {({ index, style }) => (
    <div style={style}>
      <MessageItem message={messages[index]} />
    </div>
  )}
</List>
```

**图片懒加载**：
```typescript
<img 
  src={imageSrc} 
  loading="lazy"  // 原生懒加载
  alt="..."
/>
```

### 6.3 实施决策

**决定**：基础优化优先，虚拟滚动延后

**性能检查清单**：
- [x] React.memo 关键组件
- [x] useMemo/useCallback 缓存
- [x] 防抖节流（输入、滚动、搜索）
- [x] 代码分割（路由级别）
- [ ] 虚拟滚动（Phase 4，1000+ 消息时）
- [ ] Service Worker（PWA，Phase 5）

**性能监控**：
```typescript
// React DevTools Profiler
<Profiler id="ChatPage" onRender={onRenderCallback}>
  <ChatPage />
</Profiler>
```

---

## 决策总结

### 已解决的关键决策

| 决策项 | 选择 | 理由 |
|--------|------|------|
| **流式处理库** | XRequest | 完整 TS 支持、内置取消、超时控制 |
| **流式数据格式** | 保持后端格式 | 前端适配成本低，格式已合理 |
| **动画库** | framer-motion | 声明式 API、性能优秀、React 集成好 |
| **组件粒度** | 15-20 个组件 | 平衡可维护性和复杂度 |
| **状态管理** | React Hooks | 无需引入 Redux，项目规模适中 |
| **响应式方案** | Ant Design Grid | 统一技术栈，减少学习成本 |
| **性能优化** | 基础优化先行 | 虚拟滚动延后到 Phase 4 |

### 技术栈确认

**新增依赖**（需安装）：
```json
{
  "dependencies": {
    "framer-motion": "^11.0.0",
    "react-markdown": "^9.0.0",
    "react-syntax-highlighter": "^15.5.0",
    "lodash-es": "^4.17.21"
  },
  "devDependencies": {
    "@types/lodash-es": "^4.17.12",
    "@types/react-syntax-highlighter": "^15.5.11"
  }
}
```

**已安装**：
- @ant-design/x-sdk 2.1.3 ✅
- highlight.js 11.9.0 ✅

### 风险评估

| 风险项 | 等级 | 缓解措施 |
|--------|------|----------|
| XRequest 生产稳定性 | 中 | 详细错误处理、超时配置、测试验证 |
| framer-motion 性能影响 | 低 | 仅关键动画、使用 GPU 属性、监控 FPS |
| 组件拆分过度 | 低 | 中等粒度、保持简单、避免过度抽象 |
| 移动端兼容性 | 低 | 渐进增强、测试主流浏览器、Polyfill |

---

## 下一步行动

✅ **Phase 0 完成** - 所有关键技术问题已调研

**进入 Phase 1**：
1. 生成 data-model.md（前端数据模型）
2. 生成 contracts/（API 接口定义）
3. 生成 quickstart.md（快速开始指南）
4. 更新 Copilot 上下文（.github/copilot-instructions.md）

---

**研究完成时间**：2026-01-24  
**下一阶段**：Phase 1 - Design & Contracts
