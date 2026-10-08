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

    def _with_observations(self, items):
        profile = empty_profile("study_a")
        for index, (observation_type, value, session) in enumerate(items):
            profile = record_observation(
                profile,
                session_id=session,
                topic_id="topic_functions",
                observation_type=observation_type,
                value=value,
                recorded_at=f"2026-09-{10 + index:02d}T10:00:00Z",
            )
        return profile

    def test_summary_updates_only_from_repeated_observations(self):
        profile = self._with_observations([("autonomous_attempt", {"result": "correct"}, "session_1")])
        self.assertEqual("unknown", profile["summary"]["autonomy"])
        profile = self._with_observations([
            ("autonomous_attempt", {"result": "correct"}, "session_1"),
            ("autonomous_attempt", {"result": "correct"}, "session_2"),
        ])
        self.assertEqual("medium", profile["summary"]["autonomy"])

    def test_autonomy_summary_uses_success_rate_not_count(self):
        mostly_failed = self._with_observations([
            ("autonomous_attempt", {"result": "correct"}, "session_1"),
            ("autonomous_attempt", {"result": "incorrect"}, "session_1"),
            ("autonomous_attempt", {"result": "incorrect"}, "session_2"),
            ("autonomous_attempt", {"result": "partial"}, "session_2"),
        ])
        self.assertEqual("low", mostly_failed["summary"]["autonomy"])
        consistent = self._with_observations(
            [("autonomous_attempt", {"result": "correct"}, f"session_{1 + index % 2}") for index in range(5)]
            + [("autonomous_attempt", {"result": "partial"}, "session_2")]
        )
        self.assertEqual("high", consistent["summary"]["autonomy"])

    def test_high_autonomy_requires_two_sessions(self):
        profile = self._with_observations(
            [("autonomous_attempt", {"result": "correct"}, "session_1") for _ in range(5)]
        )
        self.assertEqual("medium", profile["summary"]["autonomy"])

    def test_help_dependency_counts_every_ladder_step(self):
        profile = self._with_observations([
            ("help_usage", {"help_level": 6}, "session_1"),
            ("help_usage", {"help_level": 5}, "session_2"),
        ])
        self.assertEqual("high", profile["summary"]["help_dependency"])

    def test_observation_values_are_validated(self):
        with self.assertRaises(ValueError):
            self._with_observations([("help_usage", {"support_level": 4}, "session_1")])
        with self.assertRaises(ValueError):
            self._with_observations([("autonomous_attempt", {"result": "great"}, "session_1")])
        profile = empty_profile("study_a")
        profile["observations"].append({
            "observation_id": "profile_observation_a",
            "session_id": "session_1",
            "topic_id": None,
            "type": "help_usage",
            "value": {"help_level": 9},
            "recorded_at": "2026-09-21T10:00:00Z",
        })
        self.assertIn("help_usage requires help_level from 0 to 6: profile_observation_a", validate_profile(profile))

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

    def test_v2_migration_renames_legacy_help_key_and_refreshes_summary(self):
        with tempfile.TemporaryDirectory() as temporary:
            study = Path(temporary) / "study"
            initialize_study(ROOT, study, CONFIG)
            profile_path = study / ".ai-tutor" / "learner-profile.json"
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
            state_path = study / ".ai-tutor" / "state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["sessions"] = [{
                "session_id": "session_1",
                "status": "completed",
                "transitions": ["in_progress", "completed"],
                "lesson_ids": [],
                "started_at": "2026-09-21T09:00:00Z",
                "ended_at": "2026-09-21T10:00:00Z",
                "checkpoint": None,
                "resumable": False,
            }]
            state_path.write_text(json.dumps(state), encoding="utf-8")
            profile["observations"] = [{
                "observation_id": "profile_observation_a",
                "session_id": "session_1",
                "topic_id": None,
                "type": "help_usage",
                "value": {"support_level": 4, "note": "pista parcial"},
                "recorded_at": "2026-09-21T10:00:00Z",
            }]
            profile["summary"]["autonomy"] = "low"
            profile_path.write_text(json.dumps(profile), encoding="utf-8")
            report = migrate(study)
            repaired = json.loads(profile_path.read_text(encoding="utf-8"))
            self.assertTrue(report.changed)
            self.assertEqual({"help_level": 4, "note": "pista parcial"}, repaired["observations"][0]["value"])
            self.assertEqual("unknown", repaired["summary"]["autonomy"])
            self.assertEqual(1, repaired["revision"])
            self.assertEqual([], validate_profile(repaired))


if __name__ == "__main__":
    unittest.main()
