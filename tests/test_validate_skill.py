import shutil
import tempfile
import unittest
import json
from pathlib import Path

from scripts.validate_skill import validate_skill


ROOT = Path(__file__).resolve().parents[1]


class ValidateSkillTests(unittest.TestCase):
    def test_repository_matches_v2_contract(self):
        self.assertEqual([], validate_skill(ROOT))

    def test_learning_contract_defines_literal_response_assessment(self):
        contract = (ROOT / "references" / "learning-contract.md").read_text(encoding="utf-8").lower()
        required_clauses = [
            "ideia central",
            "contexto",
            "justificativa",
            "limites, condições e riscos",
            "omissão opcional",
            "não inferir afirmações não feitas",
            "autocorreção após feedback",
        ]
        for clause in required_clauses:
            self.assertIn(clause, contract)

    def test_rejects_nested_discoverable_skills(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "package"
            shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns(".git", "__pycache__"))
            nested = root / "skills" / "nested" / "SKILL.md"
            nested.parent.mkdir(parents=True, exist_ok=True)
            nested.write_text(
                "---\nname: nested\ndescription: Use when testing.\n---\n",
                encoding="utf-8",
            )
            errors = validate_skill(root)
            self.assertTrue(any("nested SKILL.md" in error for error in errors), errors)

    def test_rejects_unreachable_local_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "package"
            shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns(".git", "__pycache__"))
            entrypoint = root / "SKILL.md"
            entrypoint.write_text(
                entrypoint.read_text(encoding="utf-8")
                + "\nRead `references/does-not-exist.md`.\n",
                encoding="utf-8",
            )
            errors = validate_skill(root)
            self.assertTrue(any("missing local reference" in error for error in errors), errors)

    def test_rejects_domain_60_transfer_contradiction(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "package"
            shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns(".git", "__pycache__"))
            workflow = root / "references" / "workflows" / "session.md"
            workflow.parent.mkdir(parents=True, exist_ok=True)
            workflow.write_text(
                "Para domínio 60, exija transferência para contexto novo.\n",
                encoding="utf-8",
            )
            errors = validate_skill(root)
            self.assertTrue(any("domain 60" in error for error in errors), errors)

    def test_rejects_non_object_json_template_without_crashing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "package"
            shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns(".git", "__pycache__"))
            (root / "assets" / "templates" / "state.json").write_text("[]", encoding="utf-8")

            errors = validate_skill(root)

            self.assertTrue(any("root must be an object" in error for error in errors), errors)

    def test_behavioral_scenario_catalog_covers_risky_flows(self):
        scenarios = json.loads(
            (ROOT / "tests" / "scenarios" / "behavioral.json").read_text(encoding="utf-8")
        )
        identifiers = {scenario["id"] for scenario in scenarios}
        self.assertEqual({
            "one_off_no_state",
            "batch_setup",
            "resume_interrupted",
            "mastery_60_without_transfer",
            "tutor_solution_not_evidence",
            "atomic_update_failure",
            "sensitive_upload_consent",
            "browser_unavailable_fallback",
            "notebooklm_unavailable_fallback",
            "select_output_by_learning_need",
            "literal_response_assessment",
            "response_feedback_and_omission",
            "protect_cognitive_core",
            "reasoning_ownership",
            "residual_capability",
            "generated_core_is_guided",
            "delegation_readiness",
            "earned_performance_mode",
        }, identifiers)

    def test_adaptive_programming_scenarios_have_expected_and_forbidden_behaviors(self):
        scenarios = json.loads(
            (ROOT / "tests" / "scenarios" / "adaptive-programming.json").read_text(encoding="utf-8")
        )
        self.assertGreaterEqual(len(scenarios), 7)
        identifiers = [scenario["id"] for scenario in scenarios]
        self.assertEqual(len(identifiers), len(set(identifiers)))
        for scenario in scenarios:
            self.assertTrue(scenario["context"])
            self.assertTrue(scenario["expected"])
            self.assertTrue(scenario["forbidden"])

        self.assertIn("fast_mastery_omits_exposition", identifiers)
        self.assertIn("difficulty_increases_scaffolding", identifiers)
        self.assertIn("mixed_modes_within_session", identifiers)
        self.assertIn("time_pressure_protects_learning", identifiers)


if __name__ == "__main__":
    unittest.main()
