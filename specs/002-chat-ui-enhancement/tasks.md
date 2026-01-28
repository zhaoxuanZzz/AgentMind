---
description: "Task list for chat UI enhancement feature implementation"
---

# Tasks: 聊天界面增强

**Input**: Design documents from `/specs/002-chat-ui-enhancement/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/, research.md, quickstart.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `- [ ] [ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

This project uses a web app structure:
- Backend: `backend/app/`
- Frontend: `frontend/src/`

---

## 第 1 阶段：设置（共享基础设施）

**目的**：项目初始化和基础结构

**第 1 阶段的宪章合规性：**
- 使用现有依赖，前端已有 @ant-design/x ^2.1.3（原则 III）
- 配置 Loguru 进行结构化日志记录（原则 V）
- 设置类型检查和 Pydantic 验证（原则 IV）

- [X] T001 检查前端 @ant-design/x 和 @ant-design/x-sdk 依赖版本（要求 ^2.1.3）
- [X] T002 [P] 在 backend/app/core/config.py 中添加角色预设和计划模式相关配置项
- [X] T003 [P] 在 frontend/src/types/ 中创建消息类型定义文件 messageTypes.ts

---

## 第 2 阶段：基础部分（阻塞性前置条件）

**目的**：任何用户故事实现开始之前必须完成的核心基础设施

**⚠️ 关键**：任何用户故事工作开始前，此阶段必须完成

**第 2 阶段的宪章合规性：**
- 在实现之前定义 API 契约和 Pydantic 数据模型（原则 II）
- 为所有函数签名添加类型提示（原则 IV）
- 在服务边界实现结构化日志记录（原则 V）
- 确保服务模块可独立测试（原则 I）

### 后端基础设施

- [X] T004 在 backend/app/db/models.py 中新增 RolePreset 数据库模型
- [X] T005 在 backend/app/db/models.py 中新增 ConversationConfig 数据库模型
- [X] T006 在 backend/app/db/models.py 中新增 GlobalSettings 数据库模型
- [X] T007 [P] 在 backend/app/api/schemas.py 中定义 MessageType 枚举和 MessageChunk 基类
- [X] T008 [P] 在 backend/app/api/schemas.py 中定义具体消息类型 schemas（TextChunk、ThinkingChunk、ToolChunk、PlanChunk、SystemChunk）
- [X] T009 [P] 在 backend/app/api/schemas.py 中定义 ChatRequestV2、RolePresetResponse、ConversationConfigResponse schemas
- [X] T010 创建数据库迁移脚本 backend/scripts/migrations/002_add_role_and_config_tables.sql
- [X] T011 在 backend/app/core/config.py 中定义内置角色预设常量（BUILTIN_ROLES）

### 前端基础设施

- [X] T012 [P] 在 frontend/src/types/messageTypes.ts 中定义 TypeScript 消息类型接口（MessageType、MessageChunk、具体类型）
- [X] T013 [P] 在 frontend/src/api/types.ts 中定义 ChatRequestV2、RolePreset、ConversationConfig 接口
- [X] T014 在 frontend/src/api/services.ts 中创建新的 API 方法 sendMessageStreamV2

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - 多样化消息类型显示 (Priority: P1) 🎯 MVP

**Goal**: 支持在聊天界面中清晰区分和渲染不同类型的消息（text、thinking、tool、plan、system），提供透明的AI交互体验

**Independent Test**: 发送触发不同消息类型的提示（思考型问题、需要工具的问题等），验证每种类型都能正确渲染且视觉上清晰可辨

### Implementation for User Story 1

#### 后端实现

- [X] T015 [P] [US1] 在 backend/app/services/message_formatter.py 中创建 MessageFormatter 服务，实现消息类型分类和格式化逻辑
- [X] T016 [P] [US1] 在 backend/app/services/agent_service.py 中集成 MessageFormatter，修改流式输出逻辑以生成类型化消息块
- [X] T017 [US1] 在 backend/app/api/routes/chat.py 中新增 /api/chat/stream-v2 端点（依赖 T016）
- [X] T018 [US1] 在 backend/app/services/agent_service.py 中实现从 LangChain 回调中提取 thinking、tool、plan 信息的逻辑
- [X] T019 [US1] 在 backend/app/services/agent_service.py 中添加日志记录（每种消息类型的生成和发送）

#### 前端实现

- [X] T020 [P] [US1] 在 frontend/src/components/MessageRenderer/ 中创建主渲染器组件 index.tsx
- [X] T021 [P] [US1] 在 frontend/src/components/MessageRenderer/ 中创建 ThinkingMessage.tsx（思考过程渲染）
- [X] T022 [P] [US1] 在 frontend/src/components/MessageRenderer/ 中创建 ToolMessage.tsx（工具调用渲染，使用 Collapse 组件）
- [X] T023 [P] [US1] 在 frontend/src/components/MessageRenderer/ 中创建 PlanMessage.tsx（计划步骤渲染，使用 Timeline 组件）
- [X] T024 [P] [US1] 在 frontend/src/components/MessageRenderer/ 中创建 SystemMessage.tsx（系统消息渲染，使用 Alert 组件）
- [X] T025 [US1] 在 frontend/src/api/services.ts 中实现 SSE 流解析逻辑，处理不同类型的 MessageChunk（依赖 T014）
- [X] T026 [US1] 在 frontend/src/pages/ChatPage.tsx 中集成 MessageRenderer 组件，替换现有消息渲染逻辑
- [X] T027 [US1] 在 frontend/src/components/MessageRenderer/ 中为不同消息类型添加视觉样式（图标、背景色、边框）

#### 数据兼容性

- [X] T028 [P] [US1] 在 backend/app/db/models.py 的 Message 模型中添加 chunks 字段（JSONB 类型），保留旧字段以兼容
- [X] T029 [US1] 在 backend/app/services/agent_service.py 中实现旧消息格式到新格式的转换逻辑

**Checkpoint**: At this point, User Story 1 should be fully functional - different message types render correctly with distinct visual styles

---

## Phase 4: User Story 2 - 计划模式切换 (Priority: P2)

**Goal**: 允许用户切换"计划模式"，让AI在执行复杂任务前先制定详细计划，提供更结构化和可预测的执行过程

**Independent Test**: 开启/关闭计划模式开关，发送相同的复杂问题，验证AI在两种模式下的不同行为（计划模式下先生成计划再执行，简单问题自动跳过计划）

### Implementation for User Story 2

#### 后端实现

- [X] T030 [P] [US2] 在 backend/app/services/agent/plan_mode_service.py 中创建 PlanModeService，实现问题复杂度判断逻辑（should_use_plan_mode）
- [X] T031 [P] [US2] 在 backend/app/services/agent/plan_mode_service.py 中实现计划生成逻辑（generate_plan 方法）
- [X] T032 [P] [US2] 在 backend/app/services/agent/plan_mode_service.py 中实现计划步骤执行和进度追踪逻辑
- [X] T033 [US2] 在 backend/app/services/agent_service.py 中集成 PlanModeService，在 chat_stream_v2 方法中根据请求参数和会话配置启用计划模式
- [X] T034 [US2] 在 backend/app/api/routes/chat.py 的 stream-v2 端点中处理 plan_mode 请求参数
- [X] T035 [US2] 在 backend/app/services/agent/plan_mode_service.py 中添加日志记录（复杂度判断、计划生成、步骤执行）

#### 前端实现

- [X] T036 [P] [US2] 在 frontend/src/components/ 中创建 PlanModeToggle.tsx（开关组件，使用 antd Switch）
- [X] T037 [P] [US2] 在 frontend/src/hooks/ 中创建 usePlanMode.ts，管理计划模式状态（localStorage 持久化）
- [X] T038 [US2] 在 frontend/src/pages/ChatPage.tsx 中集成 PlanModeToggle 组件（放置在发送按钮旁）
- [X] T039 [US2] 在 frontend/src/api/services.ts 的 sendMessageStreamV2 方法中添加 plan_mode 参数传递

#### 会话配置存储

- [X] T040 [P] [US2] 在 backend/app/api/routes/conversation_config.py 中创建会话配置 API 路由（GET、PUT、DELETE /api/conversations/{id}/config）
- [X] T041 [P] [US2] 在 backend/app/api/routes/conversation_config.py 中创建全局设置 API 路由（GET、PUT /api/settings/global）
- [X] T042 [US2] 在 backend/app/services/agent_service.py 中实现配置优先级逻辑（请求参数 > 会话配置 > 全局默认）

**Checkpoint**: At this point, User Story 2 should be fully functional - users can toggle plan mode, and complex tasks generate structured plans while simple questions skip planning

---

## Phase 5: User Story 3 - 角色预设选择 (Priority: P2)

**Goal**: 允许用户从预设角色列表中选择AI的角色（软件工程师、产品经理、市场营销、翻译专家、研究助理），快速获得针对特定场景优化的AI行为

**Independent Test**: 选择不同角色预设，发送相同问题，验证AI回复是否符合所选角色的特征和专业领域

### Implementation for User Story 3

#### 后端实现

- [X] T043 [P] [US3] 在 backend/app/services/agent/role_preset_service.py 中创建 RolePresetService，加载和管理内置角色预设
- [X] T044 [P] [US3] 在 backend/app/api/routes/roles.py 中创建角色预设 API 路由（GET /api/roles、GET /api/roles/{role_id}）
- [X] T045 [US3] 在 backend/app/services/agent_service.py 中集成 RolePresetService，根据角色 ID 应用系统提示词和配置
- [X] T046 [US3] 在 backend/app/services/agent_service.py 中实现角色优先级逻辑（请求 role_id > 会话配置 role_id > 全局默认 role_id）
- [X] T047 [US3] 在 backend/app/api/routes/chat.py 的 stream-v2 端点中处理 role_id 请求参数
- [X] T048 [US3] 在 backend/app/services/agent/role_preset_service.py 中添加日志记录（角色加载、角色应用）

#### 前端实现

- [X] T049 [P] [US3] 在 frontend/src/components/ 中创建 RoleSelector.tsx（下拉框组件，使用 antd Select）
- [X] T050 [P] [US3] 在 frontend/src/hooks/ 中创建 useRolePreset.ts，管理角色状态和 API 调用（获取角色列表、全局默认、会话配置）
- [X] T051 [US3] 在 frontend/src/pages/ChatPage.tsx 中集成 RoleSelector 组件
- [X] T052 [US3] 在 frontend/src/api/services.ts 的 sendMessageStreamV2 方法中添加 role_id 参数传递
- [X] T053 [US3] 在 frontend/src/api/services.ts 中实现角色预设相关 API 方法（fetchRoles、fetchRoleDetail、updateGlobalSettings、updateConversationConfig）

#### 全局设置和会话配置集成

- [X] T054 [US3] 在 frontend/src/hooks/useRolePreset.ts 中实现全局默认角色和会话级覆盖的状态管理
- [X] T055 [US3] 在 frontend/src/pages/ChatPage.tsx 中实现角色切换时的配置持久化逻辑（调用会话配置 API）

**Checkpoint**: All user stories should now be independently functional - users can select roles, roles affect AI behavior appropriately

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final quality assurance

- [X] T056 [P] 在 backend/app/api/routes/chat.py 中添加错误处理和边界情况处理（格式错误、未知消息类型）
- [X] T057 [P] 在 frontend/src/components/MessageRenderer/ 中添加错误边界和降级渲染（未知类型显示为默认样式）
- [X] T058 [P] 在 frontend/src/api/services.ts 中添加网络错误处理和重试逻辑（流式数据部分到达时的处理）
- [X] T059 验证向后兼容性：旧消息在新界面中正确显示
- [X] T060 [P] 性能优化：消息渲染延迟测试和优化（目标 <100ms）
- [X] T061 [P] 在 backend/ 中添加集成测试 tests/integration/test_message_types.py（测试不同消息类型的生成）
- [X] T062 [P] 在 backend/ 中添加集成测试 tests/integration/test_plan_mode.py（测试计划模式和复杂度判断）
- [X] T063 [P] 在 frontend/ 中添加组件测试 tests/components/MessageRenderer.test.tsx
- [X] T064 更新 specs/002-chat-ui-enhancement/quickstart.md 中的示例（如需要）
- [X] T065 执行 quickstart.md 中的验收场景测试
- [X] T066 代码审查和重构（确保符合 AgentMind 宪章）

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User Story 1 (P1) is MVP - highest priority
  - User Stories 2 and 3 (P2) can proceed in parallel after US1
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1) - 多样化消息类型显示**: Can start after Foundational (Phase 2) - No dependencies on other stories. This is the MVP.
- **User Story 2 (P2) - 计划模式切换**: Depends on US1 completion (needs message type infrastructure, especially PlanChunk). Uses PlanMessage component from US1.
- **User Story 3 (P2) - 角色预设选择**: Can start after Foundational (Phase 2) - Independent of US1 and US2, but integrates with conversation config from US2.

### Within Each User Story

**User Story 1**:
- Backend foundation (T015-T019) before frontend integration (T026)
- Message type components (T020-T024) can be built in parallel
- Data compatibility (T028-T029) can be done in parallel with components

**User Story 2**:
- Backend PlanModeService (T030-T032) before integration (T033)
- Frontend components (T036-T037) in parallel
- Configuration API (T040-T041) can be built in parallel with core logic

**User Story 3**:
- Backend RolePresetService (T043) before API routes (T044)
- Frontend components (T049-T050) in parallel with backend
- Global settings integration (T054-T055) after both backend and frontend components

### Parallel Opportunities

**Phase 1 (Setup)**:
- All tasks (T001-T003) can run in parallel

**Phase 2 (Foundational)**:
- Backend models (T004-T006) → must complete before migration (T010)
- Backend schemas (T007-T009, T011) can run in parallel
- Frontend types (T012-T014) can run in parallel with backend schemas

**Phase 3 (User Story 1)**:
- Backend: T015, T016 in parallel → then T017
- Frontend message components: T020-T024 all in parallel
- Data compatibility: T028-T029 in parallel

**Phase 4 (User Story 2)**:
- Backend: T030-T032 in parallel, T040-T041 in parallel
- Frontend: T036-T037 in parallel

**Phase 5 (User Story 3)**:
- Backend: T043 → T044 (sequential), T048 parallel with T043-T044
- Frontend: T049-T050 in parallel

**Phase 6 (Polish)**:
- Error handling (T056-T058) in parallel
- Tests (T061-T063) in parallel
- Performance and validation (T059-T060) in parallel

### Critical Path

Setup → Foundational → User Story 1 (MVP) → User Story 2 (depends on US1 for PlanMessage) → User Story 3 (can integrate in parallel) → Polish

### Recommended Execution Strategy

1. **Sprint 1 (MVP)**: Phase 1 + Phase 2 + User Story 1
   - Delivers core message type display functionality
   - ~17 tasks (T001-T029)
   
2. **Sprint 2**: User Story 2 + User Story 3 (parallel)
   - Delivers plan mode and role presets
   - ~26 tasks (T030-T055)
   
3. **Sprint 3**: Polish & Testing
   - Final quality assurance
   - ~11 tasks (T056-T066)

---

## Implementation Strategy

### MVP First (User Story 1)

The minimum viable product focuses on **User Story 1** only:
- Users can see different message types (thinking, tool, plan, text, system)
- Each type has distinct visual styling
- Backend generates typed message chunks
- Frontend renders them using ant-design-x components

**Why this is MVP**: This provides immediate value by making AI interactions more transparent. Users can understand how AI processes their requests.

### Incremental Delivery

After MVP, deliver in priority order:
1. **User Story 2 (Plan Mode)**: Builds on message types infrastructure, adds planning capability
2. **User Story 3 (Role Presets)**: Independent feature, can be developed in parallel with US2

### Independent Testing Per Story

Each user story has clear test criteria:
- **US1**: Send messages that trigger different types, verify visual distinction
- **US2**: Toggle plan mode, verify plan generation for complex tasks
- **US3**: Switch roles, verify AI behavior matches role characteristics

---

## Task Summary

- **Total Tasks**: 66
- **Phase 1 (Setup)**: 3 tasks
- **Phase 2 (Foundational)**: 11 tasks
- **Phase 3 (User Story 1)**: 15 tasks
- **Phase 4 (User Story 2)**: 13 tasks
- **Phase 5 (User Story 3)**: 13 tasks
- **Phase 6 (Polish)**: 11 tasks

**Tasks by User Story**:
- User Story 1 (P1 - MVP): 15 tasks
- User Story 2 (P2): 13 tasks
- User Story 3 (P2): 13 tasks
- Shared Infrastructure: 14 tasks (Setup + Foundational)
- Polish & Testing: 11 tasks

**Parallelization**:
- Maximum parallel tasks in Phase 2: 8 tasks (schemas and types)
- Maximum parallel tasks in User Story 1: 5 tasks (message components)
- Overall parallelization factor: ~40% of tasks can run in parallel with proper planning

**Format Validation**: ✅ All tasks follow the required checklist format:
- Checkbox: `- [ ]`
- Task ID: Sequential (T001-T066)
- [P] marker: Applied to 29 parallelizable tasks
- [Story] label: Applied to all user story tasks (US1, US2, US3)
- File paths: Included in all task descriptions
