init -1000 python hide:
    from configparser import ConfigParser
    if "TBModManager.ini" in renpy.list_files():
        ini = ConfigParser()
        ini.read_string(renpy.file("TBModManager.ini").read().decode())
        if bool(int(ini.get("gameconfig", "enabled", fallback="0"))):
            renpy.bootstrap.tbmm_initialized = True
        if bool(int(ini.get("gameconfig", "developer", fallback="0"))):
            renpy.bootstrap.tbmm_developer = True
        if bool(int(ini.get("gameconfig", "console", fallback="0"))):
            renpy.bootstrap.tbmm_console = True

init 1000 python:
    if getattr(renpy.bootstrap, "tbmm_initialized", False):
        config.developer = getattr(renpy.bootstrap, "tbmm_developer", config.developer)
        config.console = getattr(renpy.bootstrap, "tbmm_console", config.console)
