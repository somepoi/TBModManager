from pathlib import Path, PurePosixPath
import shutil
import tempfile
import uuid
import zipfile

import requests
from PySide6.QtCore import QObject, Signal

import internal.config
from internal.components import install_link, is_directory_link, validate_component
from internal.paths import data_directory, launcher_directory


REPOSITORY = "somepoi/TBModManager"
RAW_BASE = f"https://raw.githubusercontent.com/{REPOSITORY}"
ARCHIVE_BASE = f"https://github.com/{REPOSITORY}/archive/refs/heads"


class UnifiedComponentUnavailable(ValueError):
    """The published main still predates the unified repository layout."""


def local_component_directory(game_directory=None):
    source = launcher_directory() / "renpy"
    if source.is_dir():
        return validate_component(source)
    root = game_directory or internal.config.working_path
    if root:
        target = Path(root) / "game/TBModManager"
        if is_directory_link(target) and target.is_dir():
            linked_source = target.resolve()
            if linked_source.name == "renpy" and (linked_source.parent / "main.py").is_file() and (linked_source.parent / "pyproject.toml").is_file():
                return validate_component(linked_source)
    return None


def _read_version(text):
    parts = text.strip().split(".")
    if len(parts) != 3 or not all(part.isdecimal() for part in parts):
        raise ValueError("Invalid component VERSION")
    return [int(part) for part in parts]


def get_local_game(game_directory=None):
    try:
        root = Path(game_directory or internal.config.working_path)
        return _read_version((root / "game/TBModManager/VERSION").read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return None


def get_remote_game():
    try:
        for branch, filename in (("main", "renpy/VERSION"), ("game-implementation", "VERSION")):
            with requests.get(f"{RAW_BASE}/{branch}/{filename}", timeout=(5, 10)) as response:
                if response.status_code == 404 and branch == "main":
                    continue
                response.raise_for_status()
                return _read_version(response.text)
    except (requests.RequestException, ValueError):
        return None


def text_game(game_directory=None):
    root = Path(game_directory or internal.config.working_path)
    local = get_local_game(root)
    source = local_component_directory(root)
    if source is not None:
        version = (source / "VERSION").read_text(encoding="utf-8").strip()
        target = root / "game/TBModManager"
        if is_directory_link(target) and target.resolve() == source.resolve():
            return ("Local game components linked ({0}).", [version])
        return ("Local game components available ({0}). Install them to connect the game.", [version])
    if not local:
        return ("Cannot get local files! Are game component files installed?", [None])
    remote = get_remote_game()
    if not remote:
        return ("Cannot get remote files! Please, check your internet connection.", [None])
    versions = [".".join(map(str, local)), ".".join(map(str, remote))]
    if tuple(remote) > tuple(local):
        return ("The current version of the game component files ({0}) is outdated.\nPlease update them to the latest version ({1}).", versions)
    return ("The current version of the game component files is up to date! ({0})", versions)


def extract_component(archive, destination, legacy=False):
    """Extract only renpy/ from main; accept the old root layout explicitly."""
    destination = Path(destination).resolve()
    with zipfile.ZipFile(archive) as stream:
        members = stream.infolist()
        if not members:
            raise ValueError("Empty component archive")
        top_folder = members[0].filename.split("/", 1)[0]
        prefix = top_folder + ("/" if legacy else "/renpy/")
        selected = [member for member in members if member.filename.startswith(prefix) and member.filename != prefix]
        if not selected and not legacy:
            raise UnifiedComponentUnavailable("Published main has no renpy component yet")
        destination.mkdir(parents=True, exist_ok=True)
        for member in selected:
            relative = PurePosixPath(member.filename[len(prefix):])
            if relative.is_absolute() or ".." in relative.parts or "\\" in member.filename or ":" in str(relative):
                raise ValueError("Invalid path in component archive")
            if not relative.parts or any(part.startswith(".") for part in relative.parts):
                continue
            output = (destination / Path(*relative.parts)).resolve()
            if not output.is_relative_to(destination):
                raise ValueError("Invalid path in component archive")
            if member.is_dir():
                output.mkdir(parents=True, exist_ok=True)
            else:
                output.parent.mkdir(parents=True, exist_ok=True)
                with stream.open(member) as src, output.open("wb") as dst:
                    shutil.copyfileobj(src, dst)
    validate_component(destination)


class DownloadGameRunner(QObject):
    status = Signal(str, list)
    finished = Signal()

    def __init__(self, game_directory=None):
        super().__init__()
        self.game_directory = Path(game_directory or internal.config.working_path)
        self.error = None
        self.backup = None

    def _download_component(self):
        # A separate persistent directory keeps the installed link working
        # until its replacement has been fully validated.
        cache = data_directory() / "components"
        cache.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=cache, prefix=".download-") as temporary:
            temporary = Path(temporary)
            archive = temporary / "component.zip"
            staging = temporary / "renpy"
            for branch, legacy in (("main", False), ("game-implementation", True)):
                self.status.emit("Starting the download...", [])
                with requests.get(f"{ARCHIVE_BASE}/{branch}.zip", stream=True, timeout=(5, 15)) as response:
                    response.raise_for_status()
                    downloaded = 0
                    with archive.open("wb") as output:
                        for chunk in response.iter_content(chunk_size=1024 * 1024):
                            output.write(chunk)
                            downloaded += len(chunk)
                            self.status.emit("{0} bytes downloaded...", [downloaded])
                try:
                    extract_component(archive, staging, legacy=legacy)
                except UnifiedComponentUnavailable:
                    continue
                version = (staging / "VERSION").read_text(encoding="utf-8").strip()
                source = cache / f"{version}-{uuid.uuid4().hex}"
                staging.rename(source)
                return source
        raise ValueError("Game component not found in repository archives")

    def run(self):
        try:
            source = local_component_directory(self.game_directory)
            if source is None:
                source = self._download_component()
            self.status.emit("Connecting game components...", [])
            self.backup = install_link(self.game_directory, source)
            if self.backup is not None:
                self.status.emit("Previous game components saved to {0}", [str(self.backup)])
            self.status.emit("Game components connected.", [])
        except PermissionError as error:
            self.error = str(error)
            self.status.emit("Cannot connect game components. Close programs using {0} and check folder permissions, then try again.",
                             [str(self.game_directory / "game/TBModManager")])
        except Exception as error:
            self.error = str(error)
            self.status.emit("Installation failed: {0}", [str(error)])
        finally:
            self.finished.emit()
