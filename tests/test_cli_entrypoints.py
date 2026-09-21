import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.init_study import initialize_study


ROOT = Path(__file__).resolve().parents[1]
CONFIG = {
    "topic": "CLI",
    "goal": "Validar a execução dos entrypoints",
    "deadline": None,
    "weekly_hours": 1,
    "preferred_times": ["flexível"],
    "initial_level": "iniciante",
    "language": "pt-BR",
    "accessibility": [],
    "source_policy": {"prefer_primary": True, "prefer_pt_br": True},
}


class CliEntrypointTests(unittest.TestCase):
    def test_validate_study_script_runs_directly(self):
        with tempfile.TemporaryDirectory() as tmp:
            study = Path(tmp) / "study"
            initialize_study(ROOT, study, CONFIG)
            result = subprocess.run(
                [sys.executable, "-B", str(ROOT / "scripts" / "validate_study.py"), str(study)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("STUDY VALIDATION: PASS", result.stdout)

    def test_projections_script_runs_directly(self):
        with tempfile.TemporaryDirectory() as tmp:
            study = Path(tmp) / "study"
            initialize_study(ROOT, study, CONFIG)
            result = subprocess.run(
                [sys.executable, "-B", str(ROOT / "scripts" / "projections.py"), str(study)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("PROJECTIONS: PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()
