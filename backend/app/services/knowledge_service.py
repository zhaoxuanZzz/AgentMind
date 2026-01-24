import chromadb
from langchain_community.embeddings import HuggingFaceEmbeddings, DashScopeEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List, Dict, Optional
from app.core.config import settings
from loguru import logger
import uuid
import dashscope


class KnowledgeService:
    """知识库服务"""
    
    def __init__(self):
        # 延迟初始化
        self._chroma_client = None
        self._embeddings = None
        
        # 文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
        )
    
    @property
    def chroma_client(self):
        """延迟初始化ChromaDB客户端"""
        if self._chroma_client is None:
            try:
                self._chroma_client = chromadb.HttpClient(
                    host=settings.CHROMA_HOST,
                    port=settings.CHROMA_PORT
                )
                logger.info(f"Connected to ChromaDB at {settings.CHROMA_HOST}:{settings.CHROMA_PORT}")
            except Exception as e:
                logger.error(f"Failed to connect to ChromaDB: {e}")
                raise
        return self._chroma_client
    
    @property
    def embeddings(self):
        """延迟初始化Embedding模型"""
        if self._embeddings is None:
            if settings.USE_DASHSCOPE_EMBEDDING and settings.DASHSCOPE_API_KEY:
                # 使用阿里百炼向量化模型
                try:
                    dashscope.api_key = settings.DASHSCOPE_API_KEY
                    self._embeddings = DashScopeEmbeddings(
                        model=settings.DASHSCOPE_EMBEDDING_MODEL,
                        dashscope_api_key=settings.DASHSCOPE_API_KEY
                    )
                    logger.info(f"Loaded DashScope embedding model: {settings.DASHSCOPE_EMBEDDING_MODEL}")
                except Exception as e:
                    logger.warning(f"Failed to load DashScope embeddings, falling back to HuggingFace: {e}")
                    self._embeddings = HuggingFaceEmbeddings(
                        model_name=settings.EMBEDDING_MODEL,
                        model_kwargs={'device': 'cpu'}
                    )
            else:
                # 使用HuggingFace模型
                self._embeddings = HuggingFaceEmbeddings(
                    model_name=settings.EMBEDDING_MODEL,
                    model_kwargs={'device': 'cpu'}
                )
                logger.info(f"Loaded embedding model: {settings.EMBEDDING_MODEL}")
        return self._embeddings
    
    def create_collection(self, collection_name: str) -> bool:
        """创建知识库集合"""
        try:
            self.chroma_client.get_or_create_collection(
                name=collection_name,
                metadata={"description": f"Collection for {collection_name}"}
            )
            logger.info(f"Created collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            return False
    
    def add_documents(
        self, 
        collection_name: str, 
        documents: List[str], 
        metadatas: Optional[List[Dict]] = None
    ) -> List[str]:
        """添加文档到知识库"""
        try:
            collection = self.chroma_client.get_collection(collection_name)
            
            # 分割文档
            all_chunks = []
            all_metadatas = []
            doc_ids = []
            
            for idx, doc in enumerate(documents):
                chunks = self.text_splitter.split_text(doc)
                all_chunks.extend(chunks)
                
                # 为每个chunk创建metadata
                base_metadata = metadatas[idx] if metadatas and idx < len(metadatas) else {}
                for chunk_idx in range(len(chunks)):
                    chunk_metadata = base_metadata.copy()
                    chunk_metadata.update({
                        "doc_index": idx,
                        "chunk_index": chunk_idx,
                        "total_chunks": len(chunks)
                    })
                    all_metadatas.append(chunk_metadata)
                    doc_ids.append(str(uuid.uuid4()))
            
            # 生成embeddings并添加到ChromaDB
            embeddings = self.embeddings.embed_documents(all_chunks)
            
            collection.add(
                embeddings=embeddings,
                documents=all_chunks,
                metadatas=all_metadatas,
                ids=doc_ids
            )
            
            logger.info(f"Added {len(all_chunks)} chunks to {collection_name}")
            return doc_ids
            
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            return []
    
    def search(
        self, 
        collection_name: str, 
        query: str, 
        top_k: int = 5
    ) -> List[Dict]:
        """检索相关文档"""
        try:
            collection = self.chroma_client.get_collection(collection_name)
            
            # 生成查询embedding
            query_embedding = self.embeddings.embed_query(query)
            
            # 查询
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
            
            # 格式化结果
            formatted_results = []
            if results and results['documents']:
                for i in range(len(results['documents'][0])):
                    formatted_results.append({
                        "content": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                        "score": 1 - results['distances'][0][i] if results['distances'] else 0  # 转换为相似度分数
                    })
            
            logger.info(f"Found {len(formatted_results)} results for query: {query}")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    def delete_collection(self, collection_name: str) -> bool:
        """删除知识库集合"""
        try:
            self.chroma_client.delete_collection(collection_name)
            logger.info(f"Deleted collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
            return False
    
    def add_role_preset(
        self, 
        db_session,
        title: str,
        prompt_content: str,
        tags: List[str] = None,
        category: str = "general"
    ) -> str:
        """添加角色预设：先保存到PostgreSQL，再存储向量到ChromaDB"""
        try:
            from app.db import models
            
            # 1. 生成唯一ID
            preset_id = str(uuid.uuid4())
            
            # 2. 保存到PostgreSQL
            role_preset = models.RolePreset(
                preset_id=preset_id,
                title=title,
                prompt_content=prompt_content,
                category=category,
                tags=tags if tags else []
            )
            db_session.add(role_preset)
            db_session.commit()
            db_session.refresh(role_preset)
            
            # 3. 存储向量到ChromaDB（分割文档）
            collection_name = "prompts"
            self.create_collection(collection_name)
            collection = self.chroma_client.get_collection(collection_name)
            
            # 分割文档
            chunks = self.text_splitter.split_text(prompt_content)
            
            # 为每个chunk创建metadata，包含preset_id用于关联
            chunk_metadatas = []
            chunk_ids = []
            for chunk_idx, chunk in enumerate(chunks):
                chunk_metadata = {
                    "preset_id": preset_id,  # 关联到PostgreSQL的preset_id
                    "title": title,
                    "category": category,
                    "tags": ",".join(tags) if tags else "",
                    "chunk_index": chunk_idx,
                    "total_chunks": len(chunks)
                }
                chunk_metadatas.append(chunk_metadata)
                chunk_ids.append(f"{preset_id}_chunk_{chunk_idx}")
            
            # 生成embeddings并添加到ChromaDB
            if chunks:
                embeddings = self.embeddings.embed_documents(chunks)
                collection.add(
                    embeddings=embeddings,
                    documents=chunks,
                    metadatas=chunk_metadatas,
                    ids=chunk_ids
                )
            
            logger.info(f"Added role preset: {title} (preset_id: {preset_id}, {len(chunks)} chunks)")
            return preset_id
                
        except Exception as e:
            db_session.rollback()
            logger.error(f"Error adding role preset: {e}")
            return ""
    
    def search_role_presets(
        self,
        db_session,
        query: str,
        category: Optional[str] = None,
        top_k: int = 3
    ) -> List[Dict]:
        """搜索角色预设：使用ChromaDB语义搜索，从PostgreSQL获取完整数据"""
        try:
            from app.db import models
            
            # 如果query为空或只包含空白字符，直接返回所有预设
            if not query or not query.strip():
                logger.info("Query is empty, returning all role presets")
                return self.get_all_role_presets(db_session=db_session, skip=0, limit=top_k)
            
            collection_name = "prompts"
            try:
                collection = self.chroma_client.get_collection(collection_name)
            except Exception:
                logger.info(f"Collection {collection_name} does not exist, returning empty list")
                return []
            
            # 使用语义搜索
            query_embedding = self.embeddings.embed_query(query)
            search_results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k * 3,  # 获取更多结果以便过滤
                include=["documents", "metadatas", "ids", "distances"]
            )
            
            # 收集唯一的preset_id（兼容旧的card_id）
            preset_ids_seen = set()
            filtered_results = []
            
            if search_results and search_results['documents']:
                for i in range(len(search_results['documents'][0])):
                    metadata = search_results['metadatas'][0][i] if search_results['metadatas'] else {}
                    preset_id = metadata.get('preset_id') or metadata.get('card_id')  # 兼容旧数据
                    
                    if not preset_id or preset_id in preset_ids_seen:
                        continue
                    
                    # 如果指定了category，过滤
                    if category and metadata.get('category') != category:
                        continue
                    
                    # 从PostgreSQL获取完整数据
                    preset = db_session.query(models.RolePreset).filter(
                        models.RolePreset.preset_id == preset_id
                    ).first()
                    
                    if preset:
                        preset_ids_seen.add(preset_id)
                        filtered_results.append({
                            "id": preset.preset_id,
                            "title": preset.title,
                            "content": preset.prompt_content,  # 使用完整内容
                            "category": preset.category,
                            "tags": preset.tags if preset.tags else [],
                            "score": 1 - search_results['distances'][0][i] if search_results.get('distances') and search_results['distances'][0] else 0
                        })
                    
                    if len(filtered_results) >= top_k:
                        break
            
            return filtered_results
            
        except Exception as e:
            logger.error(f"Error searching role presets: {e}")
            return []
    
    def get_all_role_presets(self, db_session, skip: int = 0, limit: int = 100) -> List[Dict]:
        """从PostgreSQL获取所有角色预设"""
        try:
            from app.db import models
            from sqlalchemy.orm import Query
            
            # 从PostgreSQL查询
            query: Query = db_session.query(models.RolePreset)
            total = query.count()
            presets = query.order_by(models.RolePreset.created_at.desc()).offset(skip).limit(limit).all()
            
            # 格式化结果
            formatted_results = []
            for preset in presets:
                formatted_results.append({
                    "id": preset.preset_id,  # 使用preset_id作为唯一标识
                    "title": preset.title,
                    "content": preset.prompt_content,
                    "category": preset.category,
                    "tags": preset.tags if preset.tags else [],
                    "score": 1.0,
                    "created_at": preset.created_at.isoformat() if preset.created_at else None,
                    "updated_at": preset.updated_at.isoformat() if preset.updated_at else None
                })
            
            logger.info(f"Retrieved {len(formatted_results)}/{total} role presets from PostgreSQL")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error getting all role presets: {e}")
            return []
    
    def update_role_preset(
        self,
        db_session,
        preset_id: str,
        title: Optional[str] = None,
        prompt_content: Optional[str] = None,
        tags: Optional[List[str]] = None,
        category: Optional[str] = None
    ) -> bool:
        """更新角色预设：更新PostgreSQL和ChromaDB"""
        try:
            from app.db import models
            
            # 1. 从PostgreSQL获取现有预设
            preset = db_session.query(models.RolePreset).filter(models.RolePreset.preset_id == preset_id).first()
            if not preset:
                logger.error(f"Role preset with preset_id {preset_id} not found in PostgreSQL")
                return False
            
            # 2. 更新PostgreSQL
            if title is not None:
                preset.title = title
            if prompt_content is not None:
                preset.prompt_content = prompt_content
            if tags is not None:
                preset.tags = tags
            if category is not None:
                preset.category = category
            
            db_session.commit()
            db_session.refresh(preset)
            
            # 3. 更新ChromaDB：删除旧chunks，添加新chunks
            collection_name = "prompts"
            try:
                collection = self.chroma_client.get_collection(collection_name)
                
                # 删除该preset_id的所有chunks（兼容旧的card_id）
                all_results = collection.get(include=["metadatas", "ids"])
                chunk_ids_to_delete = []
                if all_results and all_results.get('metadatas'):
                    for i, metadata in enumerate(all_results['metadatas']):
                        if metadata.get('preset_id') == preset_id or metadata.get('card_id') == preset_id:
                            chunk_ids_to_delete.append(all_results['ids'][i])
                
                if chunk_ids_to_delete:
                    collection.delete(ids=chunk_ids_to_delete)
                
                # 如果内容改变，重新分割并添加
                if prompt_content is not None:
                    chunks = self.text_splitter.split_text(preset.prompt_content)
                    chunk_metadatas = []
                    chunk_ids = []
                    for chunk_idx, chunk in enumerate(chunks):
                        chunk_metadata = {
                            "preset_id": preset_id,
                            "title": preset.title,
                            "category": preset.category,
                            "tags": ",".join(preset.tags) if preset.tags else "",
                            "chunk_index": chunk_idx,
                            "total_chunks": len(chunks)
                        }
                        chunk_metadatas.append(chunk_metadata)
                        chunk_ids.append(f"{preset_id}_chunk_{chunk_idx}")
                    
                    if chunks:
                        embeddings = self.embeddings.embed_documents(chunks)
                        collection.add(
                            embeddings=embeddings,
                            documents=chunks,
                            metadatas=chunk_metadatas,
                            ids=chunk_ids
                        )
                
            except Exception as e:
                logger.warning(f"Error updating ChromaDB, but PostgreSQL updated: {e}")
            
            logger.info(f"Updated role preset: {preset_id}")
            return True
            
        except Exception as e:
            db_session.rollback()
            logger.error(f"Error updating role preset: {e}")
            return False
    
    def delete_role_preset(self, db_session, preset_id: str) -> bool:
        """删除角色预设：从PostgreSQL和ChromaDB删除"""
        try:
            from app.db import models
            
            # 1. 从PostgreSQL删除
            preset = db_session.query(models.RolePreset).filter(models.RolePreset.preset_id == preset_id).first()
            if not preset:
                logger.error(f"Role preset with preset_id {preset_id} not found in PostgreSQL")
                return False
            
            db_session.delete(preset)
            db_session.commit()
            
            # 2. 从ChromaDB删除所有相关的chunks（兼容旧的card_id）
            collection_name = "prompts"
            try:
                collection = self.chroma_client.get_collection(collection_name)
                
                # 查询所有包含该preset_id的chunks
                all_results = collection.get(include=["metadatas", "ids"])
                chunk_ids_to_delete = []
                if all_results and all_results.get('metadatas'):
                    for i, metadata in enumerate(all_results['metadatas']):
                        if metadata.get('preset_id') == preset_id or metadata.get('card_id') == preset_id:
                            chunk_ids_to_delete.append(all_results['ids'][i])
                
                if chunk_ids_to_delete:
                    collection.delete(ids=chunk_ids_to_delete)
                    logger.info(f"Deleted {len(chunk_ids_to_delete)} chunks from ChromaDB")
                
            except Exception as e:
                logger.warning(f"Error deleting from ChromaDB, but PostgreSQL deleted: {e}")
            
            logger.info(f"Deleted role preset: {preset_id}")
            return True
            
        except Exception as e:
            db_session.rollback()
            logger.error(f"Error deleting role preset: {e}")
            return False
    
    def filter_role_presets(
        self,
        db_session,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        title_query: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict]:
        """条件查询角色预设（从PostgreSQL）"""
        try:
            from app.db import models
            from sqlalchemy.orm import Query
            from sqlalchemy import or_
            
            # 构建查询
            query: Query = db_session.query(models.RolePreset)
            
            # 按分类过滤
            if category:
                query = query.filter(models.RolePreset.category == category)
            
            # 按标题查询
            if title_query:
                query = query.filter(models.RolePreset.title.ilike(f"%{title_query}%"))
            
            # 按标签过滤（JSON数组包含）
            if tags:
                # PostgreSQL JSON数组查询：使用JSONB @> 操作符
                # 检查tags JSON数组是否包含任何一个指定的标签
                for tag in tags:
                    # 使用contains方法检查JSON数组是否包含该标签
                    query = query.filter(models.RolePreset.tags.contains([tag]))
            
            # 获取总数
            total = query.count()
            
            # 分页查询
            presets = query.order_by(models.RolePreset.created_at.desc()).offset(skip).limit(limit).all()
            
            # 格式化结果
            formatted_results = []
            for preset in presets:
                formatted_results.append({
                    "id": preset.preset_id,
                    "title": preset.title,
                    "content": preset.prompt_content,
                    "category": preset.category,
                    "tags": preset.tags if preset.tags else [],
                    "score": 1.0,
                    "created_at": preset.created_at.isoformat() if preset.created_at else None,
                    "updated_at": preset.updated_at.isoformat() if preset.updated_at else None
                })
            
            logger.info(f"Filtered {len(formatted_results)}/{total} role presets from PostgreSQL")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error filtering role presets: {e}")
            return []
    
    def list_collections(self) -> List[str]:
        """列出所有知识库集合"""
        try:
            collections = self.chroma_client.list_collections()
            return [c.name for c in collections]
        except Exception as e:
            logger.error(f"Error listing collections: {e}")
            return []


# 全局实例
knowledge_service = KnowledgeService()

