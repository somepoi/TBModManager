import pathlib, requests, zipfile, shutil, tempfile
from PySide6.QtCore import QObject, Signal

import internal.config

def get_local_game():
    try:
        return [int(i) for i in (pathlib.Path(internal.config.working_path) / "game" / "TBModManager" / "VERSION").read_text().split(".")]
    except Exception as e:
        print(str(e))
        return None

def get_remote_game():
    try:
        return [int(i) for i in requests.get("https://raw.githubusercontent.com/somepoi/TBAddonManager/game-implementation/VERSION").text.split(".")]
    except Exception as e:
        print(str(e))
        return None

def text_game():
    local = get_local_game()
    remote = get_remote_game()
    if not local:
        return ("Cannot get local files! Are game component files installed?", [None])
    if not remote:
        return ("Cannot get remote files! Please, check your internet connection.", [None])
    for i in range(3):
        if remote[i] > local[i]:
            return ("The current version of the game component files ({0}) is outdated.\nPlease update them to the latest version ({1}).", [".".join([str(i) for i in local]), ".".join([str(i) for i in remote])])
    return ("The current version of the game component files is up to date! ({0})", [".".join([str(i) for i in local]), ".".join([str(i) for i in remote])])

class DownloadGameRunner(QObject):

    status = Signal(str, list)
    finished = Signal()

    def run(self):
        self.error = None
        game_dir = (pathlib.Path(internal.config.working_path) / "game").resolve()
        target_dir = game_dir / "TBModManager"
        try:
            # Keep the installed component intact until the new archive is ready.
            with tempfile.TemporaryDirectory(dir=game_dir, prefix=".tbmm-install-") as tmp_dir:
                tmp_path = pathlib.Path(tmp_dir).resolve()
                if tmp_path.parent != game_dir:
                    raise ValueError("Invalid installation staging directory")
                archive = tmp_path / "component.zip"
                staging_dir = tmp_path / "component"
                staging_dir.mkdir()
                self.status.emit("Starting the download...", [])
                downloaded = 0
                with requests.get("https://github.com/somepoi/TBAddonManager/archive/refs/heads/game-implementation.zip", stream=True, timeout=10) as r, archive.open("wb") as tmp_file:
                    r.raise_for_status()
                    for chunk in r.iter_content(chunk_size=1024*1024):
                        tmp_file.write(chunk)
                        downloaded += len(chunk)
                        self.status.emit("{0} bytes downloaded...", [downloaded])
                with zipfile.ZipFile(archive) as z:
                    members = z.namelist()
                    top_folder = members[0].split("/", 1)[0]
                    for i, member in enumerate(members):
                        if not member.startswith(top_folder + "/"):
                            continue
                        rel = pathlib.Path(member[len(top_folder) + 1:])
                        if not rel.parts:
                            continue
                        out_path = (staging_dir / rel).resolve()
                        if not out_path.is_relative_to(staging_dir):
                            raise ValueError("Invalid path in component archive")
                        if member.endswith("/"):
                            out_path.mkdir(parents=True, exist_ok=True)
                        else:
                            out_path.parent.mkdir(parents=True, exist_ok=True)
                            with z.open(member) as src, out_path.open("wb") as dst:
                                shutil.copyfileobj(src, dst)
                        self.status.emit("Unpacking \"{0}\", {1} out of {2} files...", [str(rel), i, len(members)])

                for filename in ("VERSION", "inject.rpy", "main_menu_patch.rpy", "mods.rpy", "mods_screen.rpy", "mods_styles.rpy"):
                    if not (staging_dir / filename).is_file():
                        raise ValueError(f"Missing component file: {filename}")

                # Replace the installed component, including cached .rpyc files.
                backup = tmp_path / "previous-component"
                try:
                    if target_dir.resolve().parent != game_dir or target_dir.is_symlink():
                        raise ValueError("Invalid component installation directory")
                    if target_dir.exists():
                        target_dir.rename(backup)
                    staging_dir.rename(target_dir)
                except Exception:
                    if backup.exists():
                        backup.rename(target_dir)
                    raise
        except Exception as e:
            self.error = str(e)
            self.status.emit("Installation failed: {0}", [str(e)])
        finally:
            self.finished.emit()
