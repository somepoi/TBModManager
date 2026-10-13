from configparser import ConfigParser
from pathlib import Path

working_path = None

def save(developer: bool, console: bool, extconsole: bool):
    ini = ConfigParser()
    ini.add_section("gameconfig")
    ini["gameconfig"]["enabled"] = "1"
    ini["gameconfig"]["developer"] = str(int(developer))
    ini["gameconfig"]["console"] = str(int(console))
    ini["gameconfig"]["extconsole"] = str(int(extconsole))
    with open(Path(working_path) / "game" / "TBModManager.ini", "w", encoding="utf-8") as file:
        ini.write(file)

def load():
    ini = ConfigParser()
    try:
        ini.read(Path(working_path) / "game" / "TBModManager.ini", encoding="utf-8")
        return [bool(int(ini["gameconfig"][i])) for i in ["developer", "console", "extconsole"]]
    except Exception as e:
        return [False, False, False]
