import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.init_study import initialize_study
from scripts.migrate_state import migrate
from scripts.retrieval import needs_retrieval, record_retrieval_attempt
from scripts.validate_study import validate_state


ROOT = Path(__file__).resolve().parents[1]
CONFIG = {
    "topic": "Python",
    "goal": "Automatizar tarefas",
    "deadline": None,
    "weekly_hours": 3,
    "preferred_times": ["flexível"],
    "initial_level": "básico",
    "language": "pt-BR",
    "accessibility": [],
    "source_policy": {},
}


def base_state():
    return {
        "schema_version": 2,
        "study_id": "study_a",
        "revision": 1,
        "updated_at": "2026-09-22T12:00:00Z",
        "topics": [{
            "topic_id": "topic_a",
            "name": "Funções",
            "mastery": 0,
            "retention": "low",
            "status": "not_started",
            "last_practice": None,
            "evidence_ids": [],
        }],
        "evidences": [],
        "sessions": [{
            "session_id": "session_a",
            "status": "in_progress",
            "transitions": ["in_progress"],
            "lesson_ids": [],
            "started_at": "2026-09-22T12:00:00Z",
            "ended_at": None,
            "checkpoint": None,
            "resumable": True,
        }],
        "lessons": [],
        "weak_points": [],
        "projects": [],
        "next_focus": None,
    }


class RetrievalTests(unittest.TestCase):
    def test_record_retrieval_attempt_preserves_learning_state(self):
        state = base_state()
        updated = record_retrieval_attempt(
            state,
            session_id="session_a",
            topic_id="topic_a",
            prompt="O que você lembra sobre funções?",
            outcome="partial",
            support_level=0,
            recorded_at="2026-09-22T12:05:00Z",
        )

        self.assertEqual([], state.get("retrieval_attempts", []))
        self.assertEqual(0, updated["topics"][0]["mastery"])
        self.assertEqual([], updated["evidences"])
        self.assertEqual("partial", updated["retrieval_attempts"][0]["outcome"])
        self.assertTrue(updated["retrieval_attempts"][0]["retrieval_id"].startswith("retrieval_"))

    def test_record_retrieval_attempt_rejects_unknown_reference(self):
        with self.assertRaises(ValueError):
            record_retrieval_attempt(
                base_state(),
                session_id="session_missing",
                topic_id="topic_a",
                prompt="Lembre do conceito.",
                outcome="not_attempted",
                support_level=0,
                recorded_at="2026-09-22T12:05:00Z",
            )

    def test_retrieval_is_needed_only_for_relevant_review_targets(self):
        self.assertTrue(needs_retrieval({"retention": "low"}))
        self.assertTrue(needs_retrieval({"retention": "high"}, has_active_weak_point=True))
        self.assertTrue(needs_retrieval({"retention": "high"}, has_due_card=True))
        self.assertTrue(needs_retrieval({"retention": "medium"}, has_due_topic=True))
        self.assertFalse(needs_retrieval({"retention": "high"}))

    def test_validator_checks_retrieval_references_and_values(self):
        state = base_state()
        state["retrieval_attempts"] = [{
            "retrieval_id": "retrieval_a",
            "session_id": "session_missing",
            "topic_id": "topic_a",
            "prompt": "Recall",
            "outcome": "broken",
            "support_level": 9,
            "recorded_at": "2026-09-22T12:05:00Z",
        }]

        errors = validate_state(state)

        self.assertTrue(any("unknown session" in error for error in errors), errors)
        self.assertTrue(any("invalid retrieval outcome" in error for error in errors), errors)
        self.assertTrue(any("support_level" in error for error in errors), errors)

    def test_new_study_initializes_empty_retrieval_collection(self):
        with tempfile.TemporaryDirectory() as tmp:
            study = Path(tmp) / "study"
            initialize_study(ROOT, study, CONFIG)
            state = json.loads((study / ".ai-tutor" / "state.json").read_text(encoding="utf-8"))
            self.assertEqual([], state["retrieval_attempts"])

    def test_existing_v2_state_gets_empty_retrieval_collection_without_other_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            study = Path(tmp) / "study"
            initialize_study(ROOT, study, CONFIG)
            state_path = study / ".ai-tutor" / "state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state.pop("retrieval_attempts", None)
            state["topics"] = [{
                "topic_id": "topic_a",
                "name": "Funções",
                "mastery": 40,
                "retention": "medium",
                "status": "in_progress",
                "last_practice": None,
                "evidence_ids": [],
            }]
            state_path.write_text(json.dumps(state), encoding="utf-8")

            report = migrate(study)

            self.assertTrue(report.valid)
            migrated = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual([], migrated["retrieval_attempts"])
            self.assertEqual(40, migrated["topics"][0]["mastery"])


if __name__ == "__main__":
    unittest.main()
