import requests
import json
from settings import config, TerminalColor, print_colored
from src.llm.ollama import OllamaClient

MAIN_MODEL = config["MAIN_MODEL"]
DEBUG_MODE = config["DEBUG_MODE"]


client = OllamaClient()

def search_code(vector_store, query, k=3):
    docs = vector_store.vector_store.similarity_search(query, k=k)

    results = ""
    for doc in docs:
        divider = "-" * 50
        results += (
            f"{divider}\n"
            f"## Found in {doc.metadata['file_path']} \n\n```{doc.metadata['language']}\n"
            f"{doc.page_content}\n```\n"
            f"{divider}\n\n"
        )

    return results

def chat_with_tools(messages, vector_store, model=MAIN_MODEL):
    user_msg = messages[-1]

    while True:

        response_stream = client.chat(
            model=model,
            messages=messages,
            stream=True
        )
        print_colored("🤖 Model Response:", TerminalColor.BLUE)

        is_thinking = False
        llm_response = ""
        for line in response_stream:
            if line:
                try:
                    content = json.loads(line.decode('utf-8'))
                    token = content["message"].get('content', '')

                    if token.strip() == "<think>":
                        is_thinking = True
                    elif token.strip() == "</think>":
                        is_thinking = False
                        print_colored(f"{token}", TerminalColor.LIGHT_GRAY, end="", flush=True)
                        continue
                        
                    if is_thinking:
                        print_colored(f"{token}", TerminalColor.LIGHT_GRAY, end="", flush=True)
                    else:
                        llm_response += token
                        print_colored(f"{token}", TerminalColor.CYAN, end="", flush=True)

                    if content.get("done", False) and DEBUG_MODE:
                        print_colored("\n====================================", TerminalColor.LIGHT_GRAY)
                        print_colored(f'Total Duration: {content["total_duration"]}', TerminalColor.LIGHT_GRAY)
                        print_colored(f'Load Duration: {content["load_duration"]}', TerminalColor.LIGHT_GRAY)
                        print_colored(f'Prompt Eval Count: {content["prompt_eval_count"]}', TerminalColor.LIGHT_GRAY)
                        print_colored(f'Prompt Eval Duration: {content["prompt_eval_duration"]}', TerminalColor.LIGHT_GRAY)
                        print_colored(f'Eval Count: {content["eval_count"]}', TerminalColor.LIGHT_GRAY)
                        print_colored(f'Eval Duration: {content["eval_duration"]}', TerminalColor.LIGHT_GRAY)
                        print_colored("====================================", TerminalColor.LIGHT_GRAY)
                except json.JSONDecodeError:
                    print_colored("[Error] Error decoding JSON from stream.", TerminalColor.RED)

        # Try to get tool calls from 'tool_calls' or parse from 'content'
        parsed_tool_calls = []
        for line in llm_response.split("\n"):
            line = line.strip()
            if "search_code(" in line:
                try:
                    query = line.split("search_code(\"")[1].split("\", k=")[0]
                    k = int(line.split("k=")[1].strip(")"))
                    if not "replace this with actual query" in query:
                        parsed_tool_calls.append({"name": "search_code", "arguments": {"query": query, "k": k}})
                except Exception as e:
                    print(f"Error parsing tool call from content: {e}\nContent: {line}")
                    try:
                        query = line.split("search_code(\"")[1].split("\", k=")[0]
                        k = int(line.split("k=")[1].strip(")"))
                        print_colored(f"query: {query}, k: {k}", TerminalColor.RED)
                    except:
                        pass

        # If no tool calls, break and print final answer
        if not parsed_tool_calls:
            print_colored("\n✅ Debugging Complete.\n", TerminalColor.GREEN)
            break

        # Only support search_docs tool
        tool_result_all = ""
        for tc in parsed_tool_calls:
            print_colored(f"\n🔧 Tool Call: {tc}", TerminalColor.RED)
            tool_name = tc["name"]
            arguments = tc["arguments"]
            if tool_name == "search_code" and arguments:
                query = arguments.get("query")
                k = arguments.get("k", 2)
                tool_result = search_code(vector_store, query, k)
                print_colored(f"\n🔧 Tool Result: {tool_result[0:200]}\n" + "...\n"*3, TerminalColor.LIGHT_GRAY)
                tool_result_all += tool_result

        messages.extend([
            {
                "role": "assistant",
                "content": llm_response
            },
            {
                "role": "tool",
                "content": tool_result_all# f"## Here is the tool result from query\n query: {query} \n result: {tool_result}\n\nUse this information for further debugging."
            },
            user_msg
        ])