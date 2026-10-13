"""Connect a persistent component directory to a game without copying sources."""

import os
from pathlib import Path
import stat
import uuid


REQUIRED_FILES = ("VERSION", "inject.rpy", "main_menu_patch.rpy", "mods.rpy", "mods_screen.rpy", "mods_styles.rpy")


def validate_component(source):
    source = Path(source)
    for filename in REQUIRED_FILES:
        if not (source / filename).is_file():
            raise ValueError(f"Missing component file: {filename}")
    version = (source / "VERSION").read_text(encoding="utf-8").strip().split(".")
    if len(version) != 3 or not all(part.isdecimal() for part in version):
        raise ValueError("Invalid component VERSION")
    return source


def is_directory_link(path):
    path = Path(path)
    if path.is_symlink():
        return True
    try:
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
        return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))
    except FileNotFoundError:
        return False


def create_directory_link(source, target):
    source, target = Path(source).resolve(strict=True), Path(target).absolute()
    if os.name == "nt":
        if str(source).startswith("\\\\"):
            raise ValueError("Windows junctions require a local component directory")
        # CPython's native helper creates an NTFS junction
        import _winapi
        _winapi.CreateJunction(str(source), str(target))
    else:
        target.symlink_to(source, target_is_directory=True)


def remove_directory_link(path):
    path = Path(path)
    if not is_directory_link(path):
        raise ValueError(f"Refusing to remove a regular directory: {path}")
    if path.is_symlink():
        path.unlink()
    else:
        path.rmdir()


def install_link(game_directory, source):
    """Return a preserved previous installation, or None for an unchanged link."""
    root = Path(game_directory).resolve(strict=True)
    game = (root / "game").resolve(strict=True)
    source = Path(source).resolve(strict=True)
    if source.is_relative_to(game) or game.is_relative_to(source):
        raise ValueError("Component sources must be outside the game directory")
    validate_component(source)
    target = game / "TBModManager"
    if is_directory_link(target) and target.resolve() == source:
        return None

    backup = None
    if os.path.lexists(target):
        if not target.is_dir() and not is_directory_link(target):
            raise ValueError(f"Component installation path is not a directory: {target}")
        backup_root = root / ".tbmm-backups"
        if backup_root.resolve().parent != root or is_directory_link(backup_root):
            raise ValueError("Invalid component backup directory")
        backup = backup_root / uuid.uuid4().hex / "TBModManager"
        backup.parent.mkdir(parents=True)
        target.rename(backup)

    try:
        create_directory_link(source, target)
        if not is_directory_link(target) or target.resolve() != source:
            raise OSError("Component directory link could not be verified")
    except Exception:
        if is_directory_link(target):
            remove_directory_link(target)
        elif target.is_dir() and not any(target.iterdir()):
            # Native junction creation can leave its empty directory on failure.
            target.rmdir()
        if backup is not None:
            backup.rename(target)
        raise
    return backup
