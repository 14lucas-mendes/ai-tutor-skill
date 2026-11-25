import json
import tempfile
import unittest
from pathlib import Path

from scripts.course_check import check_course, course_path_error
from scripts.init_study import initialize_study


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

GOOD_PAGE = """# Aula 1: decompor

> origem: `lesson_a` · tempo sugerido: 2 h

## Exercícios

Cada evidência tem `evidence_id` e `topic_id`, com dados fictícios como `evidence_x1`.

<details><summary>Gabarito</summary>

resposta

</details>

Veja a [Aula 2](02.md).
"""


class CourseCheckTests(unittest.TestCase):
    def make_study(self, tmp, *, policy={"path": "curso"}, lesson_status="completed"):
        study = Path(tmp) / "study"
        initialize_study(ROOT, study, CONFIG)
        metadata = study / ".ai-tutor"
        config_path = metadata / "study-config.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        if policy is not None:
            config["course_policy"] = policy
        config_path.write_text(json.dumps(config), encoding="utf-8")
        state_path = metadata / "state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["lessons"] = [
            {"lesson_id": "lesson_a", "status": lesson_status},
            {"lesson_id": "lesson_b", "status": "completed"},
        ]
        state["evidences"] = [{"evidence_id": "evidence_real_01"}]
        state["sessions"] = [{"session_id": "session_2026-11-20-real"}]
        state["weak_points"] = [{"weak_point_id": "weak_real_01"}]
        state["diagnostics"] = [
            {"diagnostic_id": "diagnostic_real_01", "observations": [{"observation_id": "observation_real_01"}]}
        ]
        state_path.write_text(json.dumps(state), encoding="utf-8")
        course = study / "curso"
        course.mkdir()
        (course / "README.md").write_text("# Curso\n\n[Aula 1](01.md)\n", encoding="utf-8")
        (course / "01.md").write_text(GOOD_PAGE, encoding="utf-8")
        (course / "02.md").write_text(GOOD_PAGE.replace("`lesson_a`", "`lesson_b`"), encoding="utf-8")
        return study

    def test_valid_course_passes_and_field_names_are_not_private(self):
        with tempfile.TemporaryDirectory() as tmp:
            errors, notice = check_course(self.make_study(tmp))
            self.assertEqual([], errors)
            self.assertIsNone(notice)

    def test_without_course_policy_there_is_nothing_to_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            errors, notice = check_course(self.make_study(tmp, policy=None))
            self.assertEqual([], errors)
            self.assertIn("no course_policy", notice)

    def test_source_lesson_must_be_completed(self):
        with tempfile.TemporaryDirectory() as tmp:
            errors, _ = check_course(self.make_study(tmp, lesson_status="in_progress"))
            self.assertTrue(any("not completed: lesson_a" in error for error in errors), errors)

    def test_page_without_source_lesson_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            study = self.make_study(tmp)
            (study / "curso" / "01.md").write_text(GOOD_PAGE.replace("`lesson_a`", "a lição 15"), encoding="utf-8")
            errors, _ = check_course(study)
            self.assertTrue(any("01.md: no source lesson ID" in error for error in errors), errors)

    def test_real_study_ids_are_rejected_everywhere(self):
        with tempfile.TemporaryDirectory() as tmp:
            study = self.make_study(tmp)
            page = GOOD_PAGE + "\nVer evidence_real_01 e session_2026-11-20-real.\n"
            (study / "curso" / "01.md").write_text(page, encoding="utf-8")
            (study / "curso" / "README.md").write_text("# Curso\n\nobservation_real_01\n", encoding="utf-8")
            errors, _ = check_course(study)
            joined = "\n".join(errors)
            self.assertIn("evidence_real_01", joined)
            self.assertIn("session_2026-11-20-real", joined)
            self.assertIn("README.md: contains a private study ID: observation_real_01", joined)

    def test_answers_must_be_in_balanced_details(self):
        with tempfile.TemporaryDirectory() as tmp:
            study = self.make_study(tmp)
            (study / "curso" / "01.md").write_text(GOOD_PAGE.replace("</details>", ""), encoding="utf-8")
            (study / "curso" / "02.md").write_text(
                GOOD_PAGE.replace("`lesson_a`", "`lesson_b`").replace("<details><summary>Gabarito</summary>", "").replace("</details>", ""),
                encoding="utf-8",
            )
            errors, _ = check_course(study)
            self.assertTrue(any("01.md: unbalanced <details>" in error for error in errors), errors)
            self.assertTrue(any("02.md: no <details>" in error for error in errors), errors)

    def test_broken_relative_link_fails_and_external_links_are_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            study = self.make_study(tmp)
            page = GOOD_PAGE + "\n[externo](https://example.com) [âncora](#x) [falta](03.md#parte)\n"
            (study / "curso" / "01.md").write_text(page, encoding="utf-8")
            errors, _ = check_course(study)
            self.assertEqual(["01.md: broken link: 03.md#parte"], errors)

    def test_course_path_must_be_relative_and_inside_the_study(self):
        for value, valid in (
            ("curso", True),
            ("docs/curso", True),
            ("", False),
            ("../curso", False),
            ("/tmp/curso", False),
            ("C:\\curso", False),
            (".ai-tutor/curso", False),
            (["curso"], False),
        ):
            with self.subTest(value=value):
                self.assertEqual(valid, course_path_error(value) is None)


if __name__ == "__main__":
    unittest.main()
