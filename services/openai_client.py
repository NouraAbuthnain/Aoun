"""Shared OpenAI client for Aoun."""

from __future__ import annotations

from functools import lru_cache

from openai import OpenAI

from config.settings import OPENAI_API_KEY


@lru_cache(maxsize=1)
def get_openai_client() -> OpenAI:
    """Return one reusable OpenAI client."""

    if not OPENAI_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY was not found. Check the .env file."
        )

    return OpenAI(api_key=OPENAI_API_KEY)