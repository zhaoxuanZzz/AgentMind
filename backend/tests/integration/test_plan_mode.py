"""
集成测试：计划模式
"""
import pytest
from app.services.agent.plan_mode_service import plan_mode_service, PlanModeService


class TestPlanModeComplexityDetection:
    """测试复杂度判断逻辑"""
    
    def test_short_message_no_plan(self):
        """短消息不应触发计划模式"""
        service = PlanModeService()
        result = service.should_use_plan_mode(
            message="Hello",
            plan_mode_enabled=True
        )
        assert result is False
    
    def test_long_message_with_plan_enabled(self):
        """长消息在启用计划模式时应触发"""
        service = PlanModeService()
        result = service.should_use_plan_mode(
            message="请帮我设计一个完整的用户认证系统，包括注册、登录、密码重置等功能，并考虑安全性",
            plan_mode_enabled=True
        )
        assert result is True
    
    def test_long_message_without_plan_enabled(self):
        """长消息在未启用计划模式时不应触发"""
        service = PlanModeService()
        result = service.should_use_plan_mode(
            message="请帮我设计一个完整的用户认证系统，包括注册、登录、密码重置等功能",
            plan_mode_enabled=False
        )
        assert result is False
    
    def test_complexity_keywords_trigger_plan(self):
        """包含复杂度关键词的消息应触发计划模式"""
        service = PlanModeService()
        
        keywords = ["步骤", "流程", "详细", "完整", "系统", "架构", "设计"]
        for keyword in keywords:
            result = service.should_use_plan_mode(
                message=f"请{keyword}说明如何实现这个功能",
                plan_mode_enabled=True
            )
            assert result is True, f"Keyword '{keyword}' should trigger plan mode"
    
    def test_force_plan_overrides_detection(self):
        """强制计划模式应覆盖其他判断"""
        service = PlanModeService()
        result = service.should_use_plan_mode(
            message="Hi",  # 短消息
            plan_mode_enabled=True,
            force_plan=True
        )
        assert result is True


class TestPlanGeneration:
    """测试计划生成"""
    
    def test_parse_plan_text_numbered(self):
        """测试解析编号列表格式的计划"""
        service = PlanModeService()
        plan_text = """
1. 分析需求并确定功能范围
2. 设计数据库模型
3. 实现后端API
4. 开发前端界面
5. 测试和部署
        """
        
        steps = service._parse_plan_text(plan_text)
        
        assert len(steps) == 5
        assert steps[0]["description"] == "分析需求并确定功能范围"
        assert steps[4]["description"] == "测试和部署"
        assert all(step["status"] == "pending" for step in steps)
    
    def test_parse_plan_text_with_substeps(self):
        """测试解析包含子步骤的计划"""
        service = PlanModeService()
        plan_text = """
1. 准备阶段
  - 收集需求
  - 制定时间表
2. 开发阶段
  - 编写代码
  - 单元测试
3. 部署阶段
        """
        
        steps = service._parse_plan_text(plan_text)
        
        # 主步骤应该有3个
        main_steps = [s for s in steps if not s.get("is_substep")]
        assert len(main_steps) >= 3
        
        # 第一个主步骤应该有子步骤
        if "substeps" in steps[0]:
            assert len(steps[0]["substeps"]) == 2
    
    def test_parse_plan_text_dash_format(self):
        """测试解析短横线格式的计划"""
        service = PlanModeService()
        plan_text = """
- 研究现有解决方案
- 设计新架构
- 实现原型
- 收集反馈
        """
        
        steps = service._parse_plan_text(plan_text)
        assert len(steps) == 4
    
    @pytest.mark.asyncio
    async def test_generate_plan_creates_structure(self):
        """测试计划生成创建正确的结构"""
        from unittest.mock import AsyncMock
        
        service = PlanModeService()
        
        # Mock LLM
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=type('obj', (object,), {
            'content': """
1. 分析用户需求
2. 设计解决方案
3. 实现功能
4. 测试验证
5. 文档编写
            """
        })())
        
        plan = await service.generate_plan(
            message="开发一个任务管理系统",
            llm=mock_llm
        )
        
        assert "task" in plan
        assert "plan_text" in plan
        assert "steps" in plan
        assert "created_at" in plan
        assert plan["status"] == "pending"
        assert len(plan["steps"]) == 5


class TestPlanExecution:
    """测试计划执行追踪"""
    
    def test_update_step_status(self):
        """测试更新步骤状态"""
        service = PlanModeService()
        service.current_plan = {
            "steps": [
                {"step_id": 0, "description": "Step 1", "status": "pending"},
                {"step_id": 1, "description": "Step 2", "status": "pending"},
            ]
        }
        service.plan_execution_status = {0: "pending", 1: "pending"}
        
        service.update_step_status(0, "completed")
        
        assert service.plan_execution_status[0] == "completed"
        assert service.current_plan["steps"][0]["status"] == "completed"
    
    def test_get_plan_progress_no_plan(self):
        """测试无计划时的进度"""
        service = PlanModeService()
        service.current_plan = None
        
        progress = service.get_plan_progress()
        
        assert progress["has_plan"] is False
        assert progress["progress"] == 0
    
    def test_get_plan_progress_with_steps(self):
        """测试有步骤的计划进度"""
        service = PlanModeService()
        service.current_plan = {
            "steps": [{"step_id": i} for i in range(5)],
            "status": "in_progress"
        }
        service.plan_execution_status = {
            0: "completed",
            1: "completed",
            2: "in_progress",
            3: "pending",
            4: "pending"
        }
        
        progress = service.get_plan_progress()
        
        assert progress["has_plan"] is True
        assert progress["total"] == 5
        assert progress["completed"] == 2
        assert progress["progress"] == 40.0
        assert progress["status"] == "in_progress"
    
    def test_reset_plan(self):
        """测试重置计划"""
        service = PlanModeService()
        service.current_plan = {"task": "test"}
        service.plan_execution_status = {0: "completed"}
        
        service.reset_plan()
        
        assert service.current_plan is None
        assert len(service.plan_execution_status) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
