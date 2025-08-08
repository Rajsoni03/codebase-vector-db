from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.utils.proxy_utils import set_proxy_environment_variables
from src.vectorizer.codebase_vectorizer import CodebaseVectorizer
from src.embedding.ollama_embedder import OllamaEmbedder
from src.vector_store.chroma_store import ChromaStore
from settings import config

##########################################################################
###########################[ Global Variables ]###########################

CODEBASE_PATH       = config["CODEBASE_PATH"]
VECTOR_STORE_PATH   = config["VECTOR_STORE_PATH"]
MODEL               = config["MODEL"]
CODE_EXTENSIONS     = config["CODE_EXTENSIONS"]
BATCH_SIZE          = config["BATCH_SIZE"]
OLLAMA_URL          = config["OLLAMA_URL"]

##########################################################################
#######################[ Set Environment Variables ]######################

# set_proxy_environment_variables() # Uncomment if you need to set proxy environment variables

##########################################################################
####################[ Create Embedder & Text Splitter ]###################

embedder = OllamaEmbedder(
    url=OLLAMA_URL,
    model_name=MODEL,
    timeout=120
)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=7000, # model specific, adjust as needed
    chunk_overlap=1000, # 10-20% of chunk size, adjust as needed
    separators=["\n\n", "\n", ";", " ", ""]
)

##########################################################################
#########################[ Create Vectorizer ]############################

vectorizer = CodebaseVectorizer(codebase_path=CODEBASE_PATH,
                                embedder=embedder,
                                text_splitter=text_splitter,
                                code_extensions=CODE_EXTENSIONS,
                                batch_size=BATCH_SIZE)

texts, metadatas = vectorizer.vectorize_codebase()

##########################################################################
########################[ Create Vector Store ]###########################

vector_store = ChromaStore(
    embedder=embedder,
    persist_directory=VECTOR_STORE_PATH
)

vector_store.store_embeddings(texts, metadatas, batch_size=BATCH_SIZE)
print(f"Vector database created at {VECTOR_STORE_PATH}")
