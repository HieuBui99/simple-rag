import asyncio
import json
import os
import re
from contextlib import closing
from io import BytesIO
from typing import AsyncGenerator, Dict, List, Optional, Tuple

import aiohttp
import requests
from dotenv import load_dotenv

from .settings import app_settings

load_dotenv()


PROMPT_TEMPLATE = """
You are an assistant for an anime website. Answer the user's QUESTION about anime using the provided CONTEXT. Be succinct. Ignore any contexts in the list that don't seem relevant to the QUESTION.

QUESTION: {question}

CONTEXT:
{context}
""".strip()


def split_text(text):
    # Split the text into the model's thought and the rest of the text
    pattern = r"<think>(.*?)</think>\s*(.*)"
    match = re.search(pattern, text, re.DOTALL)

    if not match:
        return None, None

    thought = match.group(1).strip()
    rest = match.group(2).strip()

    return thought, rest


def build_prompt(query: str, search_results: List[str]) -> str:
    context = ""

    for doc in search_results:
        context += "Anime Title: " + doc + "\n\n"

    prompt = PROMPT_TEMPLATE.format(question=query, context=context)
    return prompt


async def stream_chat_response(url: str, payload: Dict) -> AsyncGenerator[bytes, None]:
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            async for data in response.content.iter_any():
                yield data


async def get_chat_response(prompt: str) -> Tuple[Optional[str], Optional[str]]:
    payload = {
        "model": app_settings.MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "options": {"temperature": app_settings.OLLAMA_TEMPERATURE},
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(app_settings.OLLAMA_ENDPOINT, json=payload) as response:
            response_data = await response.read()

    model_output = ""
    for line in response_data.decode("utf-8").split("\n"):
        if line:
            response_json = json.loads(line)
            model_output += response_json["message"]["content"]

    thought, answer = split_text(model_output)
    return thought, answer


async def main():
    url = os.getenv("OLLAMA_ENDPOINT")
    payload = {
        "model": "deepseek-r1:14b",
        "messages": [
            {"role": "system", "content": "You are mario from the game mario bros."},
            {"role": "user", "content": "Hello, who are you"},
        ],
        "options": {
            "temperature": 0.5,
        },
    }
    response = await get_chat_response(url, payload)

    response_data = ""
    # decode response content
    for line in response.decode("utf-8").split("\n"):
        if line:
            response_json = json.loads(line)
            response_data += response_json["message"]["content"]

    thought, answer = split_text(response_data)

    return thought, answer


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    thought, answer = loop.run_until_complete(main())
    print(thought)
    print(answer)
