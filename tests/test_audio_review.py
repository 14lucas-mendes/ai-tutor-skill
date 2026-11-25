import copy
import json
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path

from scripts.audio_review import (
    GAP_AFTER_ANSWER,
    GAP_AFTER_SAY,
    GAP_BEFORE_TONE,
    TONE_SECONDS,
    assemble_audio,
    format_transcript,
    plan_audio,
    screen_warnings,
    spoken_texts,
    tone,
    validate_audio_script,
)


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = {
    "schema_version": 1,
    "kind": "audio",
    "title": "Review: modules",
    "lesson_id": "lesson_01-modules",
    "source_ids": ["source_python-modules"],
    "segments": [
        {"type": "say", "text": "Answer during the pause."},
        {"type": "recall", "question": "How many times does a module run?", "pause_seconds": 6,
         "answer": "Once per name."},
        {"type": "questions", "intro": "To finish:", "items": ["Where should the model live?"], "outro": "The end."},
    ],
}
SUMMARY = {
    "schema_version": 1,
    "kind": "audio",
    "style": "summary",
    "title": "Summary: modules",
    "lesson_id": "lesson_01-modules",
    "source_ids": ["source_python-modules"],
    "segments": [
        {"type": "say", "text": "A module is a Python file."},
        {"type": "say", "text": "It runs once per name."},
    ],
}


class ValidationTests(unittest.TestCase):
    def test_valid_script_passes(self):
        self.assertEqual([], validate_audio_script(SCRIPT))

    def test_needs_kind_audio_and_a_recall(self):
        script = copy.deepcopy(SCRIPT)
        script["kind"] = "video"
        del script["segments"][1]
        errors = validate_audio_script(script)
        self.assertIn("kind must be audio", errors)
        self.assertIn("an audio review needs at least one recall segment", errors)

    def test_questions_must_close_the_review(self):
        script = copy.deepcopy(SCRIPT)
        script["segments"].append({"type": "say", "text": "Bonus."})
        errors = validate_audio_script(script)
        self.assertIn("segment 3: questions must be the last segment", errors)
        self.assertIn("the last segment must be questions, without answers", errors)

    def test_pause_range_and_texts(self):
        script = copy.deepcopy(SCRIPT)
        script["segments"][1]["pause_seconds"] = 0
        script["segments"][1]["answer"] = ""
        errors = validate_audio_script(script)
        self.assertIn("segment 2: pause_seconds must be between 1 and 30", errors)
        self.assertIn("segment 2: answer must be non-empty text", errors)

    def test_labels_only_override_known_keys(self):
        script = copy.deepcopy(SCRIPT)
        script["labels"] = {"question": "Pergunta: ", "beep": "x"}
        self.assertTrue(any(e.startswith("labels may only override") for e in validate_audio_script(script)))

    def test_screen_references_are_warnings(self):
        script = copy.deepcopy(SCRIPT)
        script["segments"][1]["answer"] = "Esta linha roda uma vez."
        self.assertEqual([], validate_audio_script(script))
        self.assertEqual(["points at a screen: 'Esta linha roda uma vez.'"], screen_warnings(script))


class SummaryStyleTests(unittest.TestCase):
    def test_summary_needs_no_recall_or_questions(self):
        self.assertEqual([], validate_audio_script(SUMMARY))

    def test_summary_may_close_with_questions(self):
        script = copy.deepcopy(SUMMARY)
        script["segments"].append({"type": "questions", "items": ["Where should the model live?"]})
        self.assertEqual([], validate_audio_script(script))

    def test_summary_rejects_recall_blocks(self):
        script = copy.deepcopy(SUMMARY)
        script["segments"].insert(1, copy.deepcopy(SCRIPT["segments"][1]))
        self.assertIn("a summary has no recall segments; use the recall style for question and answer blocks",
                      validate_audio_script(script))

    def test_summary_needs_a_say_and_questions_stay_last(self):
        script = copy.deepcopy(SUMMARY)
        script["segments"] = [{"type": "questions", "items": ["Why?"]}, {"type": "questions", "items": ["How?"]}]
        errors = validate_audio_script(script)
        self.assertIn("a summary needs at least one say segment", errors)
        self.assertIn("segment 1: questions must be the last segment", errors)

    def test_unknown_style_fails(self):
        script = copy.deepcopy(SCRIPT)
        script["style"] = "podcast"
        self.assertIn("style must be one of ['recall', 'summary']", validate_audio_script(script))

    def test_summary_plan_is_speech_and_gaps_only(self):
        self.assertEqual([("speech", "A module is a Python file.", ""), ("silence", GAP_AFTER_SAY, None),
                          ("speech", "It runs once per name.", ""), ("silence", GAP_AFTER_SAY, None)],
                         plan_audio(SUMMARY))


class PlanTests(unittest.TestCase):
    def test_recall_order_is_question_tone_pause_answer(self):
        kinds = [piece[0] for piece in plan_audio(SCRIPT)]
        self.assertEqual(["speech", "silence", "speech", "silence", "tone", "silence", "speech", "silence"], kinds[:8])

    def test_spoken_texts_follow_playback(self):
        self.assertEqual(["Answer during the pause.", "How many times does a module run?", "Once per name.",
                          "To finish:", "Where should the model live?", "The end."], spoken_texts(SCRIPT))

    def test_labels_can_be_localized(self):
        script = copy.deepcopy(SCRIPT)
        script["labels"] = {"question": "Pergunta: ", "pause": "[sinal e {seconds} s de pausa]"}
        pieces = plan_audio(script)
        self.assertIn(("speech", "How many times does a module run?", "Pergunta: "), pieces)
        self.assertIn(("silence", 6, "[sinal e 6 s de pausa]"), pieces)

    def test_tone_has_expected_length_and_bounds(self):
        data = tone(16000)
        self.assertEqual(int(TONE_SECONDS * 16000) * 2, len(data))
        samples = struct.unpack(f"<{len(data) // 2}h", data)
        self.assertLessEqual(max(abs(s) for s in samples), 32767)
        self.assertEqual(0, samples[0])

    def test_transcript_times(self):
        speech = [2.0, 3.0, 1.0, 1.0, 2.0, 1.0]
        text, total = format_transcript("T", plan_audio(SCRIPT), speech)
        lines = text.splitlines()
        self.assertEqual("[00:00] Answer during the pause.", lines[2])
        self.assertEqual("[00:03] Question: How many times does a module run?", lines[3])
        self.assertEqual("[00:06] [tone and 6 s pause]", lines[4])
        expected_total = sum(speech) + GAP_AFTER_SAY + GAP_BEFORE_TONE + TONE_SECONDS + 6 + GAP_AFTER_ANSWER + 0.5 + 4.0
        self.assertAlmostEqual(expected_total, total)


class CliTests(unittest.TestCase):
    def run_cli(self, script):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "script.json"
            path.write_text(json.dumps(script), encoding="utf-8")
            return subprocess.run([sys.executable, "-I", "-B", str(ROOT / "scripts" / "audio_review.py"), "validate", str(path)],
                                  cwd=ROOT, capture_output=True, text=True, check=False)

    def test_validate_runs_directly_and_isolated(self):
        result = self.run_cli(SCRIPT)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("AUDIO SCRIPT: PASS", result.stdout)

    def test_validate_accepts_a_summary(self):
        result = self.run_cli(SUMMARY)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("AUDIO SCRIPT: PASS", result.stdout)

    def test_validate_fails_on_bad_script(self):
        result = self.run_cli({"schema_version": 1, "kind": "audio"})
        self.assertNotEqual(0, result.returncode)
        self.assertIn("AUDIO SCRIPT: FAIL", result.stderr)


def _has_mp3_encoder() -> bool:
    if shutil.which("ffmpeg") is None:
        return False
    result = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True, check=False)
    return "libmp3lame" in result.stdout


@unittest.skipUnless(_has_mp3_encoder(), "ffmpeg with libmp3lame is optional")
class AssembleTests(unittest.TestCase):
    def test_assembles_mp3_from_speech_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            wavs = []
            for n, _ in enumerate(spoken_texts(SCRIPT)):
                path = work / f"{n}.wav"
                with wave.open(str(path), "wb") as handle:
                    handle.setnchannels(1)
                    handle.setsampwidth(2)
                    handle.setframerate(16000)
                    handle.writeframes(b"\x00\x00" * 16000)
                wavs.append(path)
            out = work / "review.mp3"
            seconds = assemble_audio(plan_audio(SCRIPT), wavs, out, "T")
            self.assertTrue(out.is_file() and out.stat().st_size > 0)
            _, total = format_transcript("T", plan_audio(SCRIPT), [1.0] * len(wavs))
            self.assertAlmostEqual(total, seconds, places=2)


if __name__ == "__main__":
    unittest.main()
