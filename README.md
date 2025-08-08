# Codebase Vector DB

## Overview
Codebase Vector DB is a Python toolkit for vectorizing codebases, running LLM-powered debugging, and analyzing code/project differences using modern embedding models. It supports semantic search, manifest parsing, and LLM-based code review workflows.

## Project Structure
```
codebase-vector-db/
├── main.py                # Main entry point: LLM debugger, manifest parsing, project diff
├── main.ipynb             # Example Jupyter notebook
├── query_db.py            # Querying interface for the vector DB
├── create_db.py           # Script to create the vector DB
├── settings.py            # Configuration settings
├── requirements.txt       # Python dependencies
├── db/                    # Vector store databases
├── sample_codebase/       # Example codebases for testing
├── src/
│   ├── __init__.py
│   ├── embedding/         # Embedding model interfaces & implementations
│   ├── git_engine/        # Manifest parsing, project diff logic
│   ├── llm/               # LLM chat and tool interface
│   ├── utils/             # File & language utilities
│   ├── vector_store/      # Vector DB interfaces & Chroma implementation
│   └── vectorizer/        # Codebase vectorization logic
└── README.md
```

## Installation
Clone the repository and install dependencies:

```bash
git clone <repository-url>
cd codebase-vector-db
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Main Workflow: LLM Debugger & Project Diff
The main script (`main.py`) demonstrates a workflow for:
- Parsing two manifest XMLs (e.g., `vision_apps_next.xml` and `vision_apps_prod.xml`)
- Extracting project and remote info
- Computing diffs between corresponding projects (using multiprocessing)
- Running an LLM-powered debugging session on error logs and code diffs

### Example Usage
```python
from settings import config, system_prompt
from src.llm.chat import chat_with_tools
from src.embedding.ollama_embedder import OllamaEmbedder
from src.vector_store.chroma_store import ChromaStore
from src.git_engine.workarea import parse_xml, get_all_diff

# Setup embedder and vector store
embedder = OllamaEmbedder(
    url=config["OLLAMA_URL"],
    model_name=config["MODEL"],
    timeout=120
)
vector_store = ChromaStore(
    embedder=embedder,
    persist_directory=config["VECTOR_STORE_PATH"]
)

# Parse manifests and compute diffs
next_remote_dict, next_project_dict = {}, {}
prod_remote_dict, prod_project_dict = {}, {}
parse_xml("vision_apps_next.xml", next_remote_dict, next_project_dict, config["WORKAREA_PATH"])
parse_xml("vision_apps_prod.xml", prod_remote_dict, prod_project_dict, config["WORKAREA_PATH"])
changes_dict = get_all_diff(next_project_dict, prod_project_dict, config["WORKAREA_PATH"])

# Prepare error logs and user prompt
error_logs = """
    ... (your error logs here) ...
"""
user_prompt = f"""
    What are the errors in the logs? Can you help me debug this issue?
    Here are the error logs:
    {error_logs}

    here are the differences between the next and prod projects:
    {changes_dict["mcusw"]}
"""

messages=[
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": user_prompt}
]

chat_with_tools(messages=messages, vector_store=vector_store)
```

## Features
- **LLM Debugger:** Analyze error logs and code diffs with an LLM, including code search tool calls
- **Manifest Parsing:** Parse XML manifests to extract project/remote info
- **Project Diffing:** Compute diffs between corresponding projects (next vs prod)
- **Flexible Embedding Models:** Easily add new models via the `BaseEmbedder` interface (Ollama supported)
- **Modular Vector Stores:** Store and retrieve vectors using Chroma or custom backends
- **Jupyter Notebook:** Interactive demo in `main.ipynb`

## Contributing
Contributions are welcome! Please open issues or submit pull requests for improvements or bug fixes.

## License
MIT License. See the [LICENSE](LICENSE) file for details.