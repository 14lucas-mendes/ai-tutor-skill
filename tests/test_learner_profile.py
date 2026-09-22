import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.init_study import initialize_study
from scripts.learner_profile import (
    add_inference,
    challenge_inference,
    empty_profile,
    record_observation,
    set_preference,
    update_profile_file,
    validate_profile,
)
from scripts.migrate_state import migrate
from scripts.validate_study import validate_study


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


class LearnerProfileTests(unittest.TestCase):
    def test_empty_profile_starts_unknown(self):
        profile = empty_profile("study_a")
        self.assertEqual(2, profile["schema_version"])
        self.assertEqual("unknown", profile["summary"]["autonomy"])
        self.assertEqual("unknown", profile["summary"]["help_dependency"])
        self.assertEqual([], validate_profile(profile))

    def test_preference_correction_preserves_history(self):
        profile = empty_profile("study_a")
        profile = set_preference(profile, "explanation_depth", "concise", "2026-09-21T10:00:00Z")
        profile = set_preference(profile, "explanation_depth", "detailed_for_new_topics", "2026-09-22T10:00:00Z")
        self.assertEqual(["inactive", "active"], [item["status"] for item in profile["declared_preferences"]])
        self.assertEqual([], validate_profile(profile))

    def test_observation_is_factual_and_inference_requires_provenance(self):
        profile = empty_profile("study_a")
        profile = record_observation(
            profile,
            session_id="session_1",
            topic_id="topic_functions",
            observation_type="autonomous_attempt",
            value={"result": "correct"},
            recorded_at="2026-09-21T10:00:00Z",
        )
        inference = {
            "inference_id": "inference_a",
            "signal": "autonomy_increasing",
            "status": "hypothesis",
            "confidence": "low",
            "scope": {"type": "topic", "topic_id": "topic_functions"},
            "observation_ids": ["profile_observation_missing"],
            "first_observed_at": "2026-09-21T10:00:00Z",
            "updated_at": "2026-09-21T10:00:00Z",
            "learner_feedback": None,
        }
        with self.assertRaises(ValueError):
            add_inference(profile, inference)

    def test_consistent_observations_allow_medium_inference(self):
        profile = empty_profile("study_a")
        for index in range(3):
            profile = record_observation(
                profile,
                session_id=f"session_{index + 1}",
                topic_id="topic_functions",
                observation_type="strategy_outcome",
                value={"strategy": "worked_example", "result": "autonomous_success"},
                recorded_at=f"2026-09-{21 + index:02d}T10:00:00Z",
            )
        inference = {
            "inference_id": "inference_a",
            "signal": "worked_examples_effective",
            "status": "hypothesis",
            "confidence": "medium",
            "scope": {"type": "topic", "topic_id": "topic_functions"},
            "observation_ids": [item["observation_id"] for item in profile["observations"]],
            "first_observed_at": "2026-09-21T10:00:00Z",
            "updated_at": "2026-09-23T10:00:00Z",
            "learner_feedback": None,
        }
        profile = add_inference(profile, inference)
        self.assertEqual([], validate_profile(profile))

    def test_summary_updates_only_from_repeated_observations(self):
        profile = empty_profile("study_a")
        profile = record_observation(
            profile,
            session_id="session_1",
            topic_id="topic_functions",
            observation_type="autonomous_attempt",
            value={"result": "correct"},
            recorded_at="2026-09-21T10:00:00Z",
        )
        self.assertEqual("low", profile["summary"]["autonomy"])
        profile = record_observation(
            profile,
            session_id="session_2",
            topic_id="topic_functions",
            observation_type="autonomous_attempt",
            value={"result": "correct"},
            recorded_at="2026-09-22T10:00:00Z",
        )
        self.assertEqual("medium", profile["summary"]["autonomy"])

    def test_atomic_profile_update_uses_revision(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "learner-profile.json"
            path.write_text(json.dumps(empty_profile("study_a")), encoding="utf-8")
            updated = update_profile_file(
                path,
                lambda profile: set_preference(profile, "example_context", "practical", "2026-09-21T10:00:00Z"),
                expected_revision=0,
            )
            self.assertEqual(1, updated["revision"])
            self.assertEqual("practical", updated["declared_preferences"][0]["value"])

    def test_challenge_preserves_inference_and_observations(self):
        profile = empty_profile("study_a")
        for index in range(2):
            profile = record_observation(
                profile,
                session_id=f"session_{index + 1}",
                topic_id="topic_functions",
                observation_type="autonomous_attempt",
                value={"result": "correct"},
                recorded_at=f"2026-09-{21 + index:02d}T10:00:00Z",
            )
        inference = {
            "inference_id": "inference_a",
            "signal": "autonomy_stable",
            "status": "hypothesis",
            "confidence": "low",
            "scope": {"type": "topic", "topic_id": "topic_functions"},
            "observation_ids": [item["observation_id"] for item in profile["observations"]],
            "first_observed_at": "2026-09-21T10:00:00Z",
            "updated_at": "2026-09-22T10:00:00Z",
            "learner_feedback": None,
        }
        profile = add_inference(profile, inference)
        profile = challenge_inference(profile, "inference_a", "Prefiro tentar primeiro.", "2026-09-23T10:00:00Z")
        self.assertEqual("challenged", profile["inferences"][0]["status"])
        self.assertEqual(2, len(profile["observations"]))
        self.assertEqual([], validate_profile(profile))

    def test_new_study_initializes_and_validates_profile_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            study = Path(temporary) / "study"
            initialize_study(ROOT, study, CONFIG)
            profile_path = study / ".ai-tutor" / "learner-profile.json"
            self.assertTrue(profile_path.is_file())
            self.assertEqual([], validate_study(study))

    def test_v2_migration_adds_empty_profile_without_changing_learning_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            study = Path(temporary) / "study"
            initialize_study(ROOT, study, CONFIG)
            profile_path = study / ".ai-tutor" / "learner-profile.json"
            profile_path.unlink()
            state_path = study / ".ai-tutor" / "state.json"
            before = json.loads(state_path.read_text(encoding="utf-8"))
            report = migrate(study)
            after = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertTrue(report.changed)
            self.assertEqual(before, after)
            self.assertEqual([], validate_study(study))

    def test_v2_migration_repairs_missing_profile_revision(self):
        with tempfile.TemporaryDirectory() as temporary:
            study = Path(temporary) / "study"
            initialize_study(ROOT, study, CONFIG)
            profile_path = study / ".ai-tutor" / "learner-profile.json"
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
            profile.pop("revision")
            profile_path.write_text(json.dumps(profile), encoding="utf-8")
            report = migrate(study)
            self.assertTrue(report.valid)
            self.assertEqual(0, json.loads(profile_path.read_text(encoding="utf-8"))["revision"])


if __name__ == "__main__":
    unittest.main()
