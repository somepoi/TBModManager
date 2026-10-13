import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from internal import components, config, downloading


class DownloadTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.game = self.root / "Tiny Bunny"
        (self.game / "game").mkdir(parents=True)
        self.source = self.root / "checkout" / "renpy"
        self.source.mkdir(parents=True)
        for name in components.REQUIRED_FILES:
            (self.source / name).write_text("0.1.0" if name == "VERSION" else "# script")

    def archive(self, legacy=False, extra=None):
        archive = self.root / "component.zip"
        prefix = "repo-game-implementation/" if legacy else "repo-main/renpy/"
        with zipfile.ZipFile(archive, "w") as stream:
            for name in components.REQUIRED_FILES:
                stream.writestr(prefix + name, (self.source / name).read_bytes())
            stream.writestr(prefix + "assets/images/test.png", b"image")
            if not legacy:
                stream.writestr("repo-main/main.py", "# launcher")
            if extra:
                stream.writestr(prefix + extra, "bad")
        return archive

    def test_unified_archive_extracts_only_game_component(self):
        staging = self.root / "staging"
        downloading.extract_component(self.archive(), staging)
        self.assertTrue((staging / "mods.rpy").is_file())
        self.assertTrue((staging / "assets/images/test.png").is_file())
        self.assertFalse((staging / "main.py").exists())

    def test_legacy_archive_remains_usable_during_migration(self):
        staging = self.root / "staging"
        downloading.extract_component(self.archive(legacy=True), staging, legacy=True)
        self.assertTrue((staging / "VERSION").is_file())

    def test_archive_traversal_is_rejected(self):
        staging = self.root / "staging"
        with self.assertRaises(ValueError):
            downloading.extract_component(self.archive(extra="../../escape.rpy"), staging)
        self.assertFalse((self.root / "escape.rpy").exists())

    def test_local_install_does_not_use_network(self):
        with patch.object(config, "working_path", str(self.game)), \
             patch.object(downloading, "local_component_directory", return_value=self.source), \
             patch.object(downloading.requests, "get", side_effect=AssertionError("network not needed")):
            worker = downloading.DownloadGameRunner()
            worker.run()
        self.assertIsNone(worker.error)
        self.assertEqual((self.game / "game/TBModManager").resolve(), self.source)

    def test_development_status_does_not_use_network(self):
        components.install_link(self.game, self.source)
        with patch.object(config, "working_path", str(self.game)), \
             patch.object(downloading, "local_component_directory", return_value=self.source), \
             patch.object(downloading.requests, "get", side_effect=AssertionError("network not needed")):
            status, arguments = downloading.text_game()
        self.assertIn("linked", status.lower())
        self.assertIn("0.1.0", arguments)

    def test_version_comparison_is_lexicographic(self):
        with patch.object(downloading, "local_component_directory", return_value=None), \
             patch.object(downloading, "get_local_game", return_value=[2, 0, 0]), \
             patch.object(downloading, "get_remote_game", return_value=[1, 9, 9]):
            status, _ = downloading.text_game(self.game)
        self.assertIn("up to date", status)

    def test_downloaded_component_persists_after_staging_cleanup(self):
        archive_bytes = self.archive().read_bytes()

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_):
                pass

            def raise_for_status(self):
                pass

            def iter_content(self, chunk_size):
                yield archive_bytes

        with patch.object(downloading, "local_component_directory", return_value=None), \
             patch.object(downloading, "data_directory", return_value=self.root / "user data"), \
             patch.object(downloading.requests, "get", return_value=Response()):
            worker = downloading.DownloadGameRunner(self.game)
            worker.run()
        self.assertIsNone(worker.error)
        source = (self.game / "game/TBModManager").resolve()
        self.assertTrue(source.is_relative_to(self.root / "user data/components"))
        self.assertTrue((source / "mods.rpy").is_file())
        self.assertFalse(any(source.parent.glob(".download-*")))

    def test_relocated_executable_reuses_linked_repository_sources(self):
        (self.source.parent / "main.py").touch()
        (self.source.parent / "pyproject.toml").touch()
        components.install_link(self.game, self.source)
        with patch.object(downloading, "launcher_directory", return_value=self.root / "elsewhere"):
            self.assertEqual(downloading.local_component_directory(self.game), self.source)


if __name__ == "__main__":
    unittest.main()
