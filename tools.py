import requests
import json
import time

OLLAMA_API_URL = 'http://localhost:11434/api/chat'


# Define multiple tools
tools = [
    {
        "name": "get_current_weather",
        "description": "Get the current weather in a given city",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name"
                }
            },
            "required": ["city"]
        }
    },
    {
        "name": "get_time",
        "description": "Get the current time in a given city",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name"
                }
            },
            "required": ["city"]
        }
    },
    {
        "name": "get_greeting",
        "description": "Get a greeting for a given name",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Person's name"
                }
            },
            "required": ["name"]
        }
    }
]

# Tool handler functions
def get_current_weather(city):
    return f"The weather in {city} is 29°C and partly cloudy."

def get_time(city):
    import datetime
    now = datetime.datetime.now().strftime('%H:%M:%S')
    return f"The current time in {city} is {now}."

def get_greeting(name):
    return f"Hello, {name}! Hope you have a great day."

# Map tool names to handler functions
tool_handlers = {
    "get_current_weather": lambda args: get_current_weather(args.get("city") or args.get("location")),
    "get_weather": lambda args: get_current_weather(args.get("city") or args.get("location")),
    "getWeather": lambda args: get_current_weather(args.get("city") or args.get("location")),
    "get_time": lambda args: get_time(args.get("city") or args.get("location")),
    "getTime": lambda args: get_time(args.get("city") or args.get("location")),
    "get_greeting": lambda args: get_greeting(args.get("name")),
    "getGreeting": lambda args: get_greeting(args.get("name")),
}

# Create the initial chat
def run_chat():
    messages = [
        {
            "role": "user",
            "content": "What is the weather like in Mumbai today? also tell me the time there."
        }
    ]

    while True:
        response = requests.post(OLLAMA_API_URL, json={
            "model": "qwen2.5-coder:7b",
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
                # Use regex to extract all JSON objects from the string
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
                                "id": None
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

        # Process all tool calls
        for tc in parsed_tool_calls:
            tool_name = tc["name"]
            arguments = tc["arguments"]
            tool_id = tc["id"]
            handler = tool_handlers.get(tool_name)
            if handler and arguments:
                tool_result = handler(arguments)
                tool_response_message = {
                    "role": "tool",
                    "tool_call_id": tool_id,
                    "content": tool_result
                }
                messages.append(message)  # model's tool_call message
                messages.append(tool_response_message)  # tool's result

if __name__ == "__main__":
    run_chat()
