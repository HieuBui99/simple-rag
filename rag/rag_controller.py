import json

import aiohttp
import numpy as np
from faiss import IndexFlatIP

from .settings import settings


async def semantic_search(query: str, index: IndexFlatIP, top_k: int = 5):
    vectorize_endpoint = settings.VECTORIZE_ENDPOINT
    vectorize_payload = {
        "inputs": [f"search_document: {query}"]
    }
    
    async with aiohttp.ClientSession() as session:
        response = await session.post(
            vectorize_endpoint,
            data=json.dumps(vectorize_payload),
            headers={"Content-Type": "application/json"},
        )
    response_data = await response.json()
    query_vector = np.array(response_data)

    _, index = index.search(query_vector, top_k)
    return index.squeeze()