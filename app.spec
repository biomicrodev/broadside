# -*- mode: python ; coding: utf-8 -*-

"""
See https://pyinstaller.readthedocs.io/en/stable/spec-files.html for details
See https://github.com/ssec/sift/blob/master/sift.spec for an example

Seems like napari has to be specified in data_files because there are non-python
resources scattered about in the module, and adding it to hidden_imports isn't enough.
"""

from os import environ
from os.path import join, dirname

import napari
import vispy.glsl

if "CONDA_PREFIX" not in environ:
    raise RuntimeError(
        """\
CONDA_PREFIX environment variable not found! You probably need to activate the conda 
environment first.
"""
    )


binaries = [(join(environ["CONDA_PREFIX"], "lib", "libfontconfig.so"), "lib")]

hidden_imports = ["vispy.app.backends._pyside2"]

data_files = [
    (dirname(vispy.glsl.__file__), join("vispy", "glsl")),
    (dirname(napari.__file__), "napari"),
]

block_cipher = None

a = Analysis(
    ["bin/run.py"],
    pathex=["../broadside"],
    binaries=binaries,
    datas=data_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter"],
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
