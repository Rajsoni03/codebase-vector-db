from settings import config
from src.embedding.ollama_embedder import OllamaEmbedder
from src.vector_store.chroma_store import ChromaStore



##########################################################################
###########################[ Global Variables ]###########################

VECTOR_STORE_PATH   = config["VECTOR_STORE_PATH"]
MODEL               = config["MODEL"]
CODE_EXTENSIONS     = config["CODE_EXTENSIONS"]
OLLAMA_URL          = config["OLLAMA_URL"]

##########################################################################
####################[ Create Embedder & Text Splitter ]###################

embedder = OllamaEmbedder(
    url=OLLAMA_URL,
    model_name=MODEL,
    timeout=120
)

##########################################################################
########################[ Create Vector Store ]###########################

vector_store = ChromaStore(
    embedder=embedder,
    persist_directory=VECTOR_STORE_PATH
)

##########################################################################
#########################[ Query Codebase ]###############################

def query_codebase(vector_store, query, top_k=5):
    results = vector_store.vector_store.similarity_search_with_score(query, k=top_k)
    for i, (doc, score) in enumerate(results):
        print(f"Result {i+1}:")
        print(f"Score: {score}")
        print(f"Content: {doc.page_content}")
        print(f"Metadata: {doc.metadata}\n")


query = "vxEnableGraphStreaming "
top_k = 5

query_codebase(vector_store, query, top_k)
