"""
计划模式服务
提供问题复杂度判断、计划生成和执行追踪功能
"""
from typing import Dict, List, Optional, AsyncIterator
from datetime import datetime
from loguru import logger
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


class PlanModeService:
    """计划模式服务 - 负责计划生成和执行管理"""
    
    # 复杂度判断阈值（字符数）
    COMPLEXITY_THRESHOLD = 50
    
    # 复杂度关键词（出现这些词汇通常意味着复杂任务）
    COMPLEXITY_KEYWORDS = [
        "步骤", "流程", "详细", "完整", "系统",
        "架构", "设计", "实现", "开发", "构建",
        "分析", "研究", "调研", "对比", "评估",
        "多个", "复杂", "全面", "综合"
    ]
    
    def __init__(self):
        self.current_plan: Optional[Dict] = None
        self.plan_execution_status: Dict[int, str] = {}  # step_id -> status
    
    def should_use_plan_mode(
        self, 
        message: str, 
        plan_mode_enabled: bool = False,
        force_plan: bool = False
    ) -> bool:
        """判断是否应该使用计划模式
        
        Args:
            message: 用户消息内容
            plan_mode_enabled: 用户是否启用了计划模式开关
            force_plan: 是否强制使用计划模式
            
        Returns:
            bool: 是否应该使用计划模式
        """
        # 1. 如果用户没有启用计划模式，直接返回 False
        if not plan_mode_enabled:
            logger.debug("Plan mode disabled by user")
            return False
        
        # 2. 如果强制使用计划模式，返回 True
        if force_plan:
            logger.info("Plan mode forced")
            return True
        
        # 3. 检查消息长度
        if len(message) < self.COMPLEXITY_THRESHOLD:
            logger.debug(f"Message too short ({len(message)} chars), skipping plan mode")
            return False
        
        # 4. 检查是否包含复杂度关键词
        has_keyword = any(keyword in message for keyword in self.COMPLEXITY_KEYWORDS)
        
        if has_keyword:
            logger.info(f"Complexity keyword detected in message, using plan mode")
            return True
        
        # 5. 默认对于长消息使用计划模式
        logger.info(f"Message length {len(message)} exceeds threshold, using plan mode")
        return True
    
    async def generate_plan(
        self, 
        message: str, 
        llm: any,
        context: Optional[str] = None
    ) -> Dict:
        """生成任务执行计划
        
        Args:
            message: 用户任务描述
            llm: LLM实例
            context: 可选的上下文信息
            
        Returns:
            Dict: 包含计划步骤的字典
        """
        logger.info(f"Generating plan for task: {message[:50]}...")
        
        try:
            # 构建计划生成提示
            system_prompt = """你是一个任务规划专家。请为用户的任务生成详细的执行计划。

计划格式要求：
1. 将任务分解为3-7个清晰的步骤
2. 每个步骤应该是具体可执行的
3. 步骤之间有逻辑顺序
4. 使用编号列表格式（1. 2. 3. ...）

示例：
任务：设计一个用户登录系统
计划：
1. 分析需求：确定登录方式（用户名/邮箱/手机）和安全要求
2. 设计数据库：创建用户表，包含必要字段和索引
3. 实现后端API：开发注册、登录、登出接口
4. 添加安全措施：密码加密、Token验证、频率限制
5. 开发前端界面：登录表单、注册表单、错误提示
6. 测试验证：单元测试、集成测试、安全测试
"""
            
            if context:
                user_prompt = f"上下文：{context}\n\n任务：{message}\n\n请生成执行计划："
            else:
                user_prompt = f"任务：{message}\n\n请生成执行计划："
            
            # 调用LLM生成计划
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = await llm.ainvoke(messages)
            plan_text = response.content if hasattr(response, 'content') else str(response)
            
            # 解析计划文本为结构化步骤
            steps = self._parse_plan_text(plan_text)
            
            # 保存当前计划
            self.current_plan = {
                "task": message,
                "plan_text": plan_text,
                "steps": steps,
                "created_at": datetime.now().isoformat(),
                "status": "pending"
            }
            
            # 初始化步骤执行状态
            self.plan_execution_status = {i: "pending" for i in range(len(steps))}
            
            logger.info(f"Plan generated with {len(steps)} steps")
            return self.current_plan
            
        except Exception as e:
            logger.error(f"Error generating plan: {e}")
            return {
                "task": message,
                "plan_text": f"规划失败：{str(e)}",
                "steps": [],
                "created_at": datetime.now().isoformat(),
                "status": "failed"
            }
    
    def _parse_plan_text(self, plan_text: str) -> List[Dict]:
        """解析计划文本为结构化步骤列表
        
        Args:
            plan_text: 计划文本
            
        Returns:
            List[Dict]: 步骤列表
        """
        steps = []
        lines = plan_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 识别编号列表（1. 2. 3. 或 1) 2) 3) 或 - 等）
            if line[0].isdigit() or line.startswith('-') or line.startswith('•'):
                # 提取步骤描述
                step_text = line.lstrip('0123456789.-•) ').strip()
                
                # 检查是否是子步骤（缩进或以小写字母/罗马数字开头）
                is_substep = line.startswith('  ') or line.startswith('\t')
                
                if step_text:
                    step_data = {
                        "description": step_text,
                        "status": "pending",
                        "is_substep": is_substep
                    }
                    
                    # 如果是子步骤，附加到上一个主步骤
                    if is_substep and steps and not steps[-1].get("is_substep"):
                        if "substeps" not in steps[-1]:
                            steps[-1]["substeps"] = []
                        steps[-1]["substeps"].append(step_data)
                    else:
                        steps.append(step_data)
        
        # 为每个步骤分配ID
        for i, step in enumerate(steps):
            step["step_id"] = i
        
        return steps
    
    def update_step_status(self, step_id: int, status: str) -> None:
        """更新步骤执行状态
        
        Args:
            step_id: 步骤ID
            status: 新状态 (pending/in_progress/completed/failed)
        """
        if step_id in self.plan_execution_status:
            self.plan_execution_status[step_id] = status
            logger.debug(f"Step {step_id} status updated to {status}")
            
            # 更新计划中的步骤状态
            if self.current_plan and step_id < len(self.current_plan.get("steps", [])):
                self.current_plan["steps"][step_id]["status"] = status
    
    def get_plan_progress(self) -> Dict:
        """获取计划执行进度
        
        Returns:
            Dict: 进度信息
        """
        if not self.current_plan:
            return {
                "has_plan": False,
                "progress": 0,
                "completed": 0,
                "total": 0
            }
        
        total_steps = len(self.current_plan.get("steps", []))
        completed_steps = sum(
            1 for status in self.plan_execution_status.values() 
            if status == "completed"
        )
        
        progress = (completed_steps / total_steps * 100) if total_steps > 0 else 0
        
        return {
            "has_plan": True,
            "progress": round(progress, 2),
            "completed": completed_steps,
            "total": total_steps,
            "status": self.current_plan.get("status", "unknown")
        }
    
    def reset_plan(self) -> None:
        """重置当前计划"""
        self.current_plan = None
        self.plan_execution_status = {}
        logger.debug("Plan reset")
    
    async def execute_plan_with_tracking(
        self,
        agent: any,
        user_message: str,
        plan: Dict,
        on_step_start: Optional[callable] = None,
        on_step_complete: Optional[callable] = None
    ) -> AsyncIterator[Dict]:
        """执行计划并追踪进度
        
        Args:
            agent: Agent实例
            user_message: 原始用户消息
            plan: 计划对象
            on_step_start: 步骤开始回调
            on_step_complete: 步骤完成回调
            
        Yields:
            Dict: 执行进度和结果
        """
        steps = plan.get("steps", [])
        
        if not steps:
            logger.warning("No steps in plan, executing without plan")
            return
        
        # 首先输出完整计划
        yield {
            "type": "plan",
            "plan": plan,
            "status": "started"
        }
        
        # 执行每个步骤
        for step in steps:
            step_id = step.get("step_id", 0)
            description = step.get("description", "")
            
            # 更新状态为进行中
            self.update_step_status(step_id, "in_progress")
            
            # 触发回调
            if on_step_start:
                await on_step_start(step_id, description)
            
            # 输出步骤开始
            yield {
                "type": "plan",
                "step_id": step_id,
                "description": description,
                "status": "in_progress"
            }
            
            try:
                # 这里可以根据步骤描述执行具体操作
                # 暂时简化为标记为完成
                self.update_step_status(step_id, "completed")
                
                # 触发回调
                if on_step_complete:
                    await on_step_complete(step_id, "completed")
                
                # 输出步骤完成
                yield {
                    "type": "plan",
                    "step_id": step_id,
                    "description": description,
                    "status": "completed"
                }
                
            except Exception as e:
                logger.error(f"Error executing step {step_id}: {e}")
                self.update_step_status(step_id, "failed")
                
                yield {
                    "type": "plan",
                    "step_id": step_id,
                    "description": description,
                    "status": "failed",
                    "error": str(e)
                }
        
        # 输出计划完成
        yield {
            "type": "plan",
            "plan": plan,
            "status": "completed",
            "progress": self.get_plan_progress()
        }


# 全局实例
plan_mode_service = PlanModeService()
