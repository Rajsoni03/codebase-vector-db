# Codebase Vector DB

## Overview
The Codebase Vector DB project is designed to vectorize codebases using various embedding models. It provides a structured approach to extract, embed, and store code snippets for efficient retrieval and analysis.

## Project Structure
```
codebase-vector-db
├── src
│   ├── __init__.py
│   ├── codebase_vectorizer.py
│   ├── embedding
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── minilm_embedder.py
│   │   └── ollama_embedder.py
│   ├── utils
│   │   ├── __init__.py
│   │   ├── file_utils.py
│   │   └── language_utils.py
│   └── vector_store
│       ├── __init__.py
│       └── chroma_store.py
├── requirements.txt
└── README.md
```

## Installation
To set up the project, clone the repository and install the required dependencies:

```bash
git clone <repository-url>
cd codebase-vector-db
pip install -r requirements.txt
```

## Usage
To vectorize a codebase, you can use the `CodebaseVectorizer` class from the `codebase_vectorizer.py` file. Here is an example of how to use it:

```python
from src.codebase_vectorizer import CodebaseVectorizer

vectorizer = CodebaseVectorizer(
    codebase_path="/path/to/your/codebase",
    vector_store_path="./db/vectors",
    embedding_model="ollama-all-minilm:latest"
)
vector_store = vectorizer.vectorize_codebase()
```

## Components
- **Embedding Models**: The project supports different embedding models through the `BaseEmbedder` interface, allowing for easy integration of new models.
- **File Utilities**: Utility functions for reading and processing code files are provided in the `utils` module.
- **Language Detection**: The project includes functionality to detect programming languages based on file extensions.
- **Vector Store**: The `ChromaStore` class manages the storage and retrieval of embedded vectors.

## Contributing
Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.