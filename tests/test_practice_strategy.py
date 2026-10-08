import unittest

from scripts.practice_strategy import choose_practice_strategy


def topics(*, mastery=60, applications=1):
    return [
        {
            "topic_id": "topic_a",
            "name": "Loops",
            "mastery": mastery,
            "independent_application_count": applications,
        },
        {
            "topic_id": "topic_b",
            "name": "Funções",
            "mastery": mastery,
            "independent_application_count": applications,
        },
    ]


class PracticeStrategyTests(unittest.TestCase):
    def test_mature_related_topics_can_be_interleaved(self):
        strategy = choose_practice_strategy(topics(), [], ["topic_a", "topic_b"])

        self.assertEqual("interleaved", strategy["mode"])
        self.assertEqual(["topic_a", "topic_b"], strategy["topic_ids"])
        self.assertFalse(strategy["topic_label_visible"])

    def test_immature_topic_forces_blocked_practice(self):
        strategy = choose_practice_strategy(topics(mastery=20), [], ["topic_a", "topic_b"])

        self.assertEqual("blocked", strategy["mode"])
        self.assertTrue(strategy["topic_label_visible"])
        self.assertIn("mastery", strategy["reason"])

    def test_active_prerequisite_weak_point_blocks_interleaving(self):
        weak_points = [{
            "weak_point_id": "weak_a",
            "topic_id": "topic_a",
            "status": "active",
            "is_prerequisite": True,
        }]

        strategy = choose_practice_strategy(topics(), weak_points, ["topic_a", "topic_b"])

        self.assertEqual("blocked", strategy["mode"])
        self.assertIn("prerequisite", strategy["reason"])

    def test_missing_independent_application_blocks_interleaving(self):
        strategy = choose_practice_strategy(topics(applications=0), [], ["topic_a", "topic_b"])

        self.assertEqual("blocked", strategy["mode"])
        self.assertIn("application", strategy["reason"])

    def test_one_topic_never_interleaves(self):
        strategy = choose_practice_strategy(topics()[:1], [], ["topic_a"])

        self.assertEqual("blocked", strategy["mode"])
        self.assertEqual(["topic_a"], strategy["topic_ids"])

    def test_unknown_required_topic_is_safe_blocked_fallback(self):
        strategy = choose_practice_strategy(topics(), [], ["topic_missing", "topic_a"])

        self.assertEqual("blocked", strategy["mode"])
        self.assertIn("unknown", strategy["reason"])


if __name__ == "__main__":
    unittest.main()
