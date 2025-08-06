import ollama
from src.embedding.ollama_embedder import OllamaEmbedder
from src.vector_store.chroma_store import ChromaStore
from settings import config

##########################################################################
###########################[ Global Variables ]###########################

VECTOR_STORE_PATH   = config["VECTOR_STORE_PATH"]
MODEL               = config["MODEL"]
CODE_EXTENSIONS     = config["CODE_EXTENSIONS"]
OLLAMA_URL          = config["OLLAMA_URL"]

##########################################################################
####################[ Create Embedder & Text Splitter ]###################

embedder = OllamaEmbedder(
    url=OLLAMA_URL,
    model_name=MODEL,
    timeout=120
)

##########################################################################
########################[ Create Vector Store ]###########################

vector_store = ChromaStore(
    embedder=embedder,
    persist_directory=VECTOR_STORE_PATH
)

##########################################################################
#########################[ Define Tools ]#################################

def search_docs(query, k=3):
    docs = vector_store.vector_store.similarity_search(query, k=k)
    return "\n\n".join([doc.page_content for doc in docs])


def is_tool_call(response_text: str):
    return "search_docs(" in response_text


def chat_with_tools(user_query):
    import requests
    import json
    OLLAMA_API_URL = OLLAMA_URL.rstrip("/") + "/api/chat"
    tools = [
        {
            "name": "search_docs",
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
    messages = [
        {"role": "user", "content": user_query}
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

        # Only support search_docs tool
        for tc in parsed_tool_calls:
            tool_name = tc["name"]
            arguments = tc["arguments"]
            tool_id = tc["id"]
            if tool_name == "search_docs" and arguments:
                query = arguments.get("query")
                k = arguments.get("k", 3)
                tool_result = search_docs(query, k)
                tool_response_message = {
                    "role": "tool",
                    "tool_call_id": tool_id,
                    "content": tool_result
                }
                messages.append(message)  # model's tool_call message
                messages.append(tool_response_message)  # tool's result

if __name__ == "__main__":
    chat_with_tools("how to add kernel function to enable graph streaming in TIOVX")
