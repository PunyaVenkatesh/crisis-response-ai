"""Shared LLM factory.

One place to configure the model so every agent behaves consistently and the
model can be swapped without touching agent code.
"""

import os

from langchain_groq import ChatGroq

DEFAULT_MODEL = "llama-3.3-70b-versatile"


def get_llm(temperature: float = 0.2, model: str | None = None) -> ChatGroq:
    """Return a configured Groq chat model.

    Temperature defaults low: this system produces operational plans, where
    reproducibility matters more than creative variety.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Add it to a local .env file, or as a "
            "Secret in Hugging Face Space settings."
        )

    return ChatGroq(
        model=model or os.getenv("GROQ_MODEL", DEFAULT_MODEL),
        temperature=temperature,
        api_key=api_key,
        timeout=60,
        max_retries=2,
    )
