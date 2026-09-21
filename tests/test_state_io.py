import json
import tempfile
import unittest
from pathlib import Path

from scripts.state_io import RevisionConflict, atomic_update_json


class StateIoTests(unittest.TestCase):
    def test_atomic_update_increments_revision(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            path.write_text(json.dumps({"revision": 0, "value": 0}), encoding="utf-8")
            atomic_update_json(path, lambda payload: {**payload, "value": 1}, expected_revision=0)
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(1, payload["revision"])
            self.assertEqual(1, payload["value"])
            self.assertFalse(path.with_suffix(path.suffix + ".lock").exists())

    def test_stale_revision_conflict_preserves_state_and_cleans_lock(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            path.write_text(json.dumps({"revision": 3, "value": 0}), encoding="utf-8")
            with self.assertRaises(RevisionConflict):
                atomic_update_json(path, lambda payload: {**payload, "value": 1}, expected_revision=2)
            self.assertEqual(0, json.loads(path.read_text(encoding="utf-8"))["value"])
            self.assertFalse(path.with_suffix(path.suffix + ".lock").exists())

    def test_lock_is_cleaned_when_updater_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            path.write_text(json.dumps({"revision": 0}), encoding="utf-8")
            def fail(_payload):
                raise RuntimeError("boom")

            with self.assertRaisesRegex(RuntimeError, "boom"):
                atomic_update_json(path, fail, expected_revision=0)
            self.assertFalse(path.with_suffix(path.suffix + ".lock").exists())

    def test_existing_lock_times_out_without_overwriting(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            path.write_text(json.dumps({"revision": 0}), encoding="utf-8")
            lock = path.with_suffix(path.suffix + ".lock")
            lock.write_text("held", encoding="utf-8")
            with self.assertRaises(TimeoutError):
                atomic_update_json(path, lambda payload: payload, timeout=0.01)
            self.assertTrue(lock.is_file())


if __name__ == "__main__":
    unittest.main()
