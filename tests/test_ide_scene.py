import copy
import unittest

from scripts.ide_scene import validate_ide_scene


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


if __name__ == "__main__":
    unittest.main()
