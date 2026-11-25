import copy
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path

from scripts.video_lesson import (
    build_pronouncer,
    build_timeline,
    concat_list,
    format_srt,
    iter_steps,
    render_video,
    speech_match,
    spoken_lines,
    srt_timestamp,
    validate_video_script,
)


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = {
    "schema_version": 1,
    "title": "Modules",
    "lesson_id": "lesson_01-modules",
    "source_ids": ["source_python-modules"],
    "pronunciation": {"import": "ímport", "pip install -e .": "pip instól traço i ponto", "-e": "traço i"},
    "scenes": [
        {"type": "title", "title": "Modules", "subtitle": "Part 1",
         "steps": [{"say": "A module is a file that other files import."}]},
        {"type": "list", "title": "Levels", "items": ["Module", "Package"],
         "steps": [{"show": 1, "say": "First, the module."}, {"show": 2, "say": "Then, the package."}]},
        {"type": "flow", "title": "Import", "note": "Not found: ModuleNotFoundError",
         "boxes": [{"label": "1. Find", "detail": "sys.path"}, {"label": "2. Run", "detail": "once per name"}],
         "steps": [{"active": 1, "say": "It looks in the search path."},
                   {"active": 0, "note": True, "say": "If nothing is found, the error is ModuleNotFoundError."}]},
        {"type": "code", "title": "A module", "file": "conv.py", "language": "python",
         "code": "def f(c):\n    return c * 9 / 5 + 32\n\nprint(f(100))", "command": "python conv.py",
         "steps": [{"visible": 2, "highlight": [1, 2], "say": "A function."},
                   {"visible": 4, "highlight": [4], "output": ["212.0"], "say": "It prints 212.0."}]},
        {"type": "compare", "title": "Install", "footer": "pyproject changed: reinstall",
         "left": {"head": "without -e", "lines": ["a copy"]},
         "right": {"head": "with -e", "lines": ["a shortcut"], "tone": "ok"},
         "steps": [{"show": "left", "say": "Without -e, a copy."}, {"show": "right", "say": "With -e, a shortcut."},
                   {"show": "footer", "say": "Run pip install -e . again if the pyproject changes."}]},
        {"type": "questions", "title": "Answer alone", "items": ["How many times does a module run?"],
         "steps": [{"show": 1, "say": "Pause and answer without looking."}]},
    ],
}


def with_ide(script: dict) -> dict:
    """A copy of ``script`` with the reference ide scene before the closing questions."""

    from tests.test_ide_scene import IDE_SCENE

    result = copy.deepcopy(script)
    result["scenes"].insert(len(result["scenes"]) - 1, copy.deepcopy(IDE_SCENE))
    return result


class ValidationTests(unittest.TestCase):
    def test_valid_script_passes(self):
        self.assertEqual([], validate_video_script(SCRIPT))

    def test_last_scene_must_be_questions(self):
        script = copy.deepcopy(SCRIPT)
        script["scenes"].pop()
        self.assertIn("the last scene must be retrieval questions (type questions), without answers",
                      validate_video_script(script))

    def test_sources_are_required(self):
        script = copy.deepcopy(SCRIPT)
        script["source_ids"] = []
        self.assertIn("source_ids must list at least one source", validate_video_script(script))

    def test_code_step_ranges_are_checked(self):
        script = copy.deepcopy(SCRIPT)
        script["scenes"][3]["steps"][0]["visible"] = 9
        script["scenes"][3]["steps"][1]["highlight"] = [5]
        errors = validate_video_script(script)
        self.assertIn("scene 4 step 1: visible must be between 1 and 4", errors)
        self.assertIn("scene 4 step 2: highlight must list visible line numbers", errors)

    def test_empty_speech_and_unknown_type_are_rejected(self):
        script = copy.deepcopy(SCRIPT)
        script["scenes"][0]["steps"][0]["say"] = " "
        script["scenes"][1]["type"] = "slides"
        errors = validate_video_script(script)
        self.assertIn("scene 1 step 1: say must be non-empty text", errors)
        self.assertTrue(any(e.startswith("scene 2: type must be one of") for e in errors))

    def test_inline_code_backticks_must_pair(self):
        script = copy.deepcopy(SCRIPT)
        script["scenes"][5]["items"][0] = "What does `print(__name__) show?"
        self.assertIn("scene 6: unbalanced backtick in 'What does `print(__name__) show?'",
                      validate_video_script(script))

    def test_script_with_ide_scene_passes(self):
        self.assertEqual([], validate_video_script(with_ide(SCRIPT)))

    def test_ide_code_is_not_checked_for_backticks(self):
        script = with_ide(SCRIPT)
        script["scenes"][5]["files"][0]["code"] = "s = '`'"
        script["scenes"][5]["steps"][0]["show"] = 1
        self.assertEqual([], validate_video_script(script))

    def test_footer_and_note_need_text(self):
        script = copy.deepcopy(SCRIPT)
        del script["scenes"][4]["footer"]
        del script["scenes"][2]["note"]
        errors = validate_video_script(script)
        self.assertIn("scene 5 step 3: footer shown but the scene has no footer text", errors)
        self.assertIn("scene 3 step 2: note shown but the scene has no note text", errors)


class PronunciationTests(unittest.TestCase):
    def test_whole_words_only(self):
        say = build_pronouncer({"import": "ímport"})
        self.assertEqual("ímport conv; importa", say("import conv; importa"))

    def test_longest_term_wins(self):
        say = build_pronouncer({"pip install -e .": "pip instól traço i ponto", "-e": "traço i"})
        self.assertEqual("rode pip instól traço i ponto, sem traço i", say("rode pip install -e ., sem -e"))

    def test_spoken_lines_keep_order_and_ids(self):
        lines = spoken_lines(SCRIPT)
        self.assertEqual(("s01_p01", "A module is a file that other files ímport."), lines[0])
        self.assertEqual(len(list(iter_steps(SCRIPT))), len(lines))


class TimelineTests(unittest.TestCase):
    def test_timeline_accumulates_speech_and_pause(self):
        self.assertEqual([(0.0, 2.0, 2.5), (2.5, 3.5, 4.0)], build_timeline([2.0, 1.0], pause=0.5))

    def test_srt_uses_script_text_and_speech_end(self):
        srt = format_srt(["Hello.", "World."], build_timeline([2.0, 1.25], pause=0.5))
        self.assertEqual("1\n00:00:00,000 --> 00:00:02,000\nHello.\n\n2\n00:00:02,500 --> 00:00:03,750\nWorld.\n", srt)

    def test_srt_timestamp_rolls_over(self):
        self.assertEqual("01:01:01,500", srt_timestamp(3661.5))

    def test_concat_list_repeats_last_image(self):
        text = concat_list([(Path("a.png"), 0.5), (Path("b.png"), 1.0)])
        self.assertTrue(text.rstrip().endswith(f"file '{Path('b.png').resolve().as_posix()}'"))
        self.assertIn("duration 0.5000", text)


class SpeechMatchTests(unittest.TestCase):
    def test_reports_ratio_and_differences(self):
        ratio, differences = speech_match("o módulo roda uma vez", "o módulo roda duas vezes")
        self.assertAlmostEqual(0.6, ratio)
        self.assertEqual([("uma vez", "duas vezes")], differences)

    def test_case_and_punctuation_do_not_count(self):
        self.assertEqual((1.0, []), speech_match("Rode: python!", "rode python"))


class CliTests(unittest.TestCase):
    def run_cli(self, script):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "script.json"
            path.write_text(json.dumps(script), encoding="utf-8")
            return subprocess.run([sys.executable, "-B", str(ROOT / "scripts" / "video_lesson.py"), "validate", str(path)],
                                  cwd=ROOT, capture_output=True, text=True, check=False)

    def test_validate_runs_directly(self):
        result = self.run_cli(SCRIPT)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("VIDEO SCRIPT: PASS", result.stdout)

    def test_validate_fails_on_bad_script(self):
        result = self.run_cli({"schema_version": 1})
        self.assertNotEqual(0, result.returncode)
        self.assertIn("VIDEO SCRIPT: FAIL", result.stderr)


HAS_RENDER_TOOLS = (
    importlib.util.find_spec("PIL") is not None
    and importlib.util.find_spec("pygments") is not None
    and shutil.which("ffmpeg") is not None
)


def probe_video(path: Path) -> dict:
    """Return the first video stream that ffprobe reports for ``path``."""

    result = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_streams", "-of", "json", str(path)],
                            capture_output=True, text=True, check=True)
    return json.loads(result.stdout)["streams"][0]


@unittest.skipUnless(HAS_RENDER_TOOLS, "pillow, pygments and ffmpeg are optional")
class RenderTests(unittest.TestCase):
    def test_renders_video_with_subtitles(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            audio = work / "audio"
            audio.mkdir()
            for step_id, _ in spoken_lines(SCRIPT):
                with wave.open(str(audio / f"{step_id}.wav"), "wb") as handle:
                    handle.setnchannels(1)
                    handle.setsampwidth(2)
                    handle.setframerate(16000)
                    handle.writeframes(b"\x00\x00" * 8000)
            out = work / "lesson.mp4"
            total = render_video(SCRIPT, audio, out, work / "frames")
            self.assertTrue(out.is_file())
            video = probe_video(out)
            self.assertEqual((1920, 1080, "30/1"), (video["width"], video["height"], video["r_frame_rate"]))
            self.assertAlmostEqual(len(spoken_lines(SCRIPT)) * 1.1, total, places=3)
            self.assertIn("It prints 212.0.", out.with_suffix(".srt").read_text(encoding="utf-8"))

    def test_renders_ide_scene(self):
        script = with_ide(SCRIPT)
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            audio = work / "audio"
            audio.mkdir()
            for step_id, _ in spoken_lines(script):
                with wave.open(str(audio / f"{step_id}.wav"), "wb") as handle:
                    handle.setnchannels(1)
                    handle.setsampwidth(2)
                    handle.setframerate(16000)
                    handle.writeframes(b"\x00\x00" * 8000)
            out = work / "lesson.mp4"
            total = render_video(script, audio, out, work / "frames")
            video = probe_video(out)
            self.assertEqual((1920, 1080), (video["width"], video["height"]))
            self.assertAlmostEqual(len(spoken_lines(script)) * 1.1, total, places=3)
            self.assertGreater(len(list((work / "frames").glob("s06_p02_f*.png"))), 1)


@unittest.skipUnless(HAS_RENDER_TOOLS, "pillow, pygments and ffmpeg are optional")
class IdePaintTests(unittest.TestCase):
    def paint(self, code: str):
        from scripts.ide_scene import IdeScreen, TermLine
        from scripts.video_lesson import _Painter

        scene = {"type": "ide", "title": "T", "files": [{"name": "a.py", "language": "python", "code": code}],
                 "steps": [{"show": 1, "say": "s"}]}
        screen = IdeScreen("a.py", (("a.py", len(code)),), (1,), (TermLine("cmd", "python a.py"), TermLine("out", "W" * 300)),
                           "terminal", True)
        return _Painter(SCRIPT).ide(scene, screen)

    def test_ide_frame_is_full_hd(self):
        self.assertEqual((1920, 1080), self.paint("x = 1").size)

    def test_long_line_is_clipped_at_panel_edge(self):
        from scripts.video_lesson import COLORS, HEIGHT, WIDTH, _px

        image = self.paint("W" * 300)
        column = [image.getpixel((WIDTH - _px(30), y)) for y in range(HEIGHT - _px(60))]
        self.assertTrue(all(pixel == COLORS["background"] for pixel in column))


if __name__ == "__main__":
    unittest.main()
