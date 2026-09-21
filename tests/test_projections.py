import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.init_study import atomic_write, initialize_study
from scripts.projections import sync_projections
import scripts.projections as projections


ROOT = Path(__file__).resolve().parents[1]
CONFIG = {
    "topic": "IA generativa",
    "goal": "Explicar fundamentos",
    "deadline": None,
    "weekly_hours": 2,
    "preferred_times": ["weekend"],
    "initial_level": "basic",
    "language": "pt-BR",
    "accessibility": [],
    "source_policy": {"prefer_primary": True},
}


class ProjectionTests(unittest.TestCase):
    def test_sync_projects_canonical_ids_and_is_explicit(self):
        with tempfile.TemporaryDirectory() as tmp:
            study = Path(tmp) / "study"
            initialize_study(ROOT, study, CONFIG)
            state_path = study / ".ai-tutor" / "state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["sessions"] = [{
                "session_id": "session_a",
                "status": "completed",
                "transitions": ["in_progress", "completed"],
                "lesson_ids": [],
                "started_at": "2026-09-11T10:00:00Z",
                "ended_at": "2026-09-11T11:00:00Z",
                "checkpoint": None,
                "resumable": False,
            }]
            atomic_write(state_path, json.dumps(state, indent=2) + "\n")
            cards_path = study / ".ai-tutor" / "cards.json"
            cards = json.loads(cards_path.read_text(encoding="utf-8"))
            cards["cards"] = [{
                "card_id": "card_a",
                "topic_id": None,
                "lesson_id": None,
                "source_ids": [],
                "front": "What is retrieval?",
                "back": "Active recall from memory.",
                "created_at": "2026-09-11T10:00:00Z",
                "updated_at": "2026-09-11T10:00:00Z",
                "due_at": "2026-09-12",
                "difficulty": "medium",
                "spaced_repetition_step": 0,
                "interval_days": 1,
                "review_count": 0,
                "objective_correctness": None,
                "last_result": None,
                "confidence": None,
                "status": "new",
            }]
            atomic_write(cards_path, json.dumps(cards, indent=2) + "\n")
            original_flashcards = (study / "flashcards.md").read_text(encoding="utf-8")
            self.assertEqual([], sync_projections(study))
            flashcards = (study / "flashcards.md").read_text(encoding="utf-8")
            session_log = (study / "session-log.md").read_text(encoding="utf-8")
            self.assertNotEqual(original_flashcards, flashcards)
            self.assertIn("card_a", flashcards)
            self.assertIn("session_a", session_log)

    def test_failed_render_does_not_partially_update_projections(self):
        with tempfile.TemporaryDirectory() as tmp:
            study = Path(tmp) / "study"
            initialize_study(ROOT, study, CONFIG)
            flashcards_path = study / "flashcards.md"
            session_log_path = study / "session-log.md"
            flashcards_path.write_text("old cards", encoding="utf-8")
            session_log_path.write_text("old sessions", encoding="utf-8")
            state_path = study / ".ai-tutor" / "state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["sessions"] = [None]
            atomic_write(state_path, json.dumps(state, indent=2) + "\n")

            errors = sync_projections(study)

            self.assertTrue(errors)
            self.assertEqual("old cards", flashcards_path.read_text(encoding="utf-8"))
            self.assertEqual("old sessions", session_log_path.read_text(encoding="utf-8"))

    def test_failed_second_write_rolls_back_first_projection(self):
        with tempfile.TemporaryDirectory() as tmp:
            study = Path(tmp) / "study"
            initialize_study(ROOT, study, CONFIG)
            flashcards_path = study / "flashcards.md"
            session_log_path = study / "session-log.md"
            flashcards_path.write_text("old cards", encoding="utf-8")
            session_log_path.write_text("old sessions", encoding="utf-8")
            real_atomic_write = projections.atomic_write
            calls = 0

            def flaky_atomic_write(path, content):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("simulated projection failure")
                real_atomic_write(path, content)

            with patch.object(projections, "atomic_write", side_effect=flaky_atomic_write):
                errors = sync_projections(study)

            self.assertTrue(errors)
            self.assertEqual("old cards", flashcards_path.read_text(encoding="utf-8"))
            self.assertEqual("old sessions", session_log_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
