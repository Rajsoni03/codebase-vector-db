class BaseEmbedder:
    def embed_documents(self, texts):
        raise NotImplementedError("Subclasses must implement this method.")

    def embed_query(self, text):
        raise NotImplementedError("Subclasses must implement this method.")