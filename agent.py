import re
import os
import json
import textwrap
import traceback 
from src.llm.ollama import OllamaClient
from src.parser.parser import parse_markdown
from src.utils.prompts import SUBTASK_GENERATION_PROMPT, CONTEXT_SUMMARIZER_PROMPT, SUB_AGENT_SYSTEM_PROMPT

##########################################################################
###########################[ Global Variables ]###########################

"""
MODEL NAME
-------------
deepseek-r1:8b

gemma3:4b
qwen3:0.6b
qwen3:1.7b

qwen2.5-coder:0.5b
qwen2.5-coder:7b
hhao/qwen2.5-coder-tools:1.5b 
"""

# Model configuration
MODEL_MAIN = "qwen3:1.7b"  # Main model for sub-task generation
MODEL_CODE = "qwen2.5-coder:0.5b"
MODEL_COMPRESS = "qwen3:1.7b"

# Colors for terminal output
BLUE = "\033[34m"
RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
CYAN = "\033[96m"
LIGHT_GRAY = "\033[37m"
RESET = "\033[0m"

# full conversation log (gets compressed periodically to save tokens)
conv = []

##########################################################################
#########################[ Create Ollama Client ]#########################

client = OllamaClient()

##########################################################################
###########################[ Helper Functions ]###########################

def chat(msgs, model=MODEL_MAIN, stream=True, color=RESET, heading=""):

    print(f"{'=' * 50}")
    print(f"{color}{heading}")
    is_thinking = False

    try:
        response = client.chat(messages=msgs, model=model, stream=stream)
        llm_response = ""

        for line in response:
            if line:
                try:
                    message = json.loads(line.decode('utf-8'))
                    content = message["message"].get('content', '')
                    
                    if content.strip() == "<think>":
                        is_thinking = True
                    elif content.strip() == "</think>":
                        is_thinking = False
                        print(f"{LIGHT_GRAY}{content}{RESET}", end="", flush=True)
                        continue
                        
                    if is_thinking:
                        print(f"{LIGHT_GRAY}{content}{RESET}", end="", flush=True)
                    else:
                        llm_response += content
                        print(f"{color}{content}{RESET}", end="", flush=True)
                except json.JSONDecodeError:
                    print("Error decoding JSON from stream.")
        print(f"\n{'=' * 50}")
        return llm_response
    except Exception as e:
        raise RuntimeError(f"API call failed: {e}")

def generate_subtasks(main_task):
    # Append user message to conversation and generate subtasks
    conv.append({"role": "user", "content": main_task})

    while(True):
        # Create a temporary conversation context
        temp_conv = conv + [{"role": "system", "content": SUBTASK_GENERATION_PROMPT}]

        # Generate subtasks using the chat function
        txt = chat(
            msgs=temp_conv,
            model=MODEL_MAIN,
            stream=True,
            color=RED,
            heading="🔄 Generating Subtasks"
        )
        
        # Parse the response and extract subtasks
        try:
            subtasks = parse_markdown(txt)
            conv.append({"role": "assistant", "content": txt})
            return subtasks
        except Exception as e:
            traceback_string = traceback.format_exc()
            print("Traceback stored in string:")
            print(traceback_string)
            temp_conv.append({"role": "system", "content": f"Error occurred while generating subtasks: {traceback_string}"})
            temp_conv.append({"role": "user", "content": "Fix this issue and generate again : " + main_task})


def compress():
    # uses cheaper model to summarize conversation and keep only essential info
    # prevents token limit issues while maintaining context continuity

    response = chat(
        conv + [{
            "role": "system",
            "content": CONTEXT_SUMMARIZER_PROMPT
        }],
        model=MODEL_COMPRESS,
        stream=True,
        color=YELLOW,
        heading="🗜️ Context Summarization"
    )
    return response


def subagent(prompt, ctx, color=CYAN, agent_count=1):
    # receives compressed context instead of full conversation history
    # gets essential info but uses fewer tokens
    result = chat(
        [
            {"role": "system", "content": f"Context: {ctx}"},
            {"role": "system", "content": f"You are Sub-Agent {agent_count}. {SUB_AGENT_SYSTEM_PROMPT}"},
            {"role": "user", "content": f"{prompt}"}
        ],
        model=MODEL_CODE,
        stream=True,
        color=color,
        heading=f"🤖 Sub-agent {agent_count}"
    )
    return result


def merge_results(ctx):
    return chat(
        [
            {"role": "system", "content": "Combine all the sub-results into ONE clear answer."},
            {"role": "user", "content": f"Context: {ctx}"}
        ],
        model=MODEL_MAIN,
        stream=True,
        color=BLUE,
        heading="✅ FINAL ANSWER"
    )


##########################################################################
#########################[ Start The Agent ]##############################

if __name__ == "__main__":

    task = input("📝 MAIN TASK → ").strip()
    # task = "create react js based webpage with django backend with mongo db"
    # task = "create a todo list webpage in flask with simple curd operations"
    # task = "code flask project with todo apps"
    # task =  "create a django and react based webside with mongo db in backend include user auth with jwt and provide all social media like features (chat, post, profile, connection, etc)."
    # task = "code hello world in C, C++, Python and Java"

    if not task:
        print("No task provided.")
        exit(1)

    # Append user message to conversation and generate subtasks
    subtasks_list = generate_subtasks(task)
    ctx = []

    # Print the generated subtasks
    print("Total Subtasks Generated:", len(subtasks_list))
    for i, subtask in enumerate(subtasks_list, 1):
        print(f" {i}) {subtask['name']}")

    # Iterate over each subtask and create a sub-agent for it
    for i, subtask in enumerate(subtasks_list, 1):
        # format the sub_task for sub-agent
        print("#" * 80)
        print(f"{'=' * 32}[ SUB TASK - {i} ]{'=' * 32}")
        print(f"{CYAN} {subtask['text']} {RESET}")
        print("#" * 80)

        # compress conversation before each agent step
        # keeps token usage manageable for longer tasks
        if i != 1:
            ctx = compress()

        # Call sub-agent with formatted task and context
        result = subagent(subtask['text'], ctx, color=GREEN, agent_count=i)
        conv.append({"role": "assistant", "content": f"[Sub-agent {i}] {result}"})
    
    # ctx = compress()
    # final_result = merge_results(ctx)

