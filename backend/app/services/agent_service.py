from langchain.agents import AgentExecutor, create_openai_functions_agent, create_react_agent
from langchain.tools import Tool
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain.memory import ConversationBufferMemory
from typing import List, Dict, Optional, AsyncIterator, Any
import asyncio
from app.core.config import settings
from app.services.knowledge_service import knowledge_service
from app.services.llm_factory import llm_factory
from app.services.agent import RolePresetRetriever, PromptBuilder
from app.services.memory import MemoryManager
from app.services.streaming import StreamCallbackHandler
from app.services.tools import (
    create_web_search_tool,
    web_scraper_tool,
    pdf_parser_tool,
    knowledge_retrieval_tool
)
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
        memory: Optional[ConversationBufferMemory] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        collection: Optional[str] = None,
        message: Optional[str] = None,
        search_provider: Optional[str] = None,
        role_preset_id: Optional[str] = None,
        db_session = None,
        llm_instance: Optional[Any] = None
    ) -> AgentExecutor:
        """创建Agent执行器
        
        Args:
            memory: 对话内存
            provider: LLM提供商
            model: 模型名称
            collection: 知识库集合名称
            message: 用户消息（用于检索角色预设）
            search_provider: 搜索提供商，可选值: 'tavily', 'baidu', None(默认使用tavily)
            role_preset_id: 指定的角色预设ID
            db_session: 数据库会话
            llm_instance: 可选的LLM实例（如果提供则直接使用）
        """
        
        # 获取LLM实例（如果未提供）
        if llm_instance:
            llm = llm_instance
        else:
            llm = self._get_llm(provider, model, streaming=False)
        
        # 创建工具列表（根据search_provider选择搜索工具）
        tools = self._create_tools(search_provider=search_provider)
        
        # 判断使用哪种Agent类型
        use_react = provider == 'dashscope' or settings.LLM_PROVIDER == 'dashscope'
        
        if use_react:
            # 使用 ReAct Agent（适用于qwen等中文模型）
            logger.info("Using ReAct agent for better tool usage")
            
            # 获取角色预设提示词
            role_prompts = RolePresetRetriever.retrieve_prompts(
                role_preset_id=role_preset_id,
                collection=collection,
                message=message,
                db_session=db_session,
                top_k=3
            )
            
            # 获取历史对话上下文
            history_context = MemoryManager.get_history_context(memory, max_messages=20) if memory else ""
            
            # 构建提示词
            prompt = PromptBuilder.build_react_prompt(
                tools=tools,
                knowledge_prompts=role_prompts,
                history_context=history_context
            )
            
            agent = create_react_agent(
                llm=llm,
                tools=tools,
                prompt=prompt
            )
        else:
            # 使用 OpenAI Functions Agent（适用于支持function calling的模型）
            logger.info("Using OpenAI Functions agent")
            
            # 获取角色预设提示词
            role_prompts = RolePresetRetriever.retrieve_prompts(
                role_preset_id=role_preset_id,
                collection=collection,
                message=message,
                db_session=db_session,
                top_k=3
            )
            
            # 构建提示词
            prompt = PromptBuilder.build_openai_functions_prompt(
                knowledge_prompts=knowledge_prompts
            )
            
            agent = create_openai_functions_agent(
                llm=llm,
                tools=tools,
                prompt=prompt
            )
        
        # 创建executor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            memory=memory,
            handle_parsing_errors=True,
            max_iterations=10,  # 增加迭代次数
            return_intermediate_steps=True
        )
        
        return agent_executor
    
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
    
    async def chat(
        self, 
        message: str, 
        history: Optional[List[Dict]] = None,
        collection: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        search_provider: Optional[str] = None,
        role_preset_id: Optional[str] = None,
        db_session = None
    ) -> Dict:
        """处理对话"""
        try:
            # 创建memory并加载历史对话
            memory = MemoryManager.create_memory(history=history, max_history_length=20)
            
            # 创建agent，传入collection和message参数用于检索角色预设
            agent_executor = self.create_agent(
                memory, 
                provider=provider, 
                model=model, 
                collection=collection, 
                message=message,
                search_provider=search_provider,
                role_preset_id=role_preset_id,
                db_session=db_session
            )
            
            # 执行
            response = await agent_executor.ainvoke({"input": message})
            
            # 格式化中间步骤
            raw_steps = response.get("intermediate_steps", [])
            formatted_steps = self._format_intermediate_steps(raw_steps)
            
            return {
                "success": True,
                "response": response["output"],
                "intermediate_steps": formatted_steps
            }
            
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "response": f"处理请求时出错: {str(e)}",
                "intermediate_steps": []
            }
    
    async def chat_stream(
        self,
        message: str,
        history: Optional[List[Dict]] = None,
        collection: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        search_provider: Optional[str] = None,
        role_preset_id: Optional[str] = None,
        deep_reasoning: bool = False,
        db_session = None
    ) -> AsyncIterator[Dict]:
        """流式处理对话"""
        try:
            # 创建memory并加载历史对话
            memory = MemoryManager.create_memory(history=history, max_history_length=20)
            
            # 创建流式回调处理器
            stream_handler = StreamCallbackHandler()
            
            # 获取LLM实例并启用流式输出
            llm = self._get_llm(provider, model, streaming=True)
            
            # 设置回调处理器到LLM上（必须在创建agent之前）
            if hasattr(llm, 'callbacks'):
                if llm.callbacks:
                    llm.callbacks.append(stream_handler)
                else:
                    llm.callbacks = [stream_handler]
            logger.info(f"LLM callbacks set: {hasattr(llm, 'callbacks')}")
            
            # 创建agent（使用已设置回调的LLM）
            # 注意：需要修改create_agent方法以支持传入LLM实例
            # 临时方案：直接在这里创建agent，而不是调用create_agent
            from langchain.agents import AgentExecutor, create_react_agent, create_openai_functions_agent
            from langchain import hub
            from app.services import knowledge_service
            from app.core.config import settings
            
            # 创建工具列表
            tools = self._create_tools(search_provider=search_provider)
            
            # 获取角色预设提示词
            role_prompts = RolePresetRetriever.retrieve_prompts(
                role_preset_id=role_preset_id,
                collection=collection,
                message=message,
                db_session=db_session,
                top_k=3
            )
            
            # 判断使用哪种Agent类型
            use_react = provider == 'dashscope' or settings.LLM_PROVIDER == 'dashscope'
            
            if use_react:
                # 使用 ReAct Agent
                from langchain.prompts import PromptTemplate
                
                # 构建提示词
                prompt = PromptBuilder.build_react_prompt_for_stream(
                    tools=tools,
                    knowledge_prompts=knowledge_prompts
                )
                
                agent = create_react_agent(llm, tools, prompt)
            else:
                # 使用 OpenAI Functions Agent
                from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
                from langchain_core.messages import SystemMessage
                
                # 构建提示词
                prompt = PromptBuilder.build_openai_functions_prompt_for_stream(
                    knowledge_prompts=knowledge_prompts
                )
                
                agent = create_openai_functions_agent(llm, tools, prompt)
            
            # 创建executor
            agent_executor = AgentExecutor(
                agent=agent,
                tools=tools,
                verbose=True,
                memory=memory,
                handle_parsing_errors=True,
                max_iterations=10,
                return_intermediate_steps=True
            )
            
            # 也设置到agent_executor上
            if hasattr(agent_executor, 'callbacks'):
                if agent_executor.callbacks:
                    agent_executor.callbacks.append(stream_handler)
                else:
                    agent_executor.callbacks = [stream_handler]
            logger.info(f"AgentExecutor callbacks set: {hasattr(agent_executor, 'callbacks')}")
            
            # 使用ainvoke执行，通过回调处理器捕获流式输出
            try:
                import asyncio
                
                agent_done = False
                agent_error = None
                final_result = None
                
                async def run_agent():
                    nonlocal agent_done, agent_error, final_result
                    try:
                        # 直接使用ainvoke，回调处理器会捕获流式token
                        result = await agent_executor.ainvoke({"input": message})
                        final_result = result
                        logger.info(f"Agent execution completed, output: {result.get('output', '')[:100]}...")
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
                
                # 发送LLM结束时的剩余推理内容
                if stream_handler.current_thinking.strip() and not stream_handler.in_final_answer:
                    yield {
                        "type": "thinking",
                        "content": stream_handler.current_thinking.strip()
                    }
                
                # 如果最终结果还没有通过流式发送，发送最终输出
                if final_result and final_result.get('output'):
                    output = final_result.get('output', '')
                    # 检查是否已经通过流式发送了
                    if not stream_handler.in_final_answer or len(output) > len(stream_handler.current_thinking):
                        # 如果输出还没有完全发送，发送剩余部分
                        # 这里简单处理：如果输出很长，可能是最终答案
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
                                                "content": char
                                            }
                            else:
                                # 直接发送输出
                                for char in output:
                                    yield {
                                        "type": "content",
                                        "content": char
                                    }
                
                # 检查错误
                if agent_error:
                    yield {"type": "error", "message": agent_error}
                else:
                    yield {"type": "done"}
                    
            except Exception as e:
                logger.error(f"Error in stream processing: {e}")
                import traceback
                logger.error(traceback.format_exc())
                yield {"type": "error", "message": str(e)}
                    
        except Exception as e:
            logger.error(f"Error in chat_stream: {e}")
            yield {"type": "error", "message": str(e)}
    async def plan_task(
        self, 
        task_description: str,
        provider: Optional[str] = None,
        model: Optional[str] = None
    ) -> Dict:
        """任务规划"""
        try:
            agent_executor = self.create_agent(provider=provider, model=model)
            
            prompt = f"请为以下任务制定详细的执行计划：{task_description}"
            response = await agent_executor.ainvoke({"input": prompt})
            
            return {
                "success": True,
                "plan": response["output"],
                "steps": self._parse_plan(response["output"])
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

