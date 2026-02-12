"""LLM configuration — local-first, OpenAI-compatible."""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()


def get_llm(temperature: float = 0.0) -> ChatOpenAI:
    """Return an LLM instance configured from environment variables.

    Defaults to local inference (Ollama / LM Studio) if no env vars are set.
    """
    base_url = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
    api_key = os.getenv("LLM_API_KEY", "ollama")
    model_name = os.getenv("LLM_MODEL", "llama3.2")

    return ChatOpenAI(
        base_url=base_url,
        api_key=api_key,
        model=model_name,
        temperature=temperature,
        streaming=True,
    )
