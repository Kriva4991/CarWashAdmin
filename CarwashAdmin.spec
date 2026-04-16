# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('data', 'data'), ('src/ui', 'ui'), ('src/database.py', '.')],
    hiddenimports=['sqlite3', 'bcrypt', 'matplotlib', 'matplotlib.backends.backend_qt5agg', 'reportlab', 'reportlab.lib', 'reportlab.platypus', 'database', 'ui.main_window', 'ui.order_form_multi', 'ui.login_dialog', 'ui.services_editor', 'ui.shift_manager', 'ui.reports_tab', 'ui.clients_tab', 'ui.settings_tab'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CarwashAdmin',
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
    icon=['icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CarwashAdmin',
)
