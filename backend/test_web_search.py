"""测试联网搜索工具"""
import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.tools.web_search_tool import create_web_search_tool
from app.core.config import settings
from loguru import logger

# 配置日志
logger.remove()
logger.add(sys.stderr, level="INFO")


def test_current_search_provider():
    """测试当前配置的搜索提供商"""
    print("\n" + "="*60)
    print(f"测试当前搜索提供商: {settings.SEARCH_PROVIDER}")
    print("="*60)
    
    # 根据配置检查对应的API key
    provider = settings.SEARCH_PROVIDER.lower()
    if provider == 'tavily':
        if not settings.TAVILY_API_KEY:
            print("❌ TAVILY_API_KEY 未配置")
            return False
        print(f"✓ TAVILY_API_KEY 已配置: {settings.TAVILY_API_KEY[:10]}...")
    elif provider == 'baidu':
        if not settings.BAIDU_ENABLED:
            print("ℹ️  BAIDU_ENABLED 未启用")
            return None
        if not settings.BAIDU_API_KEY:
            print("❌ BAIDU_API_KEY 未配置")
            return False
        print(f"✓ BAIDU_ENABLED: {settings.BAIDU_ENABLED}")
        print(f"✓ BAIDU_API_KEY 已配置: {settings.BAIDU_API_KEY[:10]}...")
    
    # 创建搜索工具
    tool = create_web_search_tool()
    
    if not tool:
        print(f"❌ 无法创建搜索工具（提供商: {provider}）")
        return False
    
    print(f"✓ 成功创建搜索工具: {tool.name}")
    print(f"  描述: {tool.description}")
    
    # 执行测试搜索
    test_query = "What is Python" if provider == 'tavily' else "Python编程语言"
    print(f"\n执行搜索: {test_query}")
    print("-" * 60)
    
    try:
        result = tool.invoke(test_query)
        print(f"搜索结果类型: {type(result)}")
        print(f"搜索结果长度: {len(str(result))}")
        print("\n搜索结果内容:")
        print(result)
        print("-" * 60)
        
        # 检查结果是否有效
        result_str = str(result)
        if result_str and len(result_str) > 50:
            # 检查是否包含URL或有效内容
            has_url = "http" in result_str.lower()
            has_content = len(result_str) > 100
            
            if has_url or has_content:
                print(f"✓ {provider.upper()} 搜索测试成功")
                return True
            else:
                print(f"❌ {provider.upper()} 搜索返回结果可能无效（缺少URL或内容太短）")
                return False
        else:
            print(f"❌ {provider.upper()} 搜索返回结果异常（内容太短）")
            return False
            
    except Exception as e:
        print(f"❌ {provider.upper()} 搜索失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("\n🔍 开始测试联网搜索工具")
    print("="*60)
    print(f"当前配置的搜索提供商: {settings.SEARCH_PROVIDER}")
    print("="*60)
    
    # 测试当前配置的搜索提供商
    result = test_current_search_provider()
    
    # 打印测试总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    if result is True:
        status = "✓ 通过"
        print(f"{settings.SEARCH_PROVIDER.upper():10s}: {status}")
        print(f"\n✓ 搜索工具测试通过")
        sys.exit(0)
    elif result is False:
        status = "✗ 失败"
        print(f"{settings.SEARCH_PROVIDER.upper():10s}: {status}")
        print(f"\n❌ 搜索工具测试失败")
        sys.exit(1)
    else:
        status = "- 跳过"
        print(f"{settings.SEARCH_PROVIDER.upper():10s}: {status}")
        print(f"\nℹ️  测试被跳过")
        sys.exit(0)


if __name__ == "__main__":
    main()
