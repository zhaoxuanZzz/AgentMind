"""
消息格式化服务
负责将 LangChain 输出转换为类型化的消息块
"""
from typing import Dict, Any, List, AsyncGenerator
from datetime import datetime
import json
import re
from loguru import logger

from app.api.schemas import (
    MessageType,
    TextChunk,
    ThinkingChunk,
    ToolChunk,
    PlanChunk,
    SystemChunk,
    AnyMessageChunk,
)


class MessageFormatter:
    """消息格式化器 - 将不同来源的内容转换为类型化消息块"""
    
    def __init__(self):
        self.current_plan_step = 0
    
    def format_text(self, content: str) -> TextChunk:
        """格式化普通文本消息"""
        return TextChunk(
            type=MessageType.TEXT,
            content=content,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def format_thinking(self, content: str, step: int = None) -> ThinkingChunk:
        """格式化思考过程消息"""
        return ThinkingChunk(
            type=MessageType.THINKING,
            content=content,
            reasoning_step=step,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def format_tool_call(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        tool_output: str = None,
        status: str = "pending",
        error: str = None
    ) -> ToolChunk:
        """格式化工具调用消息"""
        return ToolChunk(
            type=MessageType.TOOL,
            tool_name=tool_name,
            tool_input=tool_input,
            tool_output=tool_output,
            status=status,
            error=error,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def format_plan_step(
        self,
        step_number: int,
        description: str,
        status: str = "pending",
        result: str = None,
        substeps: List[str] = None
    ) -> PlanChunk:
        """格式化计划步骤消息"""
        return PlanChunk(
            type=MessageType.PLAN,
            step_number=step_number,
            description=description,
            status=status,
            result=result,
            substeps=substeps,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def format_system(
        self,
        content: str,
        level: str = "info"
    ) -> SystemChunk:
        """格式化系统消息"""
        return SystemChunk(
            type=MessageType.SYSTEM,
            content=content,
            level=level,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def detect_message_type(self, content: str) -> MessageType:
        """
        智能检测消息内容类型
        基于内容特征判断应该使用哪种消息类型
        """
        content_lower = content.lower().strip()
        
        # 检测思考过程标记
        thinking_patterns = [
            r'让我思考',
            r'我正在思考',
            r'分析.*问题',
            r'首先.*然后',
            r'我需要',
            r'reasoning:',
            r'思路：',
        ]
        for pattern in thinking_patterns:
            if re.search(pattern, content_lower):
                return MessageType.THINKING
        
        # 检测工具调用（通常包含特定格式）
        if 'tool:' in content_lower or 'action:' in content_lower:
            return MessageType.TOOL
        
        # 检测计划步骤
        plan_patterns = [
            r'step \d+:',
            r'步骤\s*\d+',
            r'第\s*\d+\s*步',
        ]
        for pattern in plan_patterns:
            if re.search(pattern, content_lower):
                return MessageType.PLAN
        
        # 默认为普通文本
        return MessageType.TEXT
    
    def extract_intermediate_steps(
        self,
        intermediate_steps: List[tuple]
    ) -> List[ToolChunk]:
        """
        从 LangChain intermediate_steps 提取工具调用信息
        intermediate_steps 格式: [(AgentAction, observation), ...]
        """
        tool_chunks = []
        
        for step in intermediate_steps:
            try:
                if len(step) != 2:
                    continue
                
                action, observation = step
                
                # 提取工具信息
                tool_name = getattr(action, 'tool', 'unknown')
                tool_input = getattr(action, 'tool_input', {})
                
                # 如果 tool_input 是字符串，尝试解析为 dict
                if isinstance(tool_input, str):
                    try:
                        tool_input = json.loads(tool_input)
                    except:
                        tool_input = {"input": tool_input}
                
                tool_chunk = self.format_tool_call(
                    tool_name=tool_name,
                    tool_input=tool_input,
                    tool_output=str(observation),
                    status="completed"
                )
                tool_chunks.append(tool_chunk)
                
            except Exception as e:
                logger.error(f"Failed to extract tool step: {e}")
                continue
        
        return tool_chunks
    
    def parse_plan_text(self, plan_text: str) -> List[PlanChunk]:
        """
        解析计划文本，提取步骤信息
        支持格式：
        - Step 1: 描述
        - 步骤1：描述
        - 1. 描述
        """
        plan_chunks = []
        
        # 匹配步骤模式
        patterns = [
            r'(?:Step|步骤)\s*(\d+)\s*[:：]\s*(.+)',
            r'(\d+)\.\s+(.+)',
        ]
        
        lines = plan_text.split('\n')
        step_num = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            matched = False
            for pattern in patterns:
                match = re.match(pattern, line)
                if match:
                    step_num = int(match.group(1))
                    description = match.group(2).strip()
                    
                    plan_chunk = self.format_plan_step(
                        step_number=step_num,
                        description=description,
                        status="pending"
                    )
                    plan_chunks.append(plan_chunk)
                    matched = True
                    break
            
            # 如果没有匹配到编号，但在计划上下文中，视为子步骤
            if not matched and step_num > 0 and line.startswith('-'):
                description = line[1:].strip()
                if description:
                    # 添加到最后一个步骤的 substeps
                    if plan_chunks:
                        if plan_chunks[-1].substeps is None:
                            plan_chunks[-1].substeps = []
                        plan_chunks[-1].substeps.append(description)
        
        return plan_chunks
    
    async def stream_chunks(
        self,
        content_generator: AsyncGenerator[str, None]
    ) -> AsyncGenerator[AnyMessageChunk, None]:
        """
        从内容生成器流式产生消息块
        自动检测内容类型并转换为相应的消息块
        """
        buffer = ""
        
        async for chunk in content_generator:
            buffer += chunk
            
            # 如果缓冲区足够大，尝试检测类型并发送
            if len(buffer) > 20:
                msg_type = self.detect_message_type(buffer)
                
                if msg_type == MessageType.TEXT:
                    yield self.format_text(buffer)
                    buffer = ""
                elif msg_type == MessageType.THINKING:
                    yield self.format_thinking(buffer)
                    buffer = ""
        
        # 发送剩余内容
        if buffer.strip():
            msg_type = self.detect_message_type(buffer)
            if msg_type == MessageType.TEXT:
                yield self.format_text(buffer)
            elif msg_type == MessageType.THINKING:
                yield self.format_thinking(buffer)


# 全局实例
message_formatter = MessageFormatter()
