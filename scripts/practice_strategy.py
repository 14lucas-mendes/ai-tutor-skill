"""Deterministic gate for blocked and conditional interleaved practice."""

from __future__ import annotations


def _blocked(topic_ids: list[str], reason: str) -> dict:
    return {
        "mode": "blocked",
        "topic_ids": topic_ids,
        "topic_label_visible": True,
        "reason": reason,
    }


def choose_practice_strategy(
    topics: list[dict],
    weak_points: list[dict],
    required_topic_ids: list[str],
) -> dict:
    """Choose interleaving only after the minimum readiness gate is met."""

    topic_map = {
        item.get("topic_id"): item
        for item in topics
        if isinstance(item, dict) and isinstance(item.get("topic_id"), str)
    }
    selected = list(dict.fromkeys(required_topic_ids))
    missing = [topic_id for topic_id in selected if topic_id not in topic_map]
    if missing:
        return _blocked(selected, f"unknown topic: {missing[0]}")
    if len(selected) < 2:
        return _blocked(selected, "interleaving requires at least two related topics")

    for topic_id in selected:
        topic = topic_map[topic_id]
        if topic.get("mastery", 0) < 40:
            return _blocked(selected, f"topic below minimum mastery: {topic_id}")
        if topic.get("independent_application_count", 0) < 1:
            return _blocked(selected, f"topic lacks independent application: {topic_id}")

    for weak_point in weak_points:
        if not isinstance(weak_point, dict) or weak_point.get("status") != "active":
            continue
        if weak_point.get("topic_id") in selected and weak_point.get("is_prerequisite") is True:
            return _blocked(selected, f"active prerequisite weak point: {weak_point['topic_id']}")

    return {
        "mode": "interleaved",
        "topic_ids": selected,
        "topic_label_visible": False,
        "reason": "all selected topics meet the minimum readiness gate",
    }
