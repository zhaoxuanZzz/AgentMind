"""Tavily 联网搜索工具"""
from langchain_core.tools import Tool
from app.core.config import settings
from loguru import logger
from typing import Optional
import os


def create_tavily_tool() -> Optional[Tool]:
    """创建 Tavily 搜索工具"""
    if not settings.TAVILY_API_KEY:
        logger.warning("TAVILY_API_KEY not set, Tavily search tool will not be available")
        return None
    
    # 将API_KEY设置到环境变量
    os.environ["TAVILY_API_KEY"] = settings.TAVILY_API_KEY
    
    try:
        # 尝试使用新的 langchain-tavily 包
        try:
            from langchain_tavily import TavilySearch
            tavily_search = TavilySearch()
        except ImportError:
            # 降级使用旧版本
            from langchain_community.tools.tavily_search import TavilySearchResults
            tavily_search = TavilySearchResults(
                tavily_api_key=settings.TAVILY_API_KEY,
                max_results=5,
                search_depth="advanced",
                include_answer=True,
                include_raw_content=False
            )
        
        def tavily_search_wrapper(query: str) -> str:
            """联网搜索包装器"""
            try:
                # 新版本和旧版本的调用方式不同
                if hasattr(tavily_search, 'invoke'):
                    results = tavily_search.invoke({"query": query})
                else:
                    results = tavily_search.run(query)
                
                if not results:
                    return "未找到相关搜索结果"
                
                # 确保results是列表类型
                if not isinstance(results, list):
                    # 尝试转换为列表
                    if hasattr(results, '__iter__'):
                        results = list(results)
                    else:
                        logger.error(f"Tavily search returned unexpected type: {type(results)}")
                        return "搜索返回格式错误"
                
                # 格式化结果，限制最多5条
                formatted_results = []
                max_results = min(len(results), 5)
                
                for idx in range(max_results):
                    result = results[idx]
                    title = result.get("title", "无标题") if isinstance(result, dict) else str(result)
                    url = result.get("url", "") if isinstance(result, dict) else ""
                    content = result.get("content", "") if isinstance(result, dict) else ""
                    
                    # 如果结果本身是字符串，直接使用
                    if not isinstance(result, dict):
                        content = str(result) if not content else content
                    
                    formatted_results.append(
                        f"[{idx + 1}] {title}\n"
                        f"来源: {url}\n"
                        f"摘要: {content}\n"
                    )
                
                return "\n".join(formatted_results) if formatted_results else "未找到相关搜索结果"
                
            except Exception as e:
                logger.error(f"Tavily search error: {e}")
                import traceback
                logger.error(traceback.format_exc())
                return f"搜索出错: {str(e)}"
        
        return Tool(
            name="tavily_web_search",
            func=tavily_search_wrapper,
            description=(
                "联网搜索工具。用于搜索实时信息、新闻、最新数据等。"
                "输入应该是一个搜索查询字符串。"
                "返回包含标题、URL和内容摘要的搜索结果。"
            )
        )
    
    except Exception as e:
        logger.error(f"Error creating Tavily tool: {e}")
        return None


# 创建工具实例
tavily_search_tool = create_tavily_tool()

