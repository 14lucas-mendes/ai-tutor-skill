"""Deterministic fixed and opt-in adaptive card scheduling."""

from __future__ import annotations

import copy
from datetime import datetime, timedelta


FIXED_INTERVALS = (1, 3, 7, 16, 35, 60)
MODES = {"fixed", "adaptive"}
RESULTS = {"correct", "partial", "incorrect", "failed"}
DIFFICULTY_FACTORS = {"hard": 1.25, "medium": 1.5, "easy": 2.0}


def _validate_policy(policy: dict) -> tuple[str, int | None]:
    if not isinstance(policy, dict) or policy.get("mode") not in MODES:
        raise ValueError("spacing policy mode must be fixed or adaptive")
    horizon = policy.get("target_horizon_days")
    if horizon is not None and (isinstance(horizon, bool) or not isinstance(horizon, int) or horizon <= 0):
        raise ValueError("target_horizon_days must be a positive integer or null")
    return policy["mode"], horizon


def _validate_confidence(confidence: int | None) -> None:
    if confidence is not None and (isinstance(confidence, bool) or not isinstance(confidence, int) or not 0 <= confidence <= 100):
        raise ValueError("confidence must be an integer from 0 to 100 or null")


def schedule_card(
    card: dict,
    *,
    policy: dict,
    result: str,
    confidence: int | None,
    reviewed_at: datetime,
) -> dict:
    """Return a scheduled card without mutating the input card."""

    mode, horizon = _validate_policy(policy)
    if result not in RESULTS:
        raise ValueError(f"invalid card result: {result}")
    _validate_confidence(confidence)
    if not isinstance(reviewed_at, datetime):
        raise ValueError("reviewed_at must be a datetime")

    updated = copy.deepcopy(card)
    current_step = card.get("spaced_repetition_step", 0)
    previous_interval = card.get("interval_days", 1)
    if isinstance(current_step, bool) or not isinstance(current_step, int) or current_step < 0:
        raise ValueError("spaced_repetition_step must be a non-negative integer")
    if isinstance(previous_interval, bool) or not isinstance(previous_interval, int) or previous_interval < 0:
        raise ValueError("interval_days must be a non-negative integer")

    if result in {"incorrect", "failed"}:
        step = 1
        interval = 1
    elif mode == "fixed":
        step = min(current_step + 1, len(FIXED_INTERVALS) - 1) if result == "correct" else current_step
        interval = FIXED_INTERVALS[step]
    elif result == "partial":
        step = current_step
        interval = max(1, int(previous_interval * 0.75))
    else:
        step = min(current_step + 1, len(FIXED_INTERVALS) - 1)
        factor = DIFFICULTY_FACTORS.get(card.get("difficulty"), 1.25)
        if confidence is not None and confidence < 60:
            factor = min(factor, 1.25)
        interval = max(1, round(max(previous_interval, 1) * factor))

    limit = horizon if horizon is not None else 60
    interval = min(interval, limit)
    due_at = reviewed_at + timedelta(days=interval)
    updated.update({
        "spaced_repetition_step": step,
        "interval_days": interval,
        "review_count": card.get("review_count", 0) + 1,
        "objective_correctness": True if result == "correct" else False if result in {"incorrect", "failed"} else None,
        "last_result": result,
        "confidence": confidence,
        "updated_at": reviewed_at.isoformat().replace("+00:00", "Z"),
        "due_at": due_at.isoformat().replace("+00:00", "Z"),
    })
    return updated
