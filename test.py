from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.ollama import OllamaProvider

import os
import glob
import uuid
import requests
from typing import List, Tuple
from dataclasses import dataclass

import chromadb
from chromadb.config import Settings
from pydantic_ai import Agent, RunContext

# ---------------------------
# Config
# ---------------------------
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "unclemusclez/jina-embeddings-v2-base-code:f16")
LLM_MODEL = os.environ.get("LLM_MODEL", "qwen3:1.7b")
PERSIST_DIR = "./db"
COLLECTION_NAME = "mcu_plus_sdk_vectors"

# ---------------------------
# Ollama embedding & chat
# ---------------------------
def ollama_embed(texts: List[str]) -> List[List[float]]:
    resp = requests.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={"model": EMBED_MODEL, "input": texts}
    )
    resp.raise_for_status()
    data = resp.json()
    return [item["embedding"] for item in data["embeddings"]]

# ---------------------------
# Chroma DB setup
# ---------------------------
@dataclass
class RAGDeps:
    client: chromadb.Client
    collection: chromadb.Collection

def make_deps() -> RAGDeps:
    client = chromadb.PersistentClient(path=PERSIST_DIR, settings=Settings(allow_reset=False))
    try:
        collection = client.get_collection(COLLECTION_NAME)
    except Exception:
        collection = client.create_collection(COLLECTION_NAME, metadata={"hnsw:space": "cosine"})
    return RAGDeps(client=client, collection=collection)

# ---------------------------
# Code file loader & chunker
# ---------------------------
def load_code(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def chunk_code(code: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    lines = code.splitlines()
    chunks = []
    cur = []
    cur_len = 0
    for line in lines:
        cur.append(line)
        cur_len += len(line)
        if cur_len >= chunk_size:
            chunks.append("\n".join(cur))
            cur = cur[-overlap:]  # keep some overlap
            cur_len = sum(len(l) for l in cur)
    if cur:
        chunks.append("\n".join(cur))
    return chunks

def ingest_files(files: List[str], deps: RAGDeps) -> int:
    total_chunks = 0
    for path in files:
        code = load_code(path)
        chunks = chunk_code(code)
        if not chunks:
            continue
        embeddings = ollama_embed(chunks)
        ids = [f"{os.path.basename(path)}::{i}::{uuid.uuid4().hex[:6]}" for i in range(len(chunks))]
        metas = [{"source": path, "chunk": i} for i in range(len(chunks))]
        deps.collection.add(documents=chunks, embeddings=embeddings, ids=ids, metadatas=metas)
        total_chunks += len(chunks)
    return total_chunks

def search(deps: RAGDeps, query: str, k: int = 5) -> List[Tuple[str, str]]:
    q_emb = ollama_embed([query])[0]
    res = deps.collection.query(query_embeddings=[q_emb], n_results=k, include=["documents", "ids"])
    docs = res.get("documents", [[]])[0]
    ids = res.get("ids", [[]])[0]
    return list(zip(ids, docs))

# ---------------------------
# Agent
# ---------------------------
ollama_model = OpenAIModel(
    model_name="LLM_MODEL",
    provider=OllamaProvider(base_url='http://localhost:11434/v1'),
)

agent = Agent(
    ollama_model,
    deps_type=RAGDeps,
    instructions=(
        "You are a code assistant. Use the `search_chroma` tool to retrieve code snippets from the vector DB. "
        "Answer ONLY using retrieved code context. If answer isn't found, say: 'I don't have that in my codebase.' "
        "Include doc IDs in square brackets for citations."
    ),
)

@agent.tool
def search_chroma(ctx: RunContext[RAGDeps], query: str, top_k: int = 5) -> List[Tuple[str, str]]:
    """Search code chunks in Chroma DB."""
    return search(ctx.deps, query, k=top_k)

# ---------------------------
# CLI
# ---------------------------
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Ollama + Chroma + Pydantic AI (Code RAG)")
    parser.add_argument("--ingest", nargs="*", help="Code file patterns (e.g., './src/**/*.py')")
    parser.add_argument("--ask", type=str, help="Ask a question")
    parser.add_argument("--topk", type=int, default=5)
    args = parser.parse_args()

    deps = make_deps()

    if args.ingest:
        files = []
        for pattern in args.ingest:
            files.extend(glob.glob(pattern, recursive=True))
        added = ingest_files(files, deps)
        print(f"Ingested {added} code chunks from {len(files)} files.")

    if args.ask:
        result = agent.run_sync(args.ask, deps=deps)
        print("\n=== ANSWER ===\n")
        print(result.output)
        print("\n=== RETRIEVAL ===")
        for did, snippet in search(deps, args.ask, k=args.topk):
            print(f"[{did}] {snippet[:150].replace('\\n',' ')}...")

if __name__ == "__main__":
    main()


