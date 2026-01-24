"""百度联网搜索工具 - 使用百度千帆搜索API"""
from langchain_core.tools import Tool
from app.core.config import settings
from loguru import logger
from typing import Optional
import requests
import json


def create_baidu_tool() -> Optional[Tool]:
    """创建百度搜索工具"""
    # 检查是否启用百度搜索
    if not settings.BAIDU_ENABLED:
        logger.info("Baidu search is disabled")
        return None
    
    # 检查API Key
    if not settings.BAIDU_API_KEY:
        logger.warning("BAIDU_API_KEY not set, Baidu search tool will not be available")
        return None
    
    def baidu_search_wrapper(query: str) -> str:
        """百度搜索包装器 - 使用百度千帆搜索API"""
        try:
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
                "edition": "standard",  # 可选: "standard" 或 "advanced"
                "search_source": "baidu_search_v2",
                "search_recency_filter": "week"  # 可选: "day", "week", "month", "year", "all"
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
                logger.error(f"Response: {response.text}")
                return f"搜索请求失败，状态码: {response.status_code}。响应: {response.text[:200]}"
            
            # 解析响应
            try:
                result_data = response.json()
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Response text: {response.text[:500]}")
                return f"搜索响应解析失败: {str(e)}"
            
            # 提取搜索结果
            results = []
            
            # 根据API响应结构提取结果
            # 百度千帆API的响应结构可能是：
            # {
            #   "result": {
            #     "search_results": [...],
            #     "answer": "..."
            #   }
            # }
            # 或者直接是结果列表
            
            if 'result' in result_data:
                search_result = result_data['result']
                
                # 检查是否有搜索结果列表
                if 'search_results' in search_result:
                    search_results = search_result['search_results']
                elif 'results' in search_result:
                    search_results = search_result['results']
                elif isinstance(search_result, list):
                    search_results = search_result
                else:
                    # 尝试直接使用result
                    search_results = [search_result] if search_result else []
                
                # 格式化结果
                for idx, item in enumerate(search_results[:5], 1):  # 最多5条结果
                    try:
                        # 提取标题、URL和摘要
                        title = item.get('title', item.get('name', '无标题'))
                        url = item.get('url', item.get('link', item.get('href', '')))
                        abstract = item.get('abstract', item.get('snippet', item.get('description', '暂无摘要')))
                        
                        # 如果abstract是列表，取第一个
                        if isinstance(abstract, list) and abstract:
                            abstract = abstract[0]
                        
                        # 清理文本
                        title = str(title).strip()
                        url = str(url).strip()
                        abstract = str(abstract).strip()
                        
                        # 限制摘要长度
                        if len(abstract) > 200:
                            abstract = abstract[:200] + "..."
                        
                        if title:
                            results.append(
                                f"[{idx}] {title}\n"
                                f"来源: {url}\n"
                                f"摘要: {abstract}\n"
                            )
                    except Exception as e:
                        logger.warning(f"Error formatting search result item: {e}")
                        continue
            elif 'data' in result_data:
                # 如果响应结构不同，尝试data字段
                data = result_data['data']
                if isinstance(data, list):
                    search_results = data
                elif isinstance(data, dict) and 'results' in data:
                    search_results = data['results']
                elif isinstance(data, dict) and 'search_results' in data:
                    search_results = data['search_results']
                else:
                    search_results = []
                
                for idx, item in enumerate(search_results[:5], 1):
                    try:
                        title = item.get('title', item.get('name', '无标题'))
                        url = item.get('url', item.get('link', item.get('href', '')))
                        abstract = item.get('abstract', item.get('snippet', item.get('description', '暂无摘要')))
                        
                        if isinstance(abstract, list) and abstract:
                            abstract = abstract[0]
                        
                        title = str(title).strip()
                        url = str(url).strip()
                        abstract = str(abstract).strip()
                        
                        if len(abstract) > 200:
                            abstract = abstract[:200] + "..."
                        
                        if title:
                            results.append(
                                f"[{idx}] {title}\n"
                                f"来源: {url}\n"
                                f"摘要: {abstract}\n"
                            )
                    except Exception as e:
                        logger.warning(f"Error formatting result: {e}")
                        continue
            else:
                # 如果响应结构完全不同，记录日志并返回原始响应的一部分
                logger.warning(f"Unexpected response structure. Keys: {list(result_data.keys())}")
                logger.debug(f"Full response: {json.dumps(result_data, ensure_ascii=False, indent=2)[:2000]}")
            
            if not results:
                # 如果没有找到结果，返回原始响应的一部分用于调试
                logger.warning(f"No results found for query: {query}")
                logger.debug(f"Response structure: {json.dumps(result_data, ensure_ascii=False, indent=2)[:1000]}")
                # 尝试返回answer字段（如果有）
                if 'result' in result_data and 'answer' in result_data['result']:
                    answer = result_data['result']['answer']
                    return f"搜索关键词: {query}\n搜索结果摘要: {answer}"
                return f"搜索关键词: {query}\n未找到相关搜索结果。响应数据: {json.dumps(result_data, ensure_ascii=False)[:500]}"
            
            logger.info(f"Baidu search returned {len(results)} results")
            return "\n".join(results)
            
        except requests.exceptions.Timeout:
            logger.error("Baidu search timeout")
            return "搜索超时，请稍后重试。建议使用其他搜索工具（如Tavily）。"
        except requests.exceptions.RequestException as e:
            logger.error(f"Baidu search request error: {e}")
            return f"搜索请求出错: {str(e)}。建议使用其他搜索工具（如Tavily）。"
        except Exception as e:
            logger.error(f"Baidu search error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return f"搜索出错: {str(e)}。建议使用其他搜索工具（如Tavily）。"
    
    return Tool(
        name="baidu_web_search",
        func=baidu_search_wrapper,
        description=(
            "百度联网搜索工具。用于搜索中文信息、新闻、最新数据等。"
            "特别适合搜索中文内容和国内信息。"
            "使用百度千帆搜索API，返回高质量的搜索结果。"
            "输入应该是一个搜索查询字符串。"
            "返回包含标题、URL和内容摘要的搜索结果。"
        )
    )


# 创建工具实例
baidu_search_tool = create_baidu_tool()
