# -*- mode: python ; coding: utf-8 -*-

"""
See https://pyinstaller.readthedocs.io/en/stable/spec-files.html for details
See https://github.com/ssec/sift/blob/master/sift.spec for an example
See https://stackoverflow.com/questions/24049391/how-to-bundle-jar-files-with-pyinstaller for jars

https://github.com/readbeyond/aeneas/blob/master/pyinstaller-onedir.spec#L37

Seems like napari has to be specified in data_files because there are non-python
resources scattered about in the module, and adding it to hidden_imports isn't enough.
"""
# import platform
# import sys
# from os import environ
# from os.path import join, dirname, abspath
#
# import napari
# import vispy.glsl
#
# # local resources
# base_path = getattr(sys, "_MEIPASS", join(dirname(abspath(".")), "_broadside"))
#
# local_datas = [
#     (join(base_path, "broadside", "gui", "styles"), join("broadside", "gui", "styles"))
# ]
#
# # external resources
# if "CONDA_PREFIX" not in environ:
#     raise RuntimeError(
#         """\
# CONDA_PREFIX environment variable not found! The conda environment needs to be
# activated first.
# """
#     )
#
# binaries = []
# if platform.system() != "Darwin":
#     binaries += [(join(environ["CONDA_PREFIX"], "lib", "libfontconfig.so"), "lib")]
#
# hidden_imports = ["vispy.app.backends._pyside2"]

from PyInstaller.building.api import PYZ, EXE, COLLECT
from PyInstaller.building.build_main import Analysis
from PyInstaller.building.datastruct import TOC

hidden_imports = []  # ["numcodecs"]

# excludes = ["tkinter", "black"]
excludes = []

# external_datas = [
#     (dirname(vispy.glsl.__file__), join("vispy", "glsl")),
#     (dirname(napari.__file__), "napari"),
# ]

# set up pyinstaller
block_cipher = None

a = Analysis(
    ["broadside/_run.py"],
    binaries=None,  # binaries,
    datas=[],  # local_datas + external_datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

exclude_qt = [
    # "libQt53DAnimation.so",
    # "libQt53DCore.so",
    # "libQt53DCore.so.5",
    # "libQt5DataVisualization.so.5",
    # "libQt53DExtras.so.5",
    # "libQt53DInput.so.5",
    # "libQt53DQuickInput.so.5",
    # "libQt53DRender.so.5",
    # "libQt5Bluetooth.so.5",
    # "libQt5Charts.so.5",
    # "libQt5Multimedia.so",
    # "libQt5Network.so.5",
    # "libQt5Qml.so.5",
    # "libQt5Quick.so.5",
    # "libQt5QuickParticles.so.5",
    # "libQt5RemoteObjects.so.5",
    # "libQt5WebEngineCore.so.5",
    # "libQt5XmlPatterns.so.5",
    # "QtNetwork.cpython-38-x86_64-linux-gnu.so",
    # "QtQml.cpython-38-x86_64-linux-gnu.so",
    # "qml/*",
]
# a.binaries -= TOC([(file, None, None) for file in exclude_qt])

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    # a.binaries,
    # a.zipfiles,
    # a.datas,
    # [],
    # exclude_binaries=True,
    name="broadside",
    debug=True,
    bootloader_ignore_signals=False,
    # strip=False,
    # upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
)

coll = COLLECT(
    exe, a.binaries, a.zipfiles, a.datas, name="broadside", strip=False, upx=True
)
