import sys
from langchain_community.vectorstores import Chroma
from chromadb.utils.embedding_functions.ollama_embedding_function import OllamaEmbeddingFunction

class MiniLMEmbedder:
    def __init__(self, model):
        self.model = model
    def embed_documents(self, texts):
        return self.model.encode(texts).tolist()
    def embed_query(self, text):
        return self.model.encode([text])[0].tolist()

def query_codebase(vector_store_path, query, top_k=5, embedding_model="all-MiniLM-L6-v2"):
    if embedding_model.find("ollama-") == 0:
        embeddings = OllamaEmbeddingFunction(
            url="http://localhost:11434",
            model_name=embedding_model.replace("ollama-", ""),
            timeout=120
        )
    else:
        raise ValueError("Supported models: all-MiniLM-L6-v2, ollama-<ollama model>")
    vector_store = Chroma(
        persist_directory=vector_store_path,
        embedding_function=embeddings
    )
    results = vector_store.similarity_search_with_score(query, k=top_k)
    for i, (doc, score) in enumerate(results):
        print(f"Result {i+1}:")
        print(f"Score: {score}")
        print(f"Content: {doc.page_content}")
        print(f"Metadata: {doc.metadata}\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python query_codebase.py <query> [top_k]")
        sys.exit(1)
    vector_store_path = "./db/mcu_plus_sdk_vectors"
    query = sys.argv[1]
    embedding_model = "ollama-" + "all-minilm:latest" # ollama-<model> or all-MiniLM-L6-v2
    top_k = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    query_codebase(vector_store_path, query, top_k, embedding_model)
