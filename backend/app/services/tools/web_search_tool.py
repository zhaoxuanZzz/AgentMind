"""统一的联网搜索工具 - 支持Tavily和百度搜索"""
from langchain_core.tools import Tool
from app.core.config import settings
from loguru import logger
from typing import Optional
import os
import requests
import json


def _tavily_search(query: str) -> str:
    """Tavily搜索实现"""
    try:
        if not settings.TAVILY_API_KEY:
            return "Tavily搜索不可用：未配置TAVILY_API_KEY"
        
        # 将API_KEY设置到环境变量
        os.environ["TAVILY_API_KEY"] = settings.TAVILY_API_KEY
        
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
        
        # 新版本和旧版本的调用方式不同
        if hasattr(tavily_search, 'invoke'):
            results = tavily_search.invoke({"query": query})
        else:
            results = tavily_search.run(query)
        
        if not results:
            return "未找到相关搜索结果"
        
        # 处理Tavily返回的数据结构
        # 新版本的langchain-tavily可能返回字典包含results字段
        search_results = []
        if isinstance(results, dict):
            # 如果是字典，提取results字段（如果存在）
            if 'results' in results:
                search_results = results['results']
            else:
                # 可能是单个结果，包装成列表
                logger.warning(f"Tavily returned dict without 'results' key. Keys: {list(results.keys())}")
                # 尝试查找其他可能的字段
                for key in ['data', 'items', 'search_results']:
                    if key in results and isinstance(results[key], list):
                        search_results = results[key]
                        break
                if not search_results:
                    # 如果没有找到数组字段，将整个字典当作单个结果
                    logger.info("Treating dict response as single result")
                    search_results = [results]
        elif isinstance(results, list):
            search_results = results
        else:
            logger.error(f"Tavily search returned unexpected type: {type(results)}")
            return f"搜索返回格式错误: {type(results)}"
        
        # 格式化结果，限制最多5条
        formatted_results = []
        max_results = min(len(search_results), 5)
        
        for idx in range(max_results):
            result = search_results[idx]
            
            if not isinstance(result, dict):
                logger.warning(f"Result {idx} is not a dict: {type(result)}")
                continue
            
            title = result.get("title", "无标题")
            url = result.get("url", "")
            # 优先使用content，其次snippet，再次description
            content = result.get("content", "") or result.get("snippet", "") or result.get("description", "")
            
            if not content:
                content = "暂无摘要"
            
            # 限制内容长度
            if len(content) > 300:
                content = content[:300] + "..."
            
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
        return f"Tavily搜索出错: {str(e)}"


def _baidu_search(query: str) -> str:
    """百度搜索实现"""
    try:
        if not settings.BAIDU_ENABLED:
            return "百度搜索不可用：未启用BAIDU_ENABLED"
        
        if not settings.BAIDU_API_KEY:
            return "百度搜索不可用：未配置BAIDU_API_KEY"
        
        logger.info(f"Baidu search query: {query}")
        
        # 使用百度千帆搜索API
        url = "https://qianfan.baidubce.com/v2/ai_search/web_search"
        
        # 构建请求体
        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": query
                }
            ],
            "edition": "standard",
            "search_source": "baidu_search_v2",
            "search_recency_filter": "week"
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {settings.BAIDU_API_KEY}'
        }
        
        # 发送POST请求
        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
            timeout=15
        )
        
        response.encoding = "utf-8"
        
        if response.status_code != 200:
            logger.error(f"Baidu search API failed with status code: {response.status_code}")
            logger.error(f"Response headers: {dict(response.headers)}")
            logger.error(f"Response text: {response.text[:1000]}")
            return f"搜索请求失败，状态码: {response.status_code}。响应: {response.text[:200]}"
        
        # 解析响应
        try:
            result_data = response.json()
            logger.debug(f"Baidu API response keys: {list(result_data.keys())}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response text (first 500 chars): {response.text[:500]}")
            return f"搜索响应解析失败: {str(e)}。响应内容: {response.text[:200]}"
        
        # 提取搜索结果 - 百度API返回的是references数组
        results = []
        
        # 百度API的实际响应结构：顶层有references字段（数组）
        # 结构: {"request_id": "...", "references": [...]}
        logger.debug(f"Response keys: {list(result_data.keys())}")
        
        # 优先查找references字段（百度API的标准结构）
        if 'references' in result_data:
            search_results = result_data['references']
            if isinstance(search_results, list):
                logger.info(f"Found {len(search_results)} references in response")
            else:
                logger.warning(f"references is not a list: {type(search_results)}")
                search_results = []
        elif 'result' in result_data:
            # 兼容其他可能的响应结构
            search_result = result_data['result']
            if isinstance(search_result, dict):
                if 'references' in search_result:
                    search_results = search_result['references']
                elif 'search_results' in search_result:
                    search_results = search_result['search_results']
                elif 'results' in search_result:
                    search_results = search_result['results']
                else:
                    search_results = []
            elif isinstance(search_result, list):
                search_results = search_result
            else:
                search_results = []
        elif 'data' in result_data:
            data = result_data['data']
            if isinstance(data, list):
                search_results = data
            elif isinstance(data, dict):
                search_results = data.get('references', data.get('results', data.get('search_results', [])))
            else:
                search_results = []
        else:
            logger.warning(f"Unexpected response structure. Keys: {list(result_data.keys())}")
            logger.debug(f"Full response structure: {json.dumps(result_data, ensure_ascii=False, indent=2)[:2000]}")
            search_results = []
        
        # 格式化结果
        # 确保search_results是列表
        if not isinstance(search_results, list):
            logger.error(f"search_results is not a list: {type(search_results)}")
            logger.error(f"search_results value: {str(search_results)[:500]}")
            search_results = []
        
        for idx, item in enumerate(search_results[:5], 1):
            try:
                # 确保item是字典
                if not isinstance(item, dict):
                    logger.warning(f"Item {idx} is not a dict: {type(item)}, value: {str(item)[:100]}")
                    continue
                
                # 百度API返回的字段：title, url, content, snippet
                # 根据实际数据结构：每个item包含 id, url, title, date, content, snippet 等字段
                title = item.get('title', '')
                url = item.get('url', '')
                # 优先使用content，其次snippet
                content = item.get('content', '')
                snippet = item.get('snippet', '')
                abstract = content if content else snippet
                
                # 如果都没有，尝试其他字段
                if not abstract:
                    abstract = item.get('description', '') or item.get('abstract', '') or '暂无摘要'
                
                # 处理abstract可能是列表的情况
                if isinstance(abstract, list):
                    abstract = abstract[0] if abstract else '暂无摘要'
                
                # 转换为字符串并清理
                title = str(title).strip() if title else '无标题'
                url = str(url).strip() if url else ''
                abstract = str(abstract).strip() if abstract else '暂无摘要'
                
                # 限制摘要长度（content可能很长）
                if len(abstract) > 300:
                    abstract = abstract[:300] + "..."
                
                # 即使title为空也显示结果（使用索引作为标题）
                if not title or title == '无标题':
                    title = f"结果 {idx}"
                
                results.append(
                    f"[{idx}] {title}\n"
                    f"来源: {url if url else '未知'}\n"
                    f"摘要: {abstract}\n"
                )
                logger.debug(f"Formatted result {idx}: title={title[:50]}, url={url[:50]}, abstract_len={len(abstract)}")
            except Exception as e:
                logger.warning(f"Error formatting search result item {idx}: {e}")
                logger.debug(f"Item data: {str(item)[:200]}")
                import traceback
                logger.debug(traceback.format_exc())
                continue
        
        if not results:
            logger.warning(f"No results found for query: {query}")
            logger.warning(f"Response keys: {list(result_data.keys())}")
            logger.debug(f"Full response: {json.dumps(result_data, ensure_ascii=False, indent=2)[:2000]}")
            # 尝试返回一些调试信息
            if 'references' in result_data:
                refs = result_data['references']
                logger.warning(f"Found {len(refs)} references but couldn't parse them")
                if refs and len(refs) > 0:
                    logger.warning(f"First reference keys: {list(refs[0].keys()) if isinstance(refs[0], dict) else 'not a dict'}")
            return f"搜索关键词: {query}\n未找到相关搜索结果。响应包含 {len(search_results)} 条原始结果，但解析失败。"
        
        logger.info(f"Baidu search returned {len(results)} results")
        return "\n".join(results)
        
    except requests.exceptions.Timeout:
        logger.error("Baidu search timeout")
        return "搜索超时，请稍后重试"
    except requests.exceptions.RequestException as e:
        logger.error(f"Baidu search request error: {e}")
        return f"搜索请求出错: {str(e)}"
    except Exception as e:
        logger.error(f"Baidu search error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return f"搜索出错: {str(e)}"


def create_web_search_tool() -> Optional[Tool]:
    """创建统一的联网搜索工具（从环境变量读取提供商配置）"""
    # 从配置读取搜索提供商
    provider = settings.SEARCH_PROVIDER.lower() if settings.SEARCH_PROVIDER else 'tavily'
    
    # 从配置读取搜索提供商
    provider = settings.SEARCH_PROVIDER.lower() if settings.SEARCH_PROVIDER else 'tavily'
    
    # 确定使用的搜索提供商
    if provider == 'baidu':
        provider = 'baidu'
        # 检查百度是否可用
        if not settings.BAIDU_ENABLED or not settings.BAIDU_API_KEY:
            logger.warning("Baidu search not available, falling back to Tavily")
            provider = 'tavily'
    else:
        provider = 'tavily'
        # 检查Tavily是否可用
        if not settings.TAVILY_API_KEY:
            logger.warning("Tavily search not available, falling back to Baidu")
            if settings.BAIDU_ENABLED and settings.BAIDU_API_KEY:
                provider = 'baidu'
            else:
                logger.error("No search provider available")
                return None
    
    def web_search_wrapper(query: str) -> str:
        """统一的联网搜索包装器"""
        if provider == 'baidu':
            return _baidu_search(query)
        else:
            return _tavily_search(query)
    
    provider_name = "百度" if provider == 'baidu' else "Tavily"
    logger.info(f"Creating web search tool with provider: {provider_name}")
    
    return Tool(
        name="web_search",  # 统一的工具名称
        func=web_search_wrapper,
        description=(
            "联网搜索工具。用于搜索实时信息、新闻、最新数据等。"
            f"当前使用{provider_name}搜索引擎。"
            "输入应该是一个搜索查询字符串。"
            "返回包含标题、URL和内容摘要的搜索结果。"
        )
    )


# 创建默认工具实例（使用Tavily）
web_search_tool = create_web_search_tool()

