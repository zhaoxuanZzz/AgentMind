"""提示词构建器 - 统一管理提示词模板"""
from typing import List, Optional
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain.tools import Tool
from loguru import logger


class PromptBuilder:
    """提示词构建器 - 统一管理提示词模板"""
    
    @staticmethod
    def build_react_prompt(
        tools: List[Tool],
        knowledge_prompts: str = "",
        history_context: str = ""
    ) -> PromptTemplate:
        """构建 ReAct Agent 提示词
        
        Args:
            tools: 工具列表
            knowledge_prompts: 角色预设提示词
            history_context: 历史对话上下文
        
        Returns:
            PromptTemplate 实例
        """
        # 获取所有工具名称
        tool_names_list = [tool.name for tool in tools]
        tool_names_str = ", ".join(tool_names_list)
        
        # 构建完整的提示词模板
        prompt_text = f"""你是一个智能AI助手，可以使用工具来帮助回答问题。{knowledge_prompts}{history_context}

你可以使用以下工具:
{{tools}}

工具说明:
- web_search: 联网搜索天气、新闻、实时信息（可在页面切换Tavily或百度）
- knowledge_base_search: 搜索内部知识库
- web_content_fetcher: 获取网页内容
- pdf_parser: 解析PDF文件
- calculator: 数学计算

使用以下格式回答:

Question: 用户的问题
Thought: 我应该怎么做？是否需要使用工具？
Action: 工具名称（从 {{tool_names}} 中选择）
Action Input: 工具的输入
Observation: 工具返回的结果
... (可以重复 Thought/Action/Action Input/Observation 多次)
Thought: 现在我知道最终答案了
Final Answer: 最终答案（用中文回答）

重要提示:
1. 当用户问天气、新闻等需要实时信息时，一定要使用 web_search 工具
2. Action Input 必须是简洁的搜索关键词
3. 最终答案要基于工具返回的真实信息
4. 请参考对话历史，理解用户的意图和上下文，保持对话的连贯性

开始！

Question: {{input}}
Thought: {{agent_scratchpad}}"""
        
        return PromptTemplate.from_template(prompt_text)
    
    @staticmethod
    def build_openai_functions_prompt(
        knowledge_prompts: str = ""
    ) -> ChatPromptTemplate:
        """构建 OpenAI Functions Agent 提示词
        
        Args:
            knowledge_prompts: 角色预设提示词
        
        Returns:
            ChatPromptTemplate 实例
        """
        system_prompt = """你是一个智能AI助手，拥有多种强大的工具来帮助用户解决问题。""" + knowledge_prompts + """

🔧 你可以使用的工具:
• knowledge_base_search - 从内部知识库检索信息（提示词模板、文档、历史记录）
• web_search - 联网搜索最新信息、新闻、实时数据、天气（可在页面切换Tavily或百度）
• web_content_fetcher - 获取指定URL的网页内容
• pdf_parser - 解析PDF文件内容
• calculator - 执行数学计算

💡 重要：当用户询问天气、新闻、股价等实时信息时，必须使用 web_search 工具！

请用中文回答所有问题，确保答案专业、详细、有条理。"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        return prompt
    
    @staticmethod
    def build_react_prompt_for_stream(
        tools: List[Tool],
        knowledge_prompts: str = ""
    ) -> PromptTemplate:
        """构建流式 ReAct Agent 提示词（简化版，不包含历史上下文）
        
        Args:
            tools: 工具列表
            knowledge_prompts: 角色预设提示词
        
        Returns:
            PromptTemplate 实例
        """
        # 获取所有工具名称
        tool_names_list = [tool.name for tool in tools]
        tool_names_str = ", ".join(tool_names_list)
        
        # 构建完整的提示词模板（必须包含 tool_names 和 tools 变量）
        react_template = """你是一个智能AI助手，可以使用工具来帮助回答问题。""" + knowledge_prompts + """

你可以使用以下工具:
{tools}

工具说明:
- web_search: 联网搜索天气、新闻、实时信息（可在页面切换Tavily或百度）
- knowledge_base_search: 搜索内部知识库
- web_content_fetcher: 获取网页内容
- pdf_parser: 解析PDF文件
- calculator: 数学计算

使用以下格式回答:

Question: 用户的问题
Thought: 我应该怎么做？是否需要使用工具？
Action: 工具名称（从 {tool_names} 中选择）
Action Input: 工具的输入
Observation: 工具返回的结果
... (可以重复 Thought/Action/Action Input/Observation 多次)
Thought: 现在我知道最终答案了
Final Answer: 最终答案（用中文回答）

重要提示:
1. 当用户问天气、新闻等需要实时信息时，一定要使用 web_search 工具
2. Action Input 必须是简洁的搜索关键词
3. 最终答案要基于工具返回的真实信息

开始！

Question: {input}
Thought: {agent_scratchpad}"""
        
        return PromptTemplate.from_template(react_template)
    
    @staticmethod
    def build_openai_functions_prompt_for_stream(
        knowledge_prompts: str = ""
    ) -> ChatPromptTemplate:
        """构建流式 OpenAI Functions Agent 提示词
        
        Args:
            knowledge_prompts: 角色预设提示词
        
        Returns:
            ChatPromptTemplate 实例
        """
        from langchain_core.messages import SystemMessage
        
        system_prompt = """你是一个智能AI助手，拥有多种强大的工具来帮助用户解决问题。""" + knowledge_prompts + """
        
🔧 你可以使用的工具:
• knowledge_base_search - 从内部知识库检索信息（提示词模板、文档、历史记录）
• web_search - 联网搜索最新信息、新闻、实时数据、天气（可在页面切换Tavily或百度）
• web_content_fetcher - 获取指定URL的网页内容
• pdf_parser - 解析PDF文件内容
• calculator - 执行数学计算

请根据用户的问题，选择合适的工具来获取信息，然后给出准确的答案。
"""
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        return prompt

