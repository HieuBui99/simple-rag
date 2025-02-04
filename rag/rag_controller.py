import json
import os
from typing import Dict, List

import aiohttp
import numpy as np
from faiss import IndexFlatIP
from rank_bm25 import BM25

from .settings import app_settings


async def semantic_search(query: str, index: IndexFlatIP, top_k: int = 5):
    vectorize_payload = {"inputs": [f"search_document: {query}"]}

    async with aiohttp.ClientSession() as session:
        response = await session.post(
            app_settings.VECTORIZE_ENDPOINT,
            data=json.dumps(vectorize_payload),
            headers={"Content-Type": "application/json"},
        )
    response_data = await response.json()
    query_vector = np.array(response_data)

    _, index = index.search(query_vector, top_k)
    return index.squeeze().tolist()


def lexical_search(query: str, index: BM25, top_k: int = 5):
    tokenized_query = query.lower().split()
    scores = index.get_scores(tokenized_query)
    top_n = np.argsort(scores)[::-1][:top_k]
    return top_n.tolist()


async def search(query: str, indexes: dict, top_k: int = 5):
    lexical_index = indexes["lexical"]
    semantic_index = indexes["semantic"]

    lexical_results = lexical_search(query, lexical_index, top_k)
    semantic_results = await semantic_search(query, semantic_index, top_k)
    return {
        "lexical": lexical_results,
        "semantic": semantic_results,
    }


async def rerank(
    query: str, documents: List[str], search_results: Dict, top_k: int = 4
):
    semantic_documents = documents[search_results["semantic"]].tolist()
    lexical_documents = documents[search_results["lexical"]].tolist()

    retrieved_documents = list(set(semantic_documents + lexical_documents))

    payload = {
        "query": query,
        "texts": retrieved_documents,
    }
    async with aiohttp.ClientSession() as session:
        response = await session.post(
            app_settings.RERANK_ENDPOINT,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
        )

    response_data = await response.json()
    reranked_indices = [x["index"] for x in response_data][:top_k]
    reranked_documents = [retrieved_documents[i] for i in reranked_indices]
    return reranked_documents
