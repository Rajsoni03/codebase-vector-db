from pathlib import Path
from langchain.text_splitter import RecursiveCharacterTextSplitter
from src.embedding.minilm_embedder import MiniLMEmbedder
from src.embedding.ollama_embedder import OllamaEmbedder
from src.vector_store.chroma_store import ChromaStore
from src.utils.file_utils import read_file_contents
from src.utils.language_utils import detect_language
from tqdm import tqdm

class CodebaseVectorizer:
    def __init__(self, codebase_path, vector_store_path="./code_vectors", embedding_model="all-MiniLM-L6-v2", ollama_timeout=120):
        self.codebase_path = Path(codebase_path)
        self.vector_store_path = vector_store_path
        self.embeddings = self.initialize_embedder(embedding_model, ollama_timeout)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )

    def initialize_embedder(self, embedding_model, ollama_timeout):
        if embedding_model.startswith("ollama-"):
            return OllamaEmbedder(
                url="http://localhost:11434",
                model_name=embedding_model.replace("ollama-", ""),
                timeout=ollama_timeout
            )
        else:
            return MiniLMEmbedder(model=embedding_model)

    def extract_code_files(self):
        code_extensions = {'.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cpp', '.c', '.h', '.go', '.rs', '.rb', '.php', '.mak', '.mk'}
        return [file_path for file_path in self.codebase_path.rglob('*') if file_path.suffix in code_extensions and file_path.is_file() and 'node_modules' not in str(file_path)]

    def process_file(self, file_path):
        content = read_file_contents(file_path)
        chunks = self.text_splitter.split_text(content)
        return [{'content': chunk, 'metadata': self.create_metadata(file_path, i, chunk)} for i, chunk in enumerate(chunks)]

    def create_metadata(self, file_path, chunk_id, chunk):
        return {
            'file_path': str(file_path),
            'relative_path': str(file_path.relative_to(self.codebase_path)),
            'file_extension': file_path.suffix,
            'language': detect_language(file_path.suffix),
            'chunk_id': chunk_id,
            'chunk_size': len(chunk)
        }

    def vectorize_codebase(self):
        print(f"Starting vectorization of {self.codebase_path}")
        code_files = self.extract_code_files()
        print(f"Found {len(code_files)} code files")
        all_documents = [doc for file_path in code_files for doc in self.process_file(file_path)]
        print(f"Created {len(all_documents)} code chunks")
        texts = [doc['content'] for doc in all_documents]
        metadatas = [doc['metadata'] for doc in all_documents]
        print("Embedding code chunks and building vector store...")
        embeddings = self.embed_documents_in_batches(texts)
        vector_store = ChromaStore.from_embeddings(
            embeddings=embeddings,
            texts=texts,
            metadatas=metadatas,
            persist_directory=self.vector_store_path
        )
        vector_store.persist()
        print(f"Vector database created at {self.vector_store_path}")
        return vector_store

    def embed_documents_in_batches(self, texts):
        batch_size = 16
        embeddings = []
        for i in tqdm(range(0, len(texts), batch_size), desc="Embedding"):
            batch = texts[i:i + batch_size]
            embeddings.extend(self.embeddings.embed_documents(batch))
        return embeddings


if __name__ == "__main__":
    vectorizer = CodebaseVectorizer("/home/raj/Desktop/jupyter/Notebooks/AI/mcu_plus_sdk/",
                                    vector_store_path="./db/mcu_plus_sdk_vectors",
                                    embedding_model="ollama-" + "all-minilm:latest")
    vector_store = vectorizer.vectorize_codebase()