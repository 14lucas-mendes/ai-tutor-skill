import argparse
import contextlib
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path

from scripts.audio_review import validate_audio_script
from scripts.cloud_voice import CloudOptions, CloudVoiceError
from scripts.video_lesson import add_speech_arguments, cloud_options, speak_script_texts, validate_video_script
from tests.test_audio_review import SCRIPT as AUDIO_SCRIPT
from tests.test_cloud_voice import WAV, FakeOpener, http_error
from tests.test_video_lesson import SCRIPT as VIDEO_SCRIPT

ENV = {"OPENROUTER_API_KEY": "sk-or-test"}


def script_with_maps():
    script = copy.deepcopy(VIDEO_SCRIPT)
    script["pronunciation"] = {"Python": "Páiton"}
    script["pronunciation_cloud"] = {"pip": "pipe"}
    return script


class FakePiper:
    def __init__(self):
        self.calls = []

    def __call__(self, jobs, voice="piper", model=None):
        self.calls.append((voice, model, [text for _, text in jobs]))
        for path, _ in jobs:
            path.write_bytes(WAV)
        return [path for path, _ in jobs]


class SpeakScriptTextsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.paths = [self.dir / "a.wav", self.dir / "b.wav"]
        self.cloud = CloudOptions(model="google/gemini-2.5-pro-tts", voice="Charon", cache_dir=self.dir / "cache",
                                  external_ok=True)

    def tearDown(self):
        self.tmp.cleanup()

    def test_openrouter_needs_external_ok(self):
        cloud = CloudOptions(model="m", voice="v", cache_dir=self.dir / "cache")
        with self.assertRaisesRegex(ValueError, "--external-ok"):
            speak_script_texts(self.paths, ["um", "dois"], VIDEO_SCRIPT, voice="openrouter", model=None,
                               cloud=cloud, env=ENV, opener=FakeOpener())

    def test_missing_key_is_a_clear_error(self):
        with self.assertRaisesRegex(ValueError, "OPENROUTER_API_KEY"):
            speak_script_texts(self.paths, ["um", "dois"], VIDEO_SCRIPT, voice="openrouter", model=None,
                               cloud=self.cloud, env={}, opener=FakeOpener())

    def test_cloud_uses_cloud_pronunciation(self):
        opener = FakeOpener()
        used = speak_script_texts(self.paths, ["Python e pip", "dois"], script_with_maps(), voice="openrouter",
                                  model=None, cloud=self.cloud, env=ENV, opener=opener)
        self.assertEqual("openrouter", used)
        self.assertEqual("Python e pipe", json.loads(opener.requests[0].data)["input"])

    def test_piper_uses_piper_pronunciation(self):
        piper = FakePiper()
        used = speak_script_texts(self.paths, ["Python e pip", "dois"], script_with_maps(), voice="piper",
                                  model=Path("v.onnx"), local_speak=piper)
        self.assertEqual("piper", used)
        self.assertEqual(["Páiton e pip", "dois"], piper.calls[0][2])

    def test_failure_falls_back_to_piper_for_all(self):
        piper, err = FakePiper(), io.StringIO()
        with contextlib.redirect_stderr(err):
            used = speak_script_texts(self.paths, ["Python e pip", "dois"], script_with_maps(), voice="openrouter",
                                      model=None, cloud=self.cloud, fallback_model=Path("v.onnx"), env=ENV,
                                      opener=FakeOpener(WAV, http_error(402)), local_speak=piper)
        self.assertEqual("piper", used)
        self.assertEqual([("piper", Path("v.onnx"), ["Páiton e pip", "dois"])], piper.calls)
        self.assertIn("WARNING", err.getvalue())
        self.assertIn("402", err.getvalue())

    def test_failure_without_fallback_raises(self):
        with self.assertRaises(CloudVoiceError):
            speak_script_texts(self.paths, ["um", "dois"], VIDEO_SCRIPT, voice="openrouter", model=None,
                               cloud=self.cloud, env=ENV, opener=FakeOpener(http_error(402)))


class ValidationTests(unittest.TestCase):
    def test_old_scripts_without_cloud_map_validate(self):
        self.assertEqual([], validate_video_script(VIDEO_SCRIPT))
        self.assertEqual([], validate_audio_script(AUDIO_SCRIPT))

    def test_cloud_map_is_validated_in_both_scripts(self):
        video, audio = copy.deepcopy(VIDEO_SCRIPT), copy.deepcopy(AUDIO_SCRIPT)
        video["pronunciation_cloud"] = audio["pronunciation_cloud"] = ["pip"]
        self.assertIn("pronunciation_cloud must map text to spoken text", validate_video_script(video))
        self.assertIn("pronunciation_cloud must map text to spoken text", validate_audio_script(audio))


class CliErrorTests(unittest.TestCase):
    def test_missing_consent_fails_without_traceback(self):
        import subprocess
        import sys

        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "script.json"
            path.write_text(json.dumps(VIDEO_SCRIPT), encoding="utf-8")
            result = subprocess.run([sys.executable, "-B", str(root / "scripts" / "video_lesson.py"), "speak", str(path),
                                     "--out", str(Path(tmp) / "audio"), "--voice", "openrouter", "--cloud-model", "m",
                                     "--cloud-voice", "v"], capture_output=True, text=True, check=False)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("SPEECH: FAIL", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


class ArgumentTests(unittest.TestCase):
    def test_cli_defaults_come_from_env(self):
        env = {"AI_TUTOR_PIPER_MODEL": "v.onnx", "AI_TUTOR_CLOUD_MODEL": "google/gemini-2.5-pro-tts",
               "AI_TUTOR_CLOUD_VOICE": "Charon", "AI_TUTOR_CLOUD_INSTRUCTIONS": "calmo"}
        parser = argparse.ArgumentParser()
        add_speech_arguments(parser, env=env)
        args = parser.parse_args(["--voice", "openrouter", "--external-ok"])
        self.assertEqual((Path("v.onnx"), Path("v.onnx")), (args.model, args.fallback_model))
        options = cloud_options(args)
        self.assertEqual(("google/gemini-2.5-pro-tts", "Charon", "calmo", True),
                         (options.model, options.voice, options.instructions, options.external_ok))

    def test_piper_voice_has_no_cloud_options(self):
        parser = argparse.ArgumentParser()
        add_speech_arguments(parser, env={})
        self.assertIsNone(cloud_options(parser.parse_args([])))


if __name__ == "__main__":
    unittest.main()
