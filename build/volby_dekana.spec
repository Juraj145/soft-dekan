# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec pre aplikáciu Voľby dekana TF SPU v Nitre."""
import os
import sys

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

_REPO = os.path.dirname(os.path.abspath(SPECPATH))
_SRC = os.path.join(_REPO, "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

_ASSETS = os.path.join(_SRC, "volby_dekana", "assets")
_ICON = os.path.join(_ASSETS, "logo.ico")

datas = collect_data_files("docx")
datas += [
    (os.path.join(_ASSETS, "logo.png"), "volby_dekana/assets"),
    (os.path.join(_ASSETS, "logo.ico"), "volby_dekana/assets"),
    (os.path.join(_ASSETS, "uvod.png"), "volby_dekana/assets"),
    (os.path.join(_ASSETS, "prezencna_template.docx"), "volby_dekana/assets"),
    (os.path.join(_ASSETS, "pokyny_template.docx"), "volby_dekana/assets"),
    (os.path.join(_ASSETS, "hlasovaci_listok_template.docx"), "volby_dekana/assets"),
    (os.path.join(_ASSETS, "prebratie_template.docx"), "volby_dekana/assets"),
    (os.path.join(_ASSETS, "protokol_listok_template.docx"), "volby_dekana/assets"),
    (os.path.join(_ASSETS, "zapisnica_template.docx"), "volby_dekana/assets"),
]
hiddenimports = [
    "docx",
    "PIL",
    "PIL.Image",
    "PIL.ImageTk",
] + collect_submodules("volby_dekana")

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
    icon=_ICON,
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
