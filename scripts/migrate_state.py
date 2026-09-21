#!/usr/bin/env python3
"""Migrate legacy studies and upgrade valid V2 state with current registries."""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path

try:
    from scripts.init_study import atomic_write
    from scripts.validate_study import validate_state, validate_study
except ModuleNotFoundError:  # direct execution: ``python scripts/migrate_state.py``
    from init_study import atomic_write
    from validate_study import validate_state, validate_study


LEGACY_FILES = ("progress.json", "curriculum.md", "session-log.md", "flashcards.md")


@dataclass(frozen=True)
class MigrationReport:
    changed: bool
    valid: bool
    warnings: tuple[str, ...]


def _stable_id(prefix: str, study_key: str, entity_key: str) -> str:
    value = uuid.uuid5(uuid.NAMESPACE_URL, f"ai-tutor:{study_key}:{prefix}:{entity_key}")
    return f"{prefix}_{value}"


def _convert(study_root: Path) -> tuple[dict, dict, dict, list[str]]:
    progress_path = study_root / "progress.json"
    if not progress_path.is_file():
        raise FileNotFoundError(f"legacy progress.json not found: {study_root}")
    legacy = json.loads(progress_path.read_text(encoding="utf-8-sig"))
    if not isinstance(legacy, dict):
        raise ValueError("legacy progress.json must contain a JSON object")
    study_key = str(study_root.resolve())
    study_id = _stable_id("study", study_key, legacy.get("tema", "study"))
    topic_ids: dict[str, str] = {}
    topics = []
    legacy_topics = legacy.get("topicos", {})
    if not isinstance(legacy_topics, dict):
        raise ValueError("legacy topicos must be an object")
    for key, topic in legacy_topics.items():
        if not isinstance(topic, dict):
            raise ValueError(f"legacy topic {key} must be an object")
        topic_id = _stable_id("topic", study_key, key)
        topic_ids[key] = topic_id
        mastery = topic.get("dominio", 0)
        status = "not_started" if mastery == 0 else "mastered" if mastery >= 80 else "in_progress"
        notes = topic.get("observacoes", "")
        topics.append({
            "topic_id": topic_id,
            "name": key.replace("_", " ").strip(),
            "mastery": mastery,
            "retention": "unknown",
            "status": status,
            "last_practice": topic.get("ultima_pratica"),
            "evidence_ids": [],
            "notes": notes,
        })

    weak_points = []
    warnings: list[str] = []
    legacy_weak_points = legacy.get("pontos_fracos", [])
    if not isinstance(legacy_weak_points, list):
        raise ValueError("legacy pontos_fracos must be a list")
    for index, text in enumerate(legacy_weak_points):
        weak_points.append({
            "weak_point_id": _stable_id("weak", study_key, f"{index}:{text}"),
            "topic_id": None,
            "category": "unclassified",
            "migration_pending_classification": True,
            "cause": str(text),
            "supporting_evidence_ids": [],
            "entered_at": legacy.get("ultima_atualizacao"),
            "exit_condition": "classify and collect two autonomous correct evidences in different sessions",
            "status": "active",
        })
        warnings.append(f"weak point requires topic/category classification: {text}")

    state = {
        "schema_version": 2,
        "study_id": study_id,
        "revision": 0,
        "updated_at": legacy.get("ultima_atualizacao"),
        "topics": topics,
        "evidences": [],
        "sessions": [],
        "lessons": [],
        "weak_points": weak_points,
        "projects": [],
        "next_focus": legacy.get("proximo_foco") or None,
        "diagnostics": [],
    }
    config = {
        "schema_version": 2,
        "study_id": study_id,
        "topic": legacy.get("tema", ""),
        "goal": legacy.get("objetivo_especifico", ""),
        "deadline": None,
        "weekly_hours": legacy.get("horas_semanal_disponivel", 0),
        "preferred_times": [],
        "initial_level": legacy.get("nivel_geral", ""),
        "language": "pt-BR",
        "accessibility": [],
        "source_policy": {"prefer_primary": True, "prefer_pt_br": True},
        "external_consents": {},
    }
    media = {"schema_version": 2, "study_id": study_id, "revision": 0, "artifacts": []}
    return config, state, media, warnings


def _backup_legacy(study_root: Path) -> None:
    destination = study_root / ".ai-tutor" / "migrations" / "v1-backup"
    destination.mkdir(parents=True, exist_ok=True)
    for name in LEGACY_FILES:
        source = study_root / name
        if source.is_file():
            shutil.copy2(source, destination / name)


def _candidate_errors(study_root: Path, payloads: dict[str, dict]) -> list[str]:
    """Validate a complete migrated study before touching the real directory."""

    with tempfile.TemporaryDirectory() as temporary:
        candidate = Path(temporary) / "study"
        candidate_metadata = candidate / ".ai-tutor"
        candidate_metadata.mkdir(parents=True)
        for name, payload in payloads.items():
            atomic_write(
                candidate_metadata / name,
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            )
        for name in ("curriculum.md", "session-log.md", "flashcards.md"):
            source = study_root / name
            if source.is_file():
                shutil.copy2(source, candidate / name)
        return validate_study(candidate)


def _upgrade_v2_support_files(
    study_root: Path,
    study_id: str,
    *,
    dry_run: bool = False,
) -> tuple[bool, list[str]]:
    """Add support registries to older valid v2 studies without touching state."""

    metadata = study_root / ".ai-tutor"
    pending: dict[str, dict] = {}
    warnings: list[str] = []
    migrations_dir = metadata / "migrations"
    if migrations_dir.exists() and not migrations_dir.is_dir():
        warnings.append(".ai-tutor/migrations must be a directory")

    state_path = metadata / "state.json"
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return False, [f"existing state.json is unreadable: {exc}"]
    if not isinstance(state, dict):
        return False, ["existing state.json must be an object"]
    if "diagnostics" not in state:
        state = dict(state)
        state["diagnostics"] = []
        pending["state.json"] = state
    for name, collection in (("cards.json", "cards"), ("sources.json", "sources")):
        path = metadata / name
        if not path.exists():
            pending[name] = {"schema_version": 2, "study_id": study_id, "revision": 0, collection: []}
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            warnings.append(f"existing {name} is unreadable: {exc}")
            continue
        if (
            not isinstance(payload, dict)
            or payload.get("schema_version") != 2
            or payload.get("study_id") != study_id
            or not isinstance(payload.get(collection), list)
        ):
            warnings.append(f"existing {name} does not satisfy the v2 support-file contract")
        elif "revision" not in payload:
            payload["revision"] = 0
            pending[name] = payload
        elif isinstance(payload.get("revision"), bool) or not isinstance(payload.get("revision"), int) or payload["revision"] < 0:
            warnings.append(f"existing {name} revision must be a non-negative integer")

    media_path = metadata / "media-index.json"
    if not media_path.exists():
        pending["media-index.json"] = {
            "schema_version": 2,
            "study_id": study_id,
            "revision": 0,
            "artifacts": [],
        }
    else:
        try:
            media = json.loads(media_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            warnings.append(f"existing media-index.json is unreadable: {exc}")
        else:
            if not isinstance(media, dict) or media.get("study_id") != study_id or not isinstance(media.get("artifacts"), list):
                warnings.append("existing media-index.json does not satisfy the v2 support-file contract")
            elif "revision" not in media:
                media["revision"] = 0
                pending["media-index.json"] = media
            elif isinstance(media.get("revision"), bool) or not isinstance(media.get("revision"), int) or media["revision"] < 0:
                warnings.append("existing media-index.json revision must be a non-negative integer")

    if warnings:
        return False, warnings

    candidate_payloads: dict[str, dict] = {}
    for name in ("study-config.json", "state.json", "media-index.json", "cards.json", "sources.json"):
        if name in pending:
            candidate_payloads[name] = pending[name]
        else:
            source = metadata / name
            if source.is_file():
                try:
                    candidate_payloads[name] = json.loads(source.read_text(encoding="utf-8"))
                except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                    return False, [f"existing {name} is unreadable: {exc}"]
    candidate_errors = _candidate_errors(study_root, candidate_payloads)
    if candidate_errors:
        return False, candidate_errors

    needs_migrations_dir = not migrations_dir.exists()
    if dry_run:
        return bool(pending) or needs_migrations_dir, []
    migrations_dir.mkdir(parents=True, exist_ok=True)
    for name, payload in pending.items():
        atomic_write(metadata / name, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    return bool(pending), []


def migrate(study_root: Path, dry_run: bool = False) -> MigrationReport:
    study_root = study_root.resolve()
    metadata_root = study_root / ".ai-tutor"
    if metadata_root.exists() and not metadata_root.is_dir():
        return MigrationReport(
            changed=False,
            valid=False,
            warnings=(".ai-tutor exists but is not a directory",),
        )
    state_path = metadata_root / "state.json"
    if state_path.exists():
        if not state_path.is_file():
            return MigrationReport(
                changed=False,
                valid=False,
                warnings=("existing .ai-tutor/state.json is not a file",),
            )
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            return MigrationReport(
                changed=False,
                valid=False,
                warnings=(f"existing v2 state is unreadable: {exc}",),
            )
        if not isinstance(state, dict) or state.get("schema_version") != 2:
            return MigrationReport(
                changed=False,
                valid=False,
                warnings=("existing .ai-tutor/state.json is not a supported v2 state",),
            )
        errors = validate_state(state)
        if errors:
            return MigrationReport(changed=False, valid=False, warnings=tuple(errors))
        changed, warnings = _upgrade_v2_support_files(
            study_root,
            state["study_id"],
            dry_run=dry_run,
        )
        return MigrationReport(changed=changed, valid=not warnings, warnings=tuple(warnings))

    try:
        config, state, media, warnings = _convert(study_root)
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError, AttributeError) as exc:
        return MigrationReport(changed=False, valid=False, warnings=(f"legacy state is unreadable: {exc}",))
    cards = {"schema_version": 2, "study_id": state["study_id"], "revision": 0, "cards": []}
    sources = {"schema_version": 2, "study_id": state["study_id"], "revision": 0, "sources": []}
    candidate_errors = _candidate_errors(
        study_root,
        {
            "study-config.json": config,
            "state.json": state,
            "media-index.json": media,
            "cards.json": cards,
            "sources.json": sources,
        },
    )
    if candidate_errors:
        return MigrationReport(changed=False, valid=False, warnings=tuple(warnings + candidate_errors))
    if dry_run:
        return MigrationReport(changed=True, valid=True, warnings=tuple(warnings))

    _backup_legacy(study_root)
    metadata = study_root / ".ai-tutor"
    for name, payload in (
        ("study-config.json", config),
        ("state.json", state),
        ("media-index.json", media),
        ("cards.json", cards),
        ("sources.json", sources),
    ):
        atomic_write(metadata / name, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    return MigrationReport(changed=True, valid=True, warnings=tuple(warnings))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study-root", required=True, type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    report = migrate(args.study_root, dry_run=args.dry_run)
    print(json.dumps({
        "changed": report.changed,
        "valid": report.valid,
        "warnings": list(report.warnings),
    }, ensure_ascii=False, indent=2))
    return 0 if report.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
