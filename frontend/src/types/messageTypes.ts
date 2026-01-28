/**
 * 消息类型定义
 * 用于前后端统一的消息格式规范
 */

/**
 * 消息类型枚举
 */
export enum MessageType {
  TEXT = "text",           // 普通文本内容
  THINKING = "thinking",   // AI思考过程
  TOOL = "tool",          // 工具调用
  PLAN = "plan",          // 计划步骤
  SYSTEM = "system",      // 系统消息
  CONVERSATION_ID = "conversation_id",  // 对话ID消息
  DONE = "done",          // 完成标记
  ERROR = "error"         // 错误消息
}

/**
 * 消息块基类
 */
export interface MessageChunk {
  type: MessageType;
  timestamp?: string;
  metadata?: Record<string, any>;
}

/**
 * 文本消息块
 */
export interface TextChunk extends MessageChunk {
  type: MessageType.TEXT;
  content: string;
}

/**
 * 思考过程消息块
 */
export interface ThinkingChunk extends MessageChunk {
  type: MessageType.THINKING;
  content: string;
  reasoning_step?: number;  // 推理步骤编号
}

/**
 * 工具调用消息块
 */
export interface ToolChunk extends MessageChunk {
  type: MessageType.TOOL;
  tool_name: string;
  tool_input: Record<string, any>;
  tool_output?: string;
  status: "pending" | "running" | "completed" | "failed";
  error?: string;
}

/**
 * 计划步骤消息块
 */
export interface PlanChunk extends MessageChunk {
  type: MessageType.PLAN;
  step_number: number;
  description: string;
  status: "pending" | "in_progress" | "completed" | "failed";
  result?: string;
  substeps?: string[];
}

/**
 * 系统消息块
 */
export interface SystemChunk extends MessageChunk {
  type: MessageType.SYSTEM;
  content: string;
  level: "info" | "warning" | "error";
}

/**
 * 对话ID消息块
 */
export interface ConversationIdChunk extends MessageChunk {
  type: MessageType.CONVERSATION_ID;
  conversation_id: number;
}

/**
 * 完成消息块
 */
export interface DoneChunk extends MessageChunk {
  type: MessageType.DONE;
  conversation_id?: number;
  message_id?: number;
}

/**
 * 错误消息块
 */
export interface ErrorChunk extends MessageChunk {
  type: MessageType.ERROR;
  message: string;
  code?: string;
}

/**
 * 所有消息块类型的联合类型
 */
export type AnyMessageChunk =
  | TextChunk
  | ThinkingChunk
  | ToolChunk
  | PlanChunk
  | SystemChunk
  | ConversationIdChunk
  | DoneChunk
  | ErrorChunk;
