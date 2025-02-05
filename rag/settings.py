import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """
    Config settings for the application
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.load_settings()
        return cls._instance

    def load_settings(self):
        self._OLLAMA_ENDPOINT: str = os.environ.get("OLLAMA_ENDPOINT")
        self._OLLAMA_TEMPERATURE: float = float(os.environ.get("OLLAMA_TEMPERATURE"))
        self._MODEL: str = os.environ.get("MODEL")
        self._VECTORIZE_ENDPOINT: str = os.environ.get("VECTORIZE_ENDPOINT")
        self._RERANK_ENDPOINT: str = os.environ.get("RERANK_ENDPOINT")
        self._DATA_PATH: str = os.environ.get("DATA_PATH")

    @property
    def OLLAMA_ENDPOINT(self) -> str:
        return self._OLLAMA_ENDPOINT

    @property
    def OLLAMA_TEMPERATURE(self) -> float:
        return self._OLLAMA_TEMPERATURE

    @property
    def MODEL(self) -> str:
        return self._MODEL

    @property
    def VECTORIZE_ENDPOINT(self) -> str:
        return self._VECTORIZE_ENDPOINT

    @property
    def RERANK_ENDPOINT(self) -> str:
        return self._RERANK_ENDPOINT

    @property
    def DATA_PATH(self) -> str:
        return self._DATA_PATH


app_settings = Settings()
