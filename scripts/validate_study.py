#!/usr/bin/env python3
"""Validate AI Tutor v2 study state, diagnostic extension, and cross-file invariants."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from pathlib import Path

try:
    from scripts.create_learning_pack import validate_media_item
except ModuleNotFoundError:  # direct execution: ``python scripts/validate_study.py``
    from create_learning_pack import validate_media_item


MASTERY_LEVELS = {0, 20, 40, 60, 80, 100}
RETENTION_LEVELS = {"unknown", "low", "medium", "high"}
STATUS_BY_MASTERY = {
    0: "not_started",
    20: "in_progress",
    40: "in_progress",
    60: "in_progress",
    80: "mastered",
    100: "mastered",
}
SESSION_TRANSITIONS = {
    "in_progress": {"completed", "interrupted"},
    "interrupted": {"resumed"},
    "resumed": {"completed", "interrupted"},
    "completed": set(),
}
ID_FIELDS = {
    "topics": "topic_id",
    "evidences": "evidence_id",
    "sessions": "session_id",
    "lessons": "lesson_id",
    "weak_points": "weak_point_id",
    "projects": "project_id",
}
STATE_COLLECTIONS = tuple(ID_FIELDS)
LESSON_STATUSES = {"planned", "in_progress", "blocked", "completed", "archived"}
SESSION_STATUSES = set(SESSION_TRANSITIONS)
EVIDENCE_RESULTS = {"correct", "partial", "incorrect", "failed"}
CARD_STATUSES = {"new", "learning", "review", "suspended"}
CARD_RESULTS = {"correct", "partial", "incorrect", "failed"}
CARD_DIFFICULTIES = {"easy", "medium", "hard"}
WEAK_POINT_CATEGORIES = {"conceptual", "procedural", "application", "precision", "execution"}
WEAK_POINT_STATUSES = {"active", "resolved", "archived"}
DIAGNOSTIC_STATUSES = {"not_started", "in_progress", "interrupted", "completed"}
DIAGNOSTIC_ESTIMATES = {"not_observed", "unknown", "weak", "partial", "likely_known"}
DIAGNOSTIC_CONFIDENCES = {"low", "medium", "high"}
DIAGNOSTIC_DIRECTIONS = {"probe_up", "probe_down", "probe_across"}
EVIDENCE_REFERENCE_COLLECTIONS = {
    "lesson": "lessons",
    "session": "sessions",
    "project": "projects",
}
ID_PREFIXES = {
    "topic_id": "topic_",
    "evidence_id": "evidence_",
    "session_id": "session_",
    "lesson_id": "lesson_",
    "weak_point_id": "weak_",
    "project_id": "project_",
}
REQUIRED_STATE_FIELDS = {
    "schema_version",
    "study_id",
    "revision",
    "updated_at",
    *STATE_COLLECTIONS,
    "next_focus",
}
REQUIRED_CONFIG_FIELDS = {
    "schema_version",
    "study_id",
    "topic",
    "goal",
    "deadline",
    "weekly_hours",
    "preferred_times",
    "initial_level",
    "language",
    "accessibility",
    "source_policy",
    "external_consents",
}


def _is_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _known_id(value: object, values: set[str]) -> bool:
    return isinstance(value, str) and value in values


def _is_timestamp(value: object, *, allow_none: bool = False) -> bool:
    if value is None:
        return allow_none
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try:
            date.fromisoformat(value)
        except ValueError:
            return False
    return True


def _validate_state_shape(state: object) -> list[str]:
    if not isinstance(state, dict):
        return ["state must be an object"]
    errors: list[str] = []
    missing = sorted(REQUIRED_STATE_FIELDS - state.keys())
    errors.extend(f"state missing field: {field}" for field in missing)
    for collection in STATE_COLLECTIONS:
        if collection in state and not isinstance(state[collection], list):
            errors.append(f"{collection} must be a list")
    if state.get("schema_version") != 2:
        errors.append("schema_version must be 2")
    study_id = state.get("study_id")
    if not _is_string(study_id):
        errors.append("study_id is required")
    elif not study_id.startswith("study_"):
        errors.append("study_id must start with study_")
    revision = state.get("revision")
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 0:
        errors.append("revision must be a non-negative integer")
    if not _is_timestamp(state.get("updated_at"), allow_none=True):
        errors.append("updated_at must be an ISO date/time or null")
    return errors


def _validate_config(config: object) -> list[str]:
    if not isinstance(config, dict):
        return ["study-config.json must be an object"]
    errors: list[str] = []
    missing = sorted(REQUIRED_CONFIG_FIELDS - config.keys())
    errors.extend(f"study config missing field: {field}" for field in missing)
    if config.get("schema_version") != 2:
        errors.append("study config schema_version must be 2")
    study_id = config.get("study_id")
    if not _is_string(study_id) or not study_id.startswith("study_"):
        errors.append("study config study_id must start with study_")
    for field in ("topic", "goal", "initial_level", "language"):
        if not _is_string(config.get(field)):
            errors.append(f"study config {field} must be a non-empty string")
    deadline = config.get("deadline")
    if deadline is not None and not _is_string(deadline):
        errors.append("study config deadline must be a non-empty string or null")
    weekly_hours = config.get("weekly_hours")
    if isinstance(weekly_hours, bool) or not isinstance(weekly_hours, (int, float)) or weekly_hours <= 0:
        errors.append("study config weekly_hours must be a positive number")
    preferred_times = config.get("preferred_times")
    if not isinstance(preferred_times, list) or not all(_is_string(item) for item in preferred_times):
        errors.append("study config preferred_times must be a list of non-empty strings")
    accessibility = config.get("accessibility")
    if not isinstance(accessibility, (list, dict)):
        errors.append("study config accessibility must be a list or object")
    for field in ("source_policy", "external_consents"):
        if not isinstance(config.get(field), dict):
            errors.append(f"study config {field} must be an object")
    return errors


def _unique_ids(state: dict) -> tuple[dict[str, set[str]], list[str]]:
    indexes: dict[str, set[str]] = {}
    errors: list[str] = []
    globally_seen: set[str] = set()
    for collection, field in ID_FIELDS.items():
        values: set[str] = set()
        for position, item in enumerate(state.get(collection, [])):
            if not isinstance(item, dict):
                errors.append(f"{collection}[{position}]: item must be an object")
                continue
            value = item.get(field)
            if not isinstance(value, str) or not value:
                errors.append(f"{collection}[{position}]: missing {field}")
                continue
            prefix = ID_PREFIXES[field]
            if not value.startswith(prefix):
                errors.append(f"{collection}[{position}]: {field} must start with {prefix}")
            if value in values or value in globally_seen:
                errors.append(f"duplicate id: {value}")
            values.add(value)
            globally_seen.add(value)
        indexes[collection] = values
    return indexes, errors


def _validate_topics(state: dict, indexes: dict[str, set[str]]) -> list[str]:
    errors: list[str] = []
    for position, topic in enumerate(state.get("topics", [])):
        if not isinstance(topic, dict):
            continue
        required = {"topic_id", "name", "mastery", "retention", "status", "last_practice", "evidence_ids"}
        errors.extend(
            f"topics[{position}] missing field: {field}"
            for field in sorted(required - topic.keys())
        )
        if not _is_string(topic.get("name")):
            errors.append(f"topics[{position}] name must be a non-empty string")
        if (
            isinstance(topic.get("mastery"), bool)
            or not isinstance(topic.get("mastery"), int)
            or topic.get("mastery") not in MASTERY_LEVELS
        ):
            continue
        if not isinstance(topic.get("retention"), str) or topic.get("retention") not in RETENTION_LEVELS:
            errors.append(f"invalid retention for {topic.get('topic_id')}")
        if not _is_timestamp(topic.get("last_practice"), allow_none=True):
            errors.append(f"invalid last_practice for {topic.get('topic_id')}")
        evidence_ids = topic.get("evidence_ids")
        if not isinstance(evidence_ids, list) or not all(isinstance(item, str) for item in evidence_ids):
            errors.append(f"topic evidence_ids must be a list of strings: {topic.get('topic_id')}")
        diagnostic = topic.get("diagnostic")
        if diagnostic is not None:
            if not isinstance(diagnostic, dict):
                errors.append(f"topic diagnostic must be an object or null: {topic.get('topic_id')}")
            else:
                if diagnostic.get("estimate") not in DIAGNOSTIC_ESTIMATES:
                    errors.append(f"invalid topic diagnostic estimate: {topic.get('topic_id')}")
                if diagnostic.get("confidence") not in DIAGNOSTIC_CONFIDENCES:
                    errors.append(f"invalid topic diagnostic confidence: {topic.get('topic_id')}")
                if not _is_string(diagnostic.get("diagnostic_id")):
                    errors.append(f"topic diagnostic requires diagnostic_id: {topic.get('topic_id')}")
    return errors


def _validate_lessons(state: dict, indexes: dict[str, set[str]]) -> list[str]:
    errors: list[str] = []
    topics_by_id = {
        topic.get("topic_id"): topic
        for topic in state.get("topics", [])
        if isinstance(topic, dict) and isinstance(topic.get("topic_id"), str)
    }
    for position, lesson in enumerate(state.get("lessons", [])):
        if not isinstance(lesson, dict):
            continue
        required = {"lesson_id", "topic_id", "status", "session_ids"}
        errors.extend(
            f"lessons[{position}] missing field: {field}"
            for field in sorted(required - lesson.keys())
        )
        status = lesson.get("status")
        if not isinstance(status, str) or status not in LESSON_STATUSES:
            errors.append(f"invalid lesson status for {lesson.get('lesson_id')}: {status}")
        topic_id = lesson.get("topic_id")
        if not _known_id(topic_id, indexes["topics"]):
            errors.append(f"lesson references unknown topic: {topic_id}")
        session_ids = lesson.get("session_ids")
        if not isinstance(session_ids, list) or not all(isinstance(item, str) for item in session_ids):
            errors.append(f"lesson session_ids must be a list of strings: {lesson.get('lesson_id')}")
        if status == "completed":
            topic = topics_by_id.get(topic_id, {}) if isinstance(topic_id, str) else {}
            topic_mastery = topic.get("mastery")
            if (
                isinstance(topic_mastery, bool)
                or not isinstance(topic_mastery, int)
                or topic_mastery < 80
                or not topic.get("evidence_ids")
            ):
                errors.append(
                    f"completed lesson requires mastery 80 and evidence: {lesson.get('lesson_id')}"
                )
    return errors


def _validate_evidences(state: dict, indexes: dict[str, set[str]]) -> list[str]:
    errors: list[str] = []
    evidence_by_id = {
        item.get("evidence_id"): item
        for item in state.get("evidences", [])
        if isinstance(item, dict) and isinstance(item.get("evidence_id"), str)
    }
    for position, evidence in enumerate(state.get("evidences", [])):
        if not isinstance(evidence, dict):
            continue
        required = {
            "evidence_id", "topic_id", "session_id", "kind", "autonomous", "transfer",
            "context", "recorded_at", "reference", "result", "error",
        }
        errors.extend(
            f"evidences[{position}] missing field: {field}"
            for field in sorted(required - evidence.keys())
        )
        if not _known_id(evidence.get("topic_id"), indexes["topics"]):
            errors.append(f"evidence references unknown topic: {evidence.get('topic_id')}")
        if not _known_id(evidence.get("session_id"), indexes["sessions"]):
            errors.append(f"evidence references unknown session: {evidence.get('session_id')}")
        if not _is_string(evidence.get("kind")):
            errors.append(f"evidence kind must be a non-empty string: {evidence.get('evidence_id')}")
        if not isinstance(evidence.get("autonomous"), bool):
            errors.append(f"evidence autonomous must be boolean: {evidence.get('evidence_id')}")
        if not isinstance(evidence.get("transfer"), bool):
            errors.append(f"evidence transfer must be boolean: {evidence.get('evidence_id')}")
        if not _is_string(evidence.get("context")):
            errors.append(f"evidence context must be a non-empty string: {evidence.get('evidence_id')}")
        if not _is_timestamp(evidence.get("recorded_at")):
            errors.append(f"evidence recorded_at must be an ISO date/time: {evidence.get('evidence_id')}")
        reference = evidence.get("reference")
        if not isinstance(reference, dict) or not _is_string(reference.get("type")) or not _is_string(reference.get("id")):
            errors.append(f"evidence reference must contain type and id: {evidence.get('evidence_id')}")
        else:
            reference_type = reference.get("type")
            if reference_type == "media":
                errors.append(f"media cannot be evidence: {evidence.get('evidence_id')}")
            else:
                reference_collection = EVIDENCE_REFERENCE_COLLECTIONS.get(reference_type)
                if reference_collection is None:
                    errors.append(f"unsupported evidence reference type: {reference_type}")
                elif not _known_id(reference.get("id"), indexes[reference_collection]):
                    errors.append(
                        f"evidence reference points to unknown {reference.get('type')}: {reference.get('id')}"
                    )
        if not isinstance(evidence.get("result"), str) or evidence.get("result") not in EVIDENCE_RESULTS:
            errors.append(f"invalid evidence result: {evidence.get('evidence_id')}")
        if evidence.get("error") is not None and not isinstance(evidence.get("error"), str):
            errors.append(f"evidence error must be a string or null: {evidence.get('evidence_id')}")
        if "limit_or_self_correction" in evidence and not isinstance(evidence["limit_or_self_correction"], bool):
            errors.append(f"evidence limit_or_self_correction must be boolean: {evidence.get('evidence_id')}")

    attached: dict[str, list[str]] = {evidence_id: [] for evidence_id in evidence_by_id}
    for topic in state.get("topics", []):
        if not isinstance(topic, dict):
            continue
        evidence_ids = topic.get("evidence_ids", [])
        if not isinstance(evidence_ids, list):
            continue
        for evidence_id in evidence_ids:
            if isinstance(evidence_id, str) and evidence_id in attached:
                attached[evidence_id].append(topic.get("topic_id"))
    for evidence_id, topic_ids in attached.items():
        evidence_topic = evidence_by_id[evidence_id].get("topic_id")
        if not topic_ids:
            errors.append(f"evidence not referenced by topic: {evidence_id}")
        elif topic_ids != [evidence_topic]:
            errors.append(f"evidence topic attachment mismatch: {evidence_id}")
    return errors


def _validate_projects(state: dict, indexes: dict[str, set[str]]) -> list[str]:
    errors: list[str] = []
    for position, project in enumerate(state.get("projects", [])):
        if not isinstance(project, dict):
            continue
        required = {"project_id", "name", "status"}
        errors.extend(
            f"projects[{position}] missing field: {field}"
            for field in sorted(required - project.keys())
        )
        if not _is_string(project.get("name")):
            errors.append(f"project name must be a non-empty string: {project.get('project_id')}")
        if not _is_string(project.get("status")):
            errors.append(f"project status must be a non-empty string: {project.get('project_id')}")
        for field, collection in (("lesson_ids", "lessons"), ("evidence_ids", "evidences")):
            if field not in project:
                continue
            values = project[field]
            if not isinstance(values, list) or not all(isinstance(item, str) for item in values):
                errors.append(f"project {field} must be a list of strings: {project.get('project_id')}")
                continue
            errors.extend(
                f"project references unknown {collection[:-1]}: {value}"
                for value in values
                if not _known_id(value, indexes[collection])
            )
    return errors


def _validate_weak_points(state: dict, indexes: dict[str, set[str]]) -> list[str]:
    errors: list[str] = []
    required = {
        "weak_point_id", "topic_id", "category", "cause", "supporting_evidence_ids",
        "entered_at", "exit_condition", "status",
    }
    for position, weak_point in enumerate(state.get("weak_points", [])):
        if not isinstance(weak_point, dict):
            continue
        errors.extend(
            f"weak_points[{position}] missing field: {field}"
            for field in sorted(required - weak_point.keys())
        )
        weak_point_id = weak_point.get("weak_point_id")
        if not _is_string(weak_point_id) or not weak_point_id.startswith("weak_"):
            errors.append(f"weak_point_id must start with weak_: {weak_point_id}")
        topic_id = weak_point.get("topic_id")
        if topic_id is not None and not _known_id(topic_id, indexes["topics"]):
            errors.append(f"weak point references unknown topic: {topic_id}")
        category = weak_point.get("category")
        migration_pending = weak_point.get("migration_pending_classification")
        if migration_pending is not None and not isinstance(migration_pending, bool):
            errors.append(f"weak point migration_pending_classification must be boolean: {weak_point_id}")
        if not isinstance(category, str) or (category not in WEAK_POINT_CATEGORIES and not (
            category == "unclassified" and migration_pending is True
        )):
            errors.append(f"invalid weak point category: {weak_point_id}")
        if not _is_string(weak_point.get("cause")):
            errors.append(f"weak point cause must be a non-empty string: {weak_point_id}")
        supporting = weak_point.get("supporting_evidence_ids")
        if not isinstance(supporting, list) or not all(isinstance(item, str) for item in supporting):
            errors.append(f"weak point supporting_evidence_ids must be a list of strings: {weak_point_id}")
        else:
            errors.extend(
                f"weak point references unknown evidence: {value}"
                for value in supporting
                if not _known_id(value, indexes["evidences"])
            )
        if not _is_timestamp(weak_point.get("entered_at")):
            errors.append(f"weak point entered_at must be an ISO date/time: {weak_point_id}")
        if not _is_string(weak_point.get("exit_condition")):
            errors.append(f"weak point exit_condition must be a non-empty string: {weak_point_id}")
        if not isinstance(weak_point.get("status"), str) or weak_point.get("status") not in WEAK_POINT_STATUSES:
            errors.append(f"invalid weak point status: {weak_point_id}")
    return errors


def _validate_sessions(state: dict, indexes: dict[str, set[str]]) -> list[str]:
    errors: list[str] = []
    for position, session in enumerate(state.get("sessions", [])):
        if not isinstance(session, dict):
            continue
        required = {"session_id", "status", "transitions", "lesson_ids", "started_at", "ended_at", "resumable"}
        errors.extend(
            f"sessions[{position}] missing field: {field}"
            for field in sorted(required - session.keys())
        )
        status = session.get("status")
        if not isinstance(status, str) or status not in SESSION_STATUSES:
            errors.append(f"invalid session status: {session.get('session_id')}")
        transitions = session.get("transitions", [])
        if not isinstance(transitions, list) or not transitions:
            errors.append(f"session transitions must be a non-empty list: {session.get('session_id')}")
            transitions = []
        for transition in transitions:
            if not isinstance(transition, str):
                errors.append(f"session transitions must contain strings: {session.get('session_id')}")
        if transitions and transitions[0] != "in_progress":
            errors.append(f"session must start in_progress: {session.get('session_id')}")
        for before, after in zip(transitions, transitions[1:]):
            if not isinstance(before, str) or not isinstance(after, str):
                continue
            if after not in SESSION_TRANSITIONS.get(before, set()):
                errors.append(
                    f"invalid session transition {before} -> {after} in {session.get('session_id')}"
                )
        if transitions and session.get("status") != transitions[-1]:
            errors.append(f"session status does not match transitions: {session.get('session_id')}")
        if not _is_timestamp(session.get("started_at")):
            errors.append(f"session started_at must be an ISO date/time: {session.get('session_id')}")
        if not _is_timestamp(session.get("ended_at"), allow_none=True):
            errors.append(f"session ended_at must be an ISO date/time or null: {session.get('session_id')}")
        if session.get("status") == "completed" and not session.get("ended_at"):
            errors.append(f"completed session missing ended_at: {session.get('session_id')}")
        if not isinstance(session.get("resumable"), bool):
            errors.append(f"session resumable must be boolean: {session.get('session_id')}")
        elif session.get("status") == "completed" and session.get("resumable"):
            errors.append(f"completed session cannot be resumable: {session.get('session_id')}")
        lesson_ids = session.get("lesson_ids", [])
        if not isinstance(lesson_ids, list) or not all(isinstance(item, str) for item in lesson_ids):
            errors.append(f"session lesson_ids must be a list of strings: {session.get('session_id')}")
            lesson_ids = []
        for lesson_id in lesson_ids:
            if not _known_id(lesson_id, indexes["lessons"]):
                errors.append(f"session references unknown lesson: {lesson_id}")
    return errors


def _valid_evidences(topic: dict, evidence_by_id: dict[str, dict]) -> list[dict]:
    evidence_ids = topic.get("evidence_ids", [])
    if not isinstance(evidence_ids, list):
        return []
    return [
        evidence_by_id[evidence_id]
        for evidence_id in evidence_ids
        if isinstance(evidence_id, str) and evidence_id in evidence_by_id
        and evidence_by_id[evidence_id].get("autonomous") is True
        and evidence_by_id[evidence_id].get("result") == "correct"
    ]


def _validate_mastery(state: dict, indexes: dict[str, set[str]]) -> list[str]:
    errors: list[str] = []
    evidence_by_id = {
        item.get("evidence_id"): item
        for item in state.get("evidences", [])
        if isinstance(item, dict) and isinstance(item.get("evidence_id"), str)
    }

    for topic in state.get("topics", []):
        if not isinstance(topic, dict):
            continue
        mastery = topic.get("mastery")
        if (
            isinstance(mastery, bool)
            or not isinstance(mastery, int)
            or mastery not in MASTERY_LEVELS
        ):
            errors.append(f"invalid mastery for {topic.get('topic_id')}: {mastery}")
            continue
        if topic.get("status") != STATUS_BY_MASTERY[mastery]:
            errors.append(f"status does not match mastery for {topic.get('topic_id')}")
        if not isinstance(topic.get("retention"), str) or topic.get("retention") not in RETENTION_LEVELS:
            errors.append(f"invalid retention for {topic.get('topic_id')}")
        evidence_ids = topic.get("evidence_ids", [])
        if not isinstance(evidence_ids, list):
            evidence_ids = []
        unknown = [value for value in evidence_ids if not isinstance(value, str) or value not in evidence_by_id]
        for evidence_id in unknown:
            errors.append(f"topic references unknown evidence: {evidence_id}")

        valid = _valid_evidences(topic, evidence_by_id)
        kinds = {item.get("kind") for item in valid if isinstance(item.get("kind"), str)}
        if mastery >= 60 and not {"feynman", "application"}.issubset(kinds):
            errors.append(f"mastery 60 requires autonomous Feynman and application: {topic.get('topic_id')}")
        if mastery >= 80 and not any(
            item.get("kind") == "application" and item.get("transfer") is True
            for item in valid
        ):
            errors.append(f"mastery 80 requires transfer application: {topic.get('topic_id')}")
        if mastery >= 100:
            sessions = {item.get("session_id") for item in valid if isinstance(item.get("session_id"), str)}
            contexts = {item.get("context") for item in valid if isinstance(item.get("context"), str)}
            advanced = any(item.get("limit_or_self_correction") is True for item in valid)
            if len(sessions) < 2 or len(contexts) < 2 or not advanced:
                errors.append(
                    f"mastery 100 requires two sessions, two contexts, and limit/self-correction: {topic.get('topic_id')}"
                )
    return errors


def _validate_cross_references(state: dict, indexes: dict[str, set[str]]) -> list[str]:
    errors: list[str] = []
    for lesson in state.get("lessons", []):
        if not isinstance(lesson, dict):
            continue
        session_ids = lesson.get("session_ids", [])
        if not isinstance(session_ids, list):
            continue
        for session_id in session_ids:
            if not _known_id(session_id, indexes["sessions"]):
                errors.append(f"lesson references unknown session: {session_id}")
    lessons_by_id = {
        lesson.get("lesson_id"): lesson
        for lesson in state.get("lessons", [])
        if isinstance(lesson, dict) and isinstance(lesson.get("lesson_id"), str)
    }
    for session in state.get("sessions", []):
        if not isinstance(session, dict):
            continue
        session_id = session.get("session_id")
        lesson_ids = session.get("lesson_ids", [])
        if not isinstance(lesson_ids, list):
            continue
        for lesson_id in lesson_ids:
            if not _known_id(lesson_id, indexes["lessons"]):
                continue
            lesson = lessons_by_id.get(lesson_id)
            lesson_session_ids = lesson.get("session_ids", []) if lesson is not None else []
            if lesson is not None and isinstance(lesson_session_ids, list) and session_id not in lesson_session_ids:
                errors.append(f"session/lesson attachment mismatch: {session_id} -> {lesson_id}")
    next_focus = state.get("next_focus")
    if next_focus is not None:
        if isinstance(next_focus, str):
            if (
                (next_focus.startswith("lesson_") or next_focus.startswith("topic_"))
                and not _known_id(next_focus, indexes["lessons"])
                and not _known_id(next_focus, indexes["topics"])
            ):
                errors.append(f"next_focus references unknown ID: {next_focus}")
        elif isinstance(next_focus, dict):
            for field, collection in (("lesson_id", "lessons"), ("topic_id", "topics")):
                if field in next_focus and not _known_id(next_focus[field], indexes[collection]):
                    errors.append(f"next_focus references unknown {field}: {next_focus[field]}")
        else:
            errors.append("next_focus must be a string, object, or null")
    return errors


def _validate_diagnostics(state: dict, indexes: dict[str, set[str]]) -> list[str]:
    """Validate diagnostic observations without treating them as learning evidence."""

    diagnostics = state.get("diagnostics", [])
    if diagnostics is None:
        return ["diagnostics must be a list"]
    if not isinstance(diagnostics, list):
        return ["diagnostics must be a list"]
    errors: list[str] = []
    diagnostic_ids: set[str] = set()
    observation_ids: set[str] = set()
    for position, diagnostic in enumerate(diagnostics):
        if not isinstance(diagnostic, dict):
            errors.append(f"diagnostics[{position}] must be an object")
            continue
        diagnostic_id = diagnostic.get("diagnostic_id")
        if not _is_string(diagnostic_id) or not diagnostic_id.startswith("diagnostic_"):
            errors.append(f"diagnostics[{position}] diagnostic_id must start with diagnostic_")
        elif diagnostic_id in diagnostic_ids:
            errors.append(f"duplicate diagnostic id: {diagnostic_id}")
        else:
            diagnostic_ids.add(diagnostic_id)
        if not _is_string(diagnostic.get("goal")):
            errors.append(f"diagnostic goal must be a non-empty string: {diagnostic_id}")
        scope = diagnostic.get("scope_topic_ids")
        if not isinstance(scope, list) or not all(isinstance(item, str) for item in scope):
            errors.append(f"diagnostic scope_topic_ids must be a list of strings: {diagnostic_id}")
        else:
            errors.extend(
                f"diagnostic references unknown topic: {topic_id}"
                for topic_id in scope
                if topic_id not in indexes["topics"]
            )
        status = diagnostic.get("status")
        if status not in DIAGNOSTIC_STATUSES:
            errors.append(f"invalid diagnostic status: {diagnostic_id}")
        if not _is_timestamp(diagnostic.get("started_at"), allow_none=True):
            errors.append(f"diagnostic started_at must be an ISO date/time or null: {diagnostic_id}")
        if not _is_timestamp(diagnostic.get("completed_at"), allow_none=True):
            errors.append(f"diagnostic completed_at must be an ISO date/time or null: {diagnostic_id}")
        if status == "completed" and not diagnostic.get("completed_at"):
            errors.append(f"completed diagnostic requires completed_at: {diagnostic_id}")
        entry_topic_id = diagnostic.get("entry_topic_id")
        if entry_topic_id is not None and entry_topic_id not in indexes["topics"]:
            errors.append(f"diagnostic entry_topic_id references unknown topic: {entry_topic_id}")
        observations = diagnostic.get("observations")
        if not isinstance(observations, list):
            errors.append(f"diagnostic observations must be a list: {diagnostic_id}")
            observations = []
        for observation in observations:
            if not isinstance(observation, dict):
                errors.append(f"diagnostic observation must be an object: {diagnostic_id}")
                continue
            observation_id = observation.get("observation_id")
            if not _is_string(observation_id) or not observation_id.startswith("diagnostic_observation_"):
                errors.append(f"diagnostic observation id is invalid: {observation_id}")
            elif observation_id in observation_ids:
                errors.append(f"duplicate diagnostic observation id: {observation_id}")
            else:
                observation_ids.add(observation_id)
            topic_id = observation.get("topic_id")
            if topic_id not in indexes["topics"]:
                errors.append(f"diagnostic observation references unknown topic: {topic_id}")
            if observation.get("estimate") not in DIAGNOSTIC_ESTIMATES:
                errors.append(f"invalid diagnostic estimate: {observation_id}")
            if observation.get("confidence") not in DIAGNOSTIC_CONFIDENCES:
                errors.append(f"invalid diagnostic confidence: {observation_id}")
            if observation.get("direction") not in DIAGNOSTIC_DIRECTIONS:
                errors.append(f"invalid diagnostic direction: {observation_id}")
            for field in ("prompt", "response", "reason"):
                if not _is_string(observation.get(field)):
                    errors.append(f"diagnostic observation {field} must be a non-empty string: {observation_id}")
            if not isinstance(observation.get("prerequisite_gap"), bool):
                errors.append(f"diagnostic observation prerequisite_gap must be boolean: {observation_id}")
            if not _is_timestamp(observation.get("recorded_at")):
                errors.append(f"diagnostic observation recorded_at must be an ISO date/time: {observation_id}")
        observation_ids_for_run = {
            item.get("observation_id")
            for item in observations
            if isinstance(item, dict) and isinstance(item.get("observation_id"), str)
        }
        summary = diagnostic.get("summary")
        if not isinstance(summary, list):
            errors.append(f"diagnostic summary must be a list: {diagnostic_id}")
        else:
            for item in summary:
                if not isinstance(item, dict):
                    errors.append(f"diagnostic summary item must be an object: {diagnostic_id}")
                    continue
                if item.get("topic_id") not in indexes["topics"]:
                    errors.append(f"diagnostic summary references unknown topic: {item.get('topic_id')}")
                if item.get("estimate") not in DIAGNOSTIC_ESTIMATES:
                    errors.append(f"invalid diagnostic summary estimate: {diagnostic_id}")
                if item.get("confidence") not in DIAGNOSTIC_CONFIDENCES:
                    errors.append(f"invalid diagnostic summary confidence: {diagnostic_id}")
                if not isinstance(item.get("observation_ids"), list) or not all(
                    isinstance(value, str) for value in item.get("observation_ids", [])
                ):
                    errors.append(f"diagnostic summary observation_ids must be a list of strings: {diagnostic_id}")
                else:
                    errors.extend(
                        f"diagnostic summary references unknown observation: {value}"
                        for value in item["observation_ids"]
                        if value not in observation_ids_for_run
                    )
    return errors


def _validate_sources(payload: object, state_indexes: dict[str, set[str]]) -> tuple[list[str], set[str]]:
    if not isinstance(payload, dict):
        return ["sources.json must be an object"], set()
    sources = payload.get("sources")
    if not isinstance(sources, list):
        return ["sources must be a list"], set()
    errors: list[str] = []
    source_ids: set[str] = set()
    required = {
        "source_id", "title", "author_or_institution", "url", "publication_date",
        "accessed_at", "source_type", "lesson_ids", "topic_ids", "authority_reason",
    }
    for position, source in enumerate(sources):
        if not isinstance(source, dict):
            errors.append(f"sources[{position}] must be an object")
            continue
        missing = sorted(required - source.keys())
        errors.extend(f"sources[{position}] missing field: {field}" for field in missing)
        source_id = source.get("source_id")
        if not _is_string(source_id) or not source_id.startswith("source_"):
            errors.append(f"sources[{position}] source_id must start with source_")
        elif source_id in source_ids:
            errors.append(f"duplicate source id: {source_id}")
        else:
            source_ids.add(source_id)
        for field in ("title", "author_or_institution", "url", "source_type", "authority_reason"):
            if not _is_string(source.get(field)):
                errors.append(f"source {field} must be a non-empty string: {source_id}")
        if not _is_timestamp(source.get("publication_date"), allow_none=True):
            errors.append(f"source publication_date must be an ISO date/time or null: {source_id}")
        if not _is_timestamp(source.get("accessed_at")):
            errors.append(f"source accessed_at must be an ISO date/time: {source_id}")
        for field, collection in (("lesson_ids", "lessons"), ("topic_ids", "topics")):
            values = source.get(field)
            if not isinstance(values, list) or not all(isinstance(item, str) for item in values):
                errors.append(f"source {field} must be a list of strings: {source_id}")
                continue
            errors.extend(
                f"source references unknown {collection[:-1]}: {value}"
                for value in values
                if value not in state_indexes[collection]
            )
    return errors, source_ids


def _validate_cards(
    payload: object,
    state_indexes: dict[str, set[str]],
    source_ids: set[str],
    lessons_by_id: dict[str, dict],
) -> list[str]:
    if not isinstance(payload, dict):
        return ["cards.json must be an object"]
    cards = payload.get("cards")
    if not isinstance(cards, list):
        return ["cards must be a list"]
    errors: list[str] = []
    card_ids: set[str] = set()
    required = {
        "card_id", "topic_id", "lesson_id", "source_ids", "front", "back", "created_at",
        "updated_at", "due_at", "difficulty", "spaced_repetition_step", "interval_days",
        "review_count", "objective_correctness", "last_result", "confidence", "status",
    }
    for position, card in enumerate(cards):
        if not isinstance(card, dict):
            errors.append(f"cards[{position}] must be an object")
            continue
        missing = sorted(required - card.keys())
        errors.extend(f"cards[{position}] missing field: {field}" for field in missing)
        card_id = card.get("card_id")
        if not _is_string(card_id) or not card_id.startswith("card_"):
            errors.append(f"cards[{position}] card_id must start with card_")
        elif card_id in card_ids:
            errors.append(f"duplicate card id: {card_id}")
        else:
            card_ids.add(card_id)
        for field, collection in (("topic_id", "topics"), ("lesson_id", "lessons")):
            value = card.get(field)
            if value is not None and not _known_id(value, state_indexes[collection]):
                errors.append(f"card references unknown {collection[:-1]}: {value}")
        topic_id = card.get("topic_id")
        lesson_id = card.get("lesson_id")
        if _known_id(topic_id, state_indexes["topics"]) and _known_id(lesson_id, state_indexes["lessons"]):
            lesson = lessons_by_id.get(lesson_id)
            if lesson and lesson.get("topic_id") != topic_id:
                errors.append(f"card lesson/topic mismatch: {card_id}")
        source_values = card.get("source_ids")
        if not isinstance(source_values, list) or not all(isinstance(item, str) for item in source_values):
            errors.append(f"card source_ids must be a list of strings: {card_id}")
        else:
            errors.extend(
                f"card references unknown source: {value}"
                for value in source_values
                if value not in source_ids
            )
        for field in ("front", "back"):
            if not _is_string(card.get(field)):
                errors.append(f"card {field} must be a non-empty string: {card_id}")
        for field in ("created_at", "updated_at"):
            if not _is_timestamp(card.get(field)):
                errors.append(f"card {field} must be an ISO date/time: {card_id}")
        if not _is_timestamp(card.get("due_at"), allow_none=True):
            errors.append(f"card due_at must be an ISO date/time or null: {card_id}")
        if not isinstance(card.get("difficulty"), str) or card.get("difficulty") not in CARD_DIFFICULTIES:
            errors.append(f"invalid card difficulty: {card_id}")
        step = card.get("spaced_repetition_step")
        if isinstance(step, bool) or not isinstance(step, int) or step < 0:
            errors.append(f"card spaced_repetition_step must be a non-negative integer: {card_id}")
        for field in ("interval_days", "review_count"):
            value = card.get(field)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                errors.append(f"card {field} must be a non-negative integer: {card_id}")
        if (
            card.get("last_result") is not None
            and (not isinstance(card.get("last_result"), str) or card.get("last_result") not in CARD_RESULTS)
        ):
            errors.append(f"invalid card last_result: {card_id}")
        if card.get("objective_correctness") is not None and not isinstance(card.get("objective_correctness"), bool):
            errors.append(f"card objective_correctness must be boolean or null: {card_id}")
        confidence = card.get("confidence")
        if confidence is not None and (isinstance(confidence, bool) or not isinstance(confidence, int) or not 0 <= confidence <= 100):
            errors.append(f"card confidence must be an integer from 0 to 100 or null: {card_id}")
        if not isinstance(card.get("status"), str) or card.get("status") not in CARD_STATUSES:
            errors.append(f"invalid card status: {card_id}")
    return errors


def _validate_media_item_contract(item: object) -> list[str]:
    return validate_media_item(item)


def validate_state(state: dict) -> list[str]:
    """Return deterministic errors for a state payload."""

    errors = _validate_state_shape(state)
    if not isinstance(state, dict):
        return sorted(set(errors))
    working_state = dict(state)
    for collection in STATE_COLLECTIONS:
        if not isinstance(working_state.get(collection), list):
            working_state[collection] = []
    indexes, id_errors = _unique_ids(working_state)
    errors.extend(id_errors)
    errors.extend(_validate_topics(working_state, indexes))
    errors.extend(_validate_lessons(working_state, indexes))
    errors.extend(_validate_sessions(working_state, indexes))
    errors.extend(_validate_evidences(working_state, indexes))
    errors.extend(_validate_projects(working_state, indexes))
    errors.extend(_validate_weak_points(working_state, indexes))
    errors.extend(_validate_mastery(working_state, indexes))
    errors.extend(_validate_diagnostics(working_state, indexes))
    errors.extend(_validate_cross_references(working_state, indexes))
    return sorted(set(errors))


def validate_study(study_root: Path) -> list[str]:
    metadata = study_root.resolve() / ".ai-tutor"
    errors: list[str] = []
    required_files = (
        "study-config.json",
        "state.json",
        "media-index.json",
        "cards.json",
        "sources.json",
    )
    for name in required_files:
        if not (metadata / name).is_file():
            errors.append(f"missing study file: .ai-tutor/{name}")
    if errors:
        return errors
    payloads: dict[str, dict] = {}
    for name in required_files:
        try:
            payload = json.loads((metadata / name).read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                errors.append(f"invalid {name}: root must be an object")
            else:
                payloads[name] = payload
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            errors.append(f"invalid {name}: {exc}")
    if errors:
        return errors

    state = payloads["state.json"]
    config = payloads["study-config.json"]
    media_index = payloads["media-index.json"]
    errors.extend(_validate_config(config))
    errors.extend(validate_state(state))
    expected_study_id = state.get("study_id")
    for name, payload in payloads.items():
        if payload.get("schema_version") != 2:
            errors.append(f"{name}: schema_version must be 2")
        if payload.get("study_id") != expected_study_id:
            errors.append(f"study_id mismatch: {name}")

    for name in ("media-index.json", "cards.json", "sources.json"):
        revision = payloads[name].get("revision")
        if isinstance(revision, bool) or not isinstance(revision, int) or revision < 0:
            errors.append(f"{name[:-5]} revision must be a non-negative integer")

    normalized_state = dict(state)
    for collection in STATE_COLLECTIONS:
        if not isinstance(normalized_state.get(collection), list):
            normalized_state[collection] = []
    state_indexes, _ = _unique_ids(normalized_state)
    lessons_by_id = {
        item.get("lesson_id"): item
        for item in normalized_state.get("lessons", [])
        if isinstance(item, dict) and isinstance(item.get("lesson_id"), str)
    }
    source_errors, source_ids = _validate_sources(payloads["sources.json"], state_indexes)
    errors.extend(source_errors)
    errors.extend(_validate_cards(payloads["cards.json"], state_indexes, source_ids, lessons_by_id))

    artifacts = media_index.get("artifacts")
    if not isinstance(artifacts, list):
        errors.append("media-index artifacts must be a list")
        artifacts = []
    seen_artifacts: set[str] = set()
    for item in artifacts:
        if not isinstance(item, dict):
            errors.append("media-index artifact must be an object")
            continue
        artifact_id = item.get("artifact_id")
        if isinstance(artifact_id, str) and artifact_id in seen_artifacts:
            errors.append(f"duplicate media artifact id: {artifact_id}")
        if isinstance(artifact_id, str) and artifact_id:
            seen_artifacts.add(artifact_id)
        errors.extend(_validate_media_item_contract(item))
    for relative in ("curriculum.md", "session-log.md", "flashcards.md"):
        if not (study_root.resolve() / relative).is_file():
            errors.append(f"missing study projection: {relative}")
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("study_root", type=Path)
    args = parser.parse_args()
    errors = validate_study(args.study_root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("STUDY VALIDATION: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
