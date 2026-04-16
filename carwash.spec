# carwash.spec
# -*- mode: python ; coding: utf-8 -*-

import sys
import os

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    binaries=[],
    datas=[('src/locales/*.json', 'locales')],
    hiddenimports=[
        'database',
        'database.migrations',
        'openpyxl',
        'bcrypt',
        'matplotlib',
        'reportlab',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'services',
        'services.client_service',
        'services.order_service',
        'services.user_service',
        'services.consumable_service',
        'repositories',
        'repositories.base',
        'repositories.client_repo',
        'repositories.order_repo',
        'repositories.user_repo',
        'repositories.consumable_repo',
        'models',
        'models.client',
        'models.order',
        'models.user',
        'models.consumable',
        'ui',
        'ui.widgets',
        'ui.dialogs',
        'utils',
        'license_manager',
        'backup_manager',
        'logger',
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
    [],
    exclude_binaries=True,  # ← ВАЖНО: True для --onedir
    name='CarWashAdmin',
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
    icon='icon.ico'
)

# ← ВАЖНО: секция COLLECT создаёт папку со всеми файлами
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CarWashAdmin'  # ← Имя выходной папки
)