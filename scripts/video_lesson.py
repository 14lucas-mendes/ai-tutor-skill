#!/usr/bin/env python3
"""Render a local, source-grounded video lesson from a scene script.

The pure part (script validation, pronunciation, timeline, subtitles and the
speech check) uses only the standard library. Speech, drawing and assembly
import their optional dependencies lazily:

- speech: ``piper-tts`` (any OS) or the Windows SAPI voices (Windows only);
- frames: ``pillow`` and ``pygments``;
- assembly: the ``ffmpeg`` executable;
- speech check: ``faster-whisper``.

Usage::

    python scripts/video_lesson.py validate script.json
    python scripts/video_lesson.py speak script.json --out audio --voice piper --model voice.onnx
    python scripts/video_lesson.py render script.json --audio audio --out lesson.mp4 --frames frames
    python scripts/video_lesson.py check script.json lesson.mp4

Generated videos are review material: never learning evidence.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import wave
from dataclasses import replace
from pathlib import Path
from typing import Callable, Iterator

try:
    from scripts.ide_scene import (code_lines, first_visible_line, initial_screen, quantize, step_events,
                                   terminal_tail, validate_ide_scene)
except ModuleNotFoundError:  # direct execution, also under ``python -I``
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from ide_scene import (code_lines, first_visible_line, initial_screen, quantize, step_events,
                           terminal_tail, validate_ide_scene)

SCHEMA_VERSION = 1
SCENE_TYPES = {"title", "list", "questions", "flow", "code", "compare", "ide"}
COMPARE_PARTS = ("left", "right", "footer")
VOICES = {"piper", "sapi"}

WIDTH, HEIGHT, FPS = 1920, 1080, 30
SCALE = 1.5  # the layout was drawn for 1280x720; every measure is scaled to Full HD
TRANSITION_FRAMES = 12
PAUSE_SECONDS = 0.6


def _px(value: float) -> int:
    """A measure of the 1280x720 layout, in Full HD pixels."""

    return round(value * SCALE)


# ---------------------------------------------------------------------------
# Script validation (pure)
# ---------------------------------------------------------------------------

def _is_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _check_steps(scene: dict, where: str, errors: list[str]) -> list[dict]:
    steps = scene.get("steps")
    if not isinstance(steps, list) or not steps:
        errors.append(f"{where}: steps must be a non-empty list")
        return []
    for index, step in enumerate(steps, 1):
        if not isinstance(step, dict) or not _is_text(step.get("say")):
            errors.append(f"{where} step {index}: say must be non-empty text")
    return [step for step in steps if isinstance(step, dict)]


def _validate_scene(scene: object, number: int, errors: list[str]) -> None:
    where = f"scene {number}"
    if not isinstance(scene, dict):
        errors.append(f"{where}: must be an object")
        return
    kind = scene.get("type")
    if kind not in SCENE_TYPES:
        errors.append(f"{where}: type must be one of {sorted(SCENE_TYPES)}")
        return
    if not _is_text(scene.get("title")):
        errors.append(f"{where}: title must be non-empty text")
    steps = _check_steps(scene, where, errors)

    if kind == "title" and not _is_text(scene.get("subtitle")):
        errors.append(f"{where}: subtitle must be non-empty text")

    if kind in {"list", "questions"}:
        items = scene.get("items")
        if not isinstance(items, list) or not items or not all(_is_text(item) for item in items):
            errors.append(f"{where}: items must be a non-empty list of text")
            return
        for index, step in enumerate(steps, 1):
            show = step.get("show", len(items))
            if not isinstance(show, int) or not 1 <= show <= len(items):
                errors.append(f"{where} step {index}: show must be between 1 and {len(items)}")

    if kind == "flow":
        boxes = scene.get("boxes")
        if not isinstance(boxes, list) or not 1 <= len(boxes) <= 3:
            errors.append(f"{where}: boxes must list 1 to 3 boxes")
            return
        for box in boxes:
            if not isinstance(box, dict) or not _is_text(box.get("label")) or not isinstance(box.get("detail", ""), str):
                errors.append(f"{where}: each box needs a label and an optional text detail")
        for index, step in enumerate(steps, 1):
            active = step.get("active", 0)
            if not isinstance(active, int) or not 0 <= active <= len(boxes):
                errors.append(f"{where} step {index}: active must be between 0 and {len(boxes)}")
            if step.get("note") and not _is_text(scene.get("note")):
                errors.append(f"{where} step {index}: note shown but the scene has no note text")

    if kind == "code":
        if not _is_text(scene.get("file")) or not _is_text(scene.get("language")):
            errors.append(f"{where}: file and language must be non-empty text")
        code = scene.get("code")
        if not _is_text(code):
            errors.append(f"{where}: code must be non-empty text")
            return
        total = len(code.split("\n"))
        for index, step in enumerate(steps, 1):
            visible = step.get("visible", total)
            if not isinstance(visible, int) or not 1 <= visible <= total:
                errors.append(f"{where} step {index}: visible must be between 1 and {total}")
                continue
            highlight = step.get("highlight", [])
            if not isinstance(highlight, list) or not all(
                isinstance(line, int) and 1 <= line <= visible for line in highlight
            ):
                errors.append(f"{where} step {index}: highlight must list visible line numbers")
            output = step.get("output")
            if output is not None and (not isinstance(output, list) or not all(isinstance(x, str) for x in output)):
                errors.append(f"{where} step {index}: output must be a list of text lines")

    if kind == "ide":
        validate_ide_scene(scene, where, steps, errors)

    if kind == "compare":
        for side in ("left", "right"):
            part = scene.get(side)
            if not isinstance(part, dict) or not _is_text(part.get("head")) or not isinstance(part.get("lines"), list):
                errors.append(f"{where}: {side} needs head and lines")
        for index, step in enumerate(steps, 1):
            show = step.get("show")
            if show not in COMPARE_PARTS:
                errors.append(f"{where} step {index}: show must be one of {list(COMPARE_PARTS)}")
            elif show == "footer" and not _is_text(scene.get("footer")):
                errors.append(f"{where} step {index}: footer shown but the scene has no footer text")


def _screen_texts(scene: object) -> list[str]:
    """On-screen text where `backticks` mark inline code (code scenes are already code)."""

    if not isinstance(scene, dict):
        return []
    texts = [scene.get("title"), scene.get("subtitle"), scene.get("note"), scene.get("footer")]
    texts += scene.get("items") or []
    for box in scene.get("boxes") or []:
        if isinstance(box, dict):
            texts += [box.get("label"), box.get("detail")]
    for side in ("left", "right"):
        part = scene.get(side)
        if isinstance(part, dict):
            texts += [part.get("head")] + list(part.get("lines") or [])
    return [text for text in texts if isinstance(text, str)]


def validate_video_script(script: object) -> list[str]:
    """Return every problem in a video script; an empty list means valid."""

    errors: list[str] = []
    if not isinstance(script, dict):
        return ["script must be an object"]
    if script.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    for field in ("title", "lesson_id"):
        if not _is_text(script.get(field)):
            errors.append(f"{field} must be non-empty text")
    sources = script.get("source_ids")
    if not isinstance(sources, list) or not sources or not all(_is_text(s) for s in sources):
        errors.append("source_ids must list at least one source")
    pronunciation = script.get("pronunciation", {})
    if not isinstance(pronunciation, dict) or not all(
        _is_text(k) and isinstance(v, str) for k, v in pronunciation.items()
    ):
        errors.append("pronunciation must map text to spoken text")
    scenes = script.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        errors.append("scenes must be a non-empty list")
        return errors
    for number, scene in enumerate(scenes, 1):
        _validate_scene(scene, number, errors)
    for number, scene in enumerate(scenes, 1):
        for text in _screen_texts(scene):
            if text.count("`") % 2:
                errors.append(f"scene {number}: unbalanced backtick in {text!r}")
    last = scenes[-1]
    if not isinstance(last, dict) or last.get("type") != "questions":
        errors.append("the last scene must be retrieval questions (type questions), without answers")
    return errors


# ---------------------------------------------------------------------------
# Pronunciation, steps, timeline and subtitles (pure)
# ---------------------------------------------------------------------------

def build_pronouncer(mapping: dict[str, str]) -> Callable[[str], str]:
    """Replace terms by their spoken form in one pass, longest term first.

    Terms that start or end with a word character only match whole words, so
    ``import`` does not change ``importa``.
    """

    if not mapping:
        return lambda text: text
    parts = []
    for term in sorted(mapping, key=len, reverse=True):
        pattern = re.escape(term)
        if re.match(r"\w", term):
            pattern = r"(?<!\w)" + pattern
        if re.search(r"\w$", term):
            pattern += r"(?!\w)"
        parts.append(pattern)
    compiled = re.compile("|".join(parts))
    return lambda text: compiled.sub(lambda match: mapping[match.group(0)], text)


def iter_steps(script: dict) -> Iterator[tuple[str, str, dict, dict]]:
    """Yield ``(step_id, say, scene, step)`` in playback order."""

    for scene_number, scene in enumerate(script["scenes"], 1):
        for step_number, step in enumerate(scene["steps"], 1):
            yield f"s{scene_number:02d}_p{step_number:02d}", step["say"], scene, step


def spoken_lines(script: dict) -> list[tuple[str, str]]:
    """Return ``(step_id, text for the voice)`` with the pronunciation applied."""

    pronounce = build_pronouncer(script.get("pronunciation", {}))
    return [(step_id, pronounce(say)) for step_id, say, _, _ in iter_steps(script)]


def build_timeline(speech_seconds: list[float], pause: float = PAUSE_SECONDS) -> list[tuple[float, float, float]]:
    """Return ``(start, speech_end, step_end)`` for each step."""

    timeline, start = [], 0.0
    for seconds in speech_seconds:
        timeline.append((start, start + seconds, start + seconds + pause))
        start += seconds + pause
    return timeline


def srt_timestamp(seconds: float) -> str:
    millis = int(round(seconds * 1000))
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def format_srt(texts: list[str], timeline: list[tuple[float, float, float]]) -> str:
    """Subtitles show the script text (correct spelling), not the voice text."""

    blocks = []
    for number, (text, (start, speech_end, _)) in enumerate(zip(texts, timeline), 1):
        blocks.append(f"{number}\n{srt_timestamp(start)} --> {srt_timestamp(speech_end)}\n{text}\n")
    return "\n".join(blocks)


def concat_list(entries: list[tuple[Path, float]]) -> str:
    """ffmpeg concat-demuxer list; the last image repeats, as the demuxer expects."""

    lines = [f"file '{path.resolve().as_posix()}'\nduration {seconds:.4f}" for path, seconds in entries]
    lines.append(f"file '{entries[-1][0].resolve().as_posix()}'")
    return "\n".join(lines) + "\n"


def _words(text: str) -> list[str]:
    return re.sub(r"[^\w]+", " ", text.lower()).split()


def speech_match(reference: str, heard: str) -> tuple[float, list[tuple[str, str]]]:
    """Compare the script with a transcript: share of matching words and the differences."""

    expected, got = _words(reference), _words(heard)
    if not expected:
        return 0.0, []
    matcher = difflib.SequenceMatcher(a=expected, b=got, autojunk=False)
    matched = sum(block.size for block in matcher.get_matching_blocks())
    differences = [
        (" ".join(expected[i1:i2]), " ".join(got[j1:j2]))
        for op, i1, i2, j1, j2 in matcher.get_opcodes()
        if op != "equal"
    ]
    return matched / len(expected), differences


# ---------------------------------------------------------------------------
# Speech (optional dependencies)
# ---------------------------------------------------------------------------

def synthesize(script: dict, out_dir: Path, voice: str = "piper", model: Path | None = None,
               sapi_voice: str = "Microsoft Maria Desktop", sapi_rate: int = 2) -> list[Path]:
    """Write one WAV per step. Piper needs ``model``; SAPI runs only on Windows."""

    out_dir.mkdir(parents=True, exist_ok=True)
    lines = spoken_lines(script)
    jobs = [(out_dir / f"{step_id}.wav", text) for step_id, text in lines]
    return speak_texts(jobs, voice=voice, model=model, sapi_voice=sapi_voice, sapi_rate=sapi_rate)


def speak_texts(jobs: list[tuple[Path, str]], voice: str = "piper", model: Path | None = None,
                sapi_voice: str = "Microsoft Maria Desktop", sapi_rate: int = 2) -> list[Path]:
    """Write each ``(path, text)`` as a WAV with the chosen voice; the text is already pronounced."""

    if voice not in VOICES:
        raise ValueError(f"voice must be one of {sorted(VOICES)}")
    paths = [path for path, _ in jobs]
    if voice == "piper":
        if model is None:
            raise ValueError("piper needs --model, the path to a .onnx voice")
        from piper import PiperVoice  # optional dependency: piper-tts

        speaker = PiperVoice.load(str(model))
        for path, text in jobs:
            with wave.open(str(path), "wb") as handle:
                speaker.synthesize_wav(text, handle)
        return paths
    if sys.platform != "win32":
        raise RuntimeError("the sapi voice is only available on Windows")
    with tempfile.TemporaryDirectory() as tmp:
        items = Path(tmp) / "lines.json"
        items.write_text(json.dumps([[str(p), t] for p, t in jobs], ensure_ascii=False), encoding="utf-8")
        script_ps = Path(tmp) / "speak.ps1"
        script_ps.write_text(
            "param($list)\n"
            "Add-Type -AssemblyName System.Speech\n"
            "foreach ($i in (Get-Content -Raw -Encoding UTF8 $list | ConvertFrom-Json)) {\n"
            "  $s = New-Object System.Speech.Synthesis.SpeechSynthesizer\n"
            f"  $s.SelectVoice('{sapi_voice}')\n"
            f"  $s.Rate = {int(sapi_rate)}\n"
            "  $s.SetOutputToWaveFile($i[0])\n"
            "  $s.Speak($i[1])\n"
            "  $s.Dispose()\n"
            "}\n",
            encoding="utf-8-sig",
        )
        subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script_ps), str(items)],
                       check=True)
    return paths


# ---------------------------------------------------------------------------
# Frames (optional dependencies: pillow, pygments)
# ---------------------------------------------------------------------------

COLORS = {
    "background": (15, 17, 23), "panel": (24, 27, 36), "border": (46, 51, 68),
    "text": (230, 232, 236), "muted": (140, 146, 160), "faint": (90, 95, 108),
    "accent": (122, 162, 247), "ok": (158, 206, 106), "error": (247, 118, 142),
    "amber": (224, 175, 104), "highlight": (40, 46, 70),
}
FONT_CANDIDATES = {
    "sans": ("segoeui.ttf", "DejaVuSans.ttf", "Arial.ttf", "Helvetica.ttc"),
    "bold": ("segoeuib.ttf", "DejaVuSans-Bold.ttf", "Arial Bold.ttf", "Helvetica.ttc"),
    "semibold": ("seguisb.ttf", "DejaVuSans-Bold.ttf", "Arial Bold.ttf", "Helvetica.ttc"),
    "mono": ("CascadiaMono.ttf", "consola.ttf", "DejaVuSansMono.ttf", "Menlo.ttc"),
}
FONT_DIRS = (
    Path("C:/Windows/Fonts"), Path("/usr/share/fonts/truetype/dejavu"), Path("/usr/share/fonts/TTF"),
    Path("/Library/Fonts"), Path("/System/Library/Fonts"), Path("/System/Library/Fonts/Supplemental"),
)


def _token_color(kind) -> tuple[int, int, int]:
    """Editor color of a pygments token kind (the most specific match wins)."""

    from pygments.token import Token  # optional dependency: pygments

    palette = [
        (Token.Comment, (110, 118, 140)), (Token.Literal.String, (158, 206, 106)),
        (Token.Literal.Number, (255, 158, 100)), (Token.Keyword, (187, 154, 247)),
        (Token.Name.Function, (122, 162, 247)), (Token.Name.Builtin, (125, 207, 255)),
        (Token.Operator, (137, 221, 255)), (Token.Name.Class, (224, 175, 104)),
    ]
    best = None
    for parent, color in palette:
        if kind in parent and (best is None or len(parent) > len(best[0])):
            best = (parent, color)
    return best[1] if best else COLORS["text"]


def _dimmed(color: tuple[int, int, int]) -> tuple[int, int, int]:
    return tuple(int(v * 0.55 + COLORS["panel"][i] * 0.45) for i, v in enumerate(color))


class _Painter:
    def __init__(self, script: dict):
        from PIL import Image, ImageDraw, ImageFont  # optional dependency: pillow

        self.Image, self.ImageDraw, self.ImageFont = Image, ImageDraw, ImageFont
        self._cache: dict[tuple[str, int], object] = {}
        self.footer = script.get("footer") or f"{script['title']} · {script['lesson_id']}"

    def font(self, kind: str, size: int):
        key = (kind, size)
        if key not in self._cache:
            for directory in FONT_DIRS:
                for name in FONT_CANDIDATES[kind]:
                    if (directory / name).is_file():
                        self._cache[key] = self.ImageFont.truetype(str(directory / name), size)
                        return self._cache[key]
            self._cache[key] = self.ImageFont.load_default(size)
        return self._cache[key]

    def canvas(self, title: str | None):
        image = self.Image.new("RGB", (WIDTH, HEIGHT), COLORS["background"])
        draw = self.ImageDraw.Draw(image)
        if title:
            size = _px(34)
            for line in self.rich_lines(draw, title, size, WIDTH - _px(120), kind="semibold")[:1]:
                self.draw_rich_line(draw, _px(60), _px(38), line, size, COLORS["text"], code_color=COLORS["text"], kind="semibold")
            draw.rectangle((_px(60), _px(92), _px(140), _px(96)), fill=COLORS["accent"])
        draw.text((WIDTH - _px(60), HEIGHT - _px(34)), self.footer, font=self.font("sans", _px(16)),
                  fill=COLORS["faint"], anchor="rs")
        return image, draw

    @staticmethod
    def panel(draw, box, border=None):
        draw.rounded_rectangle(box, radius=_px(14), fill=COLORS["panel"], outline=border or COLORS["border"], width=_px(2))

    def rich_lines(self, draw, text, size, width, kind="sans"):
        """Wrap text where `backticked` parts use the monospaced font.

        In proportional fonts, ``__name__`` looks like ``_name_``; code must keep
        every character visible.
        """

        words = []
        previous_ends_with_space = True
        for index, part in enumerate(text.split("`")):
            is_code = index % 2 == 1
            for k, word in enumerate(part.split(" ")):
                if word:
                    glue = k == 0 and not previous_ends_with_space
                    words.append((word, is_code, glue))
            if part:
                previous_ends_with_space = part.endswith(" ")
        lines, current, used = [], [], 0.0
        space = draw.textlength(" ", font=self.font(kind, size))
        for word, is_code, glue in words:
            font = self.code_font(size) if is_code else self.font(kind, size)
            length = draw.textlength(word, font=font)
            extra = 0 if (glue or not current) else space
            if current and used + extra + length > width:
                lines.append(current)
                current, used, extra = [], 0.0, 0
            current.append((word, is_code, extra))
            used += extra + length
        if current:
            lines.append(current)
        return lines

    def code_font(self, size):
        """Inline code: monospaced and a little smaller, to match the text's visual size."""

        return self.font("mono", max(size - _px(3), _px(10)))

    def rich_width(self, draw, line, size, kind="sans"):
        return sum(extra + draw.textlength(w, font=self.code_font(size) if c else self.font(kind, size))
                   for w, c, extra in line)

    def draw_rich_line(self, draw, x, y, line, size, color, code_color=None, kind="sans"):
        for word, is_code, extra in line:
            x += extra
            font = self.code_font(size) if is_code else self.font(kind, size)
            draw.text((x, y + (round(size * 0.12) if is_code else 0)), word, font=font,
                      fill=(code_color or COLORS["amber"]) if is_code else color)
            x += draw.textlength(word, font=font)

    @staticmethod
    def wrap(draw, text, font, width):
        lines, current = [], ""
        for word in text.split():
            attempt = f"{current} {word}".strip()
            if draw.textlength(attempt, font=font) <= width:
                current = attempt
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    def title(self, scene, step):
        image, draw = self.canvas(None)
        draw.text((WIDTH // 2, HEIGHT // 2 - _px(40)), scene["title"], font=self.font("bold", _px(60)),
                  fill=COLORS["text"], anchor="mm")
        draw.rectangle((WIDTH // 2 - _px(60), HEIGHT // 2 + _px(10), WIDTH // 2 + _px(60), HEIGHT // 2 + _px(15)),
                       fill=COLORS["accent"])
        draw.text((WIDTH // 2, HEIGHT // 2 + _px(55)), scene["subtitle"], font=self.font("sans", _px(28)),
                  fill=COLORS["muted"], anchor="mm")
        return image

    def listing(self, scene, step, numbered=False):
        image, draw = self.canvas(scene["title"])
        items = scene["items"]
        shown = step.get("show", len(items))
        size = _px(30) if len(items) <= 4 else _px(26)
        gap = _px(82) if len(items) <= 4 else _px(72)
        y = _px(140)
        for number, item in enumerate(items[:shown], 1):
            current = numbered or number == shown
            marker = f"{number}." if numbered else "●"
            draw.text((_px(80), y), marker, font=self.font("bold", _px(26)),
                      fill=COLORS["accent"] if current else COLORS["faint"])
            lines = self.rich_lines(draw, item, size, WIDTH - _px(220))
            for k, line in enumerate(lines):
                self.draw_rich_line(draw, _px(125), y - _px(4) + k * _px(38), line, size,
                                    COLORS["text"] if current else COLORS["muted"],
                                    code_color=COLORS["amber"] if current else COLORS["muted"])
            y += gap + (len(lines) - 1) * _px(38)
        return image

    def flow(self, scene, step, note_seen):
        image, draw = self.canvas(scene["title"])
        active = step.get("active", 0)
        boxes = scene["boxes"]
        width, height, top = _px(330), _px(230), _px(190)
        lefts = [_px(70), _px(475), _px(880)][: len(boxes)]
        for number, (left, box) in enumerate(zip(lefts, boxes), 1):
            on = number == active
            lit = on or active == 0
            self.panel(draw, (left, top, left + width, top + height), COLORS["accent"] if on else None)
            draw.text((left + _px(24), top + _px(24)), box["label"], font=self.font("bold", _px(30)),
                      fill=COLORS["text"] if lit else COLORS["muted"])
            for k, line in enumerate(box.get("detail", "").split("\n")):
                code_like = "." in line and " " not in line
                color = (COLORS["amber"] if code_like else COLORS["text"]) if lit else COLORS["faint"]
                draw.text((left + _px(24), top + _px(84) + k * _px(36)), line,
                          font=self.font("mono" if code_like else "sans", _px(24)), fill=color)
            if number < len(boxes):
                x, mid = left + width + _px(12), top + height // 2
                draw.line((x, mid, x + _px(50), mid), fill=COLORS["accent"], width=_px(4))
                draw.polygon([(x + _px(50), mid - _px(10)), (x + _px(64), mid), (x + _px(50), mid + _px(10))],
                             fill=COLORS["accent"])
        if note_seen:
            self.panel(draw, (_px(70), _px(480), _px(1210), _px(550)), COLORS["error"])
            draw.text((WIDTH // 2, _px(515)), scene["note"], font=self.font("semibold", _px(26)),
                      fill=COLORS["error"], anchor="mm")
        return image

    @staticmethod
    def code_rows(code: str, language: str) -> list[list[tuple[object, str]]]:
        """Syntax tokens of ``code``, one list per line."""

        from pygments import lex  # optional dependency: pygments
        from pygments.lexers import get_lexer_by_name

        rows: list[list[tuple[object, str]]] = [[]]
        for kind, value in lex(code, get_lexer_by_name(language)):
            for k, piece in enumerate(value.split("\n")):
                if k:
                    rows.append([])
                if piece:
                    rows[-1].append((kind, piece))
        return rows

    def code(self, scene, step):
        token_color = _token_color
        image, draw = self.canvas(scene["title"])
        lines = scene["code"].split("\n")
        visible = step.get("visible", len(lines))
        marked = set(step.get("highlight", []))
        mono, line_h = self.font("mono", _px(22)), _px(31)
        left, top, right = _px(60), _px(125), WIDTH - _px(60)
        bottom = min(top + _px(70) + line_h * len(lines), _px(640))
        self.panel(draw, (left, top, right, bottom))
        tab_font = self.font("mono", _px(18))
        draw.rounded_rectangle((left, top, left + _px(48) + draw.textlength(scene["file"], font=tab_font), top + _px(38)),
                               radius=_px(10), fill=COLORS["border"])
        draw.text((left + _px(24), top + _px(8)), scene["file"], font=tab_font, fill=COLORS["text"])
        rows = self.code_rows(scene["code"], scene["language"])
        for index in range(min(visible, len(lines))):
            y, number = top + _px(54) + index * line_h, index + 1
            if number in marked:
                draw.rectangle((left + _px(2), y - _px(3), right - _px(2), y + line_h - _px(5)), fill=COLORS["highlight"])
                draw.rectangle((left + _px(2), y - _px(3), left + _px(7), y + line_h - _px(5)), fill=COLORS["amber"])
            draw.text((left + _px(22), y), f"{number:>2}", font=mono, fill=COLORS["faint"])
            x, dim = left + _px(72), bool(marked) and number not in marked
            for kind, text in rows[index] if index < len(rows) else []:
                color = token_color(kind)
                if dim:
                    color = _dimmed(color)
                draw.text((x, y), text, font=mono, fill=color)
                x += draw.textlength(text, font=mono)
        output = step.get("output")
        if output:
            term = list(output) if output[0].startswith("$") else ["$ " + scene.get("command", "")] + list(output)
            t_top = bottom + _px(24)
            self.panel(draw, (left, t_top, right, min(t_top + _px(50) + _px(32) * len(term), HEIGHT - _px(50))))
            draw.text((left + _px(22), t_top + _px(12)), "terminal", font=self.font("semibold", _px(18)), fill=COLORS["muted"])
            for k, line in enumerate(term):
                color = COLORS["accent"] if line.startswith("$") else (COLORS["error"] if step.get("error") else COLORS["text"])
                draw.text((left + _px(22), t_top + _px(44) + k * _px(32)), line, font=self.font("mono", _px(21)), fill=color)
        return image

    def ide(self, scene, screen):
        """An editor with one tab per file and a terminal below, as ``screen`` describes them."""

        image, draw = self.canvas(None)
        for line in self.rich_lines(draw, scene["title"], _px(24), WIDTH - _px(120), kind="semibold")[:1]:
            self.draw_rich_line(draw, _px(60), _px(16), line, _px(24), COLORS["muted"], kind="semibold")
        left, right = _px(60), WIDTH - _px(60)
        editor_top, editor_bottom, term_top, term_bottom = _px(56), _px(458), _px(470), _px(664)
        files = {f["name"]: f for f in scene["files"]}

        self.panel(draw, (left, editor_top, right, editor_bottom))
        tab_font, x = self.font("mono", _px(18)), left
        for name in files:
            width, on = _px(48) + draw.textlength(name, font=tab_font), name == screen.active
            if on:
                draw.rounded_rectangle((x, editor_top, x + width, editor_top + _px(38)), radius=_px(10),
                                       fill=COLORS["border"])
            draw.text((x + _px(24), editor_top + _px(8)), name, font=tab_font,
                      fill=COLORS["text"] if on else COLORS["faint"])
            x += width + _px(4)

        box = (left + _px(4), editor_top + _px(46), right - _px(4), editor_bottom - _px(8))
        area = self.Image.new("RGB", (box[2] - box[0], box[3] - box[1]), COLORS["panel"])
        pen = self.ImageDraw.Draw(area)
        mono, line_h = self.font("mono", _px(22)), _px(29)
        code = files[screen.active]["code"]
        count = dict(screen.chars)[screen.active]
        lines = code_lines(code[:count]) if count else []
        rows = self.code_rows(code, files[screen.active]["language"])
        capacity = max(1, (area.height - _px(8)) // line_h)
        first = first_visible_line(len(lines), len(lines), capacity)
        marked = set(screen.highlight)
        cursor_at = (_px(68), _px(6))
        for index in range(first - 1, min(len(lines), first - 1 + capacity)):
            y, number = _px(6) + (index - first + 1) * line_h, index + 1
            if number in marked:
                pen.rectangle((0, y - _px(3), area.width, y + line_h - _px(5)), fill=COLORS["highlight"])
                pen.rectangle((0, y - _px(3), _px(5), y + line_h - _px(5)), fill=COLORS["amber"])
            pen.text((_px(18), y), f"{number:>2}", font=mono, fill=COLORS["faint"])
            x, remaining = _px(68), len(lines[index])
            dim = bool(marked) and number not in marked
            for kind, text in rows[index] if index < len(rows) else []:
                if remaining <= 0:
                    break
                piece = text[:remaining]
                remaining -= len(piece)
                color = _token_color(kind)
                pen.text((x, y), piece, font=mono, fill=_dimmed(color) if dim else color)
                x += pen.textlength(piece, font=mono)
            cursor_at = (x, y)
        if screen.cursor == "editor" and screen.cursor_on:
            pen.rectangle((cursor_at[0] + _px(2), cursor_at[1], cursor_at[0] + _px(4), cursor_at[1] + line_h - _px(6)),
                          fill=COLORS["text"])
        image.paste(area, box[:2])

        self.panel(draw, (left, term_top, right, term_bottom))
        draw.text((left + _px(22), term_top + _px(10)), "TERMINAL", font=self.font("semibold", _px(16)),
                  fill=COLORS["muted"])
        box = (left + _px(4), term_top + _px(36), right - _px(4), term_bottom - _px(6))
        area = self.Image.new("RGB", (box[2] - box[0], box[3] - box[1]), COLORS["panel"])
        pen = self.ImageDraw.Draw(area)
        mono, line_h = self.font("mono", _px(21)), _px(30)
        shown = terminal_tail(screen.terminal, max(1, (area.height - _px(4)) // line_h))
        x, y = _px(18), _px(2)
        for k, line in enumerate(shown):
            x, y = _px(18), _px(2) + k * line_h
            text = f"$ {line.text}" if line.kind == "cmd" else line.text
            color = {"cmd": COLORS["accent"], "err": COLORS["error"]}.get(line.kind, COLORS["text"])
            pen.text((x, y), text, font=mono, fill=color)
            x += pen.textlength(text, font=mono)
            if line.entry:
                pen.text((x, y), line.entry, font=mono, fill=COLORS["accent"])
                x += pen.textlength(line.entry, font=mono)
        if screen.cursor == "terminal" and screen.cursor_on:
            pen.rectangle((x + _px(2), y, x + _px(4), y + line_h - _px(6)), fill=COLORS["text"])
        image.paste(area, box[:2])
        return image

    def compare(self, scene, step, shown):
        image, draw = self.canvas(scene["title"])
        for side, left in (("left", _px(60)), ("right", _px(660))):
            if side not in shown:
                continue
            part, current = scene[side], shown[-1] == side
            color = COLORS["ok"] if part.get("tone") == "ok" else COLORS["accent"]
            self.panel(draw, (left, _px(130), left + _px(560), _px(470)), color if current else None)
            draw.text((left + _px(28), _px(155)), part["head"], font=self.font("mono", _px(26)), fill=color)
            for k, text in enumerate(part["lines"]):
                tone = COLORS["text"] if current else COLORS["muted"]
                for line in self.rich_lines(draw, text, _px(27), _px(510))[:1]:
                    self.draw_rich_line(draw, left + _px(28), _px(220) + k * _px(50), line, _px(27), tone,
                                        code_color=COLORS["amber"] if current else COLORS["muted"])
        if "footer" in shown:
            self.panel(draw, (_px(60), _px(500), _px(1220), _px(580)), COLORS["amber"])
            size = _px(24)
            lines = self.rich_lines(draw, scene["footer"], size, _px(1100), kind="semibold")
            for k, line in enumerate(lines):
                x = (WIDTH - self.rich_width(draw, line, size, kind="semibold")) / 2
                y = _px(540) - (len(lines) - 1) * _px(16) + k * _px(32) - _px(16)
                self.draw_rich_line(draw, x, y, line, size, COLORS["amber"], code_color=COLORS["amber"], kind="semibold")
        return image


Frame = tuple[object, Callable[[], object], float]  # (key, draw, seconds): equal keys draw the same image


def render_steps(script: dict, step_seconds: dict[str, tuple[float, float]]
                 ) -> Iterator[tuple[str, str, list[Frame], bool, bool]]:
    """Yield ``(step_id, say, frames, fade_in, squeezed)`` for each step.

    ``step_seconds`` maps a step id to ``(speech, step_total)``. A still scene
    gives one frame per step; an ``ide`` scene gives one frame per change on
    screen, and fades in only on its first step.
    """

    painter = _Painter(script)
    for scene_number, scene in enumerate(script["scenes"], 1):
        if scene["type"] != "ide":
            for step_id, say, image in _still_steps(painter, scene_number, scene):
                yield step_id, say, [(step_id, lambda image=image: image, step_seconds[step_id][1])], True, False
            continue
        screen = initial_screen(scene)
        for step_number, step in enumerate(scene["steps"], 1):
            step_id = f"s{scene_number:02d}_p{step_number:02d}"
            speech, total = step_seconds[step_id]
            events, squeezed = step_events(scene, screen, step, speech, total)
            screen = replace(events[-1][1], cursor_on=True)
            frames = [(shot, lambda shot=shot: painter.ide(scene, shot), seconds)
                      for shot, seconds in quantize(events, total, FPS)]
            yield step_id, step["say"], frames, step_number == 1, squeezed


def render_frames(script: dict) -> Iterator[tuple[str, str, object]]:
    """Yield ``(step_id, say, image)`` with the final screen of each step (a storyboard)."""

    painter = _Painter(script)
    for scene_number, scene in enumerate(script["scenes"], 1):
        if scene["type"] != "ide":
            yield from _still_steps(painter, scene_number, scene)
            continue
        screen = initial_screen(scene)
        for step_number, step in enumerate(scene["steps"], 1):
            events, _ = step_events(scene, screen, step, 0.0, 0.0)
            screen = replace(events[-1][1], cursor_on=True)
            yield f"s{scene_number:02d}_p{step_number:02d}", step["say"], painter.ide(scene, screen)


def _still_steps(painter, scene_number: int, scene: dict) -> Iterator[tuple[str, str, object]]:
    """Steps of a still scene; it keeps what earlier steps revealed."""

    note_seen, shown = False, []
    for step_number, step in enumerate(scene["steps"], 1):
        kind = scene["type"]
        if kind == "title":
            image = painter.title(scene, step)
        elif kind in {"list", "questions"}:
            image = painter.listing(scene, step, numbered=kind == "questions")
        elif kind == "flow":
            note_seen = note_seen or bool(step.get("note"))
            image = painter.flow(scene, step, note_seen)
        elif kind == "code":
            image = painter.code(scene, step)
        else:
            shown.append(step["show"])
            image = painter.compare(scene, step, shown)
        yield f"s{scene_number:02d}_p{step_number:02d}", step["say"], image


# ---------------------------------------------------------------------------
# Assembly (optional dependency: ffmpeg)
# ---------------------------------------------------------------------------

def render_video(script: dict, audio_dir: Path, out: Path, frames_dir: Path) -> float:
    """Draw the frames, join them with the speech and add a subtitle track. Returns seconds."""

    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg was not found on PATH")
    from PIL import Image  # optional dependency: pillow

    frames_dir.mkdir(parents=True, exist_ok=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    entries: list[tuple[Path, float]] = []
    chunks: list[bytes] = []
    texts: list[str] = []
    seconds: list[float] = []
    step_seconds: dict[str, tuple[float, float]] = {}
    params = None
    for step_id, _, _, _ in iter_steps(script):
        with wave.open(str(audio_dir / f"{step_id}.wav")) as handle:
            params = params or handle.getparams()
            frames = handle.readframes(handle.getnframes())
            speech = handle.getnframes() / handle.getframerate()
        pause_frames = int(PAUSE_SECONDS * params.framerate)
        chunks.append(frames + b"\x00" * (pause_frames * params.sampwidth * params.nchannels))
        seconds.append(speech)
        step_seconds[step_id] = (speech, speech + pause_frames / params.framerate)

    previous = Image.new("RGB", (WIDTH, HEIGHT), COLORS["background"])
    for step_id, say, frames, fade_in, squeezed in render_steps(script, step_seconds):
        texts.append(say)
        if squeezed:
            print(f"WARNING: {step_id} has more than its narration can show; split the step", file=sys.stderr)
        saved: dict[object, tuple[Path, object]] = {}
        for k, (key, draw, duration) in enumerate(frames):
            if key not in saved:
                image = draw()
                path = frames_dir / f"{step_id}_f{len(saved):04d}.png"
                image.save(path)
                saved[key] = (path, image if k == 0 else None)
            path, image = saved[key]
            if k == 0 and fade_in:
                fades = min(TRANSITION_FRAMES, int(duration * FPS))
                for n in range(1, fades + 1):
                    blend = frames_dir / f"{step_id}_t{n:02d}.png"
                    Image.blend(previous, image, n / fades).save(blend)
                    entries.append((blend, 1 / FPS))
                duration -= fades / FPS
            entries.append((path, duration))
        last_path = saved[frames[-1][0]][0]
        with Image.open(last_path) as last:
            previous = last.convert("RGB")
    timeline = build_timeline(seconds, pause=PAUSE_SECONDS)
    total = timeline[-1][2]
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        audio = work / "speech.wav"
        with wave.open(str(audio), "wb") as handle:
            handle.setparams(params)
            handle.writeframes(b"".join(chunks))
        listing = work / "frames.txt"
        listing.write_text(concat_list(entries), encoding="utf-8")
        subtitles = out.with_suffix(".srt")
        subtitles.write_text(format_srt(texts, timeline), encoding="utf-8")
        plain = work / "plain.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(listing),
                        "-i", str(audio), "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "veryfast",
                        "-tune", "stillimage", "-pix_fmt", "yuv420p", "-r", str(FPS), "-crf", "18",
                        "-c:a", "aac", "-b:a", "128k", "-t", f"{total:.3f}", str(plain)], check=True)
        # Subtitles go in a separate pass: muxing them with the concat input stalled ffmpeg.
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(plain), "-i", str(subtitles),
                        "-map", "0", "-map", "1", "-c", "copy", "-c:s", "mov_text",
                        "-metadata:s:s:0", f"language={script.get('subtitle_language', 'por')}", str(out)], check=True)
    return total


def check_speech(script: dict, video: Path, model: str = "small", language: str = "pt") -> tuple[float, list[tuple[str, str]]]:
    """Transcribe the video locally and compare it with the script text."""

    from faster_whisper import WhisperModel  # optional dependency: faster-whisper

    segments, _ = WhisperModel(model, device="cpu", compute_type="int8").transcribe(
        str(video), language=language, beam_size=5, vad_filter=True)
    heard = " ".join(segment.text.strip() for segment in segments)
    reference = " ".join(say for _, say, _, _ in iter_steps(script))
    return speech_match(reference, heard)


# ---------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------

def _load(path: Path) -> dict:
    script = json.loads(path.read_text(encoding="utf-8"))
    errors = validate_video_script(script)
    if errors:
        raise SystemExit("VIDEO SCRIPT: FAIL\n" + "\n".join(f"- {e}" for e in errors))
    return script


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render a local video lesson from a scene script.")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("validate").add_argument("script", type=Path)
    speak = commands.add_parser("speak")
    speak.add_argument("script", type=Path)
    speak.add_argument("--out", type=Path, required=True)
    speak.add_argument("--voice", choices=sorted(VOICES), default="piper")
    speak.add_argument("--model", type=Path)
    render = commands.add_parser("render")
    render.add_argument("script", type=Path)
    render.add_argument("--audio", type=Path, required=True)
    render.add_argument("--out", type=Path, required=True)
    render.add_argument("--frames", type=Path, required=True)
    check = commands.add_parser("check")
    check.add_argument("script", type=Path)
    check.add_argument("video", type=Path)
    check.add_argument("--model", default="small")
    args = parser.parse_args(argv)

    script = _load(args.script)
    if args.command == "validate":
        print("VIDEO SCRIPT: PASS")
    elif args.command == "speak":
        paths = synthesize(script, args.out, voice=args.voice, model=args.model)
        print(f"SPEECH: {len(paths)} files")
    elif args.command == "render":
        total = render_video(script, args.audio, args.out, args.frames)
        print(f"VIDEO: {args.out} ({total:.1f} s)")
    else:
        ratio, differences = check_speech(script, args.video, model=args.model)
        print(f"SPEECH CHECK: {ratio:.1%} of the script words heard")
        for expected, heard in differences:
            print(f"  - expected {expected!r}, heard {heard!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
