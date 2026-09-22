import unittest

from scripts.representation import validate_representation


def artifact(artifact_id="media_a", *, role="primary", complement=None, rationale="", contribution=""):
    return {
        "artifact_id": artifact_id,
        "objective": "Explain loops",
        "representation": {
            "role": role,
            "complements_artifact_id": complement,
            "rationale": rationale,
            "distinct_contribution": contribution,
        },
    }


class RepresentationTests(unittest.TestCase):
    def test_primary_representation_is_valid_without_extra_metadata(self):
        self.assertEqual([], validate_representation({"artifact_id": "media_a", "objective": "Explain loops"}, []))

    def test_complementary_representation_requires_existing_primary_and_contribution(self):
        primary = artifact()
        complementary = artifact(
            "media_b",
            role="complementary",
            complement="media_a",
            rationale="O diagrama torna o fluxo explícito.",
            contribution="Mostra a sequência de itens percorridos.",
        )

        self.assertEqual([], validate_representation(complementary, [primary]))

    def test_repeated_representation_is_rejected_as_missing_distinct_contribution(self):
        repeated = artifact(
            "media_b",
            role="complementary",
            complement="media_a",
            rationale="Repete o texto em áudio.",
        )

        errors = validate_representation(repeated, [artifact()])

        self.assertTrue(any("distinct_contribution" in error for error in errors), errors)

    def test_complement_without_primary_or_with_multiple_complements_is_rejected(self):
        complementary = artifact(
            "media_b",
            role="complementary",
            complement="media_missing",
            rationale="Acrescenta uma relação.",
            contribution="Mostra a sequência.",
        )
        siblings = [
            artifact(),
            artifact("media_c", role="complementary", complement="media_a", rationale="Outra relação.", contribution="Outra relação."),
        ]

        errors = validate_representation(complementary, siblings)

        self.assertTrue(any("primary" in error or "complements_artifact_id" in error for error in errors), errors)
        self.assertTrue(any("one complementary" in error for error in errors), errors)

    def test_invalid_role_is_rejected(self):
        errors = validate_representation(artifact(role="decorative"), [])
        self.assertTrue(any("role" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
