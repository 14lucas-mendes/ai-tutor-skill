"""Pure helpers for recording learner-owned retrieval attempts."""

from __future__ import annotations

import copy
import uuid
from datetime import date, datetime


RETRIEVAL_OUTCOMES = {"correct", "partial", "incorrect", "not_attempted"}


def _valid_timestamp(value: str) -> bool:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try:
            date.fromisoformat(value)
        except ValueError:
            return False
    return True


def needs_retrieval(
    topic: dict,
    *,
    has_due_card: bool = False,
    has_due_topic: bool = False,
    has_active_weak_point: bool = False,
) -> bool:
    """Return whether a short retrieval attempt is pedagogically relevant."""

    return (
        topic.get("retention") == "low"
        or has_due_card
        or has_due_topic
        or has_active_weak_point
    )


def record_retrieval_attempt(
    state: dict,
    *,
    session_id: str,
    topic_id: str,
    prompt: str,
    outcome: str,
    support_level: int,
    recorded_at: str,
) -> dict:
    """Return a copy of state with one validated retrieval attempt appended."""

    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("retrieval prompt must be a non-empty string")
    if outcome not in RETRIEVAL_OUTCOMES:
        raise ValueError(f"invalid retrieval outcome: {outcome}")
    if isinstance(support_level, bool) or not isinstance(support_level, int) or not 0 <= support_level <= 5:
        raise ValueError("retrieval support_level must be an integer from 0 to 5")
    if not isinstance(recorded_at, str) or not _valid_timestamp(recorded_at):
        raise ValueError("retrieval recorded_at must be an ISO date/time")
    topics = state.get("topics", [])
    sessions = state.get("sessions", [])
    if not any(item.get("topic_id") == topic_id for item in topics if isinstance(item, dict)):
        raise ValueError(f"retrieval references unknown topic: {topic_id}")
    if not any(item.get("session_id") == session_id for item in sessions if isinstance(item, dict)):
        raise ValueError(f"retrieval references unknown session: {session_id}")

    updated = copy.deepcopy(state)
    updated.setdefault("retrieval_attempts", []).append({
        "retrieval_id": f"retrieval_{uuid.uuid4()}",
        "session_id": session_id,
        "topic_id": topic_id,
        "prompt": prompt.strip(),
        "outcome": outcome,
        "support_level": support_level,
        "recorded_at": recorded_at,
    })
    return updated
