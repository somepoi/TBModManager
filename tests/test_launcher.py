import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QEventLoop, QTimer

from internal import config, interface
from internal.interface import GameRunner, MainWindow
import main


class LauncherTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.game = self.root / "Tiny Bunny"
        (self.game / "game").mkdir(parents=True)
        (self.game / "TinyBunny.py").touch()
        (self.game / "TinyBunny.sh").touch()
        runtime = self.game / "lib/py3-windows-x86_64"
        runtime.mkdir(parents=True)
        (runtime / "python.exe").touch()
        (runtime / "pythonw.exe").touch()

    @unittest.skipUnless(os.name == "nt", "Windows subprocess flags")
    def test_game_process_uses_game_cwd_on_windows(self):
        runner = GameRunner(None, ["runtime", "script"], False, self.game)
        with patch.object(interface.subprocess, "run") as run, \
             patch.object(interface.sys, "platform", "win32"):
            runner.run()
        self.assertEqual(run.call_args.kwargs["cwd"], str(self.game))
        self.assertEqual(run.call_args.kwargs["creationflags"], subprocess.CREATE_NO_WINDOW)

    def test_unix_process_has_no_windows_creationflags(self):
        runner = GameRunner(None, ["/bin/sh", "TinyBunny.sh"], False, self.game)
        with patch.object(interface.subprocess, "run") as run, \
             patch.object(interface.sys, "platform", "linux"):
            runner.run()
        self.assertNotIn("creationflags", run.call_args.kwargs)

    def test_launch_failure_is_reported(self):
        runner = GameRunner(None, ["missing"], False, self.game)
        errors = []
        runner.failed.connect(errors.append)
        with patch.object(interface.subprocess, "run", side_effect=OSError("runtime missing")):
            runner.run()
        self.assertEqual(errors, ["runtime missing"])

    def window(self):
        with patch.object(config, "working_path", str(self.game)), \
             patch.object(MainWindow, "update_status", lambda self: None):
            return MainWindow()

    def test_launch_starts_background_thread(self):
        window = self.window()
        with patch.object(config, "working_path", str(self.game)), \
             patch.object(GameRunner, "start") as start, \
             patch.object(GameRunner, "run", side_effect=AssertionError("GUI thread must not run the game")):
            window._start_game()
        start.assert_called_once()
        self.assertTrue((self.game / "game/TBModManager.ini").is_file())

    def test_cancelling_game_change_preserves_selection(self):
        window = self.window()
        with patch.object(config, "working_path", str(self.game)), \
             patch.object(interface.QFileDialog, "getExistingDirectory", return_value=""):
            window._select_game()
            self.assertEqual(Path(config.working_path), self.game)

    def test_standalone_launcher_uses_remembered_game(self):
        with patch.object(main, "remembered_game_directory", return_value=self.game), \
             patch.object(main, "launcher_directory", return_value=self.root / "elsewhere"), \
             patch.object(main.QFileDialog, "getExistingDirectory", side_effect=AssertionError("already remembered")):
            self.assertEqual(main.select_game_directory(), self.game)

    def test_first_run_cancel_exits_without_constructing_game_window(self):
        with patch.object(main, "remembered_game_directory", return_value=None), \
             patch.object(main, "launcher_directory", return_value=self.root), \
             patch.object(main.QFileDialog, "getExistingDirectory", return_value=""):
            self.assertIsNone(main.select_game_directory())

    def test_real_install_worker_finishes_and_closing_waits_for_it(self):
        window = self.window()
        with patch.object(config, "working_path", str(self.game)), \
             patch.object(MainWindow, "update_status", lambda self: None):
            window._start_install()
            self.assertTrue(window._busy)
            window.close()
            self.assertTrue(window._close_requested)
            loop = QEventLoop()
            timer = QTimer()
            timer.timeout.connect(lambda: loop.quit() if not window._busy else None)
            timer.start(10)
            QTimer.singleShot(3000, loop.quit)
            loop.exec()
            timer.stop()
            self.assertFalse(window._busy)
            self.assertIsNone(window._install_error)
            self.assertTrue((self.game / "game/TBModManager/mods.rpy").is_file())


if __name__ == "__main__":
    unittest.main()
