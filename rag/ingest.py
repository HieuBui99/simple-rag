import asyncio
import json
import os

import aiohttp
import faiss
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

DATA_PATH = "../data/anime.csv"


def chunked(iterable, size):
    for i in range(0, len(iterable), size):
        yield iterable[i : i + size]


async def vectorize_texts(data_path, bs=8):
    df = pd.read_csv(data_path, delimiter="\t", engine="python")
    df.dropna(subset=["title", "synopsis"], inplace=True)
    df["text"] = "search_document: " + df["title"] + " - " + df["synopsis"]

    texts = df["text"].tolist()
    timeout = aiohttp.ClientTimeout(total=30)
    retries = 3
    results = []

    async with aiohttp.ClientSession(timeout=timeout) as session:
        for batch in tqdm(chunked(texts, bs)):
            for attempt in range(retries):
                try:
                    payload = {"inputs": list(batch)}
                    result = await session.post(
                        os.getenv("VECTORIZE_ENPOINT"),
                        data=json.dumps(payload),
                        headers={"Content-Type": "application/json"},
                    )
                    result = await result.json()
                    results.extend(result)
                    break
                except Exception as e:
                    print(e, batch)
                    if attempt < retries - 1:
                        await asyncio.sleep(1)
                    else:
                        raise e

    return results


async def main():
    index = faiss.IndexFlatIP(768)
    vectors = await vectorize_texts(DATA_PATH)

    index.add(np.array(vectors))
    faiss.write_index(index, "../data/anime.faiss")


if __name__ == "__main__":
    asyncio.run(main())
