from abc import ABC, abstractmethod
from chromadb.utils.embedding_functions.ollama_embedding_function import OllamaEmbeddingFunction

class OllamaEmbedder(ABC):
    def __init__(self, url, model_name, timeout=120):
        self.ollama_ef = OllamaEmbeddingFunction(url=url, model_name=model_name, timeout=timeout)

    @abstractmethod
    def embed_documents(self, texts):
        return self.ollama_ef(texts)

    @abstractmethod
    def embed_query(self, text):
        return self.ollama_ef([text])[0]