"""任务规划 API 路由"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.db.database import get_db
from app.api.schemas import (
    PlanningRequest,
    PlanningResponse,
    TaskDependencyGraph,
    TaskStatusResponse,
    TaskStep
)
from app.services.planning_agent_service import planning_agent_service
from loguru import logger

router = APIRouter(prefix="/planning", tags=["planning"])


@router.post("/plan", response_model=PlanningResponse)
async def plan_task(
    request: PlanningRequest,
    db: Session = Depends(get_db)
):
    """规划任务"""
    try:
        # 创建 Planning Agent
        agent = await planning_agent_service.create_planning_agent(
            conversation_id=request.conversation_id,
            llm_config={
                "provider": request.llm_config.provider if request.llm_config else None,
                "model": request.llm_config.model if request.llm_config else None
            },
            enable_planning=True
        )
        
        # 执行规划
        result = await planning_agent_service.plan_task(
            task_description=request.task_description,
            conversation_id=request.conversation_id,
            agent=agent,
            db=db
        )
        
        # 转换为响应格式
        steps = [
            TaskStep(
                step_id=step.get("step_id", ""),
                description=step.get("description", ""),
                status=step.get("status", "pending"),
                priority=step.get("priority"),
                estimated_time=step.get("estimated_time"),
                dependencies=step.get("dependencies", []),
                result=step.get("result")
            )
            for step in result["steps"]
        ]
        
        dependencies = TaskDependencyGraph(
            nodes=[
                {"id": node["id"], "data": node["data"]}
                for node in result["dependencies"]["nodes"]
            ],
            edges=[
                {"source": edge["source"], "target": edge["target"]}
                for edge in result["dependencies"]["edges"]
            ]
        )
        
        return PlanningResponse(
            success=True,
            task_id=result["task_id"],
            steps=steps,
            dependencies=dependencies
        )
    except Exception as e:
        logger.error(f"规划任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}/dependencies", response_model=TaskDependencyGraph)
async def get_task_dependencies(
    task_id: int,
    db: Session = Depends(get_db)
):
    """获取任务依赖关系图"""
    try:
        result = await planning_agent_service.get_task_dependencies(
            task_id=task_id,
            db=db
        )
        
        return TaskDependencyGraph(
            nodes=[
                {"id": node["id"], "data": node["data"]}
                for node in result["nodes"]
            ],
            edges=[
                {"source": edge["source"], "target": edge["target"]}
                for edge in result["edges"]
            ]
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取任务依赖关系失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: int,
    db: Session = Depends(get_db)
):
    """获取任务执行状态"""
    try:
        result = await planning_agent_service.get_task_status(
            task_id=task_id,
            db=db
        )
        
        return TaskStatusResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取任务状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

