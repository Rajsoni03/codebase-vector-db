from src.codebase_vectorizer import CodebaseVectorizer
from src.query_database import query_codebase


# Example usage:
vectorizer = CodebaseVectorizer(codebase_path="/home/raj/Desktop/jupyter/Notebooks/AI/mcu_plus_sdk/",
                                vector_store_path="./db/mcu_plus_sdk_vectors",
                                embedding_model="ollama-" + "all-minilm:latest") # ollama-<model> or all-MiniLM-L6-v2
vector_store = vectorizer.vectorize_codebase()