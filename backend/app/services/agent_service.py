from langchain.agents import create_agent
from langchain_core.tools import Tool
from langchain_core.messages import HumanMessage, AIMessage
from typing import List, Dict, Optional, AsyncIterator, Any
import asyncio
from datetime import datetime
from app.core.config import settings
from app.services.knowledge_service import knowledge_service
from app.services.llm_factory import llm_factory
from app.services.agent import RolePresetRetriever
from app.services.memory import MemoryManager
from app.services.streaming import StreamCallbackHandler
from app.services.tools import (
    create_web_search_tool,
    web_scraper_tool,
    pdf_parser_tool,
    knowledge_retrieval_tool
)
from app.api.schemas import AgentConfig
from loguru import logger


class AgentService:
    """Agent服务 - 处理问答和推理规划"""
    
    def __init__(self):
        # 初始化默认LLM
        self.llm = llm_factory.create_llm()
    
    def _get_llm(self, provider: Optional[str] = None, model: Optional[str] = None, streaming: bool = False):
        """获取LLM实例"""
        if provider or model:
            # 直接传递streaming参数给factory
            llm = llm_factory.create_llm(provider=provider, model_name=model, streaming=streaming)
            return llm
        # 对于默认LLM，如果需要streaming，需要重新创建
        if streaming:
            return llm_factory.create_llm(streaming=True)
        return self.llm
        
    def _create_tools(self, search_provider: Optional[str] = None) -> List[Tool]:
        """创建Agent可用的工具
        
        Args:
            search_provider: 搜索提供商，可选值: 'tavily', 'baidu', None(默认使用tavily)
        """
        
        def calculator_tool(expression: str) -> str:
            """计算数学表达式"""
            try:
                # 安全的数学计算
                import math
                allowed_names = {
                    k: v for k, v in math.__dict__.items() 
                    if not k.startswith("__")
                }
                result = eval(expression, {"__builtins__": {}}, allowed_names)
                return f"计算结果: {result}"
            except Exception as e:
                return f"计算错误: {str(e)}"
        
        tools = [
            Tool(
                name="calculator",
                func=calculator_tool,
                description="执行数学计算。输入应该是一个数学表达式，例如: '2+2' 或 '10*5' 或 'sqrt(16)'。"
            )
        ]
        
        # 添加知识库检索工具
        if knowledge_retrieval_tool:
            tools.append(knowledge_retrieval_tool)
        
        # 创建统一的联网搜索工具（根据search_provider选择Tavily或百度）
        web_search = create_web_search_tool(search_provider=search_provider)
        if web_search:
            tools.append(web_search)
            logger.info(f"Added web search tool (provider: {search_provider or 'tavily'})")
        else:
            logger.warning("Web search tool not available")
        
        # 添加网页抓取工具
        if web_scraper_tool:
            tools.append(web_scraper_tool)
        
        # 添加PDF解析工具
        if pdf_parser_tool:
            tools.append(pdf_parser_tool)
        
        logger.info(f"Created {len(tools)} tools for agent (search provider: {search_provider or 'tavily'})")
        return tools
    
    def create_agent(
        self, 
        config: Optional[AgentConfig] = None,
        **kwargs  # 保持向后兼容，支持旧的方式传参
    ) -> Any:
        """创建Agent
        
        Args:
            config: Agent配置对象（推荐使用）
            **kwargs: 向后兼容的旧参数方式（如果提供了config，kwargs将被忽略）
                - memory: 对话内存
                - provider: LLM提供商
                - model: 模型名称
                - collection: 知识库集合名称
                - message: 用户消息（用于检索角色预设）
                - search_provider: 搜索提供商，可选值: 'tavily', 'baidu', None(默认使用tavily)
                - role_preset_id: 指定的角色预设ID
                - db_session: 数据库会话
                - llm_instance: 可选的LLM实例（如果提供则直接使用）
        
        Returns:
            Agent 实例（可直接调用 invoke/ainvoke）
        """
        # 如果提供了kwargs但没有config，从kwargs创建config（向后兼容）
        if config is None and kwargs:
            config = AgentConfig(**kwargs)
        elif config is None:
            config = AgentConfig()
        
        # 获取LLM实例（如果未提供）
        if config.llm_instance:
            llm = config.llm_instance
        else:
            llm = self._get_llm(config.provider, config.model, streaming=False)
        
        # 创建工具列表（根据search_provider选择搜索工具）
        tools = self._create_tools(search_provider=config.search_provider)
        
        # 获取角色预设提示词
        role_prompts = RolePresetRetriever.retrieve_prompts(
            role_preset_id=config.role_preset_id,
            collection=config.collection,
            message=config.message,
            db_session=config.db_session,
            top_k=3
        )
        
        # 获取历史对话上下文
        history_context = MemoryManager.get_history_context(config.memory, max_messages=20) if config.memory else ""
        
        # 构建系统提示词
        system_prompt = f"""你是一个智能AI助手，可以使用工具来帮助回答问题。{role_prompts}{history_context}

🔧 你可以使用的工具:
• knowledge_base_search - 从内部知识库检索信息（提示词模板、文档、历史记录）
• web_search - 联网搜索最新信息、新闻、实时数据、天气（可在页面切换Tavily或百度）
• web_content_fetcher - 获取指定URL的网页内容
• pdf_parser - 解析PDF文件内容
• calculator - 执行数学计算

💡 重要提示:
1. 当用户询问天气、新闻、股价等实时信息时，必须使用 web_search 工具！
2. 请用中文回答所有问题，确保答案专业、详细、有条理。
3. 请参考对话历史，理解用户的意图和上下文，保持对话的连贯性。"""
        
        # 获取 LangGraph 的存储实例
        checkpointer = MemoryManager.get_short_term_saver()  # 短期记忆
        store = MemoryManager.get_long_term_store()  # 长期记忆
        
        # 使用统一的 create_agent API，集成 LangGraph 的存储机制
        logger.info(f"Creating agent with {len(tools)} tools (provider: {config.provider or settings.LLM_PROVIDER})")
        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=system_prompt,
            checkpointer=checkpointer,  # 使用 InMemorySaver 管理短期记忆
            store=store  # 使用 InMemoryStore 管理长期记忆
        )
        
        return agent
    
    async def create_async_agent(
        self,
        config: Optional[AgentConfig] = None,
        **kwargs  # 保持向后兼容，支持旧的方式传参
    ) -> Any:
        """创建异步Agent（用于 ainvoke 调用）
        
        Args:
            config: Agent配置对象（推荐使用）
            **kwargs: 向后兼容的旧参数方式（如果提供了config，kwargs将被忽略）
                - provider: LLM提供商
                - model: 模型名称
                - collection: 知识库集合名称
                - message: 用户消息（用于检索角色预设）
                - search_provider: 搜索提供商，可选值: 'tavily', 'baidu', None(默认使用tavily)
                - role_preset_id: 指定的角色预设ID
                - db_session: 数据库会话
                - llm_instance: 可选的LLM实例（如果提供则直接使用）
        
        Returns:
            Agent 实例（可直接调用 ainvoke）
        """
        # 如果提供了kwargs但没有config，从kwargs创建config（向后兼容）
        if config is None and kwargs:
            config = AgentConfig(**kwargs)
        elif config is None:
            config = AgentConfig()
        
        # 获取LLM实例（如果未提供）
        if config.llm_instance:
            llm = config.llm_instance
        else:
            llm = self._get_llm(config.provider, config.model, streaming=False)
        
        # 创建工具列表（根据search_provider选择搜索工具）
        tools = self._create_tools(search_provider=config.search_provider)
        
        # 获取角色预设提示词
        role_prompts = RolePresetRetriever.retrieve_prompts(
            role_preset_id=config.role_preset_id,
            collection=config.collection,
            message=config.message,
            db_session=config.db_session,
            top_k=3
        )
        
        # 构建系统提示词
        system_prompt = f"""你是一个智能AI助手，可以使用工具来帮助回答问题。{role_prompts}

🔧 你可以使用的工具:
• knowledge_base_search - 从内部知识库检索信息（提示词模板、文档、历史记录）
• web_search - 联网搜索最新信息、新闻、实时数据、天气（可在页面切换Tavily或百度）
• web_content_fetcher - 获取指定URL的网页内容
• pdf_parser - 解析PDF文件内容
• calculator - 执行数学计算

💡 重要提示:
1. 当用户询问天气、新闻、股价等实时信息时，必须使用 web_search 工具！
2. 请用中文回答所有问题，确保答案专业、详细、有条理。
3. 请参考对话历史，理解用户的意图和上下文，保持对话的连贯性。"""
        
        # 获取 LangGraph 的异步存储实例
        checkpointer = await MemoryManager.get_short_term_saver()  # 短期记忆
        store = MemoryManager.get_long_term_store()  # 长期记忆
        
        # 使用统一的 create_agent API，集成 LangGraph 的存储机制
        logger.info(f"Creating async agent with {len(tools)} tools (provider: {config.provider or settings.LLM_PROVIDER})")
        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=system_prompt,
            checkpointer=checkpointer,  # 使用 AsyncPostgresSaver 管理短期记忆
            store=store  # 使用 InMemoryStore 管理长期记忆
        )
        
        return agent
    
    def _format_intermediate_steps(self, intermediate_steps: List) -> List[Dict]:
        """格式化中间步骤，使其更易读"""
        formatted_steps = []
        
        for step in intermediate_steps:
            try:
                # intermediate_steps 格式: [(AgentAction, result), ...]
                if isinstance(step, tuple) and len(step) == 2:
                    action, result = step
                    
                    # 提取工具名称和输入
                    tool_name = getattr(action, 'tool', 'unknown')
                    tool_input = getattr(action, 'tool_input', '')
                    log = getattr(action, 'log', '')
                    
                    # 格式化结果（限制长度）
                    result_str = str(result)
                    if len(result_str) > 500:
                        result_str = result_str[:500] + "...(内容过长已截断)"
                    
                    formatted_steps.append({
                        "tool": tool_name,
                        "input": tool_input,
                        "output": result_str,
                        "log": log
                    })
            except Exception as e:
                logger.warning(f"Error formatting step: {e}")
                continue
        
        return formatted_steps
    
    
    async def chat_stream(
        self,
        message: str,
        config: Optional[AgentConfig] = None,
        **kwargs  # 保持向后兼容，支持旧的方式传参
    ) -> AsyncIterator[Dict]:
        """流式处理对话
        
        Args:
            message: 用户消息
            config: Agent配置对象（推荐使用）
            **kwargs: 向后兼容的旧参数方式（如果提供了config，kwargs将被忽略）
                - history: 历史对话记录
                - collection: 知识库集合名称
                - provider: LLM提供商
                - model: 模型名称
                - search_provider: 搜索提供商
                - role_preset_id: 指定的角色预设ID
                - deep_reasoning: 深度推理模式
                - db_session: 数据库会话
                - thread_id: 线程ID，用于标识不同的会话（用于 LangGraph checkpoint）
        """
        # 如果提供了kwargs但没有config，从kwargs创建config（向后兼容）
        if config is None and kwargs:
            config = AgentConfig(**kwargs)
        elif config is None:
            config = AgentConfig()
        
        try:
            # 创建memory并加载历史对话
            #memory = MemoryManager.create_memory(history=config.history, max_history_length=20, thread_id=config.thread_id)
            
            # 创建流式回调处理器
            stream_handler = StreamCallbackHandler()
            
            # 获取LLM实例并启用流式输出
            llm = self._get_llm(config.provider, config.model, streaming=True)
            
            # 设置回调处理器到LLM上（必须在创建agent之前）
            if hasattr(llm, 'callbacks'):
                if llm.callbacks:
                    llm.callbacks.append(stream_handler)
                else:
                    llm.callbacks = [stream_handler]
            logger.info(f"LLM callbacks set: {hasattr(llm, 'callbacks')}")
            
            # 创建异步agent（使用已设置回调的LLM）
            agent_config = AgentConfig(
                provider=config.provider,
                model=config.model,
                collection=config.collection,
                message=message,
                search_provider=config.search_provider,
                role_preset_id=config.role_preset_id,
                db_session=config.db_session,
                llm_instance=llm
            )
            agent = await self.create_async_agent(config=agent_config)
            
            # 设置回调到agent上
            if hasattr(agent, 'callbacks'):
                if agent.callbacks:
                    agent.callbacks.append(stream_handler)
                else:
                    agent.callbacks = [stream_handler]
            logger.info(f"Agent callbacks set: {hasattr(agent, 'callbacks')}")
            
            # 使用ainvoke执行，通过回调处理器捕获流式输出
            try:
                agent_done = False
                agent_error = None
                final_result = None
                
                async def run_agent():
                    nonlocal agent_done, agent_error, final_result
                    try:
                        # 构建消息列表
                        messages = []
                        # 添加当前用户消息
                        messages.append(HumanMessage(content=message))
                        
                        # 构建调用配置（如果提供了 thread_id，使用 LangGraph checkpoint）
                        invoke_config = {}
                        if config.thread_id:
                            invoke_config = {"configurable": {"thread_id": config.thread_id}}
                        
                        # 直接使用ainvoke，回调处理器会捕获流式token
                        if invoke_config:
                            result = await agent.ainvoke({"messages": messages}, config=invoke_config)
                        else:
                            result = await agent.ainvoke({"messages": messages})
                        final_result = result
                        
                        # 提取输出
                        output = ""
                        if isinstance(result, dict) and "messages" in result:
                            for msg in reversed(result["messages"]):
                                if isinstance(msg, AIMessage):
                                    output = msg.content
                                    break
                        elif isinstance(result, dict) and "output" in result:
                            output = result["output"]
                        elif isinstance(result, list):
                            for msg in reversed(result):
                                if isinstance(msg, AIMessage):
                                    output = msg.content
                                    break
                        
                        logger.info(f"Agent execution completed, output: {output[:100] if output else 'empty'}...")
                        agent_done = True
                    except Exception as e:
                        logger.error(f"Error in stream chat: {e}")
                        import traceback
                        logger.error(traceback.format_exc())
                        agent_error = str(e)
                        agent_done = True
                
                # 启动agent任务
                agent_task = asyncio.create_task(run_agent())
                
                # 流式返回回调处理器的数据
                last_activity = asyncio.get_event_loop().time()
                empty_loops = 0
                
                while not agent_done or stream_handler.has_new_data():
                    # 检查回调处理器的数据（包含token级别的流式输出）
                    if stream_handler.has_new_data():
                        chunk = stream_handler.get_latest_chunk()
                        if chunk:
                            yield chunk
                            last_activity = asyncio.get_event_loop().time()
                            empty_loops = 0
                        else:
                            empty_loops += 1
                    else:
                        empty_loops += 1
                    
                    # 如果连续多次没有数据，稍微延长等待时间
                    if empty_loops > 10:
                        await asyncio.sleep(0.2)
                        empty_loops = 0
                    else:
                        await asyncio.sleep(0.05)
                    
                    # 检查超时（120秒无活动）
                    current_time = asyncio.get_event_loop().time()
                    if current_time - last_activity > 120 and not agent_done:
                        logger.warning("Stream timeout, agent may be stuck")
                        break
                
                # 等待agent任务完成
                try:
                    await asyncio.wait_for(agent_task, timeout=5.0)
                except asyncio.TimeoutError:
                    logger.warning("Agent task wait timeout")
                except Exception as e:
                    logger.error(f"Agent task error: {e}")
                
                # 发送剩余内容
                while stream_handler.has_new_data():
                    chunk = stream_handler.get_latest_chunk()
                    if chunk:
                        yield chunk
                
                # 如果最终结果还没有通过流式发送，发送最终输出
                if final_result:
                    output = ""
                    if isinstance(final_result, dict) and "messages" in final_result:
                        for msg in reversed(final_result["messages"]):
                            if isinstance(msg, AIMessage):
                                output = msg.content
                                break
                    elif isinstance(final_result, dict) and "output" in final_result:
                        output = final_result.get('output', '')
                    elif isinstance(final_result, list):
                        for msg in reversed(final_result):
                            if isinstance(msg, AIMessage):
                                output = msg.content
                                break
                    
                    if output:
                        # 检查是否已经通过流式发送了
                        if not stream_handler.in_final_answer or len(output) > len(stream_handler.current_thinking):
                            # 如果输出还没有完全发送，发送剩余部分
                            if "Final Answer:" in output or len(output) > 50:
                                # 提取最终答案部分
                                if "Final Answer:" in output:
                                    parts = output.split("Final Answer:", 1)
                                    if len(parts) > 1:
                                        final_content = parts[1].strip()
                                        if final_content:
                                            # 逐字符发送以模拟流式效果
                                            for char in final_content:
                                                yield {
                                                    "type": "content",
                                                    "data": {"content": char},
                                                    "timestamp": datetime.now().isoformat()
                                                }
                                else:
                                    # 直接发送输出
                                    for char in output:
                                        yield {
                                            "type": "content",
                                            "data": {"content": char},
                                            "timestamp": datetime.now().isoformat()
                                        }
                
                # 检查错误
                if agent_error:
                    yield {"type": "error", "data": {"message": agent_error}, "timestamp": datetime.now().isoformat()}
                else:
                    yield {"type": "done", "data": {}, "timestamp": datetime.now().isoformat()}
                    
            except Exception as e:
                logger.error(f"Error in stream processing: {e}")
                import traceback
                logger.error(traceback.format_exc())
                yield {"type": "error", "data": {"message": str(e)}, "timestamp": datetime.now().isoformat()}
                    
        except Exception as e:
            logger.error(f"Error in chat_stream: {e}")
            yield {"type": "error", "data": {"message": str(e)}, "timestamp": datetime.now().isoformat()}
    async def plan_task(
        self, 
        task_description: str,
        config: Optional[AgentConfig] = None,
        **kwargs  # 保持向后兼容，支持旧的方式传参
    ) -> Dict:
        """任务规划
        
        Args:
            task_description: 任务描述
            config: Agent配置对象（推荐使用）
            **kwargs: 向后兼容的旧参数方式（如果提供了config，kwargs将被忽略）
                - provider: LLM提供商
                - model: 模型名称
        """
        # 如果提供了kwargs但没有config，从kwargs创建config（向后兼容）
        if config is None and kwargs:
            config = AgentConfig(**kwargs)
        elif config is None:
            config = AgentConfig()
        
        try:
            agent_config = AgentConfig(
                provider=config.provider,
                model=config.model
            )
            agent = await self.create_async_agent(config=agent_config)
            
            prompt = f"请为以下任务制定详细的执行计划：{task_description}"
            messages = [HumanMessage(content=prompt)]
            response = await agent.ainvoke({"messages": messages})
            
            # 提取输出
            output = ""
            if isinstance(response, dict) and "messages" in response:
                for msg in reversed(response["messages"]):
                    if isinstance(msg, AIMessage):
                        output = msg.content
                        break
            elif isinstance(response, dict) and "output" in response:
                output = response["output"]
            elif isinstance(response, list):
                for msg in reversed(response):
                    if isinstance(msg, AIMessage):
                        output = msg.content
                        break
            
            return {
                "success": True,
                "plan": output,
                "steps": self._parse_plan(output)
            }
            
        except Exception as e:
            logger.error(f"Error in plan_task: {e}")
            return {
                "success": False,
                "plan": "",
                "steps": []
            }
    
    def _parse_plan(self, plan_text: str) -> List[Dict]:
        """解析计划文本为结构化步骤"""
        steps = []
        lines = plan_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-')):
                # 提取步骤
                step_text = line.lstrip('0123456789.-) ').strip()
                if step_text:
                    steps.append({
                        "description": step_text,
                        "status": "pending"
                    })
        
        return steps


# 全局实例
agent_service = AgentService()

