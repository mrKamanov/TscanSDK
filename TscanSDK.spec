# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_dynamic_libs

block_cipher = None

# Собираем все DLL из numpy и opencv
binaries = []
binaries.extend(collect_dynamic_libs('numpy'))
binaries.extend(collect_dynamic_libs('cv2'))

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=binaries,  # Добавляем собранные DLL
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
        ('assets', 'assets'),
    ],
    hiddenimports=[
        'engineio.async_drivers.threading',
        'flask',
        'flask_socketio',
        'flask_cors',
        'cv2',
        'numpy',
        'numpy.core._methods',
        'numpy.lib.format',
        'numpy.random',
        'numpy.random.common',
        'numpy.random.bounded_integers',
        'numpy.random.entropy',
        'jinja2.ext',
        'engineio.async_drivers.threading',
        'dns.resolver',
        'pkg_resources.py2_warn',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='TscanSDK',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None
) 