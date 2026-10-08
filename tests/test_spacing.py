import unittest
from datetime import datetime, timezone

from scripts.spaced_repetition import schedule_card


def card(*, step=1, interval=3, difficulty="medium"):
    return {
        "card_id": "card_a",
        "difficulty": difficulty,
        "spaced_repetition_step": step,
        "interval_days": interval,
        "review_count": 2,
        "objective_correctness": None,
        "last_result": None,
        "confidence": None,
        "updated_at": "2026-09-22T12:00:00Z",
        "due_at": "2026-09-25T12:00:00Z",
    }


REVIEWED_AT = datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc)


class SpacingTests(unittest.TestCase):
    def test_fixed_mode_keeps_the_existing_interval_ladder(self):
        updated = schedule_card(
            card(step=1, interval=3),
            policy={"mode": "fixed", "target_horizon_days": None},
            result="correct",
            confidence=100,
            reviewed_at=REVIEWED_AT,
        )

        self.assertEqual(2, updated["spaced_repetition_step"])
        self.assertEqual(7, updated["interval_days"])
        self.assertEqual("2026-09-29T12:00:00Z", updated["due_at"])

    def test_adaptive_correct_uses_difficulty_and_confidence(self):
        updated = schedule_card(
            card(step=1, interval=3, difficulty="easy"),
            policy={"mode": "adaptive", "target_horizon_days": None},
            result="correct",
            confidence=90,
            reviewed_at=REVIEWED_AT,
        )

        self.assertEqual(6, updated["interval_days"])
        self.assertEqual("correct", updated["last_result"])
        self.assertTrue(updated["objective_correctness"])

    def test_adaptive_partial_reduces_interval_without_resetting_step(self):
        updated = schedule_card(
            card(step=3, interval=16),
            policy={"mode": "adaptive", "target_horizon_days": None},
            result="partial",
            confidence=70,
            reviewed_at=REVIEWED_AT,
        )

        self.assertEqual(3, updated["spaced_repetition_step"])
        self.assertEqual(12, updated["interval_days"])
        self.assertIsNone(updated["objective_correctness"])

    def test_failure_resets_interval_and_low_confidence_caps_growth(self):
        failed = schedule_card(
            card(step=4, interval=35),
            policy={"mode": "adaptive", "target_horizon_days": None},
            result="failed",
            confidence=80,
            reviewed_at=REVIEWED_AT,
        )
        low_confidence = schedule_card(
            card(step=1, interval=3, difficulty="easy"),
            policy={"mode": "adaptive", "target_horizon_days": None},
            result="correct",
            confidence=40,
            reviewed_at=REVIEWED_AT,
        )

        self.assertEqual((1, 1), (failed["spaced_repetition_step"], failed["interval_days"]))
        self.assertEqual(4, low_confidence["interval_days"])

    def test_adaptive_schedule_respects_target_horizon(self):
        updated = schedule_card(
            card(step=4, interval=35, difficulty="easy"),
            policy={"mode": "adaptive", "target_horizon_days": 10},
            result="correct",
            confidence=100,
            reviewed_at=REVIEWED_AT,
        )

        self.assertEqual(10, updated["interval_days"])

    def test_invalid_policy_and_result_are_rejected(self):
        with self.assertRaises(ValueError):
            schedule_card(card(), policy={"mode": "unknown"}, result="correct", confidence=50, reviewed_at=REVIEWED_AT)
        with self.assertRaises(ValueError):
            schedule_card(card(), policy={"mode": "fixed"}, result="unknown", confidence=50, reviewed_at=REVIEWED_AT)


if __name__ == "__main__":
    unittest.main()
