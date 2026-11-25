"""Check the optional study course folder against its privacy and structure rules.

The course is a readable projection written by the tutor from completed lessons.
This checker does not write anything. It verifies what can be checked mechanically:

- every lesson page cites, in its first lines, at least one lesson ID of the study,
  and every lesson it cites there is ``completed``;
- every lesson page hides its answers in balanced ``<details>`` blocks;
- no file of the course contains a real identifier from the study state
  (evidence, session, weak point, diagnostic, observation, or retrieval IDs);
- relative Markdown links resolve.

Section names are not checked because they depend on the study language.
"""

from __future__ import annotations

import json
import re
from pathlib import Path, PurePosixPath, PureWindowsPath

INDEX_NAME = "README.md"
HEADER_LINES = 10
BACKTICKED = re.compile(r"`([^`\n]+)`")
MARKDOWN_LINK = re.compile(r"\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
PRIVATE_ID_FIELDS = (
    ("evidences", "evidence_id"),
    ("sessions", "session_id"),
    ("weak_points", "weak_point_id"),
    ("diagnostics", "diagnostic_id"),
    ("retrieval_attempts", "retrieval_id"),
)


def course_path_error(value: object) -> str | None:
    """Return why a ``course_policy.path`` value is invalid, or None when valid."""
    if not isinstance(value, str) or not value.strip():
        return "must be a non-empty relative path"
    if PurePosixPath(value).is_absolute() or PureWindowsPath(value).is_absolute() or PureWindowsPath(value).drive:
        return "must be relative to the study root"
    parts = value.replace("\\", "/").split("/")
    if ".." in parts:
        return "must stay inside the study root"
    if parts[0] == ".ai-tutor":
        return "must not point inside .ai-tutor"
    return None


def _private_ids(state: dict) -> set[str]:
    ids: set[str] = set()
    for collection, field in PRIVATE_ID_FIELDS:
        for item in state.get(collection) or []:
            if isinstance(item, dict) and isinstance(item.get(field), str) and item[field]:
                ids.add(item[field])
    for diagnostic in state.get("diagnostics") or []:
        if not isinstance(diagnostic, dict):
            continue
        for observation in diagnostic.get("observations") or []:
            if isinstance(observation, dict) and isinstance(observation.get("observation_id"), str):
                ids.add(observation["observation_id"])
    return ids


def _lesson_statuses(state: dict) -> dict[str, str]:
    return {
        lesson["lesson_id"]: lesson.get("status")
        for lesson in state.get("lessons") or []
        if isinstance(lesson, dict) and isinstance(lesson.get("lesson_id"), str)
    }


def _check_links(path: Path, text: str, course_root: Path, errors: list[str]) -> None:
    for target in MARKDOWN_LINK.findall(text):
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        relative = target.split("#", 1)[0]
        if not relative:
            continue
        if not (path.parent / relative).exists():
            errors.append(f"{path.relative_to(course_root).as_posix()}: broken link: {target}")


def check_course(study_root: Path) -> tuple[list[str], str | None]:
    """Return (errors, notice). A notice without errors means there is nothing to check."""
    metadata = study_root / ".ai-tutor"
    try:
        config = json.loads((metadata / "study-config.json").read_text(encoding="utf-8"))
        state = json.loads((metadata / "state.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return [f"cannot read study files: {exc}"], None

    policy = config.get("course_policy")
    if policy is None:
        return [], "no course_policy in study-config.json: this study has no course"
    if not isinstance(policy, dict):
        return ["course_policy must be an object"], None
    problem = course_path_error(policy.get("path"))
    if problem:
        return [f"course_policy.path {problem}"], None

    course_root = study_root / policy["path"]
    if not course_root.is_dir():
        return [f"course folder not found: {policy['path']}"], None

    statuses = _lesson_statuses(state)
    private_ids = _private_ids(state)
    errors: list[str] = []
    pages = sorted(course_root.rglob("*.md"))
    for path in pages:
        text = path.read_text(encoding="utf-8")
        name = path.relative_to(course_root).as_posix()
        leaked = sorted(identifier for identifier in private_ids if identifier in text)
        for identifier in leaked:
            errors.append(f"{name}: contains a private study ID: {identifier}")
        _check_links(path, text, course_root, errors)
        if path.name == INDEX_NAME:
            continue
        header = "\n".join(text.splitlines()[:HEADER_LINES])
        cited = [token for token in BACKTICKED.findall(header) if token in statuses]
        if not cited:
            errors.append(f"{name}: no source lesson ID in the first {HEADER_LINES} lines")
        for lesson_id in dict.fromkeys(cited):
            if statuses[lesson_id] != "completed":
                errors.append(f"{name}: source lesson is not completed: {lesson_id} ({statuses[lesson_id]})")
        opened = len(re.findall(r"<details\b", text))
        closed = text.count("</details>")
        if opened == 0:
            errors.append(f"{name}: no <details> block for hidden answers")
        elif opened != closed:
            errors.append(f"{name}: unbalanced <details> blocks ({opened} opened, {closed} closed)")
    if not any(path.name != INDEX_NAME for path in pages):
        return errors, "the course has no lesson pages yet"
    return errors, None


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("study_root", type=Path)
    args = parser.parse_args()
    errors, notice = check_course(args.study_root.resolve())
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        print("COURSE CHECK: FAIL")
        return 1
    if notice:
        print(f"NOTICE: {notice}")
    print("COURSE CHECK: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
