#!/usr/bin/env python3
"""Cloud speech through OpenRouter's speech endpoint, with a local cache.

Standard library only. Sending lesson text to a cloud voice is an external upload:
callers must obtain the learner's consent first (``CloudOptions.external_ok``).
The API key is passed in by the caller and never appears in messages.
"""

from __future__ import annotations

import hashlib
import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

ENDPOINT = "https://openrouter.ai/api/v1/audio/speech"
DEFAULT_CACHE = Path.home() / ".cache" / "ai-tutor" / "tts"


@dataclass(frozen=True)
class CloudOptions:
    model: str
    voice: str
    instructions: str = ""
    cache_dir: Path = DEFAULT_CACHE
    external_ok: bool = False


class CloudVoiceError(RuntimeError):
    """A cloud voice request failed; the message never contains the API key."""


def cache_key(text: str, options: CloudOptions) -> str:
    payload = json.dumps({"model": options.model, "voice": options.voice, "instructions": options.instructions,
                          "text": text}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def openrouter_wav(text: str, options: CloudOptions, api_key: str, opener=urllib.request.urlopen) -> bytes:
    """Ask OpenRouter for ``text`` as WAV and return the bytes."""

    body = {"model": options.model, "input": text, "voice": options.voice, "response_format": "wav"}
    if options.instructions:
        body["instructions"] = options.instructions
    request = urllib.request.Request(ENDPOINT, data=json.dumps(body).encode("utf-8"), method="POST", headers={
        "Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
    try:
        with opener(request, timeout=180) as response:
            audio = response.read()
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "replace")[:300]
        raise CloudVoiceError(f"OpenRouter answered {error.code}: {detail}".replace(api_key, "***")) from None
    except (urllib.error.URLError, OSError) as error:
        raise CloudVoiceError(f"OpenRouter could not be reached: {error}".replace(api_key, "***")) from None
    if not (audio[:4] == b"RIFF" and audio[8:12] == b"WAVE"):
        raise CloudVoiceError(f"OpenRouter did not return WAV audio: {audio[:120]!r}".replace(api_key, "***"))
    return audio


def speak_cloud(paths: list[Path], texts: list[str], options: CloudOptions, api_key: str,
                opener=urllib.request.urlopen) -> list[Path]:
    """Write one WAV per text, all or none: on any failure, no output file is left behind."""

    options.cache_dir.mkdir(parents=True, exist_ok=True)
    audios = []
    for text in texts:
        cached = options.cache_dir / f"{cache_key(text, options)}.wav"
        if not cached.is_file():
            audio = openrouter_wav(text, options, api_key, opener=opener)
            cached.write_bytes(audio)
        audios.append(cached.read_bytes())
    for path, audio in zip(paths, audios):
        path.write_bytes(audio)
    return paths
