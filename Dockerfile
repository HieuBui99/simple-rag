FROM python:3.12-slim

WORKDIR /app

RUN pip install uv

#copy data
COPY data/anime.faiss data/anime.faiss
COPY data/anime_clean.csv data/anime_clean.csv

COPY pyproject.toml pyproject.toml

RUN uv pip install -r pyproject.toml --system

COPY rag/ rag/

CMD ["uvicorn", "rag.app:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]