import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.migrate_state import migrate
from scripts.init_study import initialize_study


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "v1-study"
CONFIG = {
    "topic": "AI",
    "goal": "Learn",
    "deadline": None,
    "weekly_hours": 2,
    "preferred_times": ["weekend"],
    "initial_level": "basic",
    "language": "pt-BR",
    "accessibility": [],
    "source_policy": {},
}


def snapshot(root: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.study = Path(self.temp.name) / "legacy study"
        shutil.copytree(FIXTURE, self.study)

    def tearDown(self):
        self.temp.cleanup()

    def test_dry_run_does_not_write(self):
        before = snapshot(self.study)
        report = migrate(self.study, dry_run=True)
        self.assertEqual(before, snapshot(self.study))
        self.assertTrue(report.valid)
        self.assertTrue(report.changed)

    def test_migration_is_idempotent(self):
        first = migrate(self.study)
        once = snapshot(self.study)
        second = migrate(self.study)
        self.assertEqual(once, snapshot(self.study))
        self.assertTrue(first.changed)
        self.assertFalse(second.changed)

    def test_preserves_observation_without_inventing_evidence(self):
        migrate(self.study)
        state = json.loads((self.study / ".ai-tutor" / "state.json").read_text(encoding="utf-8"))
        self.assertEqual([], state["evidences"])
        self.assertEqual(40, state["topics"][0]["mastery"])
        self.assertIn("Ainda confunde retorno", state["topics"][0]["notes"])

    def test_keeps_recoverable_backup(self):
        migrate(self.study)
        backup = self.study / ".ai-tutor" / "migrations" / "v1-backup"
        self.assertTrue((backup / "progress.json").is_file())
        self.assertEqual((FIXTURE / "progress.json").read_bytes(), (backup / "progress.json").read_bytes())

    def test_migration_creates_empty_canonical_registries(self):
        report = migrate(self.study)
        self.assertTrue(report.valid)
        state = json.loads((self.study / ".ai-tutor" / "state.json").read_text(encoding="utf-8"))
        for name, collection in (("cards.json", "cards"), ("sources.json", "sources")):
            payload = json.loads((self.study / ".ai-tutor" / name).read_text(encoding="utf-8"))
            self.assertEqual(state["study_id"], payload["study_id"])
            self.assertEqual([], payload[collection])
        media = json.loads((self.study / ".ai-tutor" / "media-index.json").read_text(encoding="utf-8"))
        self.assertEqual(0, media["revision"])

    def test_invalid_v2_state_is_not_treated_as_already_migrated(self):
        metadata = self.study / ".ai-tutor"
        metadata.mkdir()
        malformed = {
            "schema_version": 2,
            "study_id": "study_x",
            "topics": [{"topic_id": "topic_x"}, {"topic_id": "topic_x"}],
        }
        (metadata / "state.json").write_text(json.dumps(malformed), encoding="utf-8")

        report = migrate(self.study)

        self.assertFalse(report.valid)
        self.assertFalse(report.changed)
        self.assertTrue(any("duplicate id" in warning for warning in report.warnings))
        self.assertEqual(malformed, json.loads((metadata / "state.json").read_text(encoding="utf-8")))

    def test_corrupt_existing_state_blocks_legacy_migration(self):
        metadata = self.study / ".ai-tutor"
        metadata.mkdir()
        state_path = metadata / "state.json"
        state_path.write_text("{broken", encoding="utf-8")
        before = snapshot(self.study)

        report = migrate(self.study)

        self.assertFalse(report.valid)
        self.assertFalse(report.changed)
        self.assertTrue(any("unreadable" in warning for warning in report.warnings))
        self.assertEqual(before, snapshot(self.study))

    def test_metadata_file_blocks_legacy_migration_without_overwrite(self):
        metadata = self.study / ".ai-tutor"
        metadata.write_text("preserve me", encoding="utf-8")
        before = snapshot(self.study)

        report = migrate(self.study)

        self.assertFalse(report.valid)
        self.assertFalse(report.changed)
        self.assertTrue(any("not a directory" in warning for warning in report.warnings), report)
        self.assertEqual(before, snapshot(self.study))

    def test_upgrades_valid_v2_with_missing_canonical_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            study = Path(tmp) / "v2 study"
            initialize_study(ROOT, study, CONFIG)
            metadata = study / ".ai-tutor"
            (metadata / "cards.json").unlink()
            (metadata / "sources.json").unlink()
            media = json.loads((metadata / "media-index.json").read_text(encoding="utf-8"))
            media.pop("revision", None)
            (metadata / "media-index.json").write_text(json.dumps(media), encoding="utf-8")

            report = migrate(study)

            self.assertTrue(report.valid)
            self.assertTrue(report.changed)
            self.assertTrue((metadata / "cards.json").is_file())
            self.assertTrue((metadata / "sources.json").is_file())
            self.assertTrue((metadata / "migrations").is_dir())
            self.assertEqual(0, json.loads((metadata / "media-index.json").read_text())["revision"])

    def test_v2_upgrade_adds_fixed_spacing_policy_without_changing_learning_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            study = Path(tmp) / "v2 study"
            initialize_study(ROOT, study, CONFIG)
            metadata = study / ".ai-tutor"
            config_path = metadata / "study-config.json"
            config = json.loads(config_path.read_text(encoding="utf-8"))
            config.pop("spacing_policy", None)
            config_path.write_text(json.dumps(config), encoding="utf-8")
            state_before = json.loads((metadata / "state.json").read_text(encoding="utf-8"))

            report = migrate(study)

            self.assertTrue(report.valid)
            migrated_config = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertEqual({"mode": "fixed", "target_horizon_days": None}, migrated_config["spacing_policy"])
            self.assertEqual(state_before, json.loads((metadata / "state.json").read_text(encoding="utf-8")))

    def test_rejects_invalid_v2_support_files_without_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            study = Path(tmp) / "v2 study"
            initialize_study(ROOT, study, CONFIG)
            cards_path = study / ".ai-tutor" / "cards.json"
            cards = json.loads(cards_path.read_text(encoding="utf-8"))
            cards["cards"] = [{}]
            cards_path.write_text(json.dumps(cards), encoding="utf-8")
            before = snapshot(study)

            report = migrate(study)

            self.assertFalse(report.valid)
            self.assertFalse(report.changed)
            self.assertTrue(any("cards" in warning for warning in report.warnings))
            self.assertEqual(before, snapshot(study))

    def test_rejects_v2_study_missing_configuration(self):
        with tempfile.TemporaryDirectory() as tmp:
            study = Path(tmp) / "v2 study"
            initialize_study(ROOT, study, CONFIG)
            (study / ".ai-tutor" / "study-config.json").unlink()
            before = snapshot(study)

            report = migrate(study)

            self.assertFalse(report.valid)
            self.assertFalse(report.changed)
            self.assertTrue(any("study-config.json" in warning for warning in report.warnings), report)
            self.assertEqual(before, snapshot(study))

    def test_rejects_legacy_study_with_invalid_configuration_without_writing(self):
        progress_path = self.study / "progress.json"
        progress = json.loads(progress_path.read_text(encoding="utf-8"))
        progress["objetivo_especifico"] = ""
        progress_path.write_text(json.dumps(progress), encoding="utf-8")
        before = snapshot(self.study)

        report = migrate(self.study)

        self.assertFalse(report.valid)
        self.assertFalse(report.changed)
        self.assertTrue(any("goal" in warning for warning in report.warnings), report)
        self.assertEqual(before, snapshot(self.study))

    def test_rejects_malformed_legacy_collections_without_writing(self):
        progress_path = self.study / "progress.json"
        progress = json.loads(progress_path.read_text(encoding="utf-8"))
        progress["pontos_fracos"] = "not-a-list"
        progress_path.write_text(json.dumps(progress), encoding="utf-8")
        before = snapshot(self.study)

        report = migrate(self.study)

        self.assertFalse(report.valid)
        self.assertFalse(report.changed)
        self.assertTrue(any("pontos_fracos" in warning for warning in report.warnings), report)
        self.assertEqual(before, snapshot(self.study))

    def test_upgrades_support_files_missing_revision(self):
        with tempfile.TemporaryDirectory() as tmp:
            study = Path(tmp) / "v2 study"
            initialize_study(ROOT, study, CONFIG)
            metadata = study / ".ai-tutor"
            for name in ("cards.json", "sources.json", "media-index.json"):
                path = metadata / name
                payload = json.loads(path.read_text(encoding="utf-8"))
                payload.pop("revision", None)
                path.write_text(json.dumps(payload), encoding="utf-8")

            report = migrate(study)

            self.assertTrue(report.valid)
            self.assertTrue(report.changed)
            for name in ("cards.json", "sources.json", "media-index.json"):
                self.assertEqual(0, json.loads((metadata / name).read_text())["revision"])

    def test_v2_dry_run_does_not_write_support_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            study = Path(tmp) / "v2 study"
            initialize_study(ROOT, study, CONFIG)
            metadata = study / ".ai-tutor"
            (metadata / "cards.json").unlink()
            before = {
                str(path.relative_to(study)): path.read_bytes()
                for path in study.rglob("*") if path.is_file()
            }

            report = migrate(study, dry_run=True)

            self.assertTrue(report.valid)
            self.assertTrue(report.changed)
            after = {
                str(path.relative_to(study)): path.read_bytes()
                for path in study.rglob("*") if path.is_file()
            }
            self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
