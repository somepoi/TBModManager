"""Restore system library lookup when starting an external game from PyInstaller."""

import os
from pathlib import PurePosixPath, PureWindowsPath
import sys


def external_program_environment(environ=None, bundle_directory=None, platform=None):
    environment = dict(os.environ if environ is None else environ)
    platform = platform or sys.platform
    if bundle_directory is None and getattr(sys, "frozen", False):
        bundle_directory = getattr(sys, "_MEIPASS", None)
    if bundle_directory is None:
        return environment

    path_class = PureWindowsPath if platform == "win32" else PurePosixPath
    bundle = path_class(bundle_directory)
    separator = ";" if platform == "win32" else ":"
    if platform not in ("win32", "darwin"):
        original = environment.pop("LD_LIBRARY_PATH_ORIG", None)
        if original is None:
            environment.pop("LD_LIBRARY_PATH", None)
        else:
            environment["LD_LIBRARY_PATH"] = original
    for variable in ("PATH", "DYLD_LIBRARY_PATH", "QT_PLUGIN_PATH", "QT_QPA_PLATFORM_PLUGIN_PATH"):
        if variable not in environment:
            continue
        values = environment[variable].split(separator)
        environment[variable] = separator.join(value for value in values
                                               if not value or not path_class(value).is_relative_to(bundle))
        if not environment[variable] and variable != "PATH":
            environment.pop(variable)
    return environment


