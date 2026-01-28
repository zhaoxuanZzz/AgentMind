# 实现计划：聊天界面增强

**分支**：`002-chat-ui-enhancement` | **日期**：2026-01-26 | **规范**：[spec.md](./spec.md)
**输入**：来自 `/specs/002-chat-ui-enhancement/spec.md` 的特性规范

**注意**：此模板由 `/speckit.plan` 命令填充。详见 `.specify/templates/commands/plan.md` 以了解执行工作流程。

## 摘要

本特性旨在增强聊天界面，支持多样化消息类型的展示（thinking、tools、plan等），新增计划模式和角色预设功能。前端使用ant-design-x组件进行消息渲染，后端基于LangChain/LangGraph实现。允许创建新的API接口而非局限于现有接口。

核心需求：
1. **多样化消息类型显示**（P1）：支持文本、思考过程、工具调用、计划步骤等不同类型的消息渲染
2. **计划模式切换**（P2）：在发送按钮旁提供开关，让AI先制定计划再执行
3. **角色预设选择**（P2）：提供下拉框选择预定义AI角色（软件工程师、产品经理、市场营销、翻译专家、研究助理）

技术方向：
- 前端：ant-design-x的Bubble、Prompts等组件实现消息渲染
- 后端：LangChain/LangGraph实现计划模式和角色系统提示词管理
- API：新的消息格式协议，支持结构化消息类型
- 状态管理：全局默认角色+对话级覆盖的混合模式

## 技术背景

**语言/版本**：
- 前端：TypeScript 5.2+、React 18.2+
- 后端：Python 3.11+

**主要依赖**：
- 前端：@ant-design/x ^2.1.3、@ant-design/x-sdk ^2.1.3、antd ^6.2.1、React 18.2+
- 后端：FastAPI 0.115.6、LangChain >=1.2.0、LangGraph、Pydantic 2.10.6

**存储**：
- PostgreSQL：对话、消息、角色预设、会话配置存储
- Redis：会话状态缓存、全局设置缓存
- ChromaDB：知识库向量存储（已有）

**测试**：
- 前端：Vitest（单元测试）、用户验收测试
- 后端：pytest（单元测试、集成测试）、契约测试（验证API格式）

**目标平台**：桌面浏览器（主要）、移动浏览器（兼容）

**项目类型**：Web应用（前后端分离）

**性能目标**：
- 消息类型渲染延迟 <100ms（从接收到显示）
- 计划模式切换响应 <500ms
- 角色切换响应 <300ms
- 流式消息平滑渲染，无卡顿

**约束**：
- 必须保持与现有对话历史的兼容性
- 流式传输必须支持渐进式渲染
- 消息格式必须可扩展（未来支持图像、文件等）
- 角色预设初期硬编码，后续可扩展为动态配置

**规模/范围**：
- 5种预定义角色
- 4-5种消息类型（text、thinking、tool、plan、system）
- 影响范围：前端聊天页面、后端chat API、数据库schema
- 新增表：role_presets、conversation_configs、global_settings
- 预计新增代码：前端~800行、后端~600行

## 宪章检查

*门控：必须在第 0 阶段研究之前通过。在第 1 阶段设计后重新检查。*

验证是否符合 AgentMind 宪章（v1.0.0）：

- [x] **模块化服务设计**：✅ 已验证。前端消息渲染组件（MessageRenderer、MessageTypeHandlers）独立可测试。后端角色管理（RolePresetService）、计划模式（PlanModeService）、消息格式化（MessageFormatter）分离为独立服务。
- [x] **API 优先开发**：✅ 已验证。已定义完整API契约：message-format.yaml、role-preset-api.yaml、conversation-config-api.yaml。所有端点使用Pydantic模型和OpenAPI文档。
- [x] **依赖管理**：✅ 已验证。前端已有@ant-design/x ^2.1.3。后端无需新增依赖（LangChain已安装）。
- [x] **类型安全**：✅ 已验证。前端TypeScript严格类型（MessageType枚举、RolePreset接口、MessageChunk联合类型）。后端Pydantic模型完整（MessageChunk、RolePreset、ConversationConfig、GlobalSettings）。
- [x] **可观测性**：✅ 已验证。设计包含关键日志点：角色切换、计划模式激活、消息类型分发、复杂度判断逻辑、工具调用。

**违规项（如有）**：无。所有原则都得到遵守。

**Phase 1后重新评估结果**：
- [x] 数据模型设计保持模块化：✅ MessageChunk基类+5个子类，RolePreset独立，配置分层清晰
- [x] API契约完整且类型安全：✅ 3个OpenAPI文件，覆盖所有端点，Pydantic验证完整
- [x] 复杂度没有超出必要范围：✅ 无过度设计，所有复杂度都有明确理由（研究文档第7节）

**最终结论**：通过所有宪章检查，可以进入实施阶段（Phase 2）。

## Project Structure

### Documentation (this feature)

```text
specs/002-chat-ui-enhancement/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── message-format.yaml        # 新消息格式API契约
│   ├── role-preset-api.yaml       # 角色预设API契约
│   └── conversation-config-api.yaml  # 会话配置API契约
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── chat.py                    # [修改] 新增stream-v2端点
│   │   │   ├── roles.py                   # [新增] 角色预设管理API
│   │   │   └── conversation_config.py     # [新增] 会话配置API
│   │   └── schemas.py                     # [修改] 新增消息格式schemas
│   ├── services/
│   │   ├── agent/
│   │   │   ├── role_preset_service.py     # [新增] 角色预设服务
│   │   │   └── plan_mode_service.py       # [新增] 计划模式服务
│   │   ├── message_formatter.py           # [新增] 消息格式化服务
│   │   └── agent_service.py               # [修改] 集成新服务
│   ├── db/
│   │   └── models.py                      # [修改] 新增RolePreset、ConversationConfig、GlobalSettings模型
│   └── core/
│       └── config.py                      # [修改] 添加角色预设配置
└── tests/
    ├── contract/
    │   └── test_message_format.py         # [新增] 消息格式契约测试
    └── integration/
        └── test_plan_mode.py              # [新增] 计划模式集成测试

frontend/
├── src/
│   ├── components/
│   │   ├── MessageRenderer/               # [新增] 消息渲染组件
│   │   │   ├── index.tsx                  # 主渲染器
│   │   │   ├── ThinkingMessage.tsx        # 思考过程渲染
│   │   │   ├── ToolMessage.tsx            # 工具调用渲染
│   │   │   ├── PlanMessage.tsx            # 计划步骤渲染
│   │   │   └── types.ts                   # 消息类型定义
│   │   ├── PlanModeToggle.tsx             # [新增] 计划模式开关
│   │   └── RoleSelector.tsx               # [新增] 角色选择器
│   ├── pages/
│   │   └── ChatPage.tsx                   # [修改] 集成新组件和消息类型
│   ├── api/
│   │   ├── types.ts                       # [修改] 新增消息类型定义
│   │   └── services.ts                    # [修改] 新增API调用
│   └── hooks/
│       ├── useRolePreset.ts               # [新增] 角色预设hook
│       └── usePlanMode.ts                 # [新增] 计划模式hook
└── tests/
    └── components/
        └── MessageRenderer.test.tsx       # [新增] 消息渲染器测试
```

**Structure Decision**: 采用Web应用结构（frontend + backend）。新增服务模块独立于现有代码，保持向后兼容。前端组件模块化，每种消息类型有独立的渲染器。

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

无违规项需要追踪。
