#!/usr/bin/env python3
"""Render human-readable projections from canonical AI Tutor JSON files."""

from __future__ import annotations

import json
from pathlib import Path

try:
    from scripts.init_study import atomic_write
except ModuleNotFoundError:  # direct execution/import from the scripts directory
    from init_study import atomic_write


def render_flashcards(payload: dict) -> str:
    if not isinstance(payload, dict) or not isinstance(payload.get("cards"), list):
        raise ValueError("cards.json cards must be a list")
    lines = [
        "# Flashcards",
        "",
        "<!-- Generated from .ai-tutor/cards.json. Edit the canonical JSON, then sync. -->",
        "",
    ]
    cards = payload.get("cards", [])
    if not cards:
        lines.append("Nenhum card canônico registrado.")
        lines.append("")
        return "\n".join(lines)
    for card in cards:
        if not isinstance(card, dict):
            raise ValueError("cards.json cards must contain objects")
        lines.extend([
            f"## {card.get('card_id', 'card_unknown')}",
            "",
            f"**Frente:** {card.get('front', '')}",
            "",
            f"**Verso:** {card.get('back', '')}",
            "",
            f"- Tópico: `{card.get('topic_id') or 'não vinculado'}`",
            f"- Lição: `{card.get('lesson_id') or 'não vinculada'}`",
            f"- Fontes: {', '.join(f'`{value}`' for value in card.get('source_ids', [])) or 'nenhuma'}",
            f"- Status: `{card.get('status', 'unknown')}`",
            f"- Próxima revisão: `{card.get('due_at') or 'não agendada'}`",
            f"- Intervalo: `{card.get('interval_days', 0)} dias`",
            "",
        ])
    return "\n".join(lines)


def render_session_log(state: dict) -> str:
    if not isinstance(state, dict) or not isinstance(state.get("sessions"), list):
        raise ValueError("state.json sessions must be a list")
    lines = [
        "# Registro de sessões",
        "",
        "<!-- Generated from .ai-tutor/state.json. Edit canonical state, then sync. -->",
        "",
    ]
    sessions = state.get("sessions", [])
    if not sessions:
        lines.append("Nenhuma sessão registrada.")
        lines.append("")
        return "\n".join(lines)
    for session in sessions:
        if not isinstance(session, dict):
            raise ValueError("state.json sessions must contain objects")
        lines.extend([
            f"## {session.get('session_id', 'session_unknown')}",
            "",
            f"- Status: `{session.get('status', 'unknown')}`",
            f"- Transições: `{' → '.join(session.get('transitions', []))}`",
            f"- Início: `{session.get('started_at') or 'não registrado'}`",
            f"- Fim: `{session.get('ended_at') or 'não registrado'}`",
            f"- Lições: {', '.join(f'`{value}`' for value in session.get('lesson_ids', [])) or 'nenhuma'}",
            f"- Checkpoint: {session.get('checkpoint') or 'nenhum'}",
            "",
        ])
    return "\n".join(lines)


def _load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} must contain an object")
    return payload


def sync_projections(study_root: Path) -> list[str]:
    """Synchronize Markdown projections from canonical JSON; return errors."""

    study_root = study_root.resolve()
    metadata = study_root / ".ai-tutor"
    try:
        cards = _load_json(metadata / "cards.json")
        state = _load_json(metadata / "state.json")
        flashcards_text = render_flashcards(cards)
        session_log_text = render_session_log(state)
        targets = {
            study_root / "flashcards.md": flashcards_text,
            study_root / "session-log.md": session_log_text,
        }
        previous: dict[Path, str] = {}
        missing: set[Path] = set()
        for target in targets:
            if target.is_file():
                previous[target] = target.read_text(encoding="utf-8")
            else:
                missing.add(target)
        try:
            for target, content in targets.items():
                atomic_write(target, content)
        except (OSError, TypeError, ValueError) as exc:
            rollback_errors: list[str] = []
            for target, content in previous.items():
                try:
                    atomic_write(target, content)
                except (OSError, TypeError, ValueError) as rollback_exc:
                    rollback_errors.append(f"rollback {target.name}: {rollback_exc}")
            for target in missing:
                try:
                    if target.exists():
                        target.unlink()
                except OSError as rollback_exc:
                    rollback_errors.append(f"rollback {target.name}: {rollback_exc}")
            if rollback_errors:
                return [str(exc), *rollback_errors]
            return [str(exc)]
    except (OSError, json.JSONDecodeError, TypeError, AttributeError, ValueError) as exc:
        return [str(exc)]
    return []


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("study_root", type=Path)
    args = parser.parse_args()
    errors = sync_projections(args.study_root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("PROJECTIONS: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
