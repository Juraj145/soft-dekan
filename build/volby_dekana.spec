# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec pre aplikáciu Voľby dekana TF SPU v Nitre."""
import os
import sys

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

_REPO = os.path.dirname(os.path.abspath(SPECPATH))
_SRC = os.path.join(_REPO, "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

datas = collect_data_files("docx")
hiddenimports = ["docx"] + collect_submodules("volby_dekana")

a = Analysis(
    [os.path.join(_REPO, "main.py")],
    pathex=[_SRC],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="VolbyDekana",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="VolbyDekana",
)
