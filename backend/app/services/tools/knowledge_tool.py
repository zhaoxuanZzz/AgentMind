"""知识库检索工具"""
from langchain.tools import Tool
from app.services.knowledge_service import knowledge_service
from loguru import logger


def create_knowledge_retrieval_tool() -> Tool:
    """创建知识库检索工具"""
    
    def search_knowledge_base(query: str) -> str:
        """搜索知识库"""
        try:
            # 搜索多个集合
            collections_to_search = ["prompts", "default", "documents"]
            all_results = []
            
            for collection_name in collections_to_search:
                try:
                    results = knowledge_service.search(collection_name, query, top_k=2)
                    if results:
                        for r in results:
                            r['source_collection'] = collection_name
                        all_results.extend(results)
                except Exception as e:
                    logger.debug(f"Collection {collection_name} not found or error: {e}")
                    continue
            
            if not all_results:
                return "未在知识库中找到相关信息"
            
            # 按相似度排序
            all_results.sort(key=lambda x: x.get('score', 0), reverse=True)
            
            # 取top 5
            top_results = all_results[:5]
            
            # 格式化结果
            formatted = []
            for i, r in enumerate(top_results, 1):
                source = r.get('source_collection', 'unknown')
                score = r.get('score', 0)
                content = r.get('content', '')
                metadata = r.get('metadata', {})
                
                formatted.append(
                    f"[结果 {i}] (来源: {source}, 相似度: {score:.2f})\n"
                    f"{content}"
                )
                
                # 如果有标题或其他metadata，也显示
                if metadata.get('title'):
                    formatted[-1] = f"[结果 {i}] 标题: {metadata['title']}\n" + formatted[-1]
            
            return "\n\n".join(formatted)
            
        except Exception as e:
            logger.error(f"Knowledge retrieval error: {e}")
            return f"知识库检索出错: {str(e)}"
    
    return Tool(
        name="knowledge_base_search",
        func=search_knowledge_base,
        description=(
            "知识库检索工具。用于从内部知识库中检索相关信息，包括提示词模板、文档、历史记录等。"
            "输入应该是一个检索查询字符串。"
            "返回最相关的知识库内容，包括相似度分数和来源信息。"
        )
    )


# 创建工具实例
knowledge_retrieval_tool = create_knowledge_retrieval_tool()

