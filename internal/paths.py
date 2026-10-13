"""Game and launcher locations independent of the process working directory."""

from configparser import ConfigParser, Error as ConfigError
import os
from pathlib import Path
import plistlib
import sys


def launcher_directory():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def data_directory():
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or Path.home() / "AppData" / "Local")
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    return base / "TBModManager"


def normalize_game_directory(selection):
    if not selection:
        return None
    path = Path(selection).expanduser().resolve()
    candidates = [path, path.parent if path.name == "game" else path]
    if path.suffix.lower() == ".app":
        candidates.append(path / "Contents" / "Resources" / "autorun")
    elif path.is_dir():
        candidates.extend(bundle / "Contents" / "Resources" / "autorun"
                          for bundle in sorted(path.glob("TinyBunny*.app")))
    for candidate in candidates:
        if (candidate / "game").is_dir() and (candidate / "TinyBunny.py").is_file():
            return candidate
    return None


def game_command(game_directory, external_console=False, platform=None):
    root = Path(game_directory).resolve()
    platform = platform or sys.platform
    if platform == "win32":
        runtime = root / "lib" / "py3-windows-x86_64"
        executable = runtime / ("python.exe" if external_console else "pythonw.exe")
        if not executable.is_file():
            executable = runtime / "python.exe"
        if executable.is_file() and (root / "TinyBunny.py").is_file():
            return [str(executable), str(root / "TinyBunny.py")]
    elif platform == "darwin":
        for bundle in root.parents:
            if bundle.suffix.lower() != ".app":
                continue
            try:
                with (bundle / "Contents" / "Info.plist").open("rb") as stream:
                    name = plistlib.load(stream)["CFBundleExecutable"]
                executable = bundle / "Contents" / "MacOS" / name
                if executable.is_file() and executable.resolve().parent == (bundle / "Contents" / "MacOS").resolve():
                    return [str(executable)]
            except (OSError, KeyError, plistlib.InvalidFileException):
                pass
    if platform != "win32" and (root / "TinyBunny.sh").is_file():
        return ["/bin/sh", str(root / "TinyBunny.sh")]
    raise FileNotFoundError(f"Tiny Bunny runtime not found for {platform}: {root}")


def remember_game_directory(game_directory, settings_path=None):
    path = Path(settings_path) if settings_path is not None else data_directory() / "launcher.ini"
    config = ConfigParser(interpolation=None)
    config["launcher"] = {"game_directory": str(Path(game_directory).resolve())}
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        config.write(stream)


def remembered_game_directory(settings_path=None):
    path = Path(settings_path) if settings_path is not None else data_directory() / "launcher.ini"
    config = ConfigParser(interpolation=None)
    try:
        config.read(path, encoding="utf-8")
        return normalize_game_directory(config.get("launcher", "game_directory", fallback=""))
    except (OSError, ConfigError, RuntimeError):
        return None
