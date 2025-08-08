import requests
import json
from settings import config

OLLAMA_URL = config["OLLAMA_URL"]

def search_code(vector_store, query, k=3):
    docs = vector_store.vector_store.similarity_search(query, k=k)
    return "\n\n".join([doc.page_content for doc in docs])

def chat_with_tools(messages, vector_store):

    OLLAMA_API_URL = OLLAMA_URL.rstrip("/") + "/api/chat"
    tools = [
        {
            "name": "search_code",
            "description": "Searches codebase documents for relevant information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "k": {"type": "integer", "description": "Number of results", "default": 3}
                },
                "required": ["query"]
            }
        }
    ]

    while True:
        response = requests.post(OLLAMA_API_URL, json={
            "model": "qwen2.5-coder:3b",
            "messages": messages,
            "tools": tools,
            "stream": False
        })
        result = response.json()
        message = result.get('message', {})
        print("🤖 Model Response:")
        print(json.dumps(message, indent=2))

        # Try to get tool calls from 'tool_calls' or parse from 'content'
        tool_calls = message.get("tool_calls")
        parsed_tool_calls = []
        if tool_calls:
            for tc in tool_calls:
                try:
                    arguments = json.loads(tc['arguments']) if isinstance(tc['arguments'], str) else tc['arguments']
                except Exception:
                    arguments = tc['arguments']
                parsed_tool_calls.append({
                    "name": tc['name'],
                    "arguments": arguments,
                    "id": tc.get("id")
                })
        else:
            # Fallback: parse tool call(s) from 'content' if present
            if isinstance(message.get("content"), str):
                content_str = message["content"].strip()
                import re
                json_objects = re.findall(r'\{[^{}]*\{[^{}]*\}[^{}]*\}|\{[^{}]*\}', content_str)
                for obj_str in json_objects:
                    obj_str = obj_str.strip()
                    try:
                        content_json = json.loads(obj_str)
                        if isinstance(content_json, dict) and content_json.get("name"):
                            parsed_tool_calls.append({
                                "name": content_json.get("name"),
                                "arguments": content_json.get("arguments", {}),
                            })
                            print("\n🔧 Parsed Tool Call from content:")
                            print(json.dumps(parsed_tool_calls[-1], indent=2))
                    except Exception as e:
                        print(f"Error parsing tool call from content: {e}\nContent: {obj_str}")

        # If no tool calls, break and print final answer
        if not parsed_tool_calls:
            print("\n✅ Final Model Reply:")
            print(message.get("content", "No content returned."))
            break

        # Only support search_docs tool
        for tc in parsed_tool_calls:
            print(f"\n🔧 Tool Call: {tc}")
            tool_name = tc["name"]
            arguments = tc["arguments"]
            if tool_name == "search_code" and arguments:
                query = arguments.get("query")
                k = arguments.get("k", 3)
                tool_result = search_code(vector_store, query, k)
                print(f"\n🔧 Tool Result: {tool_result}")
                tool_response_message = {
                    "role": "tool",
                    "content": tool_result
                }
                messages.append(message)  # model's tool_call message
                messages.append(tool_response_message)  # tool's result