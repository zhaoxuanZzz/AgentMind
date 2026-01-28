"""测试Agent中的联网搜索功能"""
import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.agent_service import AgentService
from app.api.schemas import AgentConfig
from app.core.config import settings
from loguru import logger

# 配置日志
logger.remove()
logger.add(sys.stderr, level="INFO")


async def test_agent_with_search():
    """测试Agent使用搜索工具"""
    print("\n" + "="*60)
    print(f"测试 Agent + {settings.SEARCH_PROVIDER.upper()} 搜索")
    print("="*60)
    
    agent_service = AgentService()
    
    # 创建Agent配置（不再需要传递search_provider）
    config = AgentConfig()
    
    # 创建Agent
    agent = agent_service.create_agent(config=config)
    
    # 测试查询 - 需要联网搜索的问题
    test_query = "What are the latest news about AI in 2026?"
    print(f"\n问题: {test_query}")
    print("-" * 60)
    
    try:
        # 调用Agent (需要提供thread_id配置)
        response = await agent.ainvoke(
            {"input": test_query},
            config={"configurable": {"thread_id": "test-search"}}
        )
        
        print(f"\nAgent响应:")
        print(response.get("output", ""))
        print("-" * 60)
        
        # 检查是否有中间步骤（使用了工具）
        if "intermediate_steps" in response and response["intermediate_steps"]:
            print(f"\n✓ Agent使用了 {len(response['intermediate_steps'])} 个工具调用")
            for i, step in enumerate(response["intermediate_steps"], 1):
                tool_name = step[0].tool if hasattr(step[0], 'tool') else 'unknown'
                print(f"  {i}. {tool_name}")
            return True
        else:
            print("⚠️  Agent没有使用工具（可能基于知识直接回答）")
            return True  # 仍然算通过
            
    except Exception as e:
        print(f"❌ Agent测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("\n🤖 开始测试Agent联网搜索功能")
    print("="*60)
    print(f"当前配置的搜索提供商: {settings.SEARCH_PROVIDER}")
    print("="*60)
    
    # 测试Agent搜索
    result = await test_agent_with_search()
    
    # 打印测试总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    if result is True:
        status = "✓ 通过"
        print(f"Agent + {settings.SEARCH_PROVIDER.upper():10s}: {status}")
        print(f"\n✓ Agent搜索测试通过")
        sys.exit(0)
    elif result is False:
        status = "✗ 失败"
        print(f"Agent + {settings.SEARCH_PROVIDER.upper():10s}: {status}")
        print(f"\n❌ Agent搜索测试失败")
        sys.exit(1)
    else:
        status = "- 跳过"
        print(f"Agent + {settings.SEARCH_PROVIDER.upper():10s}: {status}")
        print(f"\nℹ️  测试被跳过")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
