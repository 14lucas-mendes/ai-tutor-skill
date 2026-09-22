"""Validation helpers for complementary educational representations."""

from __future__ import annotations


def validate_representation(artifact: dict, sibling_artifacts: list[dict]) -> list[str]:
    """Validate representation metadata without changing evidence eligibility."""

    representation = artifact.get("representation")
    if representation is None:
        return []
    if not isinstance(representation, dict):
        return ["representation must be an object"]

    errors: list[str] = []
    role = representation.get("role")
    if role not in {"primary", "complementary"}:
        errors.append("representation role must be primary or complementary")
        return errors

    complement_id = representation.get("complements_artifact_id")
    rationale = representation.get("rationale")
    contribution = representation.get("distinct_contribution")
    if role == "primary":
        if complement_id is not None:
            errors.append("primary representation cannot complement another artifact")
        return errors

    if not isinstance(complement_id, str) or not complement_id.strip():
        errors.append("complementary representation requires complements_artifact_id")
    if not isinstance(rationale, str) or not rationale.strip():
        errors.append("complementary representation requires rationale")
    if not isinstance(contribution, str) or not contribution.strip():
        errors.append("complementary representation requires distinct_contribution")

    siblings_by_id = {
        item.get("artifact_id"): item
        for item in sibling_artifacts
        if isinstance(item, dict) and isinstance(item.get("artifact_id"), str)
    }
    primary = siblings_by_id.get(complement_id)
    if not isinstance(primary, dict):
        errors.append("complements_artifact_id must reference a sibling artifact")
    elif primary.get("representation", {}).get("role", "primary") != "primary":
        errors.append("complementary representation must reference a primary artifact")

    all_artifacts_by_id = {
        item.get("artifact_id"): item
        for item in [artifact, *sibling_artifacts]
        if isinstance(item, dict) and isinstance(item.get("artifact_id"), str)
    }
    all_artifacts = list(all_artifacts_by_id.values())
    objective = artifact.get("objective")
    complementary_for_objective = [
        item for item in all_artifacts
        if isinstance(item, dict)
        and item.get("objective") == objective
        and isinstance(item.get("representation"), dict)
        and item["representation"].get("role") == "complementary"
    ]
    if len(complementary_for_objective) > 1:
        errors.append("only one complementary representation is allowed per objective")
    return errors
