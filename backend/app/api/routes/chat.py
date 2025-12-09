from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import json
import asyncio
from app.db.database import get_db
from app.db import models
from app.api.schemas import (
    ChatRequest, ChatResponse,
    ConversationCreate, ConversationResponse,
    MessageResponse,
    LLMProvidersResponse
)
from app.services.agent_service import agent_service
from app.services.llm_factory import llm_factory
from loguru import logger

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """处理聊天请求"""
    try:
        # 获取或创建对话
        if request.conversation_id:
            conversation = db.query(models.Conversation).filter(
                models.Conversation.id == request.conversation_id
            ).first()
            if not conversation:
                raise HTTPException(status_code=404, detail="对话不存在")
        else:
            # 创建新对话
            conversation = models.Conversation(title=request.message[:50])
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
        
        # 获取历史消息
        history = []
        messages = db.query(models.Message).filter(
            models.Message.conversation_id == conversation.id
        ).order_by(models.Message.created_at).all()
        
        for msg in messages:
            history.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # 保存用户消息
        user_message = models.Message(
            conversation_id=conversation.id,
            role="user",
            content=request.message
        )
        db.add(user_message)
        db.commit()
        
        # 调用agent服务
        # 处理LLM配置
        provider = None
        model = None
        if request.llm_config:
            provider = request.llm_config.provider
            model = request.llm_config.model
        
        result = await agent_service.chat(
            message=request.message,
            history=history,
            collection=request.use_knowledge_base if not request.role_preset_id else None,  # 如果指定了预设ID，则不使用collection检索
            provider=provider,
            model=model,
            search_provider=request.search_provider,
            role_preset_id=request.role_preset_id,
            db_session=db
        )
        
        # 保存助手回复
        assistant_message = models.Message(
            conversation_id=conversation.id,
            role="assistant",
            content=result["response"],
            meta_info={"intermediate_steps": result.get("intermediate_steps", [])}
        )
        db.add(assistant_message)
        db.commit()
        
        return ChatResponse(
            success=result["success"],
            response=result["response"],
            conversation_id=conversation.id,
            intermediate_steps=result.get("intermediate_steps", [])
        )
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations", response_model=List[ConversationResponse])
def get_conversations(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """获取对话列表"""
    conversations = db.query(models.Conversation).order_by(
        models.Conversation.updated_at.desc()
    ).offset(skip).limit(limit).all()
    return conversations


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
def get_conversation(conversation_id: int, db: Session = Depends(get_db)):
    """获取对话详情"""
    conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id
    ).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    return conversation


@router.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: int, db: Session = Depends(get_db)):
    """删除对话"""
    conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id
    ).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    db.delete(conversation)
    db.commit()
    return {"success": True, "message": "对话已删除"}


@router.post("/stream")
async def chat_stream(request: ChatRequest, db: Session = Depends(get_db)):
    """流式处理聊天请求"""
    async def generate():
        try:
            # 获取或创建对话
            if request.conversation_id:
                conversation = db.query(models.Conversation).filter(
                    models.Conversation.id == request.conversation_id
                ).first()
                if not conversation:
                    yield f"data: {json.dumps({'type': 'error', 'message': '对话不存在'})}\n\n"
                    return
            else:
                # 创建新对话
                conversation = models.Conversation(title=request.message[:50])
                db.add(conversation)
                db.commit()
                db.refresh(conversation)
                yield f"data: {json.dumps({'type': 'conversation_id', 'conversation_id': conversation.id})}\n\n"
            
            # 获取历史消息
            history = []
            messages = db.query(models.Message).filter(
                models.Message.conversation_id == conversation.id
            ).order_by(models.Message.created_at).all()
            
            for msg in messages:
                history.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # 保存用户消息
            user_message = models.Message(
                conversation_id=conversation.id,
                role="user",
                content=request.message
            )
            db.add(user_message)
            db.commit()
            
            # 处理LLM配置
            provider = None
            model = None
            if request.llm_config:
                provider = request.llm_config.provider
                model = request.llm_config.model
            
            # 调用流式agent服务
            final_response = ""
            intermediate_steps = []
            thinking_content = ""  # 收集推理过程
            
            async for chunk in agent_service.chat_stream(
                message=request.message,
                history=history,
                collection=request.use_knowledge_base if not request.role_preset_id else None,
                provider=provider,
                model=model,
                search_provider=request.search_provider,
                role_preset_id=request.role_preset_id,
                deep_reasoning=request.deep_reasoning or False,
                db_session=db
            ):
                if chunk.get("type") == "thinking":
                    # 推理过程
                    thinking_chunk = chunk.get('content', '')
                    thinking_content += thinking_chunk  # 累积推理过程
                    yield f"data: {json.dumps({'type': 'thinking', 'content': thinking_chunk})}\n\n"
                elif chunk.get("type") == "tool":
                    # 工具调用
                    tool_info = chunk.get("tool_info", {})
                    intermediate_steps.append(tool_info)
                    yield f"data: {json.dumps({'type': 'tool', 'tool_info': tool_info})}\n\n"
                elif chunk.get("type") == "content":
                    # 最终答案内容
                    content = chunk.get("content", "")
                    final_response += content
                    yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
                elif chunk.get("type") == "done":
                    # 完成
                    # 保存助手回复，包含推理过程和工具调用
                    assistant_message = models.Message(
                        conversation_id=conversation.id,
                        role="assistant",
                        content=final_response,
                        meta_info={
                            "intermediate_steps": intermediate_steps,
                            "thinking": thinking_content  # 保存推理过程
                        }
                    )
                    db.add(assistant_message)
                    db.commit()
                    
                    yield f"data: {json.dumps({'type': 'done', 'conversation_id': conversation.id})}\n\n"
                elif chunk.get("type") == "error":
                    yield f"data: {json.dumps({'type': 'error', 'message': chunk.get('message', '')})}\n\n"
                    return
                    
        except Exception as e:
            logger.error(f"Error in stream chat: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/llm-providers", response_model=LLMProvidersResponse)
def get_llm_providers():
    """获取可用的LLM提供商和模型列表"""
    providers = llm_factory.get_available_providers()
    default_config = llm_factory.get_default_config()
    
    return LLMProvidersResponse(
        providers=providers,
        default=default_config
    )

