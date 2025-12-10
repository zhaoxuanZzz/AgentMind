"""任务规划工具包装器"""
from typing import List, Dict, Any, Optional
from langchain.tools import Tool
import json
import os
from pathlib import Path
from app.core.config import settings
from loguru import logger


def write_todos_tool(todos: List[Dict[str, Any]], dependencies: Optional[Dict[str, List[str]]] = None) -> str:
    """创建任务列表工具
    
    Args:
        todos: 任务列表，每个任务包含：
            - id: 任务ID
            - description: 任务描述
            - priority: 优先级 (high, medium, low)
            - estimated_time: 预估时间
        dependencies: 依赖关系映射 {task_id: [dependency_ids]}
    
    Returns:
        任务创建结果
    """
    try:
        # 验证任务格式
        validated_todos = {}
        for todo in todos:
            if 'id' not in todo or 'description' not in todo:
                raise ValueError("任务必须包含 id 和 description")
            validated_todos[todo['id']] = todo
        
        # 应用依赖关系
        if dependencies:
            for task_id, deps in dependencies.items():
                if task_id in validated_todos:
                    validated_todos[task_id]['dependencies'] = deps
        
        result = {
            "success": True,
            "message": f"成功创建 {len(validated_todos)} 个任务",
            "todos": validated_todos,
            "dependencies": dependencies or {}
        }
        
        logger.info(f"创建任务列表: {len(validated_todos)} 个任务")
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        logger.error(f"创建任务列表失败: {e}")
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)


def create_task_agent_tool(task_description: str, tools: Optional[List[str]] = None, context: Optional[Dict] = None) -> str:
    """创建子代理处理特定任务
    
    Args:
        task_description: 子任务描述
        tools: 需要的工具列表
        context: 上下文信息
    
    Returns:
        子代理执行结果
    """
    try:
        # 这里应该调用实际的子代理创建逻辑
        # 目前返回模拟结果
        agent_id = f"agent_{hash(task_description) % 10000}"
        
        result = {
            "success": True,
            "agent_id": agent_id,
            "status": "created",
            "task_description": task_description,
            "tools": tools or [],
            "context": context or {}
        }
        
        logger.info(f"创建子代理: {agent_id}")
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        logger.error(f"创建子代理失败: {e}")
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)


def ls_tool(path: str = ".") -> str:
    """列出目录内容"""
    try:
        base_dir = Path(settings.WORKSPACE_DIR if hasattr(settings, 'WORKSPACE_DIR') else "./workspace")
        target_path = base_dir / path
        
        if not target_path.exists():
            return json.dumps({"success": False, "error": f"路径不存在: {path}"}, ensure_ascii=False)
        
        if not target_path.is_dir():
            return json.dumps({"success": False, "error": f"不是目录: {path}"}, ensure_ascii=False)
        
        items = []
        for item in target_path.iterdir():
            items.append({
                "name": item.name,
                "type": "directory" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else None
            })
        
        result = {
            "success": True,
            "path": str(target_path),
            "items": items
        }
        
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        logger.error(f"列出目录失败: {e}")
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)


def read_file_tool(path: str) -> str:
    """读取文件内容"""
    try:
        base_dir = Path(settings.WORKSPACE_DIR if hasattr(settings, 'WORKSPACE_DIR') else "./workspace")
        file_path = base_dir / path
        
        if not file_path.exists():
            return json.dumps({"success": False, "error": f"文件不存在: {path}"}, ensure_ascii=False)
        
        if not file_path.is_file():
            return json.dumps({"success": False, "error": f"不是文件: {path}"}, ensure_ascii=False)
        
        content = file_path.read_text(encoding='utf-8')
        
        result = {
            "success": True,
            "path": str(file_path),
            "content": content,
            "size": len(content)
        }
        
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        logger.error(f"读取文件失败: {e}")
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)


def write_file_tool(path: str, content: str) -> str:
    """写入文件内容"""
    try:
        base_dir = Path(settings.WORKSPACE_DIR if hasattr(settings, 'WORKSPACE_DIR') else "./workspace")
        file_path = base_dir / path
        
        # 确保目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_path.write_text(content, encoding='utf-8')
        
        result = {
            "success": True,
            "path": str(file_path),
            "size": len(content)
        }
        
        logger.info(f"写入文件: {file_path}")
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        logger.error(f"写入文件失败: {e}")
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)


def edit_file_tool(path: str, edits: List[Dict[str, Any]]) -> str:
    """编辑文件内容
    
    Args:
        path: 文件路径
        edits: 编辑操作列表，每个操作包含：
            - type: 操作类型 (insert, delete, replace)
            - line: 行号
            - content: 内容
    """
    try:
        base_dir = Path(settings.WORKSPACE_DIR if hasattr(settings, 'WORKSPACE_DIR') else "./workspace")
        file_path = base_dir / path
        
        if not file_path.exists():
            return json.dumps({"success": False, "error": f"文件不存在: {path}"}, ensure_ascii=False)
        
        content = file_path.read_text(encoding='utf-8')
        lines = content.split('\n')
        
        # 应用编辑操作
        for edit in edits:
            edit_type = edit.get('type')
            line_num = edit.get('line', 0) - 1  # 转换为0-based索引
            edit_content = edit.get('content', '')
            
            if edit_type == 'insert':
                lines.insert(line_num, edit_content)
            elif edit_type == 'delete':
                if 0 <= line_num < len(lines):
                    lines.pop(line_num)
            elif edit_type == 'replace':
                if 0 <= line_num < len(lines):
                    lines[line_num] = edit_content
        
        new_content = '\n'.join(lines)
        file_path.write_text(new_content, encoding='utf-8')
        
        result = {
            "success": True,
            "path": str(file_path),
            "edits_applied": len(edits)
        }
        
        logger.info(f"编辑文件: {file_path}, 应用了 {len(edits)} 个编辑")
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        logger.error(f"编辑文件失败: {e}")
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)


def save_context_to_file(conversation_id: int, task_id: str, step_id: str, content: str) -> str:
    """保存上下文到文件"""
    try:
        base_dir = Path(settings.WORKSPACE_DIR if hasattr(settings, 'WORKSPACE_DIR') else "./workspace")
        task_dir = base_dir / "planning" / str(conversation_id) / f"task_{task_id}"
        context_dir = task_dir / "context"
        context_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = context_dir / f"step_{step_id}_context.txt"
        file_path.write_text(content, encoding='utf-8')
        
        logger.info(f"保存上下文到文件: {file_path}")
        return str(file_path)
    except Exception as e:
        logger.error(f"保存上下文失败: {e}")
        raise


def write_todos_wrapper(todos_str: str, dependencies_str: str = "{}") -> str:
    """write_todos 工具的包装器"""
    try:
        todos = json.loads(todos_str) if isinstance(todos_str, str) else todos_str
        deps = json.loads(dependencies_str) if isinstance(dependencies_str, str) and dependencies_str else None
        return write_todos_tool(todos, deps)
    except Exception as e:
        return json.dumps({"success": False, "error": f"参数解析失败: {str(e)}"}, ensure_ascii=False)


def create_task_agent_wrapper(task_description: str, tools_str: str = "[]", context_str: str = "{}") -> str:
    """create_task_agent 工具的包装器"""
    try:
        tools = json.loads(tools_str) if isinstance(tools_str, str) and tools_str else None
        context = json.loads(context_str) if isinstance(context_str, str) and context_str else None
        return create_task_agent_tool(task_description, tools, context)
    except Exception as e:
        return json.dumps({"success": False, "error": f"参数解析失败: {str(e)}"}, ensure_ascii=False)


def edit_file_wrapper(path: str, edits_str: str) -> str:
    """edit_file 工具的包装器"""
    try:
        edits = json.loads(edits_str) if isinstance(edits_str, str) else edits_str
        return edit_file_tool(path, edits)
    except Exception as e:
        return json.dumps({"success": False, "error": f"参数解析失败: {str(e)}"}, ensure_ascii=False)


def create_planning_tools() -> List[Tool]:
    """创建任务规划相关工具列表"""
    tools = [
        Tool(
            name="write_todos",
            func=write_todos_wrapper,
            description="""创建任务列表。输入格式：第一个参数是JSON格式的任务列表字符串，第二个参数是JSON格式的依赖关系映射（可选）。
任务列表格式：[{"id": "step_001", "description": "任务描述", "priority": "high", "estimated_time": "1h"}, ...]
依赖关系格式：{"step_002": ["step_001"], "step_003": ["step_001", "step_002"]}
示例：write_todos('[{"id":"step_001","description":"设计数据库","priority":"high","estimated_time":"2h"}]', '{}')"""
        ),
        Tool(
            name="create_task_agent",
            func=create_task_agent_wrapper,
            description="""创建子代理处理特定任务。输入：task_description（任务描述字符串）、tools（工具列表JSON字符串，可选）、context（上下文JSON字符串，可选）。
示例：create_task_agent("分析数据", "[]", "{}")"""
        ),
        Tool(
            name="ls",
            func=ls_tool,
            description="列出目录内容。输入：path（目录路径字符串，默认为当前目录）。"
        ),
        Tool(
            name="read_file",
            func=read_file_tool,
            description="读取文件内容。输入：path（文件路径字符串）。"
        ),
        Tool(
            name="write_file",
            func=write_file_tool,
            description="写入文件内容。输入：path（文件路径字符串）、content（文件内容字符串）。"
        ),
        Tool(
            name="edit_file",
            func=edit_file_wrapper,
            description="""编辑文件内容。输入：path（文件路径字符串）、edits（编辑操作列表JSON字符串）。
编辑操作格式：[{"type": "insert", "line": 1, "content": "新内容"}, {"type": "delete", "line": 2}, {"type": "replace", "line": 3, "content": "替换内容"}]"""
        )
    ]
    
    return tools

