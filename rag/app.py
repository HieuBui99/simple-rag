import re
from contextlib import asynccontextmanager
from pathlib import Path

import faiss
import pandas as pd
from fastapi import FastAPI, Request
from rank_bm25 import BM25Okapi

from .models import Query
from .settings import app_settings
from .rag_controller import search, rerank

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Initializing vector search index!!")

    document_path = Path(app_settings.DATA_PATH) / "anime_clean.csv"
    index_path = Path(app_settings.DATA_PATH) / "anime.faiss"
    documents = pd.read_csv(document_path)["text"]
    # BM25
    tokenized_documents = [
        re.sub(r"[^a-zA-Z0-9]", " ", document).lower().split() for document in documents
    ]
    lexical_index = BM25Okapi(tokenized_documents)

    # Faiss
    semantic_index = faiss.read_index(str(index_path))

    app.state.index = {
        "lexical": lexical_index,
        "semantic": semantic_index,
    }
    app.state.documents = documents

    yield

    app.state.index = None
    app.state.documents = None


app = FastAPI(lifespan=lifespan)


@app.get("/health_check")
async def health_check(request: Request):
    return {"status": "ok"}


@app.post("/query")
async def handle_query(query: Query):
    search_results = await search(query.query, app.state.index)
    reranked_results = await rerank(query.query, app.state.documents, search_results)
    return {"query": query.query}