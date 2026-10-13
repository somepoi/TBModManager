import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from internal import paths


class PathsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.game = self.root / "Tiny Bunny"
        (self.game / "game").mkdir(parents=True)
        (self.game / "TinyBunny.py").write_text("", encoding="utf-8")
        self.runtime = self.game / "lib" / "py3-windows-x86_64"
        self.runtime.mkdir(parents=True)
        (self.runtime / "python.exe").touch()
        (self.runtime / "pythonw.exe").touch()

    def test_select_root_or_game_directory(self):
        self.assertEqual(paths.normalize_game_directory(self.game), self.game)
        self.assertEqual(paths.normalize_game_directory(self.game / "game"), self.game)

    def test_cancel_and_invalid_selection_do_not_become_cwd(self):
        self.assertIsNone(paths.normalize_game_directory(""))
        self.assertIsNone(paths.normalize_game_directory(self.root))

    def test_windows_command_uses_selected_game(self):
        self.assertEqual(
            paths.game_command(self.game, False, platform="win32"),
            [str(self.runtime / "pythonw.exe"), str(self.game / "TinyBunny.py")],
        )

    def test_linux_uses_native_shell_script(self):
        (self.game / "TinyBunny.sh").touch()
        self.assertEqual(paths.game_command(self.game, False, platform="linux"),
                         ["/bin/sh", str(self.game / "TinyBunny.sh")])

    def test_mac_bundle_selection_and_executable(self):
        import plistlib
        bundle = self.root / "TinyBunny.app"
        autorun = bundle / "Contents" / "Resources" / "autorun"
        (autorun / "game").mkdir(parents=True)
        (autorun / "TinyBunny.py").touch()
        executable = bundle / "Contents" / "MacOS" / "TinyBunny"
        executable.parent.mkdir(parents=True)
        executable.touch()
        with (bundle / "Contents" / "Info.plist").open("wb") as stream:
            plistlib.dump({"CFBundleExecutable": "TinyBunny"}, stream)
        self.assertEqual(paths.normalize_game_directory(bundle), autorun)
        self.assertEqual(paths.game_command(autorun, False, platform="darwin"),
                         [str(executable)])

    def test_remembered_game_survives_launcher_relocation(self):
        settings = self.root / "user data" / "launcher.ini"
        paths.remember_game_directory(self.game, settings)
        self.assertEqual(paths.remembered_game_directory(settings), self.game)
        (self.game / "TinyBunny.py").unlink()
        self.assertIsNone(paths.remembered_game_directory(settings))

    def test_frozen_source_uses_executable_directory_not_meipass(self):
        with patch.object(paths.sys, "frozen", True, create=True), \
             patch.object(paths.sys, "executable", str(self.root / "launcher.exe")), \
             patch.object(paths.sys, "_MEIPASS", str(self.root / "temporary"), create=True):
            self.assertEqual(paths.launcher_directory(), self.root)

    def test_percent_signs_in_game_path_are_literal(self):
        import shutil
        percent_game = self.root / "100% Tiny Bunny %(literal)s"
        shutil.copytree(self.game, percent_game)
        settings = self.root / "launcher.ini"
        paths.remember_game_directory(percent_game, settings)
        self.assertEqual(paths.remembered_game_directory(settings), percent_game)


if __name__ == "__main__":
    unittest.main()
