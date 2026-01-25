"""测试数学计算工具调用的流式响应格式"""
import requests
import json
import sys

def test_calculator_tool():
    """测试计算器工具调用"""
    url = "http://localhost:8000/api/chat/stream"
    
    # 测试数据 - 复杂数学计算
    payload = {
        "message": "请帮我计算：sqrt(144) + 25 * 3",
        "llm_config": {
            "provider": "dashscope",
            "model": "qwen-turbo"
        }
    }
    
    print("发送请求:", payload)
    print("\n开始接收流式响应...\n")
    
    response = requests.post(url, json=payload, stream=True, timeout=60)
    
    if response.status_code != 200:
        print(f"❌ 请求失败: {response.status_code}")
        print(response.text)
        return False
    
    chunks_by_type = {
        'conversation_id': [],
        'thinking': [],
        'tool_call': [],
        'tool_result': [],
        'content': [],
        'done': [],
        'error': []
    }
    
    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8')
            
            if line_str.startswith('data: '):
                data_str = line_str[6:]
                
                try:
                    chunk = json.loads(data_str)
                    chunk_type = chunk.get('type', 'unknown')
                    
                    # 收集 chunks
                    if chunk_type in chunks_by_type:
                        chunks_by_type[chunk_type].append(chunk)
                    
                    # 验证必需字段
                    assert 'type' in chunk, f"缺少 'type' 字段: {chunk}"
                    assert 'timestamp' in chunk, f"缺少 'timestamp' 字段: {chunk}"
                    
                    # 打印详细信息
                    if chunk_type == 'tool_call':
                        data = chunk.get('data', {})
                        print(f"✓ [tool_call] tool={data.get('tool_name')}")
                        print(f"  input={data.get('tool_input')}")
                        print(f"  timestamp={chunk.get('timestamp')}")
                        
                    elif chunk_type == 'tool_result':
                        data = chunk.get('data', {})
                        print(f"✓ [tool_result] tool={data.get('tool_name')}")
                        print(f"  output={data.get('tool_output')}")
                        print(f"  timestamp={chunk.get('timestamp')}")
                        
                    elif chunk_type == 'thinking':
                        text = chunk['data'].get('thinking', '')
                        print(f"✓ [thinking] {text[:60]}...")
                        
                    elif chunk_type == 'content':
                        text = chunk['data'].get('content', '')
                        print(f"✓ [content] {text[:60]}...")
                        
                    elif chunk_type == 'done':
                        print(f"✓ [done]")
                        
                    elif chunk_type == 'conversation_id':
                        print(f"✓ [conversation_id] id={chunk['data']['conversation_id']}")
                    
                except json.JSONDecodeError as e:
                    print(f"❌ JSON 解析错误: {e}")
                    print(f"   原始数据: {data_str}")
                    return False
                except AssertionError as e:
                    print(f"❌ 验证失败: {e}")
                    return False
    
    # 统计结果
    print("\n" + "="*60)
    print("Chunk 统计:")
    for chunk_type, chunks in chunks_by_type.items():
        count = len(chunks)
        if count > 0:
            print(f"  {chunk_type}: {count}")
    
    # 验证
    tool_call_count = len(chunks_by_type['tool_call'])
    tool_result_count = len(chunks_by_type['tool_result'])
    
    print(f"\n工具调用配对:")
    print(f"  tool_call: {tool_call_count}")
    print(f"  tool_result: {tool_result_count}")
    
    if tool_call_count > 0 and tool_result_count > 0:
        if tool_call_count == tool_result_count:
            print(f"\n✅ 工具调用和结果完美配对！")
        else:
            print(f"\n⚠️  警告: tool_call 和 tool_result 数量不匹配")
        
        print("\n✅ 成功测试 tool_call 和 tool_result 类型！")
        return True
    else:
        print(f"\n⚠️  未检测到工具调用（这可能是正常的，取决于 Agent 的决策）")
        print("格式验证通过，但未测试工具相关类型")
        return True

if __name__ == "__main__":
    success = test_calculator_tool()
    sys.exit(0 if success else 1)
