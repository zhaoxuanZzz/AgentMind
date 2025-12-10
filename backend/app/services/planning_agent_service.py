"""任务规划 Agent 服务"""
from typing import List, Dict, Optional, Any
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage, AIMessage
from sqlalchemy.orm import Session
import json
import networkx as nx
from pathlib import Path

from app.core.config import settings
from app.services.llm_factory import llm_factory
from app.services.planning_tools import create_planning_tools, save_context_to_file
from app.db import models
from loguru import logger


class PlanningAgentService:
    """任务规划 Agent 服务"""
    
    def __init__(self):
        self.workspace_dir = Path(settings.WORKSPACE_DIR)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_llm(self, provider: Optional[str] = None, model: Optional[str] = None, streaming: bool = False):
        """获取LLM实例"""
        if provider or model:
            return llm_factory.create_llm(provider=provider, model_name=model, streaming=streaming)
        return llm_factory.create_llm(streaming=streaming)
    
    def _get_planning_prompt(self) -> str:
        """获取任务规划系统提示词"""
        return """你是一个专业的任务规划助手。你的职责是：
1. 分析用户输入的复杂任务
2. 将任务拆解为可执行的子步骤
3. 识别步骤间的依赖关系
4. 为每个步骤分配优先级和预估时间
5. 使用 write_todos 工具创建任务列表

在规划任务时，请考虑：
- 任务的逻辑顺序
- 步骤间的依赖关系
- 资源的可用性
- 时间的合理性

当用户提出任务规划需求时，请使用 write_todos 工具来创建结构化的任务列表。
每个任务应该包含：
- id: 唯一标识符（如 step_001, step_002）
- description: 清晰的步骤描述
- priority: 优先级（high, medium, low）
- estimated_time: 预估时间（如 "1h", "30min"）

依赖关系应该明确指出哪些步骤必须在其他步骤之前完成。"""
    
    async def create_planning_agent(
        self,
        conversation_id: int,
        llm_config: Optional[Dict] = None,
        enable_planning: bool = True,
        history: Optional[List[Dict]] = None
    ) -> AgentExecutor:
        """创建任务规划 Agent"""
        
        # 获取 LLM
        llm = self._get_llm(
            provider=llm_config.get('provider') if llm_config else None,
            model=llm_config.get('model') if llm_config else None,
            streaming=False
        )
        
        # 创建工具列表
        tools = create_planning_tools()
        
        # 创建记忆
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # 加载历史对话
        if history:
            for msg in history:
                if msg.get('role') == 'user':
                    memory.chat_memory.add_user_message(msg.get('content', ''))
                elif msg.get('role') == 'assistant':
                    memory.chat_memory.add_ai_message(msg.get('content', ''))
        
        # 创建系统提示词
        system_prompt = self._get_planning_prompt() if enable_planning else None
        
        # 创建 Agent Prompt
        if system_prompt:
            from langchain_core.prompts import ChatPromptTemplate
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ])
        else:
            from langchain import hub
            try:
                prompt = hub.pull("hwchase17/react")
            except:
                # 如果无法拉取，使用默认模板
                from langchain_core.prompts import ChatPromptTemplate
                prompt = ChatPromptTemplate.from_messages([
                    MessagesPlaceholder(variable_name="chat_history"),
                    ("human", "{input}"),
                    MessagesPlaceholder(variable_name="agent_scratchpad"),
                ])
        
        agent = create_react_agent(llm, tools, prompt)
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            memory=memory,
            verbose=True,
            handle_parsing_errors=True
        )
        
        logger.info(f"创建任务规划 Agent (conversation_id: {conversation_id})")
        return agent_executor
    
    async def plan_task(
        self,
        task_description: str,
        conversation_id: int,
        agent: AgentExecutor,
        db: Session
    ) -> Dict[str, Any]:
        """规划任务"""
        
        try:
            # 构建规划提示
            planning_prompt = f"""请为以下任务制定详细的执行计划，并将计划拆解为可执行的子步骤：

任务描述：{task_description}

请使用 write_todos 工具创建任务列表。每个任务应该：
1. 有唯一的ID（如 step_001, step_002）
2. 有清晰的描述
3. 有优先级（high, medium, low）
4. 有预估时间
5. 明确依赖关系（如果有）

请开始规划。"""
            
            # 调用 Agent 进行规划
            response = await agent.ainvoke({
                "input": planning_prompt,
                "chat_history": []
            })
            
            # 从响应中提取任务列表
            todos = self._extract_todos_from_response(response)
            
            # 保存到数据库
            planning_task = self._save_planning_task(
                conversation_id=conversation_id,
                description=task_description,
                todos=todos,
                db=db
            )
            
            # 构建依赖关系图
            dependency_graph = self._build_dependency_graph(todos)
            
            return {
                "task_id": planning_task.id,
                "steps": todos,
                "dependencies": dependency_graph
            }
        except Exception as e:
            logger.error(f"规划任务失败: {e}")
            raise
    
    def _extract_todos_from_response(self, response: Dict) -> List[Dict]:
        """从 Agent 响应中提取任务列表"""
        try:
            output = response.get("output", "")
            
            # 尝试从输出中解析 JSON
            # 首先查找 write_todos 工具的输出
            if "write_todos" in output.lower():
                # 尝试提取 JSON 部分
                import re
                json_match = re.search(r'\{.*\}', output, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    if result.get("success") and "todos" in result:
                        todos_list = []
                        for task_id, task_data in result["todos"].items():
                            todos_list.append({
                                "step_id": task_id,
                                "description": task_data.get("description", ""),
                                "priority": task_data.get("priority", "medium"),
                                "estimated_time": task_data.get("estimated_time", ""),
                                "dependencies": task_data.get("dependencies", []),
                                "status": "pending"
                            })
                        return todos_list
            
            # 如果无法解析，返回空列表
            logger.warning("无法从响应中提取任务列表")
            return []
        except Exception as e:
            logger.error(f"提取任务列表失败: {e}")
            return []
    
    def _save_planning_task(
        self,
        conversation_id: int,
        description: str,
        todos: List[Dict],
        db: Session
    ) -> models.PlanningTask:
        """保存规划任务到数据库"""
        try:
            # 创建规划任务
            planning_task = models.PlanningTask(
                conversation_id=conversation_id,
                title=description[:200] if len(description) > 200 else description,
                description=description,
                status="planned",
                plan_data={"steps": todos}
            )
            db.add(planning_task)
            db.flush()
            
            # 创建任务步骤
            for todo in todos:
                task_step = models.TaskStep(
                    planning_task_id=planning_task.id,
                    step_id=todo.get("step_id", ""),
                    description=todo.get("description", ""),
                    status="pending",
                    priority=todo.get("priority"),
                    estimated_time=todo.get("estimated_time"),
                    dependencies=todo.get("dependencies", [])
                )
                db.add(task_step)
            
            db.commit()
            db.refresh(planning_task)
            
            logger.info(f"保存规划任务: {planning_task.id}, 包含 {len(todos)} 个步骤")
            return planning_task
        except Exception as e:
            db.rollback()
            logger.error(f"保存规划任务失败: {e}")
            raise
    
    def _build_dependency_graph(self, todos: List[Dict]) -> Dict:
        """构建依赖关系图"""
        try:
            G = nx.DiGraph()
            
            # 添加节点
            for todo in todos:
                step_id = todo.get("step_id", "")
                G.add_node(step_id, **todo)
            
            # 添加边（依赖关系）
            for todo in todos:
                step_id = todo.get("step_id", "")
                dependencies = todo.get("dependencies", [])
                for dep in dependencies:
                    if dep in G.nodes:
                        G.add_edge(dep, step_id)
            
            # 转换为前端需要的格式
            nodes = [
                {
                    "id": node_id,
                    "data": data
                }
                for node_id, data in G.nodes(data=True)
            ]
            
            edges = [
                {
                    "source": source,
                    "target": target
                }
                for source, target in G.edges()
            ]
            
            return {
                "nodes": nodes,
                "edges": edges
            }
        except Exception as e:
            logger.error(f"构建依赖关系图失败: {e}")
            return {"nodes": [], "edges": []}
    
    async def get_task_dependencies(
        self,
        task_id: int,
        db: Session
    ) -> Dict:
        """获取任务依赖关系图"""
        try:
            planning_task = db.query(models.PlanningTask).filter(
                models.PlanningTask.id == task_id
            ).first()
            
            if not planning_task:
                raise ValueError(f"任务不存在: {task_id}")
            
            # 获取所有步骤
            steps = db.query(models.TaskStep).filter(
                models.TaskStep.planning_task_id == task_id
            ).all()
            
            # 构建步骤列表
            todos = []
            for step in steps:
                todos.append({
                    "step_id": step.step_id,
                    "description": step.description,
                    "status": step.status,
                    "priority": step.priority,
                    "estimated_time": step.estimated_time,
                    "dependencies": step.dependencies or []
                })
            
            # 构建依赖关系图
            dependency_graph = self._build_dependency_graph(todos)
            
            return dependency_graph
        except Exception as e:
            logger.error(f"获取任务依赖关系失败: {e}")
            raise
    
    async def get_task_status(
        self,
        task_id: int,
        db: Session
    ) -> Dict:
        """获取任务执行状态"""
        try:
            planning_task = db.query(models.PlanningTask).filter(
                models.PlanningTask.id == task_id
            ).first()
            
            if not planning_task:
                raise ValueError(f"任务不存在: {task_id}")
            
            # 获取所有步骤
            steps = db.query(models.TaskStep).filter(
                models.TaskStep.planning_task_id == task_id
            ).all()
            
            # 统计状态
            status_count = {
                "pending": 0,
                "in_progress": 0,
                "completed": 0,
                "failed": 0
            }
            
            for step in steps:
                status = step.status or "pending"
                if status in status_count:
                    status_count[status] += 1
            
            total = len(steps)
            completed = status_count["completed"]
            progress = (completed / total * 100) if total > 0 else 0
            
            return {
                "task_id": task_id,
                "status": planning_task.status,
                "total_steps": total,
                "completed_steps": completed,
                "progress": round(progress, 2),
                "status_count": status_count
            }
        except Exception as e:
            logger.error(f"获取任务状态失败: {e}")
            raise


# 创建单例
planning_agent_service = PlanningAgentService()

