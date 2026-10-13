# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import os
import sys
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT

project_root = Path(SPECPATH)

if sys.platform == 'win32':
    # Resolve DLLs from this Python/Qt installation and Windows. Editors may
    # prepend unrelated runtimes to PATH, including incompatible UCRT DLLs.
    site_packages = Path(sys.prefix) / 'Lib' / 'site-packages'
    runtime_paths = [
        Path(sys.base_prefix),
        Path(sys.base_prefix) / 'DLLs',
        site_packages / 'PySide6',
        site_packages / 'shiboken6',
        Path(os.environ.get('SystemRoot', 'C:/Windows')) / 'System32',
        Path(os.environ.get('SystemRoot', 'C:/Windows')),
    ]
    os.environ['PATH'] = os.pathsep.join(str(path) for path in runtime_paths if path.is_dir())

a = Analysis(
    [str(project_root / 'main.py')],
    pathex=[str(project_root)],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    excludes=[
        "PySide6.QtWebEngineWidgets*",
        "PySide6.QtWebEngineCore*",
        "PySide6.QtWebEngineQuick*",
        "PySide6.QtMultimedia*",
        "PySide6.QtMultimediaWidgets*",
        "PySide6.QtSvg*",
        "PySide6.QtSvgWidgets*",
        "PySide6.QtOpenGL*",
        "PySide6.QtOpenGLWidgets*",
        "PySide6.Qt3DCore*",
        "PySide6.Qt3DRender*",
        "PySide6.Qt3DInput*",
        "PySide6.QtCharts*",
        "PySide6.QtLocation*",
        "PySide6.QtPositioning*",
        "PySide6.QtSensors*",
        "PySide6.QtTextToSpeech*",
        "PySide6.QtNetworkAuth*",
        "PySide6.QtRemoteObjects*",
    ],
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='launcher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[str(project_root / 'icon.ico')],
)
