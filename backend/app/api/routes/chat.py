from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import json
import asyncio
from datetime import datetime
from app.db.database import get_db
from app.db import models
from app.api.schemas import (
    ChatRequest, ChatResponse,
    ChatRequestV2,
    ConversationCreate, ConversationResponse,
    MessageResponse,
    LLMProvidersResponse,
    AgentConfig,
    MessageType,
    ConversationIdChunk,
    DoneChunk,
    ErrorChunk,
)
from app.services.agent_service import agent_service
from app.services.llm_factory import llm_factory
from app.services.message_formatter import message_formatter
from app.services.agent.plan_mode_service import plan_mode_service
from loguru import logger

router = APIRouter(prefix="/chat", tags=["chat"])




@router.get("/conversations", response_model=List[ConversationResponse])
def get_conversations(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """获取对话列表"""
    conversations = db.query(models.Conversation).order_by(
        models.Conversation.updated_at.desc()
    ).offset(skip).limit(limit).all()
    return conversations


@router.post("/conversations", response_model=ConversationResponse)
def create_conversation(body: ConversationCreate, db: Session = Depends(get_db)):
    """创建新对话"""
    conversation = models.Conversation(title=body.title)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
def get_conversation(conversation_id: int, db: Session = Depends(get_db)):
    """获取对话详情"""
    conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id
    ).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    return conversation


@router.patch("/conversations/{conversation_id}", response_model=ConversationResponse)
def update_conversation(
    conversation_id: int, 
    body: ConversationCreate, 
    db: Session = Depends(get_db)
):
    """更新对话标题"""
    conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id
    ).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    conversation.title = body.title
    db.commit()
    db.refresh(conversation)
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
async def chat_stream(
    chat_request: ChatRequest,
    raw_request: Request,
    db: Session = Depends(get_db)
):
    """流式处理聊天请求"""
    async def generate():
        try:
            # 获取或创建对话
            if chat_request.conversation_id:
                conversation = db.query(models.Conversation).filter(
                    models.Conversation.id == chat_request.conversation_id
                ).first()
                if not conversation:
                    yield f"data: {json.dumps({'type': 'error', 'data': {'message': '对话不存在'}, 'timestamp': datetime.now().isoformat()}, ensure_ascii=False)}\n\n"
                    return
            else:
                # 创建新对话
                conversation = models.Conversation(title=chat_request.message[:50])
                db.add(conversation)
                db.commit()
                db.refresh(conversation)
                yield f"data: {json.dumps({'type': 'conversation_id', 'data': {'conversation_id': conversation.id}, 'timestamp': datetime.now().isoformat()}, ensure_ascii=False)}\n\n"
            
            # 获取历史消息
            #history = []
            # messages = db.query(models.Message).filter(
            #     models.Message.conversation_id == conversation.id
            # ).order_by(models.Message.created_at).all()
            
            # for msg in messages:
            #     history.append({
            #         "role": msg.role,
            #         "content": msg.content
            #     })
            
            # 保存用户消息
            user_message = models.Message(
                conversation_id=conversation.id,
                role="user",
                content=chat_request.message
            )
            db.add(user_message)
            db.commit()
            
            # 构建AgentConfig配置
            agent_config = AgentConfig(
                collection=chat_request.use_knowledge_base if not chat_request.role_preset_id else None,
                provider=chat_request.llm_config.provider if chat_request.llm_config else None,
                model=chat_request.llm_config.model if chat_request.llm_config else None,
                role_preset_id=chat_request.role_preset_id,
                thread_id=str(conversation.id),
                db_session=db,
                deep_reasoning=chat_request.deep_reasoning or False
            )
            
            # 调用流式agent服务
            final_response = ""
            intermediate_steps = []
            thinking_content = ""  # 收集推理过程
            
            async for chunk in agent_service.chat_stream(
                message=chat_request.message,
                config=agent_config
            ):
                # 检测客户端是否断开连接
                if await raw_request.is_disconnected():
                    logger.info("Client disconnected, stopping stream")
                    break
                    
                chunk_type = chunk.get("type")
                
                if chunk_type == "thinking":
                    # 推理过程 - chunk 已经包含正确的格式（data 和 timestamp）
                    thinking_chunk = chunk.get('data', {}).get('thinking', '')
                    thinking_content += thinking_chunk  # 累积推理过程
                    yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                    
                elif chunk_type == "tool_call":
                    # 工具调用 - chunk 已经包含正确的格式
                    tool_info = chunk.get("data", {})
                    intermediate_steps.append({
                        "tool": tool_info.get("tool_name", ""),
                        "input": str(tool_info.get("tool_input", "")),
                        "timestamp": chunk.get("timestamp", "")
                    })
                    yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                    
                elif chunk_type == "tool_result":
                    # 工具结果 - chunk 已经包含正确的格式
                    tool_data = chunk.get("data", {})
                    # 更新 intermediate_steps 中对应的工具记录
                    for step in intermediate_steps:
                        if step.get("tool") == tool_data.get("tool_name"):
                            step["output"] = str(tool_data.get("tool_output", ""))
                            break
                    yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                    
                elif chunk_type == "content":
                    # 最终答案内容 - chunk 已经包含正确的格式
                    content = chunk.get("data", {}).get("content", "")
                    final_response += content
                    yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                    
                elif chunk_type == "done":
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
                    
                    yield f"data: {json.dumps({'type': 'done', 'data': {'conversation_id': conversation.id}, 'timestamp': datetime.now().isoformat()}, ensure_ascii=False)}\n\n"
                    
                elif chunk_type == "error":
                    error_msg = chunk.get('data', {}).get('message', '') or chunk.get('message', '')
                    yield f"data: {json.dumps({'type': 'error', 'data': {'message': error_msg}, 'timestamp': datetime.now().isoformat()}, ensure_ascii=False)}\n\n"
                    return
                    
        except asyncio.CancelledError:
            logger.info("Stream cancelled by client")
            # 不要重新抛出，优雅退出
        except GeneratorExit:
            logger.info("Stream generator exit")
        except Exception as e:
            logger.error(f"Error in stream chat: {e}", exc_info=True)
            try:
                yield f"data: {json.dumps({'type': 'error', 'data': {'message': str(e)}, 'timestamp': datetime.now().isoformat()}, ensure_ascii=False)}\n\n"
            except:
                pass  # 如果无法发送错误，静默失败
    
    return StreamingResponse(
        generate(), 
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 禁用nginx缓冲
        }
    )


@router.get("/llm-providers", response_model=LLMProvidersResponse)
def get_llm_providers():
    """获取可用的LLM提供商和模型列表"""
    providers = llm_factory.get_available_providers()
    default_config = llm_factory.get_default_config()
    
    return LLMProvidersResponse(
        providers=providers,
        default=default_config
    )


@router.post("/stream-v2")
async def chat_stream_v2(body: ChatRequestV2, db: Session = Depends(get_db)):
    """
    聊天流式接口 v2（增强版）
    支持多样化消息类型：thinking、tool、plan、text、system
    支持计划模式和角色预设
    """
    logger.info(f"Chat stream v2 request: message='{body.message[:50]}...', role_id={body.role_id}, plan_mode={body.plan_mode}")
    
    async def generate():
        try:
            # 1. 创建或获取对话
            conversation = None
            if body.conversation_id:
                conversation = db.query(models.Conversation).filter(
                    models.Conversation.id == body.conversation_id
                ).first()
                if not conversation:
                    yield f"data: {ErrorChunk(message='Conversation not found').model_dump_json()}\n\n"
                    return
            else:
                # 创建新对话
                conversation = models.Conversation(
                    title=body.message[:50] if len(body.message) > 50 else body.message
                )
                db.add(conversation)
                db.flush()
                
                # 发送对话ID
                conv_chunk = ConversationIdChunk(
                    type=MessageType.CONVERSATION_ID,
                    conversation_id=conversation.id
                )
                yield f"data: {conv_chunk.model_dump_json()}\n\n"
            
            # 2. 保存用户消息
            user_message = models.Message(
                conversation_id=conversation.id,
                role="user",
                content=body.message
            )
            db.add(user_message)
            db.flush()
            
            # 3. 获取对话配置（角色、计划模式）
            # 优先级：请求参数 > 会话配置 > 全局默认
            role_id = body.role_id
            plan_mode = body.plan_mode
            
            if role_id is None or plan_mode is None:
                # 检查会话配置
                conv_config = db.query(models.ConversationConfig).filter(
                    models.ConversationConfig.conversation_id == conversation.id
                ).first()
                
                if conv_config:
                    if role_id is None:
                        role_id = conv_config.role_id
                    if plan_mode is None and conv_config.plan_mode_enabled is not None:
                        plan_mode = bool(conv_config.plan_mode_enabled)
            
            if role_id is None or plan_mode is None:
                # 使用全局默认值
                global_settings = {}
                settings_records = db.query(models.GlobalSettings).all()
                for record in settings_records:
                    try:
                        value = json.loads(record.setting_value) if record.setting_value else None
                        global_settings[record.setting_key] = value
                    except:
                        global_settings[record.setting_key] = record.setting_value
                
                if role_id is None:
                    role_id = global_settings.get('default_role_id', 'software_engineer')
                if plan_mode is None:
                    plan_mode = global_settings.get('default_plan_mode', False)
            
            logger.info(f"Using role_id={role_id}, plan_mode={plan_mode}")
            
            # 4. 创建 AgentConfig
            agent_config = AgentConfig(
                provider=body.llm_config.provider if body.llm_config else None,
                model=body.llm_config.model if body.llm_config else None,
                collection=body.use_knowledge_base,
                message=body.message,
                role_preset_id=role_id,
                thread_id=str(conversation.id),  # 使用对话ID作为thread_id
                db_session=db,
                deep_reasoning=body.deep_reasoning or False
            )
            
            # 5. 判断是否使用计划模式
            should_plan = plan_mode_service.should_use_plan_mode(
                message=body.message,
                plan_mode_enabled=plan_mode
            )
            
            # 如果启用计划模式，先生成计划
            if should_plan:
                logger.info("Plan mode enabled, generating plan...")
                
                try:
                    # 创建LLM实例用于生成计划
                    llm = llm_factory.create_llm(
                        provider=agent_config.provider,
                        model_name=agent_config.model,
                        streaming=False
                    )
                    
                    # 生成计划
                    plan = await plan_mode_service.generate_plan(
                        message=body.message,
                        llm=llm
                    )
                    
                    # 输出计划
                    for step in plan.get("steps", []):
                        plan_chunk = message_formatter.format_plan_step(
                            step_number=step.get("step_id", 0) + 1,
                            description=step.get("description", ""),
                            status="pending"
                        )
                        yield f"data: {plan_chunk.model_dump_json()}\n\n"
                    
                    # 输出系统消息：开始执行计划
                    system_chunk = message_formatter.format_system(
                        "开始执行计划...",
                        level="info"
                    )
                    yield f"data: {system_chunk.model_dump_json()}\n\n"
                    
                except Exception as plan_error:
                    logger.error(f"Plan generation failed: {plan_error}", exc_info=True)
                    # 计划生成失败不应阻塞执行，发送警告后继续
                    warning_chunk = message_formatter.format_system(
                        f"计划生成失败：{str(plan_error)}，将直接执行任务",
                        level="warning"
                    )
                    yield f"data: {warning_chunk.model_dump_json()}\n\n"
            
            # 6. 调用 agent 流式生成
            collected_chunks = []
            final_response = ""
            thinking_content = ""
            intermediate_steps = []
            
            async for chunk in agent_service.chat_stream(
                message=body.message,
                config=agent_config
            ):
                chunk_type = chunk.get("type")
                
                if chunk_type == "thinking":
                    # 转换为新格式
                    thinking_text = chunk.get('data', {}).get('thinking', '')
                    thinking_content += thinking_text
                    thinking_chunk = message_formatter.format_thinking(thinking_text)
                    collected_chunks.append(thinking_chunk)
                    yield f"data: {thinking_chunk.model_dump_json()}\n\n"
                    
                elif chunk_type == "tool_call":
                    tool_info = chunk.get("data", {})
                    tool_chunk = message_formatter.format_tool_call(
                        tool_name=tool_info.get("tool_name", ""),
                        tool_input=tool_info.get("tool_input", {}),
                        status="running"
                    )
                    collected_chunks.append(tool_chunk)
                    yield f"data: {tool_chunk.model_dump_json()}\n\n"
                    intermediate_steps.append(tool_info)
                    
                elif chunk_type == "tool_result":
                    tool_data = chunk.get("data", {})
                    tool_chunk = message_formatter.format_tool_call(
                        tool_name=tool_data.get("tool_name", ""),
                        tool_input=tool_data.get("tool_input", {}),
                        tool_output=tool_data.get("tool_output", ""),
                        status="completed"
                    )
                    collected_chunks.append(tool_chunk)
                    yield f"data: {tool_chunk.model_dump_json()}\n\n"
                    
                elif chunk_type == "content":
                    content = chunk.get("data", {}).get("content", "")
                    final_response += content
                    text_chunk = message_formatter.format_text(content)
                    collected_chunks.append(text_chunk)
                    yield f"data: {text_chunk.model_dump_json()}\n\n"
                    
                elif chunk_type == "done":
                    # 保存助手回复
                    assistant_message = models.Message(
                        conversation_id=conversation.id,
                        role="assistant",
                        content=final_response,
                        chunks=json.dumps([c.model_dump() for c in collected_chunks]) if collected_chunks else None,
                        thinking=thinking_content if thinking_content else None,
                        intermediate_steps=json.dumps(intermediate_steps) if intermediate_steps else None
                    )
                    db.add(assistant_message)
                    db.commit()
                    
                    done_chunk = DoneChunk(
                        type=MessageType.DONE,
                        conversation_id=conversation.id,
                        message_id=assistant_message.id
                    )
                    yield f"data: {done_chunk.model_dump_json()}\n\n"
                    return
                    
                elif chunk_type == "error":
                    error_msg = chunk.get('data', {}).get('message', '') or chunk.get('message', '')
                    error_chunk = ErrorChunk(message=error_msg)
                    yield f"data: {error_chunk.model_dump_json()}\n\n"
                    return
                
                else:
                    # 未知消息类型，记录警告但不中断
                    logger.warning(f"Unknown chunk type in stream: {chunk_type}")
                    # 可选：发送系统消息通知前端
                    # system_chunk = message_formatter.format_system(
                    #     f"未知消息类型: {chunk_type}",
                    #     level="warning"
                    # )
                    # yield f"data: {system_chunk.model_dump_json()}\n\n"
                    
        except ValueError as ve:
            # 参数验证错误
            logger.error(f"Validation error in stream-v2: {ve}", exc_info=True)
            error_chunk = ErrorChunk(message=f"参数错误: {str(ve)}", code="VALIDATION_ERROR")
            yield f"data: {error_chunk.model_dump_json()}\n\n"
        except KeyError as ke:
            # 数据结构错误
            logger.error(f"Data structure error in stream-v2: {ke}", exc_info=True)
            error_chunk = ErrorChunk(message=f"数据结构错误: {str(ke)}", code="DATA_ERROR")
            yield f"data: {error_chunk.model_dump_json()}\n\n"
        except Exception as e:
            # 通用错误
            logger.error(f"Error in stream-v2: {e}", exc_info=True)
            error_chunk = ErrorChunk(message=f"服务器错误: {str(e)}", code="INTERNAL_ERROR")
            yield f"data: {error_chunk.model_dump_json()}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
