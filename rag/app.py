from contextlib import asynccontextmanager
from pathlib import Path

import re
import faiss
import pandas as pd
from fastapi import FastAPI, Request
from rank_bm25 import BM25Okapi

from .settings import settings


search_index = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Initializing vector search index!!")

    document_path = Path(settings.DATA_PATH) / "anime_clean.csv"
    documents = pd.read_csv(document_path)['text']

    #BM25
    tokenized_documents = [re.sub(r"[^a-zA-Z0-9]", " ", document).lower().split() for document in documents]
    lexical_index = BM25Okapi(tokenized_documents)

    #Faiss
    semantic_index = faiss.read_index(settings.DATA_PATH / "anime.faiss") 

    search_index['lexical'] = lexical_index
    search_index['semantic'] = semantic_index

    yield

    search_index.clear()

app = FastAPI()


@app.get("/health_check")
async def health_check(request: Request):
    return {"status": "ok"}
