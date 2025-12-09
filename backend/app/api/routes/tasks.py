from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.db import models
from app.api.schemas import (
    TaskCreate, TaskResponse,
    TaskPlanRequest, TaskPlanResponse
)
from app.services.agent_service import agent_service
from loguru import logger

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=TaskResponse)
async def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """创建任务"""
    try:
        # 创建任务记录
        new_task = models.Task(
            title=task.title,
            description=task.description,
            status="pending"
        )
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
        
        return new_task
        
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plan", response_model=TaskPlanResponse)
async def plan_task(request: TaskPlanRequest):
    """为任务生成执行计划"""
    try:
        llm_config = request.llm_config or {}
        result = await agent_service.plan_task(
            task_description=request.description,
            provider=llm_config.provider if hasattr(llm_config, 'provider') else None,
            model=llm_config.model if hasattr(llm_config, 'model') else None
        )
        return TaskPlanResponse(
            success=result["success"],
            plan=result["plan"],
            steps=result["steps"]
        )
        
    except Exception as e:
        logger.error(f"Error planning task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{task_id}/plan", response_model=TaskResponse)
async def plan_existing_task(task_id: int, db: Session = Depends(get_db)):
    """为已存在的任务生成执行计划"""
    try:
        # 获取任务
        task = db.query(models.Task).filter(models.Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 生成计划
        result = await agent_service.plan_task(task.description)
        
        if result["success"]:
            # 更新任务
            task.plan = {
                "plan_text": result["plan"],
                "steps": result["steps"]
            }
            task.status = "planned"
            db.commit()
            db.refresh(task)
        
        return task
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error planning existing task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[TaskResponse])
def get_tasks(
    skip: int = 0, 
    limit: int = 20, 
    status: str = None,
    db: Session = Depends(get_db)
):
    """获取任务列表"""
    query = db.query(models.Task)
    
    if status:
        query = query.filter(models.Task.status == status)
    
    tasks = query.order_by(models.Task.created_at.desc()).offset(skip).limit(limit).all()
    return tasks


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    """获取任务详情"""
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@router.patch("/{task_id}/status")
def update_task_status(
    task_id: int, 
    status: str,
    result: dict = None,
    db: Session = Depends(get_db)
):
    """更新任务状态"""
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task.status = status
    if result:
        task.result = result
    
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """删除任务"""
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    db.delete(task)
    db.commit()
    return {"success": True, "message": "任务已删除"}

