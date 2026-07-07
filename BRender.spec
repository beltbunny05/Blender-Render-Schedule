# PyInstaller spec for building a standalone Windows executable.

from pathlib import Path


project_root = Path.cwd()
icon_path = project_root / "blender.ico"


a = Analysis(
    ["BRender_App.py"],
    pathex=[str(project_root)],
    binaries=[],
    datas=[],
    hiddenimports=["customtkinter"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="BRender",
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
    icon=str(icon_path) if icon_path.exists() else None,
)
