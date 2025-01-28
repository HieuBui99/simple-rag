import json
import os
import re
import asyncio
import aiohttp
from contextlib import closing
from io import BytesIO
from typing import Dict, Iterator, Optional, AsyncGenerator

import requests
from dotenv import load_dotenv

load_dotenv()


def split_text(text):
    # Split the text into the model's thought and the rest of the text
    pattern = r'<think>(.*?)</think>\s*(.*)'
    match = re.search(pattern, text, re.DOTALL)
    
    if not match:
        return None, None
        
    thought = match.group(1).strip()
    rest = match.group(2).strip()
    
    return thought, rest


async def stream_chat_response(url: str, payload: Dict) -> AsyncGenerator[bytes, None]:
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            async for data in response.content.iter_any():
                yield data


async def main():
    url = os.getenv("OLLAMA_ENDPOINT")
    payload =  {
        "model": "deepseek-r1:14b",
        "messages": [
            {
                "role": "system",
                "content": "You are mario from the game mario bros."
            },
            {
                "role": "user",
                "content": "Hello, who are you"
            }
        ],
        "options": {
            "temperature": 0.5,
        },
        "stream": True
    }
    buffer = BytesIO()
    async for chunk in stream_chat_response(url, payload):
        buffer.write(chunk)
    buffer.seek(0)
    response_data = ""
    # decode response content
    for line in buffer.read().decode("utf-8").split("\n"):
        if line:
            response_json = json.loads(line)
            response_data += response_json["message"]["content"]

    thought, answer = split_text(response_data)

    return thought, answer

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    thought, answer = loop.run_until_complete(main())
    print(thought)
    print(answer)