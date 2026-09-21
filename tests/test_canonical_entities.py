import json
import tempfile
import unittest
from pathlib import Path

from scripts.init_study import atomic_write, initialize_study
from scripts.validate_study import validate_study


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


def source(source_id="source_a"):
    return {
        "source_id": source_id,
        "title": "Official guide",
        "author_or_institution": "Example University",
        "url": "https://example.edu/guide",
        "publication_date": None,
        "accessed_at": "2026-09-11",
        "source_type": "official_documentation",
        "lesson_ids": [],
        "topic_ids": [],
        "authority_reason": "Primary institutional reference",
    }


def card(card_id="card_a", source_ids=None):
    return {
        "card_id": card_id,
        "topic_id": None,
        "lesson_id": None,
        "source_ids": [] if source_ids is None else source_ids,
        "front": "What is a model?",
        "back": "A representation of a system.",
        "created_at": "2026-09-11T12:00:00Z",
        "updated_at": "2026-09-11T12:00:00Z",
        "due_at": "2026-09-11",
        "difficulty": "medium",
        "spaced_repetition_step": 0,
        "interval_days": 1,
        "review_count": 0,
        "objective_correctness": None,
        "last_result": None,
        "confidence": None,
        "status": "new",
    }


class CanonicalEntityTests(unittest.TestCase):
    def test_valid_canonical_cards_and_sources_validate(self):
        with tempfile.TemporaryDirectory() as tmp:
            study = Path(tmp) / "study"
            initialize_study(ROOT, study, CONFIG)
            sources = source()
            cards = card(source_ids=["source_a"])
            atomic_write(
                study / ".ai-tutor" / "sources.json",
                json.dumps({
                    "schema_version": 2,
                    "study_id": json.loads((study / ".ai-tutor" / "state.json").read_text())["study_id"],
                    "revision": 0,
                    "sources": [sources],
                }, indent=2) + "\n",
            )
            atomic_write(
                study / ".ai-tutor" / "cards.json",
                json.dumps({
                    "schema_version": 2,
                    "study_id": json.loads((study / ".ai-tutor" / "state.json").read_text())["study_id"],
                    "revision": 0,
                    "cards": [cards],
                }, indent=2) + "\n",
            )
            self.assertEqual([], validate_study(study))

    def test_card_rejects_unknown_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            study = Path(tmp) / "study"
            initialize_study(ROOT, study, CONFIG)
            state = json.loads((study / ".ai-tutor" / "state.json").read_text())
            payload = {
                "schema_version": 2,
                "study_id": state["study_id"],
                "revision": 0,
                "cards": [card(source_ids=["source_missing"])],
            }
            atomic_write(study / ".ai-tutor" / "cards.json", json.dumps(payload, indent=2) + "\n")
            errors = validate_study(study)
            self.assertTrue(any("card references unknown source" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
