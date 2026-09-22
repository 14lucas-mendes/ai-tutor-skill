import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.init_study import initialize_study
from scripts.validate_study import validate_study
from scripts.validate_study import validate_state


ROOT = Path(__file__).resolve().parents[1]
CONFIG = {
    "topic": "Python",
    "goal": "Aprender",
    "deadline": None,
    "weekly_hours": 2,
    "preferred_times": ["flexível"],
    "initial_level": "básico",
    "language": "pt-BR",
    "accessibility": [],
    "source_policy": {},
}


def evidence(evidence_id, kind, *, session_id="session_a", transfer=False, autonomous=True, reference_type="lesson"):
    return {
        "evidence_id": evidence_id,
        "topic_id": "topic_a",
        "session_id": session_id,
        "kind": kind,
        "autonomous": autonomous,
        "transfer": transfer,
        "context": f"context-{evidence_id}",
        "recorded_at": "2026-08-29",
        "reference": {"type": reference_type, "id": "lesson_a"},
        "result": "correct",
        "error": None,
    }


def base_state():
    return {
        "schema_version": 2,
        "study_id": "study_a",
        "revision": 1,
        "updated_at": "2026-08-29T12:00:00Z",
        "topics": [{
            "topic_id": "topic_a",
            "name": "Consistency",
            "mastery": 0,
            "retention": "unknown",
            "status": "not_started",
            "last_practice": None,
            "evidence_ids": [],
        }],
        "evidences": [],
        "sessions": [{
            "session_id": "session_a",
            "status": "completed",
            "transitions": ["in_progress", "completed"],
            "lesson_ids": ["lesson_a"],
            "started_at": "2026-08-29T12:00:00Z",
            "ended_at": "2026-08-29T13:00:00Z",
            "checkpoint": None,
            "resumable": False,
        }],
        "lessons": [{"lesson_id": "lesson_a", "topic_id": "topic_a", "status": "planned", "session_ids": ["session_a"]}],
        "weak_points": [],
        "projects": [],
        "next_focus": None,
    }


class ValidateStudyTests(unittest.TestCase):
    def test_validate_study_accepts_one_complementary_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            study = Path(tmp) / "study"
            initialize_study(ROOT, study, CONFIG)
            media_path = study / ".ai-tutor" / "media-index.json"
            media = json.loads(media_path.read_text(encoding="utf-8"))
            primary = {
                "artifact_id": "media_primary",
                "lesson_id": "lesson_a",
                "type": "learning_pack",
                "provider": "local",
                "source_ids": [],
                "objective": "Explain loops",
                "local_path": "media/lesson_a/primary",
                "url": None,
                "status": "prepared",
                "verified": False,
                "created_at": "2026-09-22T12:00:00Z",
                "verified_at": None,
                "accessibility": {},
                "evidence_eligible": False,
            }
            complementary = dict(primary)
            complementary.update({
                "artifact_id": "media_complement",
                "local_path": "media/lesson_a/diagram",
                "representation": {
                    "role": "complementary",
                    "complements_artifact_id": "media_primary",
                    "rationale": "O diagrama mostra a sequência.",
                    "distinct_contribution": "Explicita o fluxo entre itens.",
                },
            })
            media["artifacts"] = [primary, complementary]
            media_path.write_text(json.dumps(media), encoding="utf-8")

            self.assertEqual([], validate_study(study))

    def test_domain_60_needs_feynman_and_application(self):
        state = base_state()
        item = evidence("evidence_f", "feynman")
        state["evidences"] = [item]
        state["topics"][0].update(mastery=60, status="in_progress", evidence_ids=[item["evidence_id"]])
        self.assertTrue(any("mastery 60" in error for error in validate_state(state)))

    def test_domain_60_does_not_need_transfer(self):
        state = base_state()
        items = [evidence("evidence_f", "feynman"), evidence("evidence_a", "application")]
        state["evidences"] = items
        state["topics"][0].update(mastery=60, status="in_progress", evidence_ids=[item["evidence_id"] for item in items])
        self.assertEqual([], validate_state(state))

    def test_domain_80_needs_transfer(self):
        state = base_state()
        items = [evidence("evidence_f", "feynman"), evidence("evidence_a", "application")]
        state["evidences"] = items
        state["topics"][0].update(mastery=80, status="mastered", evidence_ids=[item["evidence_id"] for item in items])
        self.assertTrue(any("mastery 80" in error and "transfer" in error for error in validate_state(state)))

    def test_domain_100_needs_two_sessions_and_contexts(self):
        state = base_state()
        items = [
            evidence("evidence_f", "feynman", session_id="session_a"),
            evidence("evidence_a", "application", session_id="session_a", transfer=True),
        ]
        state["evidences"] = items
        state["topics"][0].update(mastery=100, status="mastered", evidence_ids=[item["evidence_id"] for item in items])
        errors = validate_state(state)
        self.assertTrue(any("mastery 100" in error for error in errors), errors)

    def test_interrupted_session_can_transition_to_resumed(self):
        state = base_state()
        state["sessions"] = [{
            "session_id": "session_a",
            "status": "resumed",
            "transitions": ["in_progress", "interrupted", "resumed"],
            "lesson_ids": ["lesson_a"],
            "started_at": "2026-08-29T12:00:00Z",
            "ended_at": None,
            "checkpoint": "exercise-2",
            "resumable": True,
        }]
        state["lessons"][0]["session_ids"] = ["session_a"]
        self.assertEqual([], validate_state(state))

    def test_rejects_invalid_session_transition(self):
        state = base_state()
        state["sessions"] = [{
            "session_id": "session_a",
            "status": "completed",
            "transitions": ["in_progress", "completed", "resumed"],
            "lesson_ids": [],
            "started_at": "2026-08-29T12:00:00Z",
            "ended_at": "2026-08-29T13:00:00Z",
            "checkpoint": None,
            "resumable": False,
        }]
        self.assertTrue(any("invalid session transition" in error for error in validate_state(state)))

    def test_completed_session_cannot_be_resumable(self):
        state = base_state()
        state["sessions"][0]["resumable"] = True

        errors = validate_state(state)

        self.assertTrue(any("completed session cannot be resumable" in error for error in errors), errors)

    def test_media_cannot_be_evidence(self):
        state = base_state()
        item = evidence("evidence_m", "application", reference_type="media")
        state["evidences"] = [item]
        state["topics"][0]["evidence_ids"] = [item["evidence_id"]]
        self.assertTrue(any("media cannot be evidence" in error for error in validate_state(state)))

    def test_malformed_evidence_reference_returns_error(self):
        state = base_state()
        item = evidence("evidence_bad_reference", "application")
        item["reference"] = None
        state["evidences"] = [item]
        state["topics"][0]["evidence_ids"] = [item["evidence_id"]]

        errors = validate_state(state)

        self.assertTrue(any("reference must contain type and id" in error for error in errors), errors)

    def test_rejects_evidence_reference_to_unknown_lesson(self):
        state = base_state()
        item = evidence("evidence_dangling", "application")
        item["reference"]["id"] = "lesson_absent"
        state["evidences"] = [item]
        state["topics"][0]["evidence_ids"] = [item["evidence_id"]]

        errors = validate_state(state)

        self.assertTrue(any("reference points to unknown lesson" in error for error in errors), errors)

    def test_rejects_duplicate_ids_and_dangling_references(self):
        state = base_state()
        duplicate = copy.deepcopy(state["topics"][0])
        state["topics"].append(duplicate)
        state["topics"][0]["evidence_ids"] = ["evidence_missing"]
        errors = validate_state(state)
        self.assertTrue(any("duplicate id" in error for error in errors), errors)
        self.assertTrue(any("unknown evidence" in error for error in errors), errors)

    def test_rejects_lesson_with_unknown_topic(self):
        state = base_state()
        state["lessons"][0]["topic_id"] = "topic_missing"
        errors = validate_state(state)
        self.assertTrue(any("unknown topic" in error for error in errors), errors)

    def test_rejects_evidence_with_unknown_session(self):
        state = base_state()
        item = evidence("evidence_a", "application", session_id="session_missing")
        state["evidences"] = [item]
        state["topics"][0]["evidence_ids"] = [item["evidence_id"]]
        errors = validate_state(state)
        self.assertTrue(any("unknown session" in error for error in errors), errors)

    def test_rejects_orphan_evidence_not_attached_to_topic(self):
        state = base_state()
        item = evidence("evidence_a", "application")
        state["evidences"] = [item]
        errors = validate_state(state)
        self.assertTrue(any("not referenced by topic" in error for error in errors), errors)

    def test_rejects_completed_lesson_without_mastery(self):
        state = base_state()
        state["lessons"][0]["status"] = "completed"
        errors = validate_state(state)
        self.assertTrue(any("completed lesson" in error for error in errors), errors)

    def test_rejects_malformed_state_collection(self):
        state = base_state()
        state["topics"] = {}
        errors = validate_state(state)
        self.assertTrue(any("topics must be a list" in error for error in errors), errors)

    def test_malformed_collections_return_errors_instead_of_raising(self):
        for field, value in (("topics", None), ("lessons", 4)):
            with self.subTest(field=field):
                state = base_state()
                state[field] = value
                errors = validate_state(state)
                self.assertTrue(any(f"{field} must be a list" in error for error in errors), errors)

    def test_malformed_nested_values_return_errors_instead_of_raising(self):
        state = base_state()
        state["topics"][0]["evidence_ids"] = None
        state["topics"][0]["mastery"] = {"bad": True}
        state["topics"][0]["retention"] = {"bad": True}
        state["lessons"][0]["session_ids"] = None
        state["lessons"][0]["status"] = {"bad": True}
        state["sessions"][0]["transitions"] = ["in_progress", {"bad": True}]
        state["sessions"][0]["status"] = {"bad": True}

        errors = validate_state(state)

        self.assertTrue(errors)

    def test_unhashable_ids_return_errors_instead_of_raising(self):
        state = base_state()
        state["topics"][0]["evidence_ids"] = [{}]
        state["evidences"] = [{"evidence_id": {"bad": True}}]
        state["lessons"][0]["topic_id"] = {}
        state["lessons"][0]["session_ids"] = [{}]
        state["sessions"][0]["lesson_ids"] = [{}]

        errors = validate_state(state)

        self.assertTrue(errors)

    def test_rejects_invalid_weak_point_contract(self):
        state = base_state()
        state["weak_points"] = [{
            "weak_point_id": "weak_a",
            "topic_id": "topic_missing",
            "category": "made_up",
            "cause": "",
            "supporting_evidence_ids": ["evidence_missing"],
            "entered_at": "not-a-date",
            "exit_condition": "",
            "status": "active",
        }]

        errors = validate_state(state)

        self.assertTrue(any("unknown topic" in error for error in errors), errors)
        self.assertTrue(any("invalid weak point category" in error for error in errors), errors)
        self.assertTrue(any("unknown evidence" in error for error in errors), errors)

    def test_rejects_unsupported_evidence_reference_type(self):
        state = base_state()
        item = evidence("evidence_bad_type", "application")
        item["reference"] = {"type": "unsupported", "id": "lesson_a"}
        state["evidences"] = [item]
        state["topics"][0]["evidence_ids"] = [item["evidence_id"]]

        errors = validate_state(state)

        self.assertTrue(any("unsupported evidence reference type" in error for error in errors), errors)

    def test_unhashable_evidence_fields_do_not_crash_mastery_validation(self):
        state = base_state()
        state["topics"][0].update(mastery=100, status="mastered", evidence_ids=["evidence_a"])
        item = evidence("evidence_a", "application", transfer=True)
        item["kind"] = {"bad": True}
        item["session_id"] = {"bad": True}
        item["context"] = ["bad"]
        state["evidences"] = [item]

        errors = validate_state(state)

        self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
