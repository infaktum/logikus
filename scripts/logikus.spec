# -*- mode: python ; coding: utf-8 -*-
# PyInstaller specification file for Logikus

import os
import sys

# Resolve project paths from scripts/logikus.spec
spec_dir = os.path.dirname(os.path.abspath(SPEC))
project_root = os.path.abspath(os.path.join(spec_dir, '..'))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

a = Analysis(
    [os.path.join(src_path, 'logikus', 'main.py')],
    pathex=[src_path],
    binaries=[],
    datas=[
        (os.path.join(src_path, 'logikus', 'images', '*.png'), 'images'),
        (os.path.join(src_path, 'logikus', 'fonts', '*.ttf'), 'fonts'),
    ],
    hiddenimports=[
        'pygame',
        'logikus',
        'logikus.assets',
        'logikus.controller',
        'logikus.logic',
        'logikus.ui',
        'logikus.wiring',
        'tkinter',
        'tkinter.filedialog',
        'tkinter.messagebox',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[
        'pkg_resources',
        'setuptools',
        'jaraco',
        'jaraco.text',
        'jaraco.functools',
        'platformdirs'
    ],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Logikus',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
