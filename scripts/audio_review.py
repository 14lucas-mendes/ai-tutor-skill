#!/usr/bin/env python3
"""Render a local audio review: question, tone, pause, answer (retrieval first).

Two styles share one script format:

- ``recall`` (the default): retrieval first, with question, tone, pause and
  answer blocks, closed by questions without answers;
- ``summary``: a narrated summary of the lesson, only ``say`` segments and an
  optional closing ``questions`` segment, for a learner who already does
  retrieval in cards and asked for a screen-free retelling.

The audio is written for the ear: it has its own script, never the video
narration, because a video narration points at the screen ("this line").

The pure part (validation, screen-reference warnings, the playback plan, the
tone and the transcript) uses only the standard library. Speech needs
``piper-tts`` (or the Windows SAPI voices), the MP3 needs ``ffmpeg`` and the
speech check needs ``faster-whisper``; see ``requirements-video.txt``.

Usage::

    python scripts/audio_review.py validate script.json
    python scripts/audio_review.py render script.json --out review.mp3 --voice piper --model voice.onnx
    python scripts/audio_review.py check script.json review.mp3

Generated audio is review material: never learning evidence.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import struct
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

try:
    from scripts.video_lesson import VOICES, build_pronouncer, speak_texts, speech_match
except ModuleNotFoundError:  # direct execution, also under ``python -I``
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from video_lesson import VOICES, build_pronouncer, speak_texts, speech_match

SCHEMA_VERSION = 1
SEGMENT_TYPES = {"say", "recall", "questions"}
STYLES = ("recall", "summary")
SCREEN_WORDS = (
    "esta linha", "este bloco", "na tela", "veja aqui", "dá uma olhada", "aqui em cima",
    "this line", "this block", "on screen", "look here",
)
MAX_PAUSE = 30
GAP_AFTER_SAY = 1.0
GAP_BEFORE_TONE = 0.4
GAP_AFTER_ANSWER = 1.0
GAP_AFTER_INTRO = 0.5
THINK_AFTER_FINAL_QUESTION = 4.0
TONE_HZ, TONE_SECONDS, TONE_VOLUME = 880.0, 0.22, 0.22
DEFAULT_LABELS = {
    "question": "Question: ",
    "answer": "Answer: ",
    "pause": "[tone and {seconds} s pause]",
    "final": "Final question {number}: ",
    "think": "[{seconds} s to think]",
}


# ---------------------------------------------------------------------------
# Script validation (pure)
# ---------------------------------------------------------------------------

def _is_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_audio_script(script: object) -> list[str]:
    """Return every problem in an audio review script; an empty list means valid."""

    if not isinstance(script, dict):
        return ["script must be an object"]
    errors: list[str] = []
    if script.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    if script.get("kind") != "audio":
        errors.append("kind must be audio")
    for field in ("title", "lesson_id"):
        if not _is_text(script.get(field)):
            errors.append(f"{field} must be non-empty text")
    sources = script.get("source_ids")
    if not isinstance(sources, list) or not sources or not all(_is_text(s) for s in sources):
        errors.append("source_ids must list at least one source")
    pronunciation = script.get("pronunciation", {})
    if not isinstance(pronunciation, dict) or not all(_is_text(k) and isinstance(v, str) for k, v in pronunciation.items()):
        errors.append("pronunciation must map text to spoken text")
    labels = script.get("labels", {})
    if not isinstance(labels, dict) or not all(k in DEFAULT_LABELS and isinstance(v, str) for k, v in labels.items()):
        errors.append(f"labels may only override {sorted(DEFAULT_LABELS)} with text")
    style = script.get("style", "recall")
    if style not in STYLES:
        errors.append(f"style must be one of {list(STYLES)}")
    segments = script.get("segments")
    if not isinstance(segments, list) or not segments:
        errors.append("segments must be a non-empty list")
        return errors
    recalls = 0
    says = 0
    for number, segment in enumerate(segments, 1):
        where = f"segment {number}"
        if not isinstance(segment, dict) or segment.get("type") not in SEGMENT_TYPES:
            errors.append(f"{where}: type must be one of {sorted(SEGMENT_TYPES)}")
            continue
        kind = segment["type"]
        if kind == "say":
            says += 1
            if not _is_text(segment.get("text")):
                errors.append(f"{where}: text must be non-empty text")
        if kind == "recall":
            recalls += 1
            for field in ("question", "answer"):
                if not _is_text(segment.get(field)):
                    errors.append(f"{where}: {field} must be non-empty text")
            pause = segment.get("pause_seconds")
            if not isinstance(pause, (int, float)) or isinstance(pause, bool) or not 1 <= pause <= MAX_PAUSE:
                errors.append(f"{where}: pause_seconds must be between 1 and {MAX_PAUSE}")
        if kind == "questions":
            items = segment.get("items")
            if not isinstance(items, list) or not items or not all(_is_text(i) for i in items):
                errors.append(f"{where}: items must be a non-empty list of text")
            for field in ("intro", "outro"):
                if field in segment and not _is_text(segment[field]):
                    errors.append(f"{where}: {field} must be non-empty text when present")
            if number != len(segments):
                errors.append(f"{where}: questions must be the last segment")
    if style == "summary":
        if recalls:
            errors.append("a summary has no recall segments; use the recall style for question and answer blocks")
        if says == 0:
            errors.append("a summary needs at least one say segment")
        return errors
    if recalls == 0:
        errors.append("an audio review needs at least one recall segment")
    last = segments[-1]
    if not isinstance(last, dict) or last.get("type") != "questions":
        errors.append("the last segment must be questions, without answers")
    return errors


def spoken_texts(script: dict) -> list[str]:
    """Every text the voice says, in order and in correct spelling."""

    texts: list[str] = []
    for segment in script["segments"]:
        if segment["type"] == "say":
            texts.append(segment["text"])
        elif segment["type"] == "recall":
            texts += [segment["question"], segment["answer"]]
        else:
            texts += [t for t in (segment.get("intro"),) if t] + segment["items"] + [t for t in (segment.get("outro"),) if t]
    return texts


def screen_warnings(script: dict) -> list[str]:
    """Spoken lines that point at a screen the listener does not have."""

    return [f"points at a screen: {text!r}" for text in spoken_texts(script)
            if any(word in text.lower() for word in SCREEN_WORDS)]


# ---------------------------------------------------------------------------
# Playback plan, tone and transcript (pure)
# ---------------------------------------------------------------------------

def plan_audio(script: dict) -> list[tuple]:
    """Return the playback pieces: ``("speech", text, label)``, ``("tone",)``, ``("silence", seconds, note)``."""

    labels = {**DEFAULT_LABELS, **script.get("labels", {})}
    pieces: list[tuple] = []
    for segment in script["segments"]:
        if segment["type"] == "say":
            pieces += [("speech", segment["text"], ""), ("silence", GAP_AFTER_SAY, None)]
        elif segment["type"] == "recall":
            pause = segment["pause_seconds"]
            pieces += [
                ("speech", segment["question"], labels["question"]),
                ("silence", GAP_BEFORE_TONE, None),
                ("tone",),
                ("silence", pause, labels["pause"].format(seconds=f"{pause:g}")),
                ("speech", segment["answer"], labels["answer"]),
                ("silence", GAP_AFTER_ANSWER, None),
            ]
        else:
            if segment.get("intro"):
                pieces += [("speech", segment["intro"], ""), ("silence", GAP_AFTER_INTRO, None)]
            for number, item in enumerate(segment["items"], 1):
                think = labels["think"].format(seconds=f"{THINK_AFTER_FINAL_QUESTION:g}")
                pieces += [("speech", item, labels["final"].format(number=number)),
                           ("silence", THINK_AFTER_FINAL_QUESTION, think)]
            if segment.get("outro"):
                pieces.append(("speech", segment["outro"], ""))
    return pieces


def tone(rate: int, hz: float = TONE_HZ, seconds: float = TONE_SECONDS, volume: float = TONE_VOLUME) -> bytes:
    """A short sine tone (16-bit mono) with soft edges, marking the start of the pause."""

    total = int(seconds * rate)
    samples = []
    for i in range(total):
        envelope = min(1.0, i / (0.02 * rate), (total - i) / (0.05 * rate))
        samples.append(int(32767 * volume * envelope * math.sin(2 * math.pi * hz * i / rate)))
    return struct.pack(f"<{total}h", *samples)


def _clock(seconds: float) -> str:
    minutes, secs = divmod(int(seconds), 60)
    return f"{minutes:02d}:{secs:02d}"


def format_transcript(title: str, pieces: list[tuple], speech_seconds: list[float]) -> tuple[str, float]:
    """Transcript with times, tones and pauses; returns the text and the total length."""

    lines, clock, speeches = [], 0.0, iter(speech_seconds)
    for piece in pieces:
        if piece[0] == "speech":
            lines.append(f"[{_clock(clock)}] {piece[2]}{piece[1]}")
            clock += next(speeches)
        elif piece[0] == "tone":
            clock += TONE_SECONDS
        else:
            if piece[2]:
                lines.append(f"[{_clock(clock)}] {piece[2]}")
            clock += piece[1]
    return f"{title}\n\n" + "\n".join(lines) + "\n", clock


# ---------------------------------------------------------------------------
# Speech, MP3 and check (optional dependencies)
# ---------------------------------------------------------------------------

def assemble_audio(pieces: list[tuple], speech_wavs: list[Path], out: Path, title: str) -> float:
    """Join speech WAVs, tones and silences into an MP3 with ``ffmpeg``; returns seconds."""

    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg was not found on PATH")
    wavs = iter(speech_wavs)
    chunks, params, seconds = [], None, 0.0
    for piece in pieces:
        if piece[0] == "speech":
            with wave.open(str(next(wavs))) as handle:
                if params is None:
                    params = handle.getparams()
                elif (handle.getframerate(), handle.getnchannels(), handle.getsampwidth()) != (
                        params.framerate, params.nchannels, params.sampwidth):
                    raise ValueError("all speech files must share rate, channels and sample width")
                chunks.append(handle.readframes(handle.getnframes()))
                seconds += handle.getnframes() / handle.getframerate()
        else:
            chunks.append(piece)
    if params is None or params.nchannels != 1 or params.sampwidth != 2:
        raise ValueError("speech must be 16-bit mono WAV")
    rate = params.framerate
    audio = []
    for chunk in chunks:
        if isinstance(chunk, bytes):
            audio.append(chunk)
        elif chunk[0] == "tone":
            audio.append(tone(rate))
            seconds += TONE_SECONDS
        else:
            audio.append(b"\x00\x00" * int(chunk[1] * rate))
            seconds += chunk[1]
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        joined = Path(tmp) / "review.wav"
        with wave.open(str(joined), "wb") as handle:
            handle.setnchannels(1)
            handle.setsampwidth(2)
            handle.setframerate(rate)
            handle.writeframes(b"".join(audio))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(joined), "-c:a", "libmp3lame", "-b:a", "64k",
                        "-metadata", f"title={title}", str(out)], check=True)
    return seconds


def render_audio(script: dict, out: Path, voice: str = "piper", model: Path | None = None) -> float:
    """Speak every text, join with tones and pauses, and write the MP3 and its ``.txt`` transcript."""

    pronounce = build_pronouncer(script.get("pronunciation", {}))
    pieces = plan_audio(script)
    texts = [piece[1] for piece in pieces if piece[0] == "speech"]
    with tempfile.TemporaryDirectory() as tmp:
        jobs = [(Path(tmp) / f"t{n:03d}.wav", pronounce(text)) for n, text in enumerate(texts)]
        wavs = speak_texts(jobs, voice=voice, model=model)
        durations = []
        for path in wavs:
            with wave.open(str(path)) as handle:
                durations.append(handle.getnframes() / handle.getframerate())
        total = assemble_audio(pieces, wavs, out, script["title"])
    transcript, _ = format_transcript(script["title"], pieces, durations)
    out.with_suffix(".txt").write_text(transcript, encoding="utf-8")
    return total


def check_audio(script: dict, audio: Path, model: str = "small", language: str = "pt") -> tuple[float, list[tuple[str, str]]]:
    """Transcribe the MP3 locally and compare it with the script text."""

    from faster_whisper import WhisperModel  # optional dependency: faster-whisper

    segments, _ = WhisperModel(model, device="cpu", compute_type="int8").transcribe(
        str(audio), language=language, beam_size=5, vad_filter=True)
    heard = " ".join(segment.text.strip() for segment in segments)
    return speech_match(" ".join(spoken_texts(script)), heard)


# ---------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------

def _load(path: Path) -> dict:
    script = json.loads(path.read_text(encoding="utf-8"))
    errors = validate_audio_script(script)
    if errors:
        raise SystemExit("AUDIO SCRIPT: FAIL\n" + "\n".join(f"- {e}" for e in errors))
    for warning in screen_warnings(script):
        print(f"WARNING: {warning}")
    return script


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render a local audio review from a script.")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("validate").add_argument("script", type=Path)
    render = commands.add_parser("render")
    render.add_argument("script", type=Path)
    render.add_argument("--out", type=Path, required=True)
    render.add_argument("--voice", choices=sorted(VOICES), default="piper")
    render.add_argument("--model", type=Path)
    check = commands.add_parser("check")
    check.add_argument("script", type=Path)
    check.add_argument("audio", type=Path)
    check.add_argument("--model", default="small")
    args = parser.parse_args(argv)

    script = _load(args.script)
    if args.command == "validate":
        print("AUDIO SCRIPT: PASS")
    elif args.command == "render":
        total = render_audio(script, args.out, voice=args.voice, model=args.model)
        print(f"AUDIO: {args.out} ({total:.1f} s)")
    else:
        ratio, differences = check_audio(script, args.audio, model=args.model)
        print(f"SPEECH CHECK: {ratio:.1%} of the script words heard")
        for expected, heard in differences:
            print(f"  - expected {expected!r}, heard {heard!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
