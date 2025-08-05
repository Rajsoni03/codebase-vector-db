class ChromaStore:
    def __init__(self, embeddings, texts, metadatas, persist_directory):
        self.embeddings = embeddings
        self.texts = texts
        self.metadatas = metadatas
        self.persist_directory = persist_directory

    def create_vector_store(self):
        from langchain_community.vectorstores import Chroma
        vector_store = Chroma.from_embeddings(
            embeddings=self.embeddings,
            texts=self.texts,
            metadatas=self.metadatas,
            persist_directory=self.persist_directory
        )
        return vector_store

    def persist(self, vector_store):
        vector_store.persist()
        print(f"Vector database created at {self.persist_directory}")