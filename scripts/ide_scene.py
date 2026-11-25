#!/usr/bin/env python3
"""The pure part of the ``ide`` scene of a video lesson: validation, screen state and pacing.

An ``ide`` scene shows an editor with one tab per file and a terminal below it.
Code is typed letter by letter in time with the narration, then it runs in the
terminal. This module uses only the standard library; ``video_lesson.py`` draws
the screens it describes.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

TERMINAL_KINDS = ("cmd", "out", "err", "in")
MAX_FILES = 4

# Pacing (spec 7.2): everything that moves in a step ends by 75% of its narration.
START_DELAY = 0.3
DEADLINE_SHARE = 0.75
REVEAL_GAP = 0.3
FLOOR_CPS = 8.0
CEIL_CPS = 60.0
BLINK_SECONDS = 0.5


@dataclass(frozen=True)
class TermLine:
    kind: str          # "cmd", "out" or "err"
    text: str          # for cmd, without the "$ " prompt
    entry: str = ""    # what the user typed on this line (from an "in")


@dataclass(frozen=True)
class IdeScreen:
    active: str                         # name of the file in the active tab
    chars: tuple[tuple[str, int], ...]  # (name, visible characters of its code), in the order of "files"
    highlight: tuple[int, ...]
    terminal: tuple[TermLine, ...]
    cursor: str                         # "editor" or "terminal"
    cursor_on: bool


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


# ---------------------------------------------------------------------------
# Screen state and pacing
# ---------------------------------------------------------------------------

def initial_screen(scene: dict) -> IdeScreen:
    names = [f["name"] for f in scene["files"]]
    return IdeScreen(names[0], tuple((name, 0) for name in names), (), (), "editor", True)


def _prefix_length(code: str, lines: int) -> int:
    """Characters of ``code`` up to the end of its first ``lines`` lines."""

    return len("\n".join(code_lines(code)[:lines]))


class _Timeline:
    """Builds the events of one step, starting from the screen at its first instant."""

    def __init__(self, screen: IdeScreen):
        self.screen = screen
        self.events: list[tuple[float, IdeScreen]] = [(0.0, screen)]

    def set(self, t: float, **changes) -> None:
        self.screen = replace(self.screen, **changes)
        if t <= self.events[-1][0]:
            self.events[-1] = (self.events[-1][0], self.screen)
        else:
            self.events.append((t, self.screen))

    def chars(self, name: str, count: int) -> tuple[tuple[str, int], ...]:
        return tuple((n, count if n == name else c) for n, c in self.screen.chars)


def _terminal_ops(entries: list[dict]) -> list[tuple[str, str]]:
    return [next(iter(entry.items())) for entry in entries]


def _apply_terminal(terminal: tuple[TermLine, ...], kind: str, text: str) -> tuple[TermLine, ...]:
    if kind == "in":
        last = terminal[-1]
        return terminal[:-1] + (replace(last, entry=text),)
    return terminal + (TermLine(kind, text),)


def step_events(scene: dict, before: IdeScreen, step: dict, speech: float, step_total: float
                ) -> tuple[list[tuple[float, IdeScreen]], bool]:
    """Timed screens of one step, first at 0.0, and whether the step was squeezed.

    A step is squeezed when its code had to appear line by line, or its
    terminal all at once, to end by the deadline.
    """

    codes = {f["name"]: f["code"] for f in scene["files"]}
    active = step.get("file", before.active)
    code = codes[active]
    start = dict(before.chars)[active]
    target = start
    if "show" in step:
        start = target = _prefix_length(code, step["show"])
    elif "type" in step:
        target = _prefix_length(code, step["type"])
    segment = code[start:target]
    ops = _terminal_ops(step.get("terminal", []))
    highlight = tuple(step.get("highlight", []))
    terminal = () if step.get("clear_terminal") else before.terminal

    timeline = _Timeline(replace(before, active=active, chars=tuple(
        (n, start if n == active else c) for n, c in before.chars), highlight=(), terminal=terminal,
        cursor="editor" if segment or not ops else before.cursor, cursor_on=True))

    typed = len(segment) + sum(len(text) for kind, text in ops if kind in ("cmd", "in"))
    reveals = sum(1 for kind, _ in ops if kind in ("out", "err"))
    deadline = DEADLINE_SHARE * speech
    window = deadline - START_DELAY
    squeezed = False

    def type_code(t0: float, speed: float) -> float:
        for k in range(1, len(segment) + 1):
            timeline.set(t0 + k / speed, chars=timeline.chars(active, start + k))
        return t0 + len(segment) / speed

    def code_by_lines(t0: float, span: float) -> float:
        first = len(code_lines(code[:start])) if start else 0
        last = len(code_lines(code[:target]))
        count = last - first
        for j in range(1, count + 1):
            timeline.set(t0 + j * span / count, chars=timeline.chars(active, _prefix_length(code, first + j)))
        return t0 + span

    def run_terminal(t0: float, speed: float) -> None:
        t = t0
        for kind, text in ops:
            if kind in ("out", "err"):
                t += REVEAL_GAP
                timeline.set(t, terminal=_apply_terminal(timeline.screen.terminal, kind, text), cursor="terminal")
                continue
            if kind == "cmd":
                timeline.set(t, terminal=timeline.screen.terminal + (TermLine("cmd", ""),), cursor="terminal")
            for k in range(1, len(text) + 1):
                timeline.set(t + k / speed, terminal=_apply_terminal_partial(timeline.screen.terminal, kind, text[:k]),
                             cursor="terminal")
            t += len(text) / speed

    def terminal_at_once(t: float) -> None:
        current = timeline.screen.terminal
        for kind, text in ops:
            current = _apply_terminal(current, kind, text)
        timeline.set(t, terminal=current, cursor="terminal")

    if not segment and not ops:
        timeline.set(0.0, highlight=highlight)
    elif window <= 0:
        timeline.set(0.0, chars=timeline.chars(active, target), highlight=highlight)
        terminal_at_once(0.0)
        squeezed = True
    else:
        budget = window - REVEAL_GAP * reveals
        speed = typed / budget if typed and budget > 0 else (float("inf") if typed else 0.0)
        if typed == 0:
            timeline.set(0.0, highlight=highlight)
            if budget >= 0:
                run_terminal(START_DELAY, CEIL_CPS)
            else:
                terminal_at_once(deadline)
                squeezed = True
        elif speed <= CEIL_CPS:
            speed = max(speed, FLOOR_CPS)
            end = type_code(START_DELAY, speed)
            timeline.set(end if segment else 0.0, highlight=highlight)
            run_terminal(end, speed)
        else:
            squeezed = True
            term_typed = typed - len(segment)
            term_time = term_typed / CEIL_CPS + REVEAL_GAP * reveals
            code_time = window - term_time
            if code_time > 0:
                end = code_by_lines(START_DELAY, code_time) if segment else START_DELAY
                timeline.set(end if segment else 0.0, highlight=highlight)
                run_terminal(end if segment else START_DELAY, CEIL_CPS)
            else:
                end = code_by_lines(START_DELAY, window) if segment else 0.0
                timeline.set(end, highlight=highlight)
                if ops:
                    terminal_at_once(deadline)

    last = timeline.events[-1][0]
    on = True
    t = last + BLINK_SECONDS
    while t < step_total - 1e-9:
        on = not on
        timeline.set(t, cursor_on=on)
        t += BLINK_SECONDS
    return timeline.events, squeezed


def _apply_terminal_partial(terminal: tuple[TermLine, ...], kind: str, text: str) -> tuple[TermLine, ...]:
    """The terminal while ``text`` is being typed by a ``cmd`` (last line) or an ``in`` (entry of the last line)."""

    last = terminal[-1]
    if kind == "cmd":
        return terminal[:-1] + (replace(last, text=text),)
    return terminal[:-1] + (replace(last, entry=text),)
