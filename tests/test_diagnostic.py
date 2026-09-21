import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.init_study import initialize_study
from scripts.migrate_state import migrate
from scripts.validate_study import validate_state


ROOT = Path(__file__).resolve().parents[1]
CONFIG = {
    "topic": "Python",
    "goal": "Automação",
    "deadline": None,
    "weekly_hours": 2,
    "preferred_times": ["weekend"],
    "initial_level": "basic",
    "language": "pt-BR",
    "accessibility": [],
    "source_policy": {},
}


def base_state():
    return {
        "schema_version": 2,
        "study_id": "study_a",
        "revision": 0,
        "updated_at": None,
        "topics": [{
            "topic_id": "topic_functions",
            "name": "Functions",
            "mastery": 0,
            "retention": "unknown",
            "status": "not_started",
            "last_practice": None,
            "evidence_ids": [],
        }],
        "evidences": [],
        "sessions": [],
        "lessons": [],
        "weak_points": [],
        "projects": [],
        "next_focus": None,
        "diagnostics": [],
    }


def completed_diagnostic():
    return {
        "diagnostic_id": "diagnostic_a",
        "goal": "Automação",
        "scope_topic_ids": ["topic_functions"],
        "status": "completed",
        "started_at": "2026-09-21T10:00:00Z",
        "completed_at": "2026-09-21T10:10:00Z",
        "entry_topic_id": "topic_functions",
        "observations": [{
            "observation_id": "diagnostic_observation_a",
            "topic_id": "topic_functions",
            "estimate": "partial",
            "confidence": "medium",
            "direction": "probe_down",
            "prompt": "Escreva uma função.",
            "response": "Confundiu return e print.",
            "prerequisite_gap": False,
            "reason": "Cria a função, mas não retorna o valor.",
            "recorded_at": "2026-09-21T10:05:00Z",
        }],
        "summary": [{
            "topic_id": "topic_functions",
            "estimate": "partial",
            "confidence": "medium",
            "observation_ids": ["diagnostic_observation_a"],
        }],
    }


class DiagnosticValidationTests(unittest.TestCase):
    def test_completed_diagnostic_is_valid_and_not_evidence(self):
        state = base_state()
        state["diagnostics"] = [completed_diagnostic()]
        self.assertEqual([], validate_state(state))
        self.assertEqual([], state["evidences"])
        self.assertEqual(0, state["topics"][0]["mastery"])

    def test_rejects_unknown_topic_and_invalid_estimate(self):
        state = base_state()
        diagnostic = completed_diagnostic()
        diagnostic["observations"][0]["topic_id"] = "topic_missing"
        diagnostic["observations"][0]["estimate"] = "mastered"
        state["diagnostics"] = [diagnostic]
        errors = validate_state(state)
        self.assertTrue(any("diagnostic observation references unknown topic" in error for error in errors))
        self.assertTrue(any("invalid diagnostic estimate" in error for error in errors))

    def test_rejects_completed_diagnostic_without_completion_timestamp(self):
        state = base_state()
        diagnostic = completed_diagnostic()
        diagnostic["completed_at"] = None
        state["diagnostics"] = [diagnostic]
        self.assertTrue(any("completed diagnostic requires completed_at" in error for error in validate_state(state)))

    def test_rejects_invalid_topic_projection(self):
        state = base_state()
        state["topics"][0]["diagnostic"] = {
            "estimate": "mastered",
            "confidence": "certain",
            "diagnostic_id": "diagnostic_a",
        }
        errors = validate_state(state)
        self.assertTrue(any("invalid topic diagnostic estimate" in error for error in errors))
        self.assertTrue(any("invalid topic diagnostic confidence" in error for error in errors))

    def test_v2_upgrade_adds_empty_diagnostic_without_touching_history(self):
        with tempfile.TemporaryDirectory() as temporary:
            study = Path(temporary) / "study"
            initialize_study(ROOT, study, CONFIG)
            state_path = study / ".ai-tutor" / "state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state.pop("diagnostics", None)
            state["topics"] = [{
                "topic_id": "topic_functions",
                "name": "Functions",
                "mastery": 40,
                "retention": "medium",
                "status": "in_progress",
                "last_practice": None,
                "evidence_ids": [],
                "notes": "existing note",
            }]
            state_path.write_text(json.dumps(state), encoding="utf-8")
            before = copy.deepcopy(state)

            report = migrate(study)

            self.assertTrue(report.valid)
            self.assertTrue(report.changed)
            upgraded = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual([], upgraded["diagnostics"])
            self.assertEqual(before["topics"], upgraded["topics"])
            self.assertEqual(before["evidences"], upgraded["evidences"])

    def test_v2_upgrade_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temporary:
            study = Path(temporary) / "study"
            initialize_study(ROOT, study, CONFIG)
            state_path = study / ".ai-tutor" / "state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state.pop("diagnostics", None)
            state_path.write_text(json.dumps(state), encoding="utf-8")
            first = migrate(study)
            snapshot = state_path.read_bytes()
            second = migrate(study)
            self.assertTrue(first.changed)
            self.assertFalse(second.changed)
            self.assertEqual(snapshot, state_path.read_bytes())


if __name__ == "__main__":
    unittest.main()
