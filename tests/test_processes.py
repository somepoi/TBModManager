import unittest

from internal import processes


class ProcessEnvironmentTests(unittest.TestCase):
    def test_linux_restores_original_libraries_without_modifying_parent(self):
        parent = {"LD_LIBRARY_PATH": "/tmp/_MEI123:/system/lib", "LD_LIBRARY_PATH_ORIG": "/system/lib", "PATH": "/bin"}
        child = processes.external_program_environment(parent, "/tmp/_MEI123", "linux")
        self.assertEqual(child["LD_LIBRARY_PATH"], "/system/lib")
        self.assertEqual(parent["LD_LIBRARY_PATH"], "/tmp/_MEI123:/system/lib")

    def test_linux_clears_bundle_library_path_when_no_original_exists(self):
        child = processes.external_program_environment({"LD_LIBRARY_PATH": "/tmp/_MEI123"}, "/tmp/_MEI123", "linux")
        self.assertNotIn("LD_LIBRARY_PATH", child)

    def test_windows_path_keeps_game_and_system_entries(self):
        parent = {"PATH": r"C:\Temp\_MEI123;C:\Temp\_MEI123\PySide6;C:\Windows;D:\Games\lib"}
        child = processes.external_program_environment(parent, r"C:\Temp\_MEI123", "win32")
        self.assertEqual(child["PATH"], r"C:\Windows;D:\Games\lib")

    def test_macos_removes_only_bundled_dyld_paths(self):
        parent = {"DYLD_LIBRARY_PATH": "/tmp/_MEI123/PySide6:/usr/local/lib", "PATH": "/bin"}
        child = processes.external_program_environment(parent, "/tmp/_MEI123", "darwin")
        self.assertEqual(child["DYLD_LIBRARY_PATH"], "/usr/local/lib")

    def test_non_frozen_environment_is_unchanged(self):
        parent = {"PATH": "/bin", "LD_LIBRARY_PATH": "/custom/libs"}
        self.assertEqual(processes.external_program_environment(parent, None, "linux"), parent)

