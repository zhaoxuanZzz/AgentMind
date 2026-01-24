"""流式回调处理器"""
from langchain_core.callbacks import AsyncCallbackHandler
from typing import List, Dict, Optional
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
            "type": "tool",
            "tool_info": {
                "tool": tool_name,
                "input": tool_input,
                "status": "running"
            }
        })
        self.current_tool = tool_name
    
    async def on_tool_end(self, output, **kwargs):
        """工具执行完成时"""
        if self.current_tool:
            self.chunks.append({
                "type": "tool",
                "tool_info": {
                    "tool": self.current_tool,
                    "output": str(output)[:500],
                    "status": "completed"
                }
            })
            self.current_tool = None
    
    async def on_llm_new_token(self, token: str, **kwargs):
        """LLM输出新token时 - 这是关键的流式输出回调"""
        if not token:
            return
        
        logger.debug(f"Received token: {token[:50]}...")  # 调试日志
        
        # 累积token到buffer用于分析
        self.buffer += token
        
        # 检查是否包含"Final Answer:"标记
        if "Final Answer:" in self.buffer or "final answer:" in self.buffer.lower():
            if not self.in_final_answer:
                # 切换到最终答案模式
                # 提取"Final Answer:"之前的内容作为推理过程
                parts = self.buffer.split("Final Answer:", 1) if "Final Answer:" in self.buffer else self.buffer.split("final answer:", 1)
                if len(parts) > 1:
                    # 发送之前累积的推理内容
                    thinking_part = parts[0].strip()
                    if thinking_part:
                        self.chunks.append({
                            "type": "thinking",
                            "content": thinking_part
                        })
                    # 处理最终答案部分
                    self.buffer = parts[1]
                    self.in_final_answer = True
                else:
                    self.in_final_answer = True
        
        # 根据当前模式处理token
        if self.in_final_answer:
            # 最终答案模式 - 直接发送内容
            if self.buffer.strip():
                # 清理buffer并发送
                content = self.buffer.replace("Final Answer:", "").replace("final answer:", "").strip()
                if content:
                    self.chunks.append({
                        "type": "content",
                        "content": content
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
                        "content": self.current_thinking
                    })
                    self.current_thinking = ""
    
    async def on_llm_start(self, serialized, prompts, **kwargs):
        """LLM开始输出时"""
        self.in_final_answer = False
        self.current_thinking = ""
        self.buffer = ""
        logger.debug("LLM started, resetting state")
    
    async def on_llm_end(self, response, **kwargs):
        """LLM结束输出时，发送剩余的推理内容和最终答案"""
        logger.debug("LLM ended, flushing remaining content")
        
        # 发送剩余的推理内容
        if self.current_thinking.strip() and not self.in_final_answer:
            self.chunks.append({
                "type": "thinking",
                "content": self.current_thinking.strip()
            })
            self.current_thinking = ""
            # 清空buffer，因为current_thinking已经包含了最后一部分未发送的内容
            self.buffer = ""
        elif self.buffer.strip():
            # 如果current_thinking为空，才处理buffer
            if self.in_final_answer:
                content = self.buffer.replace("Final Answer:", "").replace("final answer:", "").strip()
                if content:
                    self.chunks.append({
                        "type": "content",
                        "content": content
                    })
            else:
                if self.buffer.strip():
                    self.chunks.append({
                        "type": "thinking",
                        "content": self.buffer.strip()
                    })
            self.buffer = ""

