"""网页抓取和 PDF 解析工具"""
from langchain_core.tools import Tool
from bs4 import BeautifulSoup
import requests
from pypdf import PdfReader
from io import BytesIO
from loguru import logger
from typing import Optional
import re


def create_web_scraper_tool() -> Tool:
    """创建网页数据抓取工具"""
    
    def scrape_web_content(url: str) -> str:
        """抓取网页内容"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 移除脚本和样式
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # 提取文本
            text = soup.get_text(separator='\n', strip=True)
            
            # 清理多余空白
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            clean_text = '\n'.join(lines)
            
            # 限制长度
            if len(clean_text) > 4000:
                clean_text = clean_text[:4000] + "...(内容过长已截断)"
            
            return f"网页内容提取成功:\n\n{clean_text}"
            
        except requests.exceptions.Timeout:
            return f"错误: 访问 {url} 超时"
        except requests.exceptions.HTTPError as e:
            return f"错误: HTTP 错误 {e.response.status_code}"
        except Exception as e:
            logger.error(f"Web scraping error: {e}")
            return f"抓取网页失败: {str(e)}"
    
    return Tool(
        name="web_content_fetcher",
        func=scrape_web_content,
        description=(
            "网页内容获取工具。用于从指定URL提取网页的文本内容。"
            "输入应该是一个完整的URL地址（以http://或https://开头）。"
            "返回网页的主要文本内容，自动过滤掉导航、脚本等无关内容。"
        )
    )


def create_pdf_parser_tool() -> Tool:
    """创建 PDF 解析工具"""
    
    def parse_pdf_content(url_or_path: str) -> str:
        """解析 PDF 内容"""
        try:
            # 判断是URL还是本地路径
            if url_or_path.startswith(('http://', 'https://')):
                # 从URL下载PDF
                response = requests.get(url_or_path, timeout=15)
                response.raise_for_status()
                pdf_file = BytesIO(response.content)
            else:
                # 本地文件
                pdf_file = url_or_path
            
            # 解析PDF
            reader = PdfReader(pdf_file)
            
            text_content = []
            page_count = len(reader.pages)
            
            # 限制解析的页数
            max_pages = min(page_count, 20)
            
            for i in range(max_pages):
                page = reader.pages[i]
                text = page.extract_text()
                if text.strip():
                    text_content.append(f"=== 第 {i+1} 页 ===\n{text}\n")
            
            full_text = '\n'.join(text_content)
            
            # 限制长度
            if len(full_text) > 5000:
                full_text = full_text[:5000] + "...(内容过长已截断)"
            
            summary = f"PDF 解析成功 (共 {page_count} 页，已解析 {max_pages} 页)\n\n{full_text}"
            return summary
            
        except requests.exceptions.Timeout:
            return "错误: PDF 下载超时"
        except Exception as e:
            logger.error(f"PDF parsing error: {e}")
            return f"PDF 解析失败: {str(e)}"
    
    return Tool(
        name="pdf_parser",
        func=parse_pdf_content,
        description=(
            "PDF 文档解析工具。用于提取PDF文件的文本内容。"
            "输入可以是PDF文件的URL地址或本地文件路径。"
            "返回PDF的文本内容，支持解析前20页。"
        )
    )


# 创建工具实例
web_scraper_tool = create_web_scraper_tool()
pdf_parser_tool = create_pdf_parser_tool()

