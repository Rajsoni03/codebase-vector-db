import os
from pathlib import Path
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from chromadb.utils.embedding_functions.ollama_embedding_function import OllamaEmbeddingFunction
from tqdm import tqdm

# Set an environment variable
os.environ["HTTPS_PROXY"] = ""
os.environ["HTTP_PROXY"] = ""
os.environ["FTP_PROXY"] = ""
os.environ["https_proxy"] = ""
os.environ["http_proxy"] = ""
os.environ["ftp_proxy"] = ""

class MiniLMEmbedder:
    def __init__(self, model):
        self.model = model
    def embed_documents(self, texts):
        return self.model.encode(texts).tolist()
    def embed_query(self, text):
        return self.model.encode([text])[0].tolist()

class OllamaEmbedder:
    def __init__(self, url, model_name, timeout=120):
        self.ollama_ef = OllamaEmbeddingFunction(url=url, model_name=model_name, timeout=timeout)
    def embed_documents(self, texts):
        return self.ollama_ef(texts)
    def embed_query(self, text):
        return self.ollama_ef([text])[0]

class CodebaseVectorizer:
    def __init__(self, codebase_path, vector_store_path="./code_vectors", embedding_model="all-MiniLM-L6-v2", ollama_timeout=120):
        self.codebase_path = Path(codebase_path)
        self.vector_store_path = vector_store_path
        if embedding_model.find("ollama-") == 0:
            self.embeddings = OllamaEmbedder(
                url="http://localhost:11434",
                model_name=embedding_model.replace("ollama-", ""),
                timeout=ollama_timeout
            )
        else:
            raise ValueError("Supported models: ollama-<ollama models>")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )

    def extract_code_files(self):
        code_extensions = {'.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cpp', '.c', '.h', '.go', '.rs', '.rb', '.php', '.mak', '.mk'}
        code_files = []
        for file_path in self.codebase_path.rglob('*'):
            if (file_path.suffix in code_extensions and file_path.is_file() and 'node_modules' not in str(file_path)):
                code_files.append(file_path)
        return code_files
    

    def detect_language(self, extension):
        language_map = {
            '.py': 'python', '.js': 'javascript', '.jsx': 'javascript', '.ts': 'typescript', '.tsx': 'typescript',
            '.java': 'java', '.cpp': 'cpp', '.c': 'c', '.h': 'c', '.go': 'go', '.rs': 'rust', '.rb': 'ruby', '.php': 'php'
        }
        return language_map.get(extension, 'unknown')

    def process_file(self, file_path):
        try:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
            chunks = self.text_splitter.split_text(content)
            documents = []
            for i, chunk in enumerate(chunks):
                metadata = {
                    'file_path': str(file_path),
                    'relative_path': str(file_path.relative_to(self.codebase_path)),
                    'file_extension': file_path.suffix,
                    'language': self.detect_language(file_path.suffix),
                    'chunk_id': i,
                    'chunk_size': len(chunk)
                }
                documents.append({'content': chunk, 'metadata': metadata})
            return documents
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return []

    def vectorize_codebase(self):
        print(f"Starting vectorization of {self.codebase_path}")
        code_files = self.extract_code_files()
        print(f"Found {len(code_files)} code files")
        all_documents = []
        for file_path in code_files:
            documents = self.process_file(file_path)
            all_documents.extend(documents)
        print(f"Created {len(all_documents)} code chunks")
        texts = [doc['content'] for doc in all_documents]
        metadatas = [doc['metadata'] for doc in all_documents]
        print("Embedding code chunks and building vector store...")
        # Embed in batches with progress bar
        batch_size = 16
        embeddings = []
        for i in tqdm(range(0, len(texts), batch_size), desc="Embedding"):
            batch = texts[i:i+batch_size]
            embeddings.extend(self.embeddings.embed_documents(batch))
        vector_store = Chroma.from_embeddings(
            embeddings=embeddings,
            texts=texts,
            metadatas=metadatas,
            persist_directory=self.vector_store_path
        )
        vector_store.persist()
        print(f"Vector database created at {self.vector_store_path}")
        return vector_store


if __name__ == "__main__":
    # Example usage:
    vectorizer = CodebaseVectorizer("/home/raj/Desktop/jupyter/Notebooks/AI/mcu_plus_sdk/",
                                    vector_store_path="./db/mcu_plus_sdk_vectors",
                                    embedding_model="ollama-" + "all-minilm:latest") # ollama-<model> or all-MiniLM-L6-v2
    vector_store = vectorizer.vectorize_codebase()
