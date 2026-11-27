import io
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path

from scripts.cloud_voice import CloudOptions, CloudVoiceError, cache_key, openrouter_wav, speak_cloud

KEY = "sk-or-test-SECRET"
WAV = b"RIFF\x24\x00\x00\x00WAVEfmt " + b"\x00" * 24


class FakeOpener:
    """Records each request and answers with the next scripted reply (bytes or an HTTPError)."""

    def __init__(self, *replies):
        self.replies = list(replies)
        self.requests = []

    def __call__(self, request, timeout=None):
        self.requests.append(request)
        reply = self.replies.pop(0) if self.replies else WAV
        if isinstance(reply, Exception):
            raise reply
        return io.BytesIO(reply)


def http_error(code=402, body=b'{"error": {"message": "Insufficient credits"}}'):
    return urllib.error.HTTPError("https://openrouter.ai/api/v1/audio/speech", code, "error", {}, io.BytesIO(body))


def options(tmp, **extra):
    return CloudOptions(model="google/gemini-2.5-pro-tts", voice="Charon", cache_dir=Path(tmp), **extra)


class RequestTests(unittest.TestCase):
    def test_request_has_model_voice_wav_and_bearer(self):
        with tempfile.TemporaryDirectory() as tmp:
            opener = FakeOpener()
            self.assertEqual(WAV, openrouter_wav("Olá", options(tmp), KEY, opener=opener))
            request = opener.requests[0]
            self.assertEqual("https://openrouter.ai/api/v1/audio/speech", request.full_url)
            self.assertEqual(f"Bearer {KEY}", request.get_header("Authorization"))
            body = json.loads(request.data)
            self.assertEqual({"model": "google/gemini-2.5-pro-tts", "input": "Olá", "voice": "Charon",
                              "response_format": "wav"}, body)

    def test_instructions_are_sent_only_when_given(self):
        with tempfile.TemporaryDirectory() as tmp:
            opener = FakeOpener()
            openrouter_wav("Olá", options(tmp, instructions="calmo"), KEY, opener=opener)
            self.assertEqual("calmo", json.loads(opener.requests[0].data)["instructions"])

    def test_http_error_becomes_cloud_voice_error_without_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(CloudVoiceError) as caught:
                openrouter_wav("Olá", options(tmp), KEY, opener=FakeOpener(http_error()))
            self.assertIn("402", str(caught.exception))
            self.assertIn("Insufficient credits", str(caught.exception))
            self.assertNotIn(KEY, str(caught.exception))

    def test_non_wav_body_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(CloudVoiceError):
                openrouter_wav("Olá", options(tmp), KEY, opener=FakeOpener(b'{"error": "quota"}'))


class CacheAndBatchTests(unittest.TestCase):
    def test_cache_avoids_second_request(self):
        with tempfile.TemporaryDirectory() as tmp:
            opener = FakeOpener()
            out = Path(tmp) / "out"
            out.mkdir()
            speak_cloud([out / "a.wav"], ["Olá"], options(tmp), KEY, opener=opener)
            speak_cloud([out / "b.wav"], ["Olá"], options(tmp), KEY, opener=opener)
            self.assertEqual(1, len(opener.requests))
            self.assertEqual(WAV, (out / "b.wav").read_bytes())

    def test_cache_key_changes_with_voice(self):
        with tempfile.TemporaryDirectory() as tmp:
            charon = options(tmp)
            kore = CloudOptions(model=charon.model, voice="Kore", cache_dir=charon.cache_dir)
            self.assertNotEqual(cache_key("Olá", charon), cache_key("Olá", kore))
            self.assertNotEqual(cache_key("Olá", charon), cache_key("Olá", options(tmp, instructions="calmo")))

    def test_partial_failure_leaves_no_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            out.mkdir()
            paths = [out / "a.wav", out / "b.wav"]
            with self.assertRaises(CloudVoiceError):
                speak_cloud(paths, ["um", "dois"], options(tmp), KEY, opener=FakeOpener(WAV, http_error(500)))
            self.assertEqual([], [p for p in paths if p.exists()])


if __name__ == "__main__":
    unittest.main()
