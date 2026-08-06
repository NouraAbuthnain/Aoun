"""Speech-to-text service for clinical dictation."""

from __future__ import annotations

from io import BytesIO

from config.settings import OPENAI_STT_MODEL
from services.openai_client import get_openai_client


def transcribe_audio(
    audio_bytes: bytes,
    filename: str = "clinical_note.wav",
    language: str | None = None,
) -> str:
    """Convert recorded clinical audio into text."""

    if not audio_bytes:
        raise ValueError("The audio recording is empty.")

    client = get_openai_client()

    audio_file = BytesIO(audio_bytes)
    audio_file.name = filename

    request = {
        "model": OPENAI_STT_MODEL,
        "file": audio_file,
        "prompt": (
            "This is a healthcare clinical note. Preserve medical terms, "
            "medication names, diagnoses, measurements, dates, and negations."
        ),
    }

    if language in {"ar", "en"}:
        request["language"] = language

    response = client.audio.transcriptions.create(**request)

    transcript = response.text.strip()

    if not transcript:
        raise RuntimeError("The transcription response was empty.")

    return transcript