"""测试流式响应格式是否符合前端契约"""
import requests
import json
import sys

def test_stream_format():
    """测试流式响应格式"""
    url = "http://localhost:8000/api/chat/stream"
    
    # 测试数据
    payload = {
        "message": "你好",
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
    
    chunk_count = 0
    valid_chunks = 0
    invalid_chunks = []
    
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
                    
                    # 验证 data 字段（除了某些类型可能没有 data）
                    chunk_type = chunk['type']
                    if chunk_type not in ['done'] and 'data' not in chunk:
                        invalid_chunks.append(f"缺少 'data' 字段: {chunk}")
                        continue
                    
                    # 根据类型验证 data 内容
                    if chunk_type == 'conversation_id':
                        if 'conversation_id' not in chunk.get('data', {}):
                            invalid_chunks.append(f"conversation_id chunk 缺少 conversation_id 字段: {chunk}")
                            continue
                    elif chunk_type == 'thinking':
                        if 'thinking' not in chunk.get('data', {}):
                            invalid_chunks.append(f"thinking chunk 缺少 thinking 字段: {chunk}")
                            continue
                    elif chunk_type == 'tool_call':
                        data = chunk.get('data', {})
                        if 'tool_name' not in data or 'tool_input' not in data:
                            invalid_chunks.append(f"tool_call chunk 缺少必需字段: {chunk}")
                            continue
                    elif chunk_type == 'tool_result':
                        data = chunk.get('data', {})
                        if 'tool_name' not in data or 'tool_output' not in data:
                            invalid_chunks.append(f"tool_result chunk 缺少必需字段: {chunk}")
                            continue
                    elif chunk_type == 'content':
                        if 'content' not in chunk.get('data', {}):
                            invalid_chunks.append(f"content chunk 缺少 content 字段: {chunk}")
                            continue
                    elif chunk_type == 'error':
                        if 'message' not in chunk.get('data', {}):
                            invalid_chunks.append(f"error chunk 缺少 message 字段: {chunk}")
                            continue
                    
                    valid_chunks += 1
                    
                    # 打印 chunk 信息（简化版）
                    if chunk_type == 'conversation_id':
                        print(f"✓ [{chunk_type}] conversation_id={chunk['data']['conversation_id']}")
                    elif chunk_type == 'thinking':
                        thinking_text = chunk['data']['thinking'][:50]
                        print(f"✓ [{chunk_type}] {thinking_text}...")
                    elif chunk_type == 'tool_call':
                        print(f"✓ [{chunk_type}] tool={chunk['data']['tool_name']}")
                    elif chunk_type == 'tool_result':
                        output = str(chunk['data']['tool_output'])[:50]
                        print(f"✓ [{chunk_type}] tool={chunk['data']['tool_name']}, output={output}...")
                    elif chunk_type == 'content':
                        content = chunk['data']['content'][:50]
                        print(f"✓ [{chunk_type}] {content}...")
                    elif chunk_type == 'done':
                        print(f"✓ [{chunk_type}] 流式响应完成")
                    elif chunk_type == 'error':
                        print(f"✗ [{chunk_type}] {chunk['data']['message']}")
                    
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
    
    if invalid_chunks:
        print("\n❌ 无效的 chunks:")
        for invalid in invalid_chunks:
            print(f"  - {invalid}")
        return False
    else:
        print("\n✅ 所有 chunks 格式正确，符合前端契约！")
        return True

if __name__ == "__main__":
    success = test_stream_format()
    sys.exit(0 if success else 1)
