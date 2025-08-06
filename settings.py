
"""
This file contains global settings and configurations for the codebase vectorization process.
"""

config = {
    "CODEBASE_PATH": "./sample_codebase/tiovx",
    "VECTOR_STORE_PATH": "./db/tiovx_vectors",
    "OLLAMA_URL": "http://localhost:11434",
    "MODEL": "unclemusclez/jina-embeddings-v2-base-code:f16",
    "CODE_EXTENSIONS": {'.py', '.js', '.jsx', '.ts', '.tsx', '.cpp', '.c', '.h', '.mak', '.mk', '.cmake', '.sh', '.txt', '.md', '.json', '.yaml', '.yml', '.xml', '.html'},
    "BATCH_SIZE": 128
}