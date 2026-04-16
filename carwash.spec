# carwash.spec
import os
import sys
from PyInstaller.utils.hooks import collect_submodules

# Получаем путь к корню проекта (работает в .spec файле)
ROOT_DIR = os.getcwd()
SRC_DIR = os.path.join(ROOT_DIR, 'src')
DATA_DIR = os.path.join(ROOT_DIR, 'data')

print(f"📁 ROOT_DIR: {ROOT_DIR}")
print(f"📁 SRC_DIR: {SRC_DIR}")
print(f"📁 DATA_DIR: {DATA_DIR}")

block_cipher = None

a = Analysis(
    [os.path.join(SRC_DIR, 'main.py')],
    pathex=[SRC_DIR, ROOT_DIR],
    binaries=[],
    datas=[
        (DATA_DIR, 'data'),
        (os.path.join(SRC_DIR, 'ui'), 'ui'),
        (os.path.join(SRC_DIR, 'database.py'), '.'),
    ],
    hiddenimports=[
        'PyQt6',
        'PyQt6.QtWidgets',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'sqlite3',
        'database',
        'ui.main_window',
        'ui.order_form',
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
    name='CarwashAdmin',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)