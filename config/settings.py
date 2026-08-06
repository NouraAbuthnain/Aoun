"""Aoun application settings."""

from __future__ import annotations

import os

from dotenv import load_dotenv


load_dotenv()


APP_TITLE = "Aoun – AI Healthcare Claims Validation"

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./aoun.db",
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

OPENAI_MODEL = os.getenv(
    "OPENAI_MODEL",
    "gpt-4.1-mini",
)

OPENAI_STT_MODEL = os.getenv(
    "OPENAI_STT_MODEL",
    "gpt-4o-mini-transcribe",
)

OPENAI_TTS_MODEL = os.getenv(
    "OPENAI_TTS_MODEL",
    "gpt-4o-mini-tts",
)

OPENAI_TTS_VOICE = os.getenv(
    "OPENAI_TTS_VOICE",
    "coral",
)