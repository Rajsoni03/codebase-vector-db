from langchain_community.vectorstores import Chroma
from tqdm import tqdm

class ChromaStore:
    def __init__(self, embedder, persist_directory):
        self.embedder = embedder
        self.persist_directory = persist_directory

        self.vector_store = Chroma(
            embedding_function=embedder,
            persist_directory=persist_directory
        )

    def store_embeddings(self, texts, metadatas, batch_size=16):
        for i in tqdm(range(0, len(texts), batch_size), desc="Processing Batches"):
            texts_batch = texts[i:i + batch_size]
            metadatas_batch = metadatas[i:i + batch_size]
            self.vector_store.add_texts(texts=texts_batch, metadatas=metadatas_batch)
