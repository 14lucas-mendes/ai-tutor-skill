import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.init_study import initialize_study


ROOT = Path(__file__).resolve().parents[1]
VALID_CONFIG = {
    "topic": "Sistemas distribuídos",
    "goal": "Projetar serviços resilientes",
    "deadline": None,
    "weekly_hours": 6,
    "preferred_times": ["noite"],
    "initial_level": "iniciante",
    "language": "pt-BR",
    "accessibility": [],
    "source_policy": {"prefer_primary": True, "prefer_pt_br": True},
}


class InitializeStudyTests(unittest.TestCase):
    def test_initializes_path_with_spaces_without_fake_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            study = Path(tmp) / "meu estudo"
            created = initialize_study(ROOT, study, VALID_CONFIG)
            self.assertIn((study / ".ai-tutor" / "state.json").resolve(), created)
            state = json.loads((study / ".ai-tutor" / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(2, state["schema_version"])
            self.assertEqual([], state["topics"])
            self.assertEqual([], state["sessions"])
            self.assertNotIn("exemplo_topico", json.dumps(state))
            for name in ("cards.json", "sources.json"):
                payload = json.loads((study / ".ai-tutor" / name).read_text(encoding="utf-8"))
                self.assertEqual(2, payload["schema_version"])
                self.assertEqual(state["study_id"], payload["study_id"])
                self.assertEqual([], payload[name.removesuffix(".json")])

    def test_persists_every_setup_answer(self):
        with tempfile.TemporaryDirectory() as tmp:
            study = Path(tmp) / "study"
            initialize_study(ROOT, study, VALID_CONFIG)
            config = json.loads((study / ".ai-tutor" / "study-config.json").read_text(encoding="utf-8"))
            for key, value in VALID_CONFIG.items():
                self.assertEqual(value, config[key])

    def test_refuses_to_overwrite_existing_study(self):
        with tempfile.TemporaryDirectory() as tmp:
            study = Path(tmp) / "study"
            initialize_study(ROOT, study, VALID_CONFIG)
            with self.assertRaises(FileExistsError):
                initialize_study(ROOT, study, VALID_CONFIG)

    def test_preserves_existing_markdown_projections(self):
        with tempfile.TemporaryDirectory() as tmp:
            study = Path(tmp) / "study"
            study.mkdir()
            originals = {
                "curriculum.md": "# Existing curriculum\n",
                "session-log.md": "# Existing sessions\n",
                "flashcards.md": "# Existing cards\n",
            }
            for name, content in originals.items():
                (study / name).write_text(content, encoding="utf-8")

            initialize_study(ROOT, study, VALID_CONFIG)

            for name, content in originals.items():
                self.assertEqual(content, (study / name).read_text(encoding="utf-8"))

    def test_creates_migrations_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            study = Path(tmp) / "study"
            initialize_study(ROOT, study, VALID_CONFIG)
            self.assertTrue((study / ".ai-tutor" / "migrations").is_dir())

    def test_force_cannot_overwrite_existing_study(self):
        with tempfile.TemporaryDirectory() as tmp:
            study = Path(tmp) / "study"
            initialize_study(ROOT, study, VALID_CONFIG)
            with self.assertRaises(FileExistsError):
                initialize_study(ROOT, study, VALID_CONFIG, force=True)

    def test_conflicting_projection_fails_before_creating_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            study = Path(tmp) / "study"
            study.mkdir()
            (study / "curriculum.md").mkdir()
            with self.assertRaises(FileExistsError):
                initialize_study(ROOT, study, VALID_CONFIG)
            self.assertFalse((study / ".ai-tutor").exists())

    def test_conflicting_study_directory_fails_before_creating_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            study = Path(tmp) / "study"
            study.mkdir()
            lessons = study / "lessons"
            lessons.write_text("preserve me", encoding="utf-8")

            with self.assertRaises(FileExistsError):
                initialize_study(ROOT, study, VALID_CONFIG)

            self.assertFalse((study / ".ai-tutor").exists())
            self.assertEqual("preserve me", lessons.read_text(encoding="utf-8"))

    def test_invalid_packaged_template_fails_before_creating_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            temporary = Path(tmp)
            skill = temporary / "skill"
            shutil.copytree(ROOT / "assets", skill / "assets")
            (skill / "assets" / "templates" / "state.json").write_text(
                "{broken",
                encoding="utf-8",
            )
            study = temporary / "study"

            with self.assertRaises(json.JSONDecodeError):
                initialize_study(skill, study, VALID_CONFIG)

            self.assertFalse((study / ".ai-tutor").exists())

    def test_rejects_non_object_or_boolean_setup_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            for key, value in (("topic", None), ("goal", 4), ("weekly_hours", True)):
                with self.subTest(key=key):
                    config = dict(VALID_CONFIG)
                    config[key] = value
                    with self.assertRaises(ValueError):
                        initialize_study(ROOT, Path(tmp) / key, config)


if __name__ == "__main__":
    unittest.main()
