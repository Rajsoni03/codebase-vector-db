# Codebase Vector DB

## Overview
Codebase Vector DB is a Python toolkit for vectorizing codebases using modern embedding models. It extracts code snippets, generates embeddings, and stores them for efficient semantic search and analysis. The project is modular, supporting multiple embedding backends and vector stores.

## Project Structure
```
codebase-vector-db/
├── main.py                # CLI entry point
├── main.ipynb             # Example Jupyter notebook
├── query_db.py            # Querying interface for the vector DB
├── settings.py            # Configuration settings
├── requirements.txt       # Python dependencies
├── db/                    # Vector store databases
├── sample_codebase/       # Example codebases for testing
├── src/
│   ├── __init__.py
│   ├── embedding/         # Embedding model interfaces & implementations
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── ollama_embedder.py
│   ├── utils/             # File & language utilities
│   │   ├── __init__.py
│   │   ├── file_utils.py
│   │   ├── language_utils.py
│   │   └── proxy_utils.py
│   ├── vector_store/      # Vector DB interfaces & Chroma implementation
│   │   ├── __init__.py
│   │   └── chroma_store.py
│   └── vectorizer/        # Codebase vectorization logic
│       ├── __init__.py
│       └── codebase_vectorizer.py
└── README.md
```

## Installation
Clone the repository and install dependencies:

```bash
git clone <repository-url>
cd codebase-vector-db
python -m venv vnev
source vnev/bin/activate
pip install -r requirements.txt
```

## Quick Start
Vectorize a codebase and store embeddings:

```python
from settings import config
from src.embedding.ollama_embedder import OllamaEmbedder
from src.vectorizer.codebase_vectorizer import CodebaseVectorizer
from src.utils.proxy_utils import set_proxy_environment_variables
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.vector_store.chroma_store import ChromaStore

# Optional: set_proxy_environment_variables()  # Uncomment if needed

embedder = OllamaEmbedder(
    url="http://localhost:11434",
    model_name=config["MODEL"],
    timeout=120
)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=["\n\n", "\n", " ", ""]
)

vectorizer = CodebaseVectorizer(
    codebase_path=config["CODEBASE_PATH"],
    embedder=embedder,
    text_splitter=text_splitter,
    code_extensions=config["CODE_EXTENSIONS"],
    batch_size=config["BATCH_SIZE"]
)
texts, metadatas = vectorizer.vectorize_codebase()

vector_store = ChromaStore(
    embedder=embedder,
    persist_directory=config["VECTOR_STORE_PATH"]
)
vector_store.store_embeddings(texts, metadatas, batch_size=config["BATCH_SIZE"])
print(f"Vector database created at {config['VECTOR_STORE_PATH']}")
```

Query the vector database:

```python
from settings import config
from src.embedding.ollama_embedder import OllamaEmbedder
from src.vector_store.chroma_store import ChromaStore

embedder = OllamaEmbedder(
    url="http://localhost:11434",
    model_name=config["MODEL"],
    timeout=120
)

vector_store = ChromaStore(
    embedder=embedder,
    persist_directory=config["VECTOR_STORE_PATH"]
)

def query_codebase(vector_store, query, top_k=5):
    results = vector_store.vector_store.similarity_search_with_score(query, k=top_k)
    for i, (doc, score) in enumerate(results):
        print(f"Result {i+1}:")
        print(f"Score: {score}")
        print(f"Content: {doc.page_content}")
        print(f"Metadata: {doc.metadata}\n")

query = "How does the main loop work?"
top_k = 5
query_codebase(vector_store, query, top_k)
```

## Features
- **Flexible Embedding Models:** Easily add new models via the `BaseEmbedder` interface. Includes Ollama support.
- **Modular Vector Stores:** Store and retrieve vectors using Chroma or custom backends.
- **File & Language Utilities:** Robust file reading, filtering, and language detection.
- **Sample Codebases:** Test and experiment with provided sample projects.
- **Jupyter Notebook:** Interactive demo in `main.ipynb`.

## Contributing
Contributions are welcome! Please open issues or submit pull requests for improvements or bug fixes.

## License
MIT License. See the LICENSE file for details.