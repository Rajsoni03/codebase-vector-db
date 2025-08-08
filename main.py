from settings import config, system_prompt
from src.llm.chat import chat_with_tools
from src.embedding.ollama_embedder import OllamaEmbedder
from src.vector_store.chroma_store import ChromaStore
from src.git_engine.workarea import parse_xml, get_all_diff

##########################################################################
###########################[ Global Variables ]###########################

VECTOR_STORE_PATH   = config["VECTOR_STORE_PATH"]
MODEL               = config["MODEL"]
CODE_EXTENSIONS     = config["CODE_EXTENSIONS"]
OLLAMA_URL          = config["OLLAMA_URL"]
WORKAREA_PATH       = config["WORKAREA_PATH"]

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
#########################[ Run LLM Debugger ]#############################

if __name__ == "__main__":
    # Parse the next manifest
    print("Parsing next manifest...")
    next_remote_dict = {}
    next_project_dict = {}
    parse_xml("vision_apps_next.xml", next_remote_dict, next_project_dict, WORKAREA_PATH)

    # Parse the prod manifest
    print("Parsing prod manifest...")
    prod_remote_dict = {}
    prod_project_dict = {}
    parse_xml("vision_apps_prod.xml", prod_remote_dict, prod_project_dict, WORKAREA_PATH)

    # Check for differences between next and prod projects 
    print("Checking differences between next and prod projects...")
    changes_dict = get_all_diff(next_project_dict, prod_project_dict, WORKAREA_PATH)
    
    # Print the results
    print("Differences found in the following projects:")
    for name, data in changes_dict.items():    
        print(name, len(data))
    
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

    user_prompt = f"""
        What are the errors in the logs? Can you help me debug this issue?
        Here are the error logs:
        {error_logs}

        here are the differences between the next and prod projects:
        {changes_dict["mcusw"]}
    """

    messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]

    print("\n🔍 Starting LLM Debugger...")
    chat_with_tools(messages=messages, vector_store=vector_store)
