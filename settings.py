
"""
This file contains global settings and configurations for the codebase vectorization process.
"""

config = {
    "CODEBASE_PATH": "./sample_codebase/tiovx",
    "VECTOR_STORE_PATH": "./db/mcu_plus_sdk_vectors",
    "OLLAMA_URL": "http://localhost:11434",
    "OLLAMA_KEEP_ALIVE": "5m",
    "EMBEDDING_MODEL": "unclemusclez/jina-embeddings-v2-base-code:f16",
    "MAIN_MODEL": "qwen2.5-coder:1.5b",
    "CODE_EXTENSIONS": {'.py', '.js', '.jsx', '.ts', '.tsx', '.cpp', '.c', '.h', '.mak', '.mk', '.cmake', '.sh', '.txt', '.md', '.json', '.yaml', '.yml', '.xml', '.html'},
    "BATCH_SIZE": 32,
    # "WORKAREA_PATH": "/home/raj/Desktop/edgeai/sdk_workareas/j742s2_linux/" 
    "WORKAREA_PATH": "/Users/raj/Development/codebase-vector-db/sample_codebase/",
    "DEBUG_MODE": False
}

class TerminalColor:
    # Colors for terminal output
    BLUE = "\033[34m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    CYAN = "\033[96m"
    LIGHT_GRAY = "\033[37m"
    RESET = "\033[0m"

def print_colored(text, color, **kwargs):
    print(f"{color}{text}{TerminalColor.RESET}", **kwargs)