"""内存管理器 - 统一管理对话内存"""
from typing import List, Dict, Optional
from langchain.memory import ConversationBufferMemory
from loguru import logger


class MemoryManager:
    """统一管理对话内存"""
    
    @staticmethod
    def create_memory(
        history: Optional[List[Dict]] = None,
        max_history_length: int = 20
    ) -> ConversationBufferMemory:
        """创建并初始化内存
        
        Args:
            history: 历史对话记录，格式: [{"role": "user/assistant", "content": "..."}]
            max_history_length: 最大历史消息数量（只保留最近的消息）
        
        Returns:
            ConversationBufferMemory 实例
        """
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        if history:
            MemoryManager._load_history(memory, history, max_history_length)
            logger.info(f"Loaded {len(memory.chat_memory.messages)} messages into memory")
        else:
            logger.info("No history provided, starting fresh conversation")
        
        return memory
    
    @staticmethod
    def _load_history(
        memory: ConversationBufferMemory,
        history: List[Dict],
        max_history_length: int = 20
    ):
        """加载历史对话到内存
        
        Args:
            memory: ConversationBufferMemory 实例
            history: 历史对话记录
            max_history_length: 最大历史消息数量
        """
        # 只保留最近的消息，避免token超限
        recent_history = history[-max_history_length:] if len(history) > max_history_length else history
        
        for msg in recent_history:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            if role == "user":
                memory.chat_memory.add_user_message(content)
            elif role == "assistant":
                memory.chat_memory.add_ai_message(content)
        
        logger.debug(f"Loaded {len(recent_history)} messages from history (total: {len(history)})")
    
    @staticmethod
    def get_history_context(
        memory: ConversationBufferMemory,
        max_messages: int = 20
    ) -> str:
        """从内存中获取历史对话上下文（用于提示词）
        
        Args:
            memory: ConversationBufferMemory 实例
            max_messages: 最大消息数量
        
        Returns:
            格式化的历史对话上下文字符串
        """
        if not memory or not memory.chat_memory.messages:
            return ""
        
        # 只取最近的消息
        recent_messages = memory.chat_memory.messages[-max_messages:] if len(memory.chat_memory.messages) > max_messages else memory.chat_memory.messages
        
        history_context = "\n\n📜 对话历史（请参考之前的对话内容，保持对话连贯性）:\n"
        for msg in recent_messages:
            if hasattr(msg, 'content'):
                # 更可靠的消息类型判断
                msg_type = type(msg).__name__
                if 'Human' in msg_type or 'User' in msg_type:
                    role = "用户"
                else:
                    role = "助手"
                
                # 限制每条消息长度，避免过长
                content = msg.content[:500] + "..." if len(msg.content) > 500 else msg.content
                history_context += f"{role}: {content}\n"
        
        history_context += "\n请基于以上对话历史，理解用户的意图和上下文，保持对话的连贯性。\n"
        return history_context

