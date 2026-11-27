#!/usr/bin/env python3
"""Cloud speech through OpenRouter's speech endpoint, with a local cache.

Standard library only. Sending lesson text to a cloud voice is an external upload:
callers must obtain the learner's consent first (``CloudOptions.external_ok``),
and ``speak_cloud`` refuses without it. The API key is passed in by the caller
and never appears in messages.
"""

from __future__ import annotations

import hashlib
import http.client
import io
import json
import os
import urllib.error
import urllib.request
import wave
from dataclasses import dataclass
from pathlib import Path

ENDPOINT = "https://openrouter.ai/api/v1/audio/speech"
DEFAULT_CACHE = Path.home() / ".cache" / "ai-tutor" / "tts"
MIN_RATE, MAX_RATE = 8000, 48000


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


def normalize_wav(audio: bytes) -> bytes:
    """Return ``audio`` as a canonical 16-bit PCM WAV with correct sizes, or raise ``CloudVoiceError``.

    Streaming encoders write 0xFFFFFFFF as the data size; ``wave`` then reports
    billions of frames. Reading the samples and writing them again fixes the header.
    """

    if not (audio[:4] == b"RIFF" and audio[8:12] == b"WAVE"):
        raise CloudVoiceError(f"the cloud voice did not return WAV audio: {audio[:120]!r}")
    try:
        with wave.open(io.BytesIO(audio)) as handle:
            channels, width, rate = handle.getnchannels(), handle.getsampwidth(), handle.getframerate()
            body = audio[audio.find(b"data") + 8:] if handle.getnframes() >= 0x7FFFFFFF // (channels * width) \
                else handle.readframes(handle.getnframes())
    except (wave.Error, EOFError, ValueError) as error:
        raise CloudVoiceError(f"the cloud voice returned an unreadable WAV: {error}") from None
    body = body[: len(body) - len(body) % (channels * width)]
    if width != 2 or not MIN_RATE <= rate <= MAX_RATE or not body:
        raise CloudVoiceError(f"the cloud voice returned unsupported audio ({width * 8}-bit, {rate} Hz, "
                              f"{len(body) // (channels * width)} frames); 16-bit PCM is required")
    out = io.BytesIO()
    with wave.open(out, "wb") as handle:
        handle.setnchannels(channels)
        handle.setsampwidth(width)
        handle.setframerate(rate)
        handle.writeframes(body)
    return out.getvalue()


def _hide(message: str, api_key: str) -> str:
    return message.replace(api_key, "***") if api_key else message


def openrouter_wav(text: str, options: CloudOptions, api_key: str, opener=urllib.request.urlopen) -> bytes:
    """Ask OpenRouter for ``text`` as WAV and return canonical 16-bit PCM WAV bytes."""

    if not api_key:
        raise CloudVoiceError("the OpenRouter API key is empty")
    body = {"model": options.model, "input": text, "voice": options.voice, "response_format": "wav"}
    if options.instructions:
        body["instructions"] = options.instructions
    request = urllib.request.Request(ENDPOINT, data=json.dumps(body).encode("utf-8"), method="POST", headers={
        "Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
    try:
        with opener(request, timeout=180) as response:
            audio = response.read()
    except urllib.error.HTTPError as error:
        try:
            detail = error.read().decode("utf-8", "replace")[:300]
        except Exception:  # the error body itself may fail to arrive
            detail = ""
        raise CloudVoiceError(_hide(f"OpenRouter answered {error.code}: {detail}", api_key)) from None
    except (urllib.error.URLError, http.client.HTTPException, OSError) as error:
        raise CloudVoiceError(_hide(f"OpenRouter could not be reached: {error!r}", api_key)) from None
    return normalize_wav(audio)


def _cached(path: Path) -> bytes | None:
    """The cached WAV, or ``None`` when it is missing or unreadable (a broken file is removed)."""

    if not path.is_file():
        return None
    try:
        return normalize_wav(path.read_bytes())
    except CloudVoiceError:
        path.unlink(missing_ok=True)
        return None


def speak_cloud(paths: list[Path], texts: list[str], options: CloudOptions, api_key: str,
                opener=urllib.request.urlopen) -> list[Path]:
    """Write one WAV per text, all or none, in one audio format.

    Requires ``options.external_ok`` (the learner's consent). On any failure no
    output file is left behind; lines fetched before the failure stay cached.
    """

    if not options.external_ok:
        raise CloudVoiceError("sending text to a cloud voice needs the learner's consent (external_ok)")
    options.cache_dir.mkdir(parents=True, exist_ok=True)
    audios = []
    for text in texts:
        cached = options.cache_dir / f"{cache_key(text, options)}.wav"
        audio = _cached(cached)
        if audio is None:
            audio = openrouter_wav(text, options, api_key, opener=opener)
            temporary = cached.with_suffix(".tmp")
            temporary.write_bytes(audio)
            os.replace(temporary, cached)
        audios.append(audio)
    formats = set()
    for audio in audios:
        with wave.open(io.BytesIO(audio)) as handle:
            formats.add((handle.getnchannels(), handle.getsampwidth(), handle.getframerate()))
    if len(formats) > 1:
        raise CloudVoiceError(f"the cloud voice returned mixed audio formats {sorted(formats)}")
    for path, audio in zip(paths, audios):
        path.write_bytes(audio)
    return paths
