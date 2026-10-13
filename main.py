from PySide6.QtWidgets import QApplication, QMessageBox, QFileDialog
from internal.interface import MainWindow, init_fonts
import argparse
import sys

from internal.lang import gt
import internal.config
from internal.components import install_link
from internal.downloading import local_component_directory
from internal.paths import (game_command, launcher_directory, normalize_game_directory,
                            remember_game_directory, remembered_game_directory)

def select_game_directory(explicit=None):
    if explicit is not None:
        root = normalize_game_directory(explicit)
        if root is None:
            raise ValueError(gt("The program could not find Tiny Bunny game folder!"))
        game_command(root)
        return root
    for candidate in (remembered_game_directory(), launcher_directory()):
        root = normalize_game_directory(candidate)
        if root is not None:
            try:
                game_command(root)
                return root
            except FileNotFoundError:
                pass
    while True:
        selected = QFileDialog.getExistingDirectory(None, gt("Choose Tiny Bunny folder"))
        if not selected:
            return None
        root = normalize_game_directory(selected)
        try:
            if root is None:
                raise ValueError(gt("The program could not find Tiny Bunny game folder!"))
            game_command(root)
            return root
        except (OSError, ValueError) as error:
            QMessageBox.critical(None, gt("Error!"), str(error))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Tiny Bunny Mod Manager")
    parser.add_argument("--game-dir", help="Tiny Bunny directory (or its game directory)")
    arguments, qt_arguments = parser.parse_known_args(sys.argv[1:] if argv is None else argv)
    app = QApplication([sys.argv[0], *qt_arguments])
    app.setApplicationName("TBModManager")
    init_fonts()
    root = None
    try:
        root = select_game_directory(arguments.game_dir)
        if root is None:
            return 0
        remember_game_directory(root)
        internal.config.working_path = str(root)
        source = local_component_directory(root)
        if source is not None:
            install_link(root, source)
    except PermissionError as error:
        message = gt("Cannot connect game components. Close programs using {0} and check folder permissions, then try again.")
        path = root / "game/TBModManager" if root is not None else error.filename or arguments.game_dir or launcher_directory()
        QMessageBox.critical(None, gt("Error!"), message.format(path))
        return 1
    except (OSError, ValueError) as error:
        QMessageBox.critical(None, gt("Error!"), str(error))
        return 1
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
