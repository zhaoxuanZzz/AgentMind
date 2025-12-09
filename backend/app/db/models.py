from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base


class Conversation(Base):
    """对话会话表"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    """消息表"""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    meta_info = Column(JSON, nullable=True)  # 存储额外信息，如检索的知识等
    created_at = Column(DateTime, default=datetime.utcnow)
    
    conversation = relationship("Conversation", back_populates="messages")


class KnowledgeBase(Base):
    """知识库表"""
    __tablename__ = "knowledge_bases"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    collection_name = Column(String(200), nullable=False)  # ChromaDB collection name
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    documents = relationship("Document", back_populates="knowledge_base", cascade="all, delete-orphan")


class Document(Base):
    """文档表"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    knowledge_base_id = Column(Integer, ForeignKey("knowledge_bases.id"))
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String(500), nullable=True)  # 文档来源
    meta_info = Column(JSON, nullable=True)
    vector_id = Column(String(100), nullable=True)  # ChromaDB中的ID
    created_at = Column(DateTime, default=datetime.utcnow)
    
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")


class Task(Base):
    """任务表 - 用于推理规划"""
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(20), default="pending")  # pending, in_progress, completed, failed
    plan = Column(JSON, nullable=True)  # 存储规划的步骤
    result = Column(JSON, nullable=True)  # 存储执行结果
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RolePreset(Base):
    """角色预设表 - 存储完整的角色预设信息"""
    __tablename__ = "role_presets"
    
    id = Column(Integer, primary_key=True, index=True)
    preset_id = Column(String(100), unique=True, nullable=False, index=True)  # 唯一标识符，用于关联ChromaDB
    title = Column(String(200), nullable=False)
    prompt_content = Column(Text, nullable=False)  # 完整的提示词内容
    category = Column(String(50), nullable=False, default="general", index=True)  # 分类：tech, business, analysis, creative, general
    tags = Column(JSON, nullable=True)  # 标签列表，存储为JSON数组
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
