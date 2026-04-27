# -*- mode: python ; coding: utf-8 -*-
# PyInstaller specification file for Logikus

import os
import sys
import importlib
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules

# Resolve project paths from scripts/logikus.spec
spec_dir = os.path.dirname(os.path.abspath(SPEC))
project_root = os.path.abspath(os.path.join(spec_dir, '..'))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

# pygame-ce is imported as `pygame`; fail early if the active interpreter has no Window API.
pygame_mod = importlib.import_module('pygame')
if not hasattr(pygame_mod, 'Window'):
    raise SystemExit(
        "pygame-ce with `pygame.Window` is required for this build. "
        "Use the same interpreter for pip + PyInstaller (e.g. `python -m PyInstaller ...`)."
    )

if hasattr(pygame_mod, '__path__'):
    pg_datas = collect_data_files('pygame')
    pg_bins = collect_dynamic_libs('pygame')
    pg_hidden = collect_submodules('pygame._sdl2')
else:
    pg_datas = []
    pg_bins = []
    pg_hidden = []

a = Analysis(
    [os.path.join(src_path, 'logikus', 'main.py')],
    pathex=[src_path],
    binaries=pg_bins,
    datas=[
        (os.path.join(src_path, 'logikus', 'images', '*.png'), 'images'),
        (os.path.join(src_path, 'logikus', 'fonts', '*.ttf'), 'fonts'),
    ] + pg_datas,
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
    ] + pg_hidden,
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
