import http.client
import io
import json
import struct
import tempfile
import unittest
import urllib.error
import wave
from pathlib import Path

from scripts.cloud_voice import CloudOptions, CloudVoiceError, cache_key, openrouter_wav, speak_cloud

KEY = "sk-or-test-SECRET"
def make_wav(rate=24000, frames=240, width=2, channels=1) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as handle:
        handle.setnchannels(channels)
        handle.setsampwidth(width)
        handle.setframerate(rate)
        handle.writeframes(b"\x01\x00" * frames * channels if width == 2 else b"\x01" * frames * channels)
    return buffer.getvalue()


WAV = make_wav()


def streaming(audio: bytes) -> bytes:
    """The same WAV with the RIFF and data sizes set to 0xFFFFFFFF, as a streaming encoder writes them."""

    data = bytearray(audio)
    data[4:8] = b"\xff\xff\xff\xff"
    data[40:44] = b"\xff\xff\xff\xff"
    return bytes(data)


def float_wav() -> bytes:
    data = bytearray(WAV)
    data[20:22] = struct.pack("<H", 3)
    return bytes(data)


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
    extra.setdefault("external_ok", True)
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


class WavCheckTests(unittest.TestCase):
    def frames(self, audio):
        with wave.open(io.BytesIO(audio)) as handle:
            return handle.getnframes()

    def test_streaming_header_is_normalized(self):
        with tempfile.TemporaryDirectory() as tmp:
            audio = openrouter_wav("Olá", options(tmp), KEY, opener=FakeOpener(streaming(WAV)))
            self.assertEqual(240, self.frames(audio))

    def test_float_and_empty_wavs_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            for bad in (float_wav(), make_wav(frames=0), make_wav(width=1)):
                with self.assertRaises(CloudVoiceError):
                    openrouter_wav("Olá", options(tmp), KEY, opener=FakeOpener(bad))

    def test_network_protocol_errors_become_cloud_voice_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(CloudVoiceError):
                openrouter_wav("Olá", options(tmp), KEY, opener=FakeOpener(http.client.IncompleteRead(b"")))

    def test_empty_key_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(CloudVoiceError):
                openrouter_wav("Olá", options(tmp), "", opener=FakeOpener())


class CacheAndBatchTests(unittest.TestCase):
    def test_speak_cloud_requires_consent(self):
        with tempfile.TemporaryDirectory() as tmp:
            opener = FakeOpener()
            no_consent = CloudOptions(model="m", voice="v", cache_dir=Path(tmp))
            with self.assertRaises(CloudVoiceError):
                speak_cloud([Path(tmp) / "a.wav"], ["Olá"], no_consent, KEY, opener=opener)
            self.assertEqual([], opener.requests)

    def test_corrupt_cache_is_fetched_again(self):
        with tempfile.TemporaryDirectory() as tmp:
            opts = options(tmp)
            (Path(tmp) / f"{cache_key('Olá', opts)}.wav").write_bytes(b"RIFF broken")
            opener = FakeOpener()
            speak_cloud([Path(tmp) / "a.wav"], ["Olá"], opts, KEY, opener=opener)
            self.assertEqual(1, len(opener.requests))
            self.assertEqual(240, WavCheckTests.frames(None, (Path(tmp) / "a.wav").read_bytes()))

    def test_mixed_formats_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            out.mkdir()
            with self.assertRaises(CloudVoiceError):
                speak_cloud([out / "a.wav", out / "b.wav"], ["um", "dois"], options(tmp), KEY,
                            opener=FakeOpener(make_wav(24000), make_wav(16000)))

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
            kore = CloudOptions(model=charon.model, voice="Kore", cache_dir=charon.cache_dir, external_ok=True)
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
