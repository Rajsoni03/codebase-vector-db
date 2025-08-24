from settings import config, TerminalColor, print_colored
from src.llm.ollama import OllamaClient
from src.utils.prompts import *
from src.llm.chat import chat_with_tools
from src.embedding.ollama_embedder import OllamaEmbedder
from src.vector_store.chroma_store import ChromaStore
from src.git_engine.workarea import parse_git_diff, parse_xml, get_all_diff

##########################################################################
###########################[ Global Variables ]###########################

VECTOR_STORE_PATH   = config["VECTOR_STORE_PATH"]
EMBEDDING_MODEL     = config["EMBEDDING_MODEL"]
MAIN_MODEL          = config["MAIN_MODEL"]
CODE_EXTENSIONS     = config["CODE_EXTENSIONS"]
OLLAMA_URL          = config["OLLAMA_URL"]
WORKAREA_PATH       = config["WORKAREA_PATH"]
DEBUG_MODE          = config["DEBUG_MODE"]

##########################################################################
####################[ Create Embedder & Text Splitter ]###################

embedder = OllamaEmbedder(
    url=OLLAMA_URL,
    model_name=EMBEDDING_MODEL,
    timeout=120
)

##########################################################################
########################[ Create Vector Store ]###########################

vector_store = ChromaStore(
    embedder=embedder,
    persist_directory=VECTOR_STORE_PATH
)

##########################################################################
########################[ Create Ollama Client ]###########################

client = OllamaClient()


##########################################################################
#########################[ Run LLM Debugger ]#############################

if __name__ == "__main__":
    # Parse the next manifest
    print_colored(f"[INFO] Parsing next manifest...", TerminalColor.YELLOW)
    next_remote_dict = {}
    next_project_dict = {}
    parse_xml("vision_apps_next.xml", next_remote_dict, next_project_dict, WORKAREA_PATH)

    # Parse the prod manifest
    print_colored(f"[INFO] Parsing prod manifest...", TerminalColor.YELLOW)
    prod_remote_dict = {}
    prod_project_dict = {}
    parse_xml("vision_apps_prod.xml", prod_remote_dict, prod_project_dict, WORKAREA_PATH)

    # Check for differences between next and prod projects
    print_colored(f"[INFO] Checking differences between next and prod projects...", TerminalColor.YELLOW)
    changes_dict = get_all_diff(next_project_dict, prod_project_dict, WORKAREA_PATH)
    
    # Print the results
    print_colored("Differences found in the following projects:", TerminalColor.YELLOW)
    for name, data in changes_dict.items():
        num_of_lines = len(data.split('\n'))
        print_colored(f"{name}: {num_of_lines} Lines", TerminalColor.LIGHT_GRAY)

    error_logs = '''
        Booting HSM core ...
        Calling Sciclient_procBootGetProcessorState, ProcId 0x80...
        Calling Sciclient_procBootRequestProcessor, ProcId 0x80...
        Setting HALT for ProcId 0x80...
        Calling Sciclient_procBootAuthAndStart ...
        ERROR: App_loadAndAuthHsmBinary:268: Sciclient_procBootAuthAndStart...FAILED
        Clearing HALT for ProcId 0x80...
        Calling Sciclient_procBootReleaseProcessor, ProcId 0x80...
        HSM Core booted successfully
        Some tests have failed!!
        ASSERT: 3.704042s: ../main.c:main:350: 0 failed !!!
        
    '''
    # Error Summizer agent
    # detect the error and summarize 
    print_colored("\n[INFO] Summarizing error logs...", TerminalColor.YELLOW)
    response = client.chat(
        model="qwen2.5-coder:1.5b",
        messages=[
            {
                "role": "system",
                "content": EMBEDDED_ERROR_SUMMARIZER_PROMPT
            },
            {
                "role": "user",
                "content": error_logs
            }
        ]
    )

    error_logs_summary = response["message"]["content"]
    print_colored("🤖 Model Response:", TerminalColor.BLUE)
    print_colored(error_logs_summary, TerminalColor.CYAN)

    # parse the the git diff and create file wise list with meotadata
    formatted_diff = parse_git_diff(changes_dict["mcu_plus_sdk"])
    if DEBUG_MODE:
        print_colored("\n🔍 Parsed Git Diff:", TerminalColor.CYAN)
        print_colored("="* 80, TerminalColor.LIGHT_GRAY)
        for file in formatted_diff:
            print_colored(f"File started from here...", TerminalColor.RED)
            print_colored(f"  {file}", TerminalColor.LIGHT_GRAY)
        print_colored("="* 80 + "\n", TerminalColor.LIGHT_GRAY)


    # Iterate over the formatted git diff and predict potential issues
    # for git_diff_file in formatted_diff:
    git_diff_file = "".join([f"{i}\n\n" for i in formatted_diff])

    user_prompt = f"""
        What are the errors in the logs? Can you help me debug this issue?
        Here are the error logs:
        {error_logs}
        Here is the summary of the error logs:
        {error_logs_summary}

        here are the differences between the next and prod projects:
        {git_diff_file}

        Please analyze the changes and provide a detailed explanation of the potential issues.
        also call the search_code tool when you need more context about a function, variable, memory address, or file mentioned in the diff.
        ```
        TOOL_CALL : search_code("<replace this with actual query>", k=<number_of_results>)
        ```
    """

    messages=[
            {
                "role": "system",
                "content": DEBUGGER_PROMPT# DEBUGGING_AGENT_PROMPT_2 
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]

    print_colored("\n[INFO]🔍 Starting LLM Debugger...", TerminalColor.YELLOW)
    chat_with_tools(messages=messages, vector_store=vector_store, model="codegemma:7b")
