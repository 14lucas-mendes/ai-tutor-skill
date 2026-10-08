#!/usr/bin/env python3
"""Pure helpers and validation for the per-study learner profile."""

from __future__ import annotations

import copy
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Callable

try:
    from scripts.state_io import atomic_update_json
except ModuleNotFoundError:  # direct execution from the scripts directory
    from state_io import atomic_update_json


PREFERENCE_STATUSES = {"active", "inactive"}
OBSERVATION_TYPES = {
    "autonomous_attempt",
    "help_usage",
    "confidence_report",
    "difficulty_report",
    "strategy_outcome",
}
INFERENCE_STATUSES = {"hypothesis", "challenged"}
CONFIDENCE_LEVELS = {"low", "medium", "high"}
SUMMARY_LEVELS = {"unknown", "low", "medium", "high"}
CONFIDENCE_PATTERNS = {"unknown", "underconfident", "calibrated", "overconfident", "mixed"}
SCOPE_TYPES = {"topic", "study"}


def _is_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_timestamp(value: object, *, allow_none: bool = False) -> bool:
    if value is None:
        return allow_none
    if not _is_string(value):
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try:
            date.fromisoformat(value)
        except ValueError:
            return False
    return True


def empty_profile(study_id: str) -> dict:
    """Return the minimal unknown profile for a study."""

    return {
        "schema_version": 2,
        "study_id": study_id,
        "revision": 0,
        "updated_at": None,
        "declared_preferences": [],
        "observations": [],
        "inferences": [],
        "summary": {
            "autonomy": "unknown",
            "help_dependency": "unknown",
            "confidence_pattern": "unknown",
        },
    }


def validate_profile(profile: object, *, state_indexes: dict[str, set[str]] | None = None) -> list[str]:
    """Return deterministic structural and provenance errors for a profile."""

    if not isinstance(profile, dict):
        return ["learner-profile.json must be an object"]
    errors: list[str] = []
    if profile.get("schema_version") != 2:
        errors.append("learner profile schema_version must be 2")
    if not _is_string(profile.get("study_id")) or not profile["study_id"].startswith("study_"):
        errors.append("learner profile study_id must start with study_")
    revision = profile.get("revision")
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 0:
        errors.append("learner profile revision must be a non-negative integer")
    if not _is_timestamp(profile.get("updated_at"), allow_none=True):
        errors.append("learner profile updated_at must be an ISO date/time or null")

    preferences = profile.get("declared_preferences")
    observations = profile.get("observations")
    inferences = profile.get("inferences")
    summary = profile.get("summary")
    for name, value in (("declared_preferences", preferences), ("observations", observations), ("inferences", inferences)):
        if not isinstance(value, list):
            errors.append(f"learner profile {name} must be a list")
    if not isinstance(summary, dict):
        errors.append("learner profile summary must be an object")
    else:
        for field in ("autonomy", "help_dependency"):
            if summary.get(field) not in SUMMARY_LEVELS:
                errors.append(f"invalid learner profile summary {field}")
        if summary.get("confidence_pattern") not in CONFIDENCE_PATTERNS:
            errors.append("invalid learner profile summary confidence_pattern")

    preference_ids: set[str] = set()
    if isinstance(preferences, list):
        for position, preference in enumerate(preferences):
            if not isinstance(preference, dict):
                errors.append(f"declared_preferences[{position}] must be an object")
                continue
            preference_id = preference.get("preference_id")
            if not _is_string(preference_id) or not preference_id.startswith("preference_"):
                errors.append(f"preference_id must start with preference_: {preference_id}")
            elif preference_id in preference_ids:
                errors.append(f"duplicate preference id: {preference_id}")
            else:
                preference_ids.add(preference_id)
            if not _is_string(preference.get("dimension")):
                errors.append(f"preference dimension must be a non-empty string: {preference_id}")
            if "value" not in preference or preference.get("value") is None:
                errors.append(f"preference value is required: {preference_id}")
            if preference.get("source") != "learner":
                errors.append(f"preference source must be learner: {preference_id}")
            if preference.get("status") not in PREFERENCE_STATUSES:
                errors.append(f"invalid preference status: {preference_id}")
            if not _is_timestamp(preference.get("recorded_at")):
                errors.append(f"preference recorded_at must be an ISO date/time: {preference_id}")
            supersedes = preference.get("supersedes_id")
            if supersedes is not None and supersedes not in preference_ids:
                errors.append(f"preference supersedes unknown id: {supersedes}")

    observation_by_id: dict[str, dict] = {}
    if isinstance(observations, list):
        for position, observation in enumerate(observations):
            if not isinstance(observation, dict):
                errors.append(f"observations[{position}] must be an object")
                continue
            observation_id = observation.get("observation_id")
            if not _is_string(observation_id) or not observation_id.startswith("profile_observation_"):
                errors.append(f"observation_id must start with profile_observation_: {observation_id}")
            elif observation_id in observation_by_id:
                errors.append(f"duplicate profile observation id: {observation_id}")
            else:
                observation_by_id[observation_id] = observation
            if not _is_string(observation.get("session_id")):
                errors.append(f"observation session_id is required: {observation_id}")
            if observation.get("topic_id") is not None and not _is_string(observation.get("topic_id")):
                errors.append(f"observation topic_id must be a string or null: {observation_id}")
            if observation.get("type") not in OBSERVATION_TYPES:
                errors.append(f"invalid observation type: {observation_id}")
            if not isinstance(observation.get("value"), dict):
                errors.append(f"observation value must be an object: {observation_id}")
            if not _is_timestamp(observation.get("recorded_at")):
                errors.append(f"observation recorded_at must be an ISO date/time: {observation_id}")
            if state_indexes:
                session_ids = state_indexes.get("sessions", set())
                topic_ids = state_indexes.get("topics", set())
                if observation.get("session_id") not in session_ids:
                    errors.append(f"observation references unknown session: {observation.get('session_id')}")
                if observation.get("topic_id") is not None and observation.get("topic_id") not in topic_ids:
                    errors.append(f"observation references unknown topic: {observation.get('topic_id')}")

    inference_ids: set[str] = set()
    if isinstance(inferences, list):
        for position, inference in enumerate(inferences):
            if not isinstance(inference, dict):
                errors.append(f"inferences[{position}] must be an object")
                continue
            inference_id = inference.get("inference_id")
            if not _is_string(inference_id) or not inference_id.startswith("inference_"):
                errors.append(f"inference_id must start with inference_: {inference_id}")
            elif inference_id in inference_ids:
                errors.append(f"duplicate inference id: {inference_id}")
            else:
                inference_ids.add(inference_id)
            if not _is_string(inference.get("signal")):
                errors.append(f"inference signal is required: {inference_id}")
            if inference.get("status") not in INFERENCE_STATUSES:
                errors.append(f"invalid inference status: {inference_id}")
            confidence = inference.get("confidence")
            if confidence not in CONFIDENCE_LEVELS:
                errors.append(f"invalid inference confidence: {inference_id}")
            refs = inference.get("observation_ids")
            if not isinstance(refs, list) or not refs or not all(isinstance(item, str) for item in refs):
                errors.append(f"inference observation_ids must be a non-empty list of strings: {inference_id}")
                refs = []
            referenced = [observation_by_id[item] for item in refs if item in observation_by_id]
            if len(referenced) != len(refs):
                errors.append(f"inference references unknown observation: {inference_id}")
            minimum = {"low": 2, "medium": 3, "high": 5}.get(confidence, 0)
            if len(refs) < minimum:
                errors.append(f"inference confidence {confidence} requires at least {minimum} observations: {inference_id}")
            if confidence == "high" and len({item.get("session_id") for item in referenced}) < 2:
                errors.append(f"high confidence inference requires two sessions: {inference_id}")
            scope = inference.get("scope")
            if not isinstance(scope, dict) or scope.get("type") not in SCOPE_TYPES:
                errors.append(f"invalid inference scope: {inference_id}")
            elif scope.get("type") == "topic":
                if not _is_string(scope.get("topic_id")):
                    errors.append(f"topic inference scope requires topic_id: {inference_id}")
                if any(item.get("topic_id") != scope.get("topic_id") for item in referenced):
                    errors.append(f"topic inference references observations outside scope: {inference_id}")
            elif scope.get("type") == "study" and len({item.get("topic_id") for item in referenced if item.get("topic_id")}) < 2:
                errors.append(f"study inference requires observations from two topics: {inference_id}")
            for field in ("first_observed_at", "updated_at"):
                if not _is_timestamp(inference.get(field)):
                    errors.append(f"inference {field} must be an ISO date/time: {inference_id}")
            if inference.get("learner_feedback") is not None and not _is_string(inference.get("learner_feedback")):
                errors.append(f"inference learner_feedback must be a string or null: {inference_id}")
    return sorted(set(errors))


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4()}"


def record_observation(
    profile: dict,
    *,
    session_id: str,
    topic_id: str | None,
    observation_type: str,
    value: dict,
    recorded_at: str,
) -> dict:
    """Append one objective observation and return a new profile."""

    if not _is_string(session_id) or observation_type not in OBSERVATION_TYPES or not isinstance(value, dict):
        raise ValueError("session_id, observation_type, and object value are required")
    updated = copy.deepcopy(profile)
    updated.setdefault("observations", []).append({
        "observation_id": _new_id("profile_observation"),
        "session_id": session_id,
        "topic_id": topic_id,
        "type": observation_type,
        "value": copy.deepcopy(value),
        "recorded_at": recorded_at,
    })
    refresh_summary(updated)
    errors = validate_profile(updated)
    if errors:
        raise ValueError("invalid observation: " + "; ".join(errors))
    return updated


def refresh_summary(profile: dict) -> dict:
    """Update conservative summaries from repeated observations only."""

    observations = profile.get("observations", [])
    summary = profile.setdefault("summary", {})
    attempts = [item for item in observations if item.get("type") == "autonomous_attempt"]
    successful_attempts = [
        item for item in attempts
        if item.get("value", {}).get("result") in {"correct", "autonomous_success"}
    ]
    if len(successful_attempts) >= 5 and len({item.get("session_id") for item in successful_attempts}) >= 2:
        summary["autonomy"] = "high"
    elif len(successful_attempts) >= 2:
        summary["autonomy"] = "medium"
    elif successful_attempts:
        summary["autonomy"] = "low"

    help_events = [item for item in observations if item.get("type") == "help_usage"]
    help_levels = [item.get("value", {}).get("help_level") for item in help_events]
    help_levels = [value for value in help_levels if isinstance(value, int) and 1 <= value <= 5]
    if len(help_levels) >= 2:
        average = sum(help_levels) / len(help_levels)
        summary["help_dependency"] = "high" if average >= 4 else "medium" if average >= 2 else "low"

    patterns = [
        item.get("value", {}).get("pattern")
        for item in observations
        if item.get("type") == "confidence_report"
    ]
    patterns = [value for value in patterns if value in {"underconfident", "calibrated", "overconfident"}]
    if len(patterns) >= 2:
        summary["confidence_pattern"] = patterns[0] if len(set(patterns)) == 1 else "mixed"
    return profile


def set_preference(profile: dict, dimension: str, value: object, recorded_at: str) -> dict:
    """Deactivate the current value for a dimension and append the learner's correction."""

    if not _is_string(dimension) or value is None or not _is_timestamp(recorded_at):
        raise ValueError("dimension, value, and recorded_at are required")
    updated = copy.deepcopy(profile)
    preferences = updated.setdefault("declared_preferences", [])
    supersedes_id = None
    for preference in reversed(preferences):
        if preference.get("dimension") == dimension and preference.get("status") == "active":
            preference["status"] = "inactive"
            supersedes_id = preference.get("preference_id")
            break
    preferences.append({
        "preference_id": _new_id("preference"),
        "dimension": dimension,
        "value": copy.deepcopy(value),
        "source": "learner",
        "recorded_at": recorded_at,
        "status": "active",
        "supersedes_id": supersedes_id,
    })
    errors = validate_profile(updated)
    if errors:
        raise ValueError("invalid preference: " + "; ".join(errors))
    return updated


def add_inference(profile: dict, inference: dict) -> dict:
    """Append a provenance-backed hypothesis after validating its minimum signal."""

    updated = copy.deepcopy(profile)
    updated.setdefault("inferences", []).append(copy.deepcopy(inference))
    errors = validate_profile(updated)
    if errors:
        raise ValueError("invalid inference: " + "; ".join(errors))
    return updated


def challenge_inference(profile: dict, inference_id: str, feedback: str, updated_at: str) -> dict:
    """Record learner disagreement without deleting the factual observations."""

    if not _is_string(feedback) or not _is_timestamp(updated_at):
        raise ValueError("feedback and updated_at are required")
    updated = copy.deepcopy(profile)
    for inference in updated.get("inferences", []):
        if inference.get("inference_id") == inference_id:
            inference["status"] = "challenged"
            inference["learner_feedback"] = feedback
            inference["updated_at"] = updated_at
            errors = validate_profile(updated)
            if errors:
                raise ValueError("invalid challenged inference: " + "; ".join(errors))
            return updated
    raise KeyError(f"unknown inference: {inference_id}")


def update_profile_file(
    path: Path,
    updater: Callable[[dict], dict],
    *,
    expected_revision: int | None = None,
) -> dict:
    """Apply a validated profile update through the shared atomic CAS helper."""

    def apply(payload: dict) -> dict:
        updated = updater(copy.deepcopy(payload))
        errors = validate_profile(updated)
        if errors:
            raise ValueError("invalid learner profile: " + "; ".join(errors))
        return updated

    return atomic_update_json(path, apply, expected_revision=expected_revision)
