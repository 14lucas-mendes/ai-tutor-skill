#!/usr/bin/env python3
"""Initialize a portable AI Tutor study directory."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
import uuid
from copy import deepcopy
from pathlib import Path


JSON_ASSETS = (
    "study-config.json",
    "state.json",
    "media-index.json",
    "cards.json",
    "sources.json",
    "learner-profile.json",
)
MARKDOWN_ASSETS = ("curriculum.md", "session-log.md", "flashcards.md")
REQUIRED_CONFIG = (
    "topic",
    "goal",
    "deadline",
    "weekly_hours",
    "preferred_times",
    "initial_level",
    "language",
    "accessibility",
    "source_policy",
)


def atomic_write(path: Path, content: str) -> None:
    """Replace a text file atomically on the same volume."""

    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"template {path.name} must contain a JSON object")
    return payload


def _validate_config(config: dict) -> None:
    if not isinstance(config, dict):
        raise ValueError("config must be an object")
    missing = [key for key in REQUIRED_CONFIG if key not in config]
    if missing:
        raise ValueError("missing setup fields: " + ", ".join(missing))
    if not isinstance(config["topic"], str) or not isinstance(config["goal"], str):
        raise ValueError("topic and goal must be strings")
    if not config["topic"].strip() or not config["goal"].strip():
        raise ValueError("topic and goal must not be empty")
    if (
        isinstance(config["weekly_hours"], bool)
        or not isinstance(config["weekly_hours"], (int, float))
        or config["weekly_hours"] <= 0
    ):
        raise ValueError("weekly_hours must be positive")
    spacing_policy = config.get("spacing_policy", {"mode": "fixed", "target_horizon_days": None})
    if not isinstance(spacing_policy, dict) or spacing_policy.get("mode") not in {"fixed", "adaptive"}:
        raise ValueError("spacing_policy.mode must be fixed or adaptive")
    horizon = spacing_policy.get("target_horizon_days")
    if horizon is not None and (isinstance(horizon, bool) or not isinstance(horizon, int) or horizon <= 0):
        raise ValueError("spacing_policy.target_horizon_days must be a positive integer or null")


def initialize_study(
    skill_root: Path,
    study_root: Path,
    config: dict,
    *,
    force: bool = False,
) -> list[Path]:
    """Create a v2 study from packaged assets and return created files."""

    skill_root = skill_root.resolve()
    study_root = study_root.resolve()
    _validate_config(config)
    if study_root.exists() and not study_root.is_dir():
        raise FileExistsError(f"study root is not a directory: {study_root}")
    metadata_root = study_root / ".ai-tutor"
    if metadata_root.exists():
        raise FileExistsError(f"study already exists: {study_root}")
    for name in MARKDOWN_ASSETS:
        destination = study_root / name
        if destination.exists() and not destination.is_file():
            raise FileExistsError(f"study projection is not a file: {destination}")
    for name in ("lessons", "media", "projects"):
        destination = study_root / name
        if destination.exists() and not destination.is_dir():
            raise FileExistsError(f"study directory is not a directory: {destination}")

    assets = skill_root / "assets" / "templates"
    study_id = f"study_{uuid.uuid4()}"
    created: list[Path] = []

    payloads: dict[str, dict] = {}
    for name in JSON_ASSETS:
        payload = _load_json(assets / name)
        payload["study_id"] = study_id
        payloads[name] = payload
    markdown_templates = {
        name: (assets / name).read_text(encoding="utf-8")
        for name in MARKDOWN_ASSETS
    }

    study_config = payloads["study-config.json"]
    for key in REQUIRED_CONFIG:
        study_config[key] = deepcopy(config[key])
    study_config["external_consents"] = deepcopy(config.get("external_consents", {}))
    study_config["spacing_policy"] = deepcopy(config.get(
        "spacing_policy",
        {"mode": "fixed", "target_horizon_days": None},
    ))

    for directory in (
        metadata_root,
        metadata_root / "migrations",
        study_root / "lessons",
        study_root / "media",
        study_root / "projects",
    ):
        directory.mkdir(parents=True, exist_ok=True)

    for name, payload in payloads.items():
        destination = metadata_root / name
        atomic_write(destination, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
        created.append(destination)

    for name in MARKDOWN_ASSETS:
        destination = study_root / name
        if destination.exists():
            if not destination.is_file():
                raise FileExistsError(f"study projection is not a file: {destination}")
            continue
        atomic_write(destination, markdown_templates[name])
        created.append(destination)

    return created


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study-root", required=True, type=Path)
    parser.add_argument("--config-json", required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    initialize_study(
        Path(__file__).resolve().parents[1],
        args.study_root,
        json.loads(args.config_json),
        force=args.force,
    )
    print(f"Initialized AI Tutor study at {args.study_root.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
