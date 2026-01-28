"""流式回调处理器"""
from langchain_core.callbacks import AsyncCallbackHandler
from typing import List, Dict, Optional
from datetime import datetime
from loguru import logger


class StreamCallbackHandler(AsyncCallbackHandler):
    """流式回调处理器 - 处理Agent执行过程中的流式输出"""
    
    def __init__(self):
        super().__init__()
        self.chunks = []
        self.current_tool = None
        self.current_thinking = ""
        self.in_final_answer = False
        self.done = False
        self.error = None
        self.buffer = ""  # 用于累积token
        
    def has_new_data(self) -> bool:
        """检查是否有新数据"""
        return len(self.chunks) > 0
    
    def get_latest_chunk(self) -> Optional[Dict]:
        """获取最新的数据块"""
        if self.chunks:
            return self.chunks.pop(0)
        return None
    
    def is_done(self) -> bool:
        """检查是否完成"""
        return self.done
    
    def set_done(self):
        """标记为完成"""
        self.done = True
    
    def has_error(self) -> bool:
        """检查是否有错误"""
        return self.error is not None
    
    def set_error(self, error: str):
        """设置错误"""
        self.error = error
        self.done = True
    
    def get_error(self) -> Optional[str]:
        """获取错误信息"""
        return self.error
    
    async def on_agent_action(self, action, **kwargs):
        """Agent执行工具时"""
        tool_name = getattr(action, 'tool', 'unknown')
        tool_input = getattr(action, 'tool_input', '')
        
        self.chunks.append({
            "type": "tool_call",
            "data": {
                "tool_name": tool_name,
                "tool_input": tool_input
            },
            "timestamp": datetime.now().isoformat()
        })
        self.current_tool = tool_name
    
    async def on_tool_end(self, output, **kwargs):
        """工具执行完成时"""
        if self.current_tool:
            self.chunks.append({
                "type": "tool_result",
                "data": {
                    "tool_name": self.current_tool,
                    "tool_output": str(output)[:500]
                },
                "timestamp": datetime.now().isoformat()
            })
            self.current_tool = None
    
    async def on_llm_new_token(self, token: str, **kwargs):
        """LLM输出新token时 - 这是关键的流式输出回调"""
        if not token:
            return
        
        logger.debug(f"Received token: {token[:50]}...")  # 调试日志
        
        # 累积token到buffer
        self.buffer += token
        
        # 检查是否包含Agent思考标记（如 "Thought:", "Action:", "Final Answer:" 等）
        # 如果包含这些标记，说明是Agent模式，需要区分thinking和content
        agent_markers = ["Thought:", "Action:", "Action Input:", "Observation:", "Final Answer:"]
        is_agent_mode = any(marker in self.buffer for marker in agent_markers)
        
        if is_agent_mode:
            # Agent模式：区分thinking和final answer
            if "Final Answer:" in self.buffer:
                if not self.in_final_answer:
                    # 切换到最终答案模式
                    parts = self.buffer.split("Final Answer:", 1)
                    if len(parts) > 1:
                        # 发送之前累积的推理内容
                        thinking_part = parts[0].strip()
                        if thinking_part:
                            self.chunks.append({
                                "type": "thinking",
                                "data": {
                                    "thinking": thinking_part
                                },
                                "timestamp": datetime.now().isoformat()
                            })
                        # 处理最终答案部分
                        self.buffer = parts[1]
                        self.in_final_answer = True
            
            # 根据当前模式处理token
            if self.in_final_answer:
                # 最终答案模式 - 直接发送内容
                if self.buffer.strip():
                    content = self.buffer.strip()
                    if content:
                        self.chunks.append({
                            "type": "content",
                            "data": {
                                "content": content
                            },
                            "timestamp": datetime.now().isoformat()
                        })
                        self.buffer = ""
            else:
                # 推理过程模式 - 累积到current_thinking
                self.current_thinking += token
                
                # 定期发送推理内容（每30个字符或遇到换行）
                if len(self.current_thinking) >= 30 or '\n' in token:
                    if self.current_thinking.strip():
                        self.chunks.append({
                            "type": "thinking",
                            "data": {
                                "thinking": self.current_thinking
                            },
                            "timestamp": datetime.now().isoformat()
                        })
                        self.current_thinking = ""
        else:
            # 非Agent模式（直接对话）：所有内容都作为content发送
            # 每收到一些token就发送，实现真正的流式效果
            # 降低阈值以实现更实时的流式响应
            if len(self.buffer) >= 3 or '\n' in token or len(token) > 2:
                content = self.buffer
                if content:  # 不要strip，保持原始格式
                    self.chunks.append({
                        "type": "content",
                        "data": {
                            "content": content
                        },
                        "timestamp": datetime.now().isoformat()
                    })
                    logger.debug(f"Added content chunk: {content[:30]}...")
                    self.buffer = ""
    
    async def on_llm_start(self, serialized, prompts, **kwargs):
        """LLM开始输出时"""
        self.in_final_answer = False
        self.current_thinking = ""
        self.buffer = ""
        logger.debug("LLM started, resetting state")
    
    async def on_llm_end(self, response, **kwargs):
        """LLM结束输出时，发送剩余的推理内容和最终答案"""
        logger.debug(f"LLM ended, flushing remaining content. Buffer: '{self.buffer[:50]}', chunks count: {len(self.chunks)}")
        
        # 发送剩余的buffer内容
        if self.buffer:
            # 检查是否是Agent模式
            agent_markers = ["Thought:", "Action:", "Action Input:", "Observation:", "Final Answer:"]
            is_agent_mode = any(marker in self.buffer for marker in agent_markers)
            
            if is_agent_mode and self.in_final_answer:
                # Agent模式的最终答案
                content = self.buffer
                if content:
                    self.chunks.append({
                        "type": "content",
                        "data": {
                            "content": content
                        },
                        "timestamp": datetime.now().isoformat()
                    })
                    logger.debug(f"Added final answer chunk: {content[:30]}...")
            elif is_agent_mode and not self.in_final_answer:
                # Agent模式的推理过程
                if self.buffer.strip():
                    self.chunks.append({
                        "type": "thinking",
                        "data": {
                            "thinking": self.buffer.strip()
                        },
                        "timestamp": datetime.now().isoformat()
                    })
            else:
                # 非Agent模式，作为content发送
                content = self.buffer
                if content:
                    self.chunks.append({
                        "type": "content",
                        "data": {
                            "content": content
                        },
                        "timestamp": datetime.now().isoformat()
                    })
                    logger.debug(f"Added final content chunk: {content[:30]}...")
            
            self.buffer = ""
        
        # 发送剩余的current_thinking内容（仅Agent模式）
        if self.current_thinking.strip():
            self.chunks.append({
                "type": "thinking",
                "data": {
                    "thinking": self.current_thinking.strip()
                },
                "timestamp": datetime.now().isoformat()
            })
            self.current_thinking = ""

