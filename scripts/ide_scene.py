#!/usr/bin/env python3
"""The pure part of the ``ide`` scene of a video lesson: validation, screen state and pacing.

An ``ide`` scene shows an editor with one tab per file and a terminal below it.
Code is typed letter by letter in time with the narration, then it runs in the
terminal. This module uses only the standard library; ``video_lesson.py`` draws
the screens it describes.
"""

from __future__ import annotations

TERMINAL_KINDS = ("cmd", "out", "err", "in")
MAX_FILES = 4


def _is_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def code_lines(code: str) -> list[str]:
    return code.split("\n")


def validate_ide_scene(scene: dict, where: str, steps: list[dict], errors: list[str]) -> None:
    """Append every problem of an ``ide`` scene to ``errors``."""

    files = scene.get("files")
    if not isinstance(files, list) or not 1 <= len(files) <= MAX_FILES:
        errors.append(f"{where}: files must list 1 to {MAX_FILES} files")
        return
    if not all(isinstance(f, dict) and all(_is_text(f.get(k)) for k in ("name", "language", "code")) for f in files):
        errors.append(f"{where}: each file needs name, language and code")
        return
    names = [f["name"] for f in files]
    if len(set(names)) != len(names):
        errors.append(f"{where}: file names must be unique")
        return
    total = {f["name"]: len(code_lines(f["code"])) for f in files}
    shown = dict.fromkeys(names, 0)
    active, last_terminal = names[0], None

    for index, step in enumerate(steps, 1):
        at = f"{where} step {index}"
        if "file" in step:
            if step["file"] not in total:
                errors.append(f"{at}: file must name one of the scene files")
                continue
            active = step["file"]
        if "type" in step and "show" in step:
            errors.append(f"{at}: use type or show, not both")
        else:
            for key in ("type", "show"):
                if key not in step:
                    continue
                lines = step[key]
                if not isinstance(lines, int) or isinstance(lines, bool) or not 1 <= lines <= total[active]:
                    errors.append(f"{at}: {key} must be between 1 and {total[active]}")
                elif lines < shown[active]:
                    errors.append(f"{at}: {key} cannot hide lines already shown ({shown[active]})")
                else:
                    shown[active] = lines
        highlight = step.get("highlight", [])
        if not isinstance(highlight, list) or not all(
            isinstance(line, int) and 1 <= line <= shown[active] for line in highlight
        ):
            errors.append(f"{at}: highlight must list visible line numbers")
        clear = step.get("clear_terminal", False)
        if not isinstance(clear, bool):
            errors.append(f"{at}: clear_terminal must be true or false")
        elif clear:
            last_terminal = None
        terminal = step.get("terminal", [])
        if not isinstance(terminal, list) or not all(
            isinstance(line, dict) and len(line) == 1 and next(iter(line)) in TERMINAL_KINDS
            and _is_text(next(iter(line.values())))
            for line in terminal
        ):
            errors.append(f"{at}: terminal must be a list of lines with one of cmd, out, err, in")
            continue
        for line in terminal:
            kind = next(iter(line))
            if kind == "in" and last_terminal != "out":
                errors.append(f"{at}: in must follow an out line")
            last_terminal = kind
