"""内存管理器 - 使用 LangGraph 的存储机制管理对话内存"""
from typing import List, Dict, Optional, Any
from loguru import logger
from langgraph.store.memory import InMemoryStore
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from app.core.config import settings
from psycopg_pool import ConnectionPool, AsyncConnectionPool


class MemoryManager:
    """统一管理对话内存 - 使用 LangGraph 的存储机制
    
    - 短期记忆：使用 PostgresSaver 管理单次会话的消息历史（存储在 PostgreSQL）
    - 长期记忆：使用 InMemoryStore 管理跨会话的用户数据
    """
    
    # 类级别的存储实例（单例模式）
    _long_term_store: Optional[InMemoryStore] = None
    _short_term_saver: Optional[PostgresSaver] = None
    _async_short_term_saver: Optional[AsyncPostgresSaver] = None
    _connection_pool: Optional[ConnectionPool] = None
    _async_connection_pool: Optional[AsyncConnectionPool] = None
    _short_term_saver_initialized: bool = False
    _async_short_term_saver_initialized: bool = False
    
    @classmethod
    def get_long_term_store(cls) -> InMemoryStore:
        """获取长期记忆存储实例（单例）"""
        if cls._long_term_store is None:
            cls._long_term_store = InMemoryStore()
            logger.info("Initialized long-term memory store (InMemoryStore)")
        return cls._long_term_store
    
    
    @classmethod
    async def get_short_term_saver(cls) -> AsyncPostgresSaver:
        """获取异步短期记忆保存器实例
        
        使用 PostgreSQL 存储短期记忆，支持持久化和跨会话恢复。
        首次调用时会自动创建必要的数据库表。
        用于异步操作（如 ainvoke）。
        """
        if cls._async_short_term_saver is None:
            # 获取数据库连接字符串
            db_uri = settings.DATABASE_URL
            
            # 确保连接字符串包含 sslmode 参数（如果不存在）
            if '?sslmode=' not in db_uri and '?' not in db_uri:
                db_uri = f"{db_uri}?sslmode=disable"
            elif '?sslmode=' not in db_uri and '?' in db_uri:
                db_uri = f"{db_uri}&sslmode=disable"
            
            # 首次使用时，先使用自动提交连接执行 setup（CREATE INDEX CONCURRENTLY 需要）
            if not cls._async_short_term_saver_initialized:
                try:
                    # 使用 from_conn_string 异步上下文管理器执行 setup（自动提交模式）
                    async with AsyncPostgresSaver.from_conn_string(db_uri) as temp_saver:
                        await temp_saver.setup()  # 自动创建表
                    logger.info("PostgreSQL checkpoint tables initialized successfully (async)")
                except Exception as e:
                    # 如果表已存在或其他错误，记录警告但继续
                    logger.warning(f"Failed to setup PostgreSQL checkpoint tables (may already exist): {e}")
                finally:
                    cls._async_short_term_saver_initialized = True  # 标记为已尝试，避免重复尝试
            
            # 创建异步连接池（用于长期存在的连接）
            if cls._async_connection_pool is None:
                cls._async_connection_pool = AsyncConnectionPool(
                    conninfo=db_uri,
                    min_size=1,
                    max_size=10,
                    open=True
                )
                logger.info(f"Created PostgreSQL async connection pool with DB: {db_uri.split('@')[1] if '@' in db_uri else '***'}")
            
            # 使用异步连接池创建 AsyncPostgresSaver
            cls._async_short_term_saver = AsyncPostgresSaver(cls._async_connection_pool)
            logger.info("Initialized async short-term memory saver (AsyncPostgresSaver) with connection pool")
        
        return cls._async_short_term_saver
    
    @staticmethod
    def create_memory(
        history: Optional[List[Dict]] = None,
        max_history_length: int = 20,
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建并初始化内存
        
        Args:
            history: 历史对话记录，格式: [{"role": "user/assistant", "content": "..."}]
            max_history_length: 最大历史消息数量（只保留最近的消息）
            thread_id: 线程ID，用于标识不同的会话
        
        Returns:
            包含 memory 信息的字典，包含 messages 列表和 thread_id
        """
        # 只保留最近的消息，避免token超限
        recent_history = history[-max_history_length:] if history and len(history) > max_history_length else (history or [])
        
        # 转换为 LangChain 消息格式
        messages: List[BaseMessage] = []
        for msg in recent_history:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
        
        logger.info(f"Created memory with {len(messages)} messages (thread_id: {thread_id})")
        
        return {
            "messages": messages,
            "thread_id": thread_id,
            "max_history_length": max_history_length
        }
    
    @staticmethod
    def get_history_context(
        memory: Optional[Dict[str, Any]] = None,
        max_messages: int = 20
    ) -> str:
        """从内存中获取历史对话上下文（用于提示词）
        
        Args:
            memory: 内存字典，包含 messages 列表
            max_messages: 最大消息数量
        
        Returns:
            格式化的历史对话上下文字符串
        """
        if not memory or "messages" not in memory or not memory["messages"]:
            return ""
        
        messages = memory["messages"]
        # 只取最近的消息
        recent_messages = messages[-max_messages:] if len(messages) > max_messages else messages
        
        history_context = "\n\n📜 对话历史（请参考之前的对话内容，保持对话连贯性）:\n"
        for msg in recent_messages:
            if hasattr(msg, 'content'):
                # 判断消息类型
                if isinstance(msg, HumanMessage):
                    role = "用户"
                elif isinstance(msg, AIMessage):
                    role = "助手"
                else:
                    role = "系统"
                
                # 限制每条消息长度，避免过长
                content = msg.content[:500] + "..." if len(msg.content) > 500 else msg.content
                history_context += f"{role}: {content}\n"
        
        history_context += "\n请基于以上对话历史，理解用户的意图和上下文，保持对话的连贯性。\n"
        return history_context
    
    @staticmethod
    def messages_to_dict(messages: List[BaseMessage]) -> List[Dict]:
        """将 LangChain 消息列表转换为字典格式
        
        Args:
            messages: LangChain 消息列表
        
        Returns:
            字典格式的消息列表
        """
        result = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                result.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                result.append({"role": "assistant", "content": msg.content})
        return result
    
    @staticmethod
    def dict_to_messages(history: List[Dict]) -> List[BaseMessage]:
        """将字典格式的消息列表转换为 LangChain 消息格式
        
        Args:
            history: 字典格式的消息列表
        
        Returns:
            LangChain 消息列表
        """
        messages: List[BaseMessage] = []
        for msg in history:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
        
        return messages
