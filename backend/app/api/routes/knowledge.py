from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.db import models
from app.api.schemas import (
    KnowledgeBaseCreate, KnowledgeBaseResponse,
    DocumentCreate, DocumentResponse,
    SearchRequest, SearchResponse,
    SuccessResponse,
    RolePresetCreate, RolePresetResponse,
    RolePresetUpdate, RolePresetSearchRequest, RolePresetSearchResponse,
    PromptGenerateRequest, PromptGenerateResponse
)
from app.services.knowledge_service import knowledge_service
from app.services.llm_factory import llm_factory
from loguru import logger

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.post("/bases", response_model=KnowledgeBaseResponse)
def create_knowledge_base(kb: KnowledgeBaseCreate, db: Session = Depends(get_db)):
    """创建知识库"""
    try:
        # 检查名称是否已存在
        existing = db.query(models.KnowledgeBase).filter(
            models.KnowledgeBase.name == kb.name
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="知识库名称已存在")
        
        # 创建collection name
        collection_name = f"kb_{kb.name.lower().replace(' ', '_')}"
        
        # 在ChromaDB中创建collection
        success = knowledge_service.create_collection(collection_name)
        if not success:
            raise HTTPException(status_code=500, detail="创建向量库失败")
        
        # 在数据库中创建记录
        knowledge_base = models.KnowledgeBase(
            name=kb.name,
            description=kb.description,
            collection_name=collection_name
        )
        db.add(knowledge_base)
        db.commit()
        db.refresh(knowledge_base)
        
        return knowledge_base
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating knowledge base: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bases", response_model=List[KnowledgeBaseResponse])
def get_knowledge_bases(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """获取知识库列表"""
    bases = db.query(models.KnowledgeBase).order_by(
        models.KnowledgeBase.created_at.desc()
    ).offset(skip).limit(limit).all()
    return bases


@router.get("/bases/{kb_id}", response_model=KnowledgeBaseResponse)
def get_knowledge_base(kb_id: int, db: Session = Depends(get_db)):
    """获取知识库详情"""
    kb = db.query(models.KnowledgeBase).filter(
        models.KnowledgeBase.id == kb_id
    ).first()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return kb


@router.delete("/bases/{kb_id}", response_model=SuccessResponse)
def delete_knowledge_base(kb_id: int, db: Session = Depends(get_db)):
    """删除知识库"""
    kb = db.query(models.KnowledgeBase).filter(
        models.KnowledgeBase.id == kb_id
    ).first()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    # 删除ChromaDB中的collection
    knowledge_service.delete_collection(kb.collection_name)
    
    # 删除数据库记录
    db.delete(kb)
    db.commit()
    
    return SuccessResponse(success=True, message="知识库已删除")


@router.post("/bases/{kb_id}/documents", response_model=DocumentResponse)
def add_document(kb_id: int, doc: DocumentCreate, db: Session = Depends(get_db)):
    """添加文档到知识库"""
    try:
        # 获取知识库
        kb = db.query(models.KnowledgeBase).filter(
            models.KnowledgeBase.id == kb_id
        ).first()
        if not kb:
            raise HTTPException(status_code=404, detail="知识库不存在")
        
        # 添加到向量库
        vector_ids = knowledge_service.add_documents(
            collection_name=kb.collection_name,
            documents=[doc.content],
            metadatas=[{
                "title": doc.title,
                "source": doc.source or "",
                **(doc.metadata or {})
            }]
        )
        
        if not vector_ids:
            raise HTTPException(status_code=500, detail="添加文档到向量库失败")
        
        # 保存到数据库
        document = models.Document(
            knowledge_base_id=kb_id,
            title=doc.title,
            content=doc.content,
            source=doc.source,
            meta_info=doc.metadata,
            vector_id=vector_ids[0] if vector_ids else None
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bases/{kb_id}/documents", response_model=List[DocumentResponse])
def get_documents(kb_id: int, skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """获取知识库中的文档列表"""
    kb = db.query(models.KnowledgeBase).filter(
        models.KnowledgeBase.id == kb_id
    ).first()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    documents = db.query(models.Document).filter(
        models.Document.knowledge_base_id == kb_id
    ).order_by(models.Document.created_at.desc()).offset(skip).limit(limit).all()
    
    return documents


@router.post("/bases/{kb_id}/search", response_model=SearchResponse)
def search_knowledge(kb_id: int, request: SearchRequest, db: Session = Depends(get_db)):
    """搜索知识库"""
    try:
        # 获取知识库
        kb = db.query(models.KnowledgeBase).filter(
            models.KnowledgeBase.id == kb_id
        ).first()
        if not kb:
            raise HTTPException(status_code=404, detail="知识库不存在")
        
        # 搜索
        results = knowledge_service.search(
            collection_name=kb.collection_name,
            query=request.query,
            top_k=request.top_k
        )
        
        return SearchResponse(
            results=results,
            query=request.query
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 角色预设相关路由
@router.post("/prompts", response_model=SuccessResponse)
def create_role_preset(preset: RolePresetCreate, db: Session = Depends(get_db)):
    """创建角色预设"""
    try:
        preset_id = knowledge_service.add_role_preset(
            db_session=db,
            title=preset.title,
            prompt_content=preset.prompt_content,
            tags=preset.tags,
            category=preset.category
        )
        
        if preset_id:
            return SuccessResponse(success=True, message="角色预设已创建")
        else:
            raise HTTPException(status_code=500, detail="创建角色预设失败")
            
    except Exception as e:
        logger.error(f"Error creating role preset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/prompts/search", response_model=RolePresetSearchResponse)
def search_role_presets(request: RolePresetSearchRequest, db: Session = Depends(get_db)):
    """搜索角色预设"""
    try:
        results = knowledge_service.search_role_presets(
            db_session=db,
            query=request.query,
            category=request.category,
            top_k=request.top_k
        )
        
        return RolePresetSearchResponse(
            results=results,
            query=request.query
        )
        
    except Exception as e:
        logger.error(f"Error searching role presets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prompts", response_model=List[RolePresetResponse])
def get_all_role_presets(
    skip: int = 0, 
    limit: int = 100,
    category: Optional[str] = None,
    tags: Optional[str] = None,
    title: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取所有角色预设（支持条件查询）"""
    try:
        # 解析tags参数（逗号分隔的字符串）
        tags_list = None
        if tags:
            tags_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        
        # 如果有查询条件，使用过滤方法
        if category or tags_list or title:
            results = knowledge_service.filter_role_presets(
                db_session=db,
                category=category,
                tags=tags_list,
                title_query=title,
                skip=skip,
                limit=limit
            )
        else:
            results = knowledge_service.get_all_role_presets(db_session=db, skip=skip, limit=limit)
        return results
    except Exception as e:
        logger.error(f"Error getting role presets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/prompts/{preset_id}", response_model=SuccessResponse)
def update_role_preset(preset_id: str, preset: RolePresetUpdate, db: Session = Depends(get_db)):
    """更新角色预设"""
    try:
        success = knowledge_service.update_role_preset(
            db_session=db,
            preset_id=preset_id,
            title=preset.title,
            prompt_content=preset.prompt_content,
            tags=preset.tags,
            category=preset.category
        )
        
        if success:
            return SuccessResponse(success=True, message="角色预设已更新")
        else:
            raise HTTPException(status_code=404, detail="角色预设不存在或更新失败")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating role preset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/prompts/{preset_id}", response_model=SuccessResponse)
def delete_role_preset(preset_id: str, db: Session = Depends(get_db)):
    """删除角色预设"""
    try:
        success = knowledge_service.delete_role_preset(db_session=db, preset_id=preset_id)

        if success:
            return SuccessResponse(success=True, message="角色预设已删除")
        else:
            raise HTTPException(status_code=404, detail="角色预设不存在或删除失败")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting role preset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collections")
def list_collections():
    """获取所有知识库集合列表"""
    try:
        collections = knowledge_service.list_collections()
        return {"collections": collections}
    except Exception as e:
        logger.error(f"Error listing collections: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/prompts/generate", response_model=PromptGenerateResponse)
async def generate_prompt(request: PromptGenerateRequest):
    """生成提示词内容（不保存对话记录）"""
    try:
        # 获取LLM配置
        provider = None
        model = None
        if request.llm_config:
            provider = request.llm_config.provider
            model = request.llm_config.model
        
        # 创建LLM实例
        llm = llm_factory.create_llm(
            provider=provider,
            model_name=model,
            temperature=0.7
        )
        
        # 直接调用LLM生成内容
        logger.info(f"Generating prompt with provider={provider}, model={model}")
        response = await llm.ainvoke(request.prompt)
        
        # 提取内容 - LangChain的ChatModel返回AIMessage对象
        if hasattr(response, 'content'):
            content = response.content
        elif isinstance(response, str):
            content = response
        else:
            content = str(response)
        
        return PromptGenerateResponse(
            success=True,
            content=content.strip()
        )
        
    except Exception as e:
        logger.error(f"Error generating prompt: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return PromptGenerateResponse(
            success=False,
            content="",
            error=str(e)
        )

