#!/usr/bin/env python3
"""测试流式响应修复"""
import asyncio
from backend.app.services.streaming.stream_handler import StreamCallbackHandler


async def test_non_agent_mode():
    """测试非Agent模式（直接对话）"""
    print("=== Testing Non-Agent Mode ===")
    handler = StreamCallbackHandler()
    
    # 模拟LLM开始
    await handler.on_llm_start({}, [])
    
    # 模拟接收token（没有Agent标记）
    tokens = ["你好", "！", "看起来", "你", "输入了", '"1"', "。", "有什么", "具体的", "问题", "或", "需要帮助", "的地方", "吗？"]
    
    for token in tokens:
        await handler.on_llm_new_token(token)
        
        # 检查是否有新数据
        while handler.has_new_data():
            chunk = handler.get_latest_chunk()
            print(f"Chunk: {chunk}")
    
    # 模拟LLM结束
    await handler.on_llm_end({})
    
    # 获取剩余的chunk
    while handler.has_new_data():
        chunk = handler.get_latest_chunk()
        print(f"Final Chunk: {chunk}")
    
    print("\n")


async def test_agent_mode():
    """测试Agent模式"""
    print("=== Testing Agent Mode ===")
    handler = StreamCallbackHandler()
    
    # 模拟LLM开始
    await handler.on_llm_start({}, [])
    
    # 模拟接收token（带Agent标记）
    tokens = [
        "Thought: ", "我需要", "思考", "一下", "\n",
        "Action: ", "calculator\n",
        "Action Input: ", "1+1\n",
        "Final Answer: ", "答案是", "2"
    ]
    
    for token in tokens:
        await handler.on_llm_new_token(token)
        
        # 检查是否有新数据
        while handler.has_new_data():
            chunk = handler.get_latest_chunk()
            print(f"Chunk: {chunk}")
    
    # 模拟LLM结束
    await handler.on_llm_end({})
    
    # 获取剩余的chunk
    while handler.has_new_data():
        chunk = handler.get_latest_chunk()
        print(f"Final Chunk: {chunk}")


if __name__ == "__main__":
    asyncio.run(test_non_agent_mode())
    asyncio.run(test_agent_mode())
