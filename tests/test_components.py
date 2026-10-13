import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from internal import components


class ComponentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="tbmm tests ")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.game = self.root / "Tiny Bunny"
        (self.game / "game").mkdir(parents=True)
        self.source = self.root / "checkout & sources" / "renpy"
        self.source.mkdir(parents=True)
        for filename in components.REQUIRED_FILES:
            (self.source / filename).write_text("0.1.0" if filename == "VERSION" else "# test", encoding="utf-8")
        self.target = self.game / "game" / "TBModManager"

    def test_link_reads_source_and_reinstall_is_idempotent(self):
        components.install_link(self.game, self.source)
        self.assertTrue(components.is_directory_link(self.target))
        self.assertEqual(self.target.resolve(), self.source.resolve())
        (self.source / "mods.rpy").write_text("# edited", encoding="utf-8")
        self.assertEqual((self.target / "mods.rpy").read_text(), "# edited")
        self.assertIsNone(components.install_link(self.game, self.source))

    def test_existing_clone_is_preserved_outside_game(self):
        (self.target / ".git").mkdir(parents=True)
        (self.target / ".git" / "HEAD").write_text("ref: refs/heads/game-implementation")
        (self.target / "mods.rpy").write_text("# previous")
        backup = components.install_link(self.game, self.source)
        self.assertFalse(backup.is_relative_to(self.game / "game"))
        self.assertEqual((backup / "mods.rpy").read_text(), "# previous")
        self.assertTrue((backup / ".git" / "HEAD").is_file())

    def test_failed_link_creation_restores_existing_component(self):
        self.target.mkdir()
        (self.target / "mods.rpy").write_text("# previous")
        with patch.object(components, "create_directory_link", side_effect=OSError("not supported")):
            with self.assertRaises(OSError):
                components.install_link(self.game, self.source)
        self.assertFalse(components.is_directory_link(self.target))
        self.assertEqual((self.target / "mods.rpy").read_text(), "# previous")

    def test_retargeting_link_does_not_modify_old_sources(self):
        components.install_link(self.game, self.source)
        other = self.root / "another checkout"
        other.mkdir()
        for filename in components.REQUIRED_FILES:
            (other / filename).write_text("0.2.0" if filename == "VERSION" else "# other")
        components.install_link(self.game, other)
        self.assertEqual(self.target.resolve(), other)
        self.assertEqual((self.source / "VERSION").read_text(), "0.1.0")

    def test_missing_source_does_not_change_installed_files(self):
        self.target.mkdir()
        (self.target / "existing.txt").touch()
        (self.source / "mods.rpy").unlink()
        with self.assertRaises(ValueError):
            components.install_link(self.game, self.source)
        self.assertTrue((self.target / "existing.txt").exists())

    def test_recursive_link_target_is_rejected(self):
        with self.assertRaises(ValueError):
            components.install_link(self.game, self.game / "game")
        self.assertFalse(os.path.lexists(self.target))


if __name__ == "__main__":
    unittest.main()
