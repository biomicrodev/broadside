# -*- mode: python ; coding: utf-8 -*-

"""
See https://pyinstaller.readthedocs.io/en/stable/spec-files.html for details
See https://github.com/ssec/sift/blob/master/sift.spec for an example
See https://stackoverflow.com/questions/24049391/how-to-bundle-jar-files-with-pyinstaller for jars


Seems like napari has to be specified in data_files because there are non-python
resources scattered about in the module, and adding it to hidden_imports isn't enough.
"""
import platform
import sys
from os import environ
from os.path import join, dirname, abspath

import napari
import vispy.glsl

# local resources
base_path = getattr(sys, "_MEIPASS", join(dirname(abspath(".")), "broadside"))

local_datas = [
    (join(base_path, "broadside", "gui", "styles"), join("broadside", "gui", "styles"))
]

# external resources
if "CONDA_PREFIX" not in environ:
    raise RuntimeError(
        """\
CONDA_PREFIX environment variable not found! The conda environment needs to be 
activated first.
"""
    )

binaries = []
if platform.system() != "Darwin":
    binaries += [(join(environ["CONDA_PREFIX"], "lib", "libfontconfig.so"), "lib")]

hidden_imports = ["vispy.app.backends._pyside2"]

excludes = ["tkinter"]

external_datas = [
    (dirname(vispy.glsl.__file__), join("vispy", "glsl")),
    (dirname(napari.__file__), "napari"),
]

# set up pyinstaller
block_cipher = None

a = Analysis(
    ["bin/run.sh"],
    pathex=["../broadside"],
    binaries=binaries,
    datas=local_datas + external_datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="Broadside",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
)
