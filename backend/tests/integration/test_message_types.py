"""
集成测试：消息类型生成
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock
from app.services.message_formatter import message_formatter
from app.services.agent_service import agent_service
from app.api.schemas import MessageType


class TestMessageTypes:
    """测试不同消息类型的生成"""
    
    def test_format_text_chunk(self):
        """测试文本块格式化"""
        chunk = message_formatter.format_text("Hello, world!")
        
        assert chunk.type == MessageType.TEXT
        assert chunk.content == "Hello, world!"
    
    def test_format_thinking_chunk(self):
        """测试思考块格式化"""
        chunk = message_formatter.format_thinking(
            "Let me analyze this problem...",
            reasoning_step=1
        )
        
        assert chunk.type == MessageType.THINKING
        assert chunk.content == "Let me analyze this problem..."
        assert chunk.reasoning_step == 1
    
    def test_format_tool_call_chunk(self):
        """测试工具调用块格式化"""
        chunk = message_formatter.format_tool_call(
            tool_name="web_search",
            tool_input={"query": "Python tutorial"},
            tool_output="Search results...",
            status="completed"
        )
        
        assert chunk.type == MessageType.TOOL
        assert chunk.tool_name == "web_search"
        assert chunk.tool_input == {"query": "Python tutorial"}
        assert chunk.tool_output == "Search results..."
        assert chunk.status == "completed"
    
    def test_format_plan_step_chunk(self):
        """测试计划步骤块格式化"""
        chunk = message_formatter.format_plan_step(
            step_number=1,
            description="Analyze requirements",
            status="completed",
            result="Requirements documented"
        )
        
        assert chunk.type == MessageType.PLAN
        assert chunk.step_number == 1
        assert chunk.description == "Analyze requirements"
        assert chunk.status == "completed"
        assert chunk.result == "Requirements documented"
    
    def test_format_system_chunk(self):
        """测试系统消息块格式化"""
        chunk = message_formatter.format_system(
            "Task completed successfully",
            level="info"
        )
        
        assert chunk.type == MessageType.SYSTEM
        assert chunk.content == "Task completed successfully"
        assert chunk.level == "info"
    
    def test_detect_message_type_thinking(self):
        """测试思考类型检测"""
        old_chunk = {
            "type": "thinking",
            "data": {"thinking": "Let me think..."}
        }
        
        msg_type = message_formatter.detect_message_type(old_chunk)
        assert msg_type == MessageType.THINKING
    
    def test_detect_message_type_tool(self):
        """测试工具调用类型检测"""
        old_chunk = {
            "type": "tool_call",
            "data": {"tool_name": "calculator"}
        }
        
        msg_type = message_formatter.detect_message_type(old_chunk)
        assert msg_type == MessageType.TOOL
    
    def test_detect_message_type_content(self):
        """测试内容类型检测"""
        old_chunk = {
            "type": "content",
            "data": {"content": "Here is the answer"}
        }
        
        msg_type = message_formatter.detect_message_type(old_chunk)
        assert msg_type == MessageType.TEXT
    
    def test_convert_legacy_message_with_thinking(self):
        """测试包含thinking字段的旧消息转换"""
        legacy_msg = {
            "content": "Final answer",
            "thinking": "Let me analyze this...",
            "intermediate_steps": []
        }
        
        chunks = agent_service.convert_legacy_message_to_chunks(legacy_msg)
        
        # 应该有2个chunks：thinking + text
        assert len(chunks) >= 2
        assert chunks[0]["type"] == "thinking"
        assert chunks[0]["content"] == "Let me analyze this..."
    
    def test_convert_legacy_message_with_tools(self):
        """测试包含工具调用的旧消息转换"""
        legacy_msg = {
            "content": "Found the answer",
            "intermediate_steps": [
                {
                    "tool": "web_search",
                    "input": "Python",
                    "output": "Python is a programming language"
                }
            ]
        }
        
        chunks = agent_service.convert_legacy_message_to_chunks(legacy_msg)
        
        # 应该有2个chunks：tool + text
        assert len(chunks) >= 2
        has_tool_chunk = any(c["type"] == "tool" for c in chunks)
        assert has_tool_chunk
    
    def test_convert_legacy_message_complete(self):
        """测试完整旧消息转换（包含thinking、tools、content）"""
        legacy_msg = {
            "content": "Based on the search, Python is great!",
            "thinking": "User wants to know about Python",
            "intermediate_steps": [
                {
                    "tool": "web_search",
                    "input": "What is Python",
                    "output": "Python is a high-level programming language"
                }
            ]
        }
        
        chunks = agent_service.convert_legacy_message_to_chunks(legacy_msg)
        
        # 应该有3个chunks：thinking + tool + text
        assert len(chunks) == 3
        assert chunks[0]["type"] == "thinking"
        assert chunks[1]["type"] == "tool"
        assert chunks[2]["type"] == "text"


class TestMessageTypeIntegration:
    """集成测试：消息类型在流式输出中的生成"""
    
    @pytest.mark.asyncio
    async def test_stream_generates_text_chunks(self, db_session):
        """测试流式输出生成文本块"""
        # 这个测试需要实际的Agent实例和Mock的LLM
        # 可以通过Mock agent_service.chat_stream来测试
        pass
    
    @pytest.mark.asyncio
    async def test_stream_generates_thinking_chunks(self, db_session):
        """测试流式输出生成思考块"""
        # Mock Agent返回thinking chunks
        pass
    
    @pytest.mark.asyncio
    async def test_stream_generates_tool_chunks(self, db_session):
        """测试流式输出生成工具调用块"""
        # Mock Agent调用工具并返回tool chunks
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
