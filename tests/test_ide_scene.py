import copy
import unittest
from dataclasses import replace

from scripts.ide_scene import (IdeScreen, TermLine, first_visible_line, initial_screen, step_events, terminal_tail,
                               validate_ide_scene)


IDE_SCENE = {
    "type": "ide", "title": "Who imports",
    "files": [{"name": "conv.py", "language": "python", "code": "def f(c):\n    return c * 9 / 5 + 32"},
              {"name": "use.py", "language": "python", "code": "import conv\nprint(conv.f(100))"}],
    "steps": [{"file": "conv.py", "show": 2, "say": "The module."},
              {"file": "use.py", "type": 2, "highlight": [1], "say": "It imports conv."},
              {"terminal": [{"cmd": "python use.py"}, {"out": "212.0"}], "say": "It prints 212.0."},
              {"clear_terminal": True, "terminal": [{"cmd": "python"}, {"out": ">>> "}, {"in": "1 + 1"}],
               "say": "A prompt."}],
}


def errors_of(scene: dict) -> list[str]:
    errors: list[str] = []
    validate_ide_scene(scene, "scene 1", scene["steps"], errors)
    return errors


class IdeValidationTests(unittest.TestCase):
    def test_valid_ide_scene_passes(self):
        self.assertEqual([], errors_of(IDE_SCENE))

    def test_files_are_checked(self):
        scene = copy.deepcopy(IDE_SCENE)
        scene["files"] = []
        self.assertIn("scene 1: files must list 1 to 4 files", errors_of(scene))
        scene = copy.deepcopy(IDE_SCENE)
        del scene["files"][0]["code"]
        self.assertIn("scene 1: each file needs name, language and code", errors_of(scene))
        scene = copy.deepcopy(IDE_SCENE)
        scene["files"][1]["name"] = "conv.py"
        self.assertIn("scene 1: file names must be unique", errors_of(scene))

    def test_step_file_must_exist(self):
        scene = copy.deepcopy(IDE_SCENE)
        scene["steps"][0]["file"] = "x.py"
        self.assertIn("scene 1 step 1: file must name one of the scene files", errors_of(scene))

    def test_type_and_show_ranges(self):
        scene = copy.deepcopy(IDE_SCENE)
        scene["steps"][1]["show"] = 2
        self.assertIn("scene 1 step 2: use type or show, not both", errors_of(scene))
        scene = copy.deepcopy(IDE_SCENE)
        scene["steps"][1]["type"] = 3
        self.assertIn("scene 1 step 2: type must be between 1 and 2", errors_of(scene))

    def test_lines_never_disappear(self):
        scene = copy.deepcopy(IDE_SCENE)
        scene["steps"].append({"file": "conv.py", "show": 1, "say": "x"})
        self.assertIn("scene 1 step 5: show cannot hide lines already shown (2)", errors_of(scene))

    def test_highlight_must_be_visible(self):
        scene = copy.deepcopy(IDE_SCENE)
        scene["steps"][1]["highlight"] = [3]
        self.assertIn("scene 1 step 2: highlight must list visible line numbers", errors_of(scene))

    def test_terminal_lines_are_checked(self):
        for bad in ({"cmd": "a", "out": "b"}, {"say": "a"}, {"cmd": " "}):
            scene = copy.deepcopy(IDE_SCENE)
            scene["steps"][2]["terminal"] = [bad]
            self.assertIn("scene 1 step 3: terminal must be a list of lines with one of cmd, out, err, in",
                          errors_of(scene), bad)

    def test_in_must_follow_out(self):
        scene = copy.deepcopy(IDE_SCENE)
        scene["steps"][3]["terminal"] = [{"in": "x"}]
        self.assertIn("scene 1 step 4: in must follow an out line", errors_of(scene))
        scene = copy.deepcopy(IDE_SCENE)
        scene["steps"][3]["terminal"] = [{"cmd": "python"}, {"in": "x"}]
        self.assertIn("scene 1 step 4: in must follow an out line", errors_of(scene))

    def test_clear_terminal_is_boolean(self):
        scene = copy.deepcopy(IDE_SCENE)
        scene["steps"][3]["clear_terminal"] = "yes"
        self.assertIn("scene 1 step 4: clear_terminal must be true or false", errors_of(scene))


def one_file(code: str, steps: list[dict]) -> dict:
    return {"type": "ide", "title": "T", "files": [{"name": "a.py", "language": "python", "code": code}], "steps": steps}


def play(code: str, step: dict, speech: float, total: float):
    scene = one_file(code, [step])
    return step_events(scene, initial_screen(scene), step, speech, total)


def without_blink(screen: IdeScreen) -> IdeScreen:
    return replace(screen, cursor_on=True)


def change_times(events) -> list[float]:
    """Times at which the screen changes, ignoring the cursor blink."""

    times, previous = [], None
    for t, screen in events:
        if previous is None or without_blink(screen) != without_blink(previous):
            times.append(t)
        previous = screen
    return times


def first_time(events, condition) -> float:
    return next(t for t, screen in events if condition(screen))


def shown(screen: IdeScreen) -> int:
    return dict(screen.chars)["a.py"]


class PacingTests(unittest.TestCase):
    def test_short_code_types_at_floor_and_finishes_early(self):
        events, squeezed = play("x" * 20, {"type": 1, "highlight": [1], "say": "s"}, 10.0, 10.6)
        self.assertAlmostEqual(0.3 + 20 / 8, change_times(events)[-1])
        typed = next(s for _, s in events if shown(s) == 20)
        self.assertEqual((1,), typed.highlight)
        self.assertFalse(squeezed)

    def test_code_is_stretched_to_the_deadline(self):
        events, squeezed = play("x" * 100, {"type": 1, "say": "s"}, 10.0, 10.6)
        self.assertAlmostEqual(7.5, change_times(events)[-1])
        self.assertEqual(101, len([t for t, _ in events if t <= 7.5 + 1e-9]))
        self.assertFalse(squeezed)

    def test_mixed_step_shares_one_deadline(self):
        step = {"type": 1, "terminal": [{"cmd": "python usar.py"}, {"out": "212.0"}], "say": "s"}
        events, _ = play("x" * 30, step, 10.0, 10.6)
        self.assertAlmostEqual(4.05, first_time(events, lambda s: shown(s) == 30))
        self.assertAlmostEqual(5.8, first_time(events, lambda s: s.terminal and s.terminal[0].text == "python usar.py"))
        self.assertAlmostEqual(6.1, first_time(events, lambda s: len(s.terminal) == 2))
        self.assertEqual(TermLine("out", "212.0"), events[-1][1].terminal[1])

    def test_long_code_goes_line_by_line(self):
        lines = ["x" * 100] * 6
        events, squeezed = play("\n".join(lines), {"type": 6, "say": "s"}, 10.0, 10.6)
        for j in range(1, 7):
            size = len("\n".join(lines[:j]))
            self.assertAlmostEqual(0.3 + j * 1.2, first_time(events, lambda s, n=size: shown(s) == n))
        self.assertTrue(squeezed)

    def test_terminal_appears_at_once_when_nothing_fits(self):
        lines = ["x" * 100] * 6
        step = {"type": 6, "terminal": [{"cmd": "y" * 500}], "say": "s"}
        events, squeezed = play("\n".join(lines), step, 10.0, 10.6)
        self.assertAlmostEqual(0.3 + 1.2, first_time(events, lambda s: shown(s) == 100))
        self.assertAlmostEqual(7.5, first_time(events, lambda s: bool(s.terminal)))
        self.assertEqual("y" * 500, next(s for _, s in events if s.terminal).terminal[0].text)
        self.assertTrue(squeezed)

    def test_very_short_speech_shows_everything_at_once(self):
        step = {"type": 1, "terminal": [{"cmd": "python a.py"}, {"out": "1"}], "say": "s"}
        events, _ = play("x" * 40, step, 0.3, 0.9)
        self.assertEqual(40, shown(events[0][1]))
        self.assertEqual(2, len(events[0][1].terminal))
        self.assertTrue(all(0.0 <= t < 0.9 for t, _ in events))

    def test_pacing_counts_characters_not_bytes(self):
        events, _ = play("ação = '°'", {"type": 1, "say": "s"}, 10.0, 10.6)
        self.assertAlmostEqual(0.3 + 10 / 8, change_times(events)[-1])

    def test_cursor_blinks_after_the_animation(self):
        events, _ = play("x = 1", {"show": 1, "say": "s"}, 2.0, 2.6)
        self.assertEqual([0.0, 0.5, 1.0, 1.5, 2.0, 2.5], [round(t, 6) for t, _ in events])
        self.assertEqual([True, False, True, False, True, False], [s.cursor_on for _, s in events])

    def test_input_is_typed_on_the_last_out_line(self):
        step = {"show": 1, "terminal": [{"out": "Nome? "}, {"in": "Ana"}], "say": "s"}
        events, _ = play("x = input()", step, 10.0, 10.6)
        self.assertEqual(TermLine("out", "Nome? ", "Ana"), events[-1][1].terminal[-1])

    def test_many_outputs_appear_at_once_when_their_gaps_do_not_fit(self):
        step = {"show": 1, "terminal": [{"out": "1"}, {"out": "2"}, {"out": "3"}], "say": "s"}
        events, squeezed = play("x = 1", step, 1.0, 1.6)
        self.assertAlmostEqual(0.75, first_time(events, lambda s: bool(s.terminal)))
        self.assertEqual(3, len(next(s for _, s in events if s.terminal).terminal))
        self.assertTrue(squeezed)

    def test_events_stay_inside_the_step(self):
        cases = [("x" * 20, {"type": 1, "say": "s"}, 10.0), ("x" * 100, {"type": 1, "say": "s"}, 10.0),
                 ("\n".join(["x" * 100] * 6), {"type": 6, "terminal": [{"cmd": "y" * 500}], "say": "s"}, 10.0),
                 ("x" * 40, {"type": 1, "terminal": [{"out": "1"}], "say": "s"}, 0.3)]
        for code, step, speech in cases:
            events, _ = play(code, step, speech, speech + 0.6)
            times = [t for t, _ in events]
            self.assertEqual(sorted(times), times)
            self.assertEqual(0.0, times[0])
            self.assertTrue(all(t < speech + 0.6 for t in times))


class ScrollTests(unittest.TestCase):
    def test_editor_scrolls_to_keep_the_cursor_visible(self):
        self.assertEqual(29, first_visible_line(40, 40, 12))
        self.assertEqual(1, first_visible_line(5, 5, 12))
        self.assertEqual(1, first_visible_line(40, 3, 12))

    def test_terminal_keeps_its_last_lines(self):
        self.assertEqual(("c", "d", "e"), terminal_tail(tuple("abcde"), 3))
        self.assertEqual(("a",), terminal_tail(("a",), 3))


if __name__ == "__main__":
    unittest.main()
