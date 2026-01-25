"""测试工具调用的流式响应格式"""
import requests
import json
import sys

def test_tool_call_stream():
    """测试包含工具调用的流式响应格式"""
    url = "http://localhost:8000/api/chat/stream"
    
    # 测试数据 - 询问需要联网搜索的问题
    payload = {
        "message": "北京今天天气怎么样？",
        "llm_config": {
            "provider": "dashscope",
            "model": "qwen-turbo"
        },
        "search_provider": "tavily"
    }
    
    print("发送请求:", payload)
    print("\n开始接收流式响应...\n")
    
    response = requests.post(url, json=payload, stream=True, timeout=120)
    
    if response.status_code != 200:
        print(f"❌ 请求失败: {response.status_code}")
        print(response.text)
        return False
    
    chunk_count = 0
    valid_chunks = 0
    invalid_chunks = []
    
    tool_call_count = 0
    tool_result_count = 0
    
    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8')
            
            # SSE 格式：data: {...}
            if line_str.startswith('data: '):
                chunk_count += 1
                data_str = line_str[6:]  # 移除 "data: " 前缀
                
                try:
                    chunk = json.loads(data_str)
                    
                    # 验证必需字段
                    if 'type' not in chunk:
                        invalid_chunks.append(f"缺少 'type' 字段: {chunk}")
                        continue
                    
                    if 'timestamp' not in chunk:
                        invalid_chunks.append(f"缺少 'timestamp' 字段: {chunk}")
                        continue
                    
                    # 验证 data 字段
                    chunk_type = chunk['type']
                    if chunk_type not in ['done'] and 'data' not in chunk:
                        invalid_chunks.append(f"缺少 'data' 字段: {chunk}")
                        continue
                    
                    # 特别验证工具相关的 chunk
                    if chunk_type == 'tool_call':
                        tool_call_count += 1
                        data = chunk.get('data', {})
                        if 'tool_name' not in data:
                            invalid_chunks.append(f"tool_call chunk 缺少 tool_name: {chunk}")
                            continue
                        if 'tool_input' not in data:
                            invalid_chunks.append(f"tool_call chunk 缺少 tool_input: {chunk}")
                            continue
                        print(f"✓ [tool_call] tool={data['tool_name']}, input={str(data['tool_input'])[:50]}...")
                        
                    elif chunk_type == 'tool_result':
                        tool_result_count += 1
                        data = chunk.get('data', {})
                        if 'tool_name' not in data:
                            invalid_chunks.append(f"tool_result chunk 缺少 tool_name: {chunk}")
                            continue
                        if 'tool_output' not in data:
                            invalid_chunks.append(f"tool_result chunk 缺少 tool_output: {chunk}")
                            continue
                        output_preview = str(data['tool_output'])[:80]
                        print(f"✓ [tool_result] tool={data['tool_name']}, output={output_preview}...")
                        
                    elif chunk_type == 'thinking':
                        thinking_text = chunk['data'].get('thinking', '')[:50]
                        print(f"✓ [thinking] {thinking_text}...")
                        
                    elif chunk_type == 'content':
                        content = chunk['data'].get('content', '')[:50]
                        print(f"✓ [content] {content}...")
                        
                    elif chunk_type == 'done':
                        print(f"✓ [done] 流式响应完成")
                        
                    elif chunk_type == 'conversation_id':
                        print(f"✓ [conversation_id] id={chunk['data']['conversation_id']}")
                    
                    valid_chunks += 1
                    
                except json.JSONDecodeError as e:
                    print(f"❌ JSON 解析错误: {e}")
                    print(f"   原始数据: {data_str}")
                    invalid_chunks.append(f"JSON 解析失败: {data_str}")
    
    # 打印测试结果
    print("\n" + "="*60)
    print("测试结果:")
    print(f"  总 chunk 数: {chunk_count}")
    print(f"  有效 chunk 数: {valid_chunks}")
    print(f"  无效 chunk 数: {len(invalid_chunks)}")
    print(f"  tool_call 数: {tool_call_count}")
    print(f"  tool_result 数: {tool_result_count}")
    
    if invalid_chunks:
        print("\n❌ 无效的 chunks:")
        for invalid in invalid_chunks:
            print(f"  - {invalid}")
        return False
    
    # 验证工具调用和结果配对
    if tool_call_count != tool_result_count:
        print(f"\n⚠️  警告: tool_call ({tool_call_count}) 和 tool_result ({tool_result_count}) 数量不匹配")
    
    if tool_call_count > 0 and tool_result_count > 0:
        print(f"\n✅ 成功测试工具调用！tool_call 和 tool_result 都已正确实现")
    
    print("\n✅ 所有 chunks 格式正确，符合前端契约！")
    return True

if __name__ == "__main__":
    success = test_tool_call_stream()
    sys.exit(0 if success else 1)
