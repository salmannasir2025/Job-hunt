"""
PyInstaller Configuration for Elite Job Agent
Generates standalone executable for macOS and Windows
"""

import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent
BUILD_DIR = PROJECT_ROOT / 'build'
DIST_DIR = PROJECT_ROOT / 'dist'
SPEC_DIR = PROJECT_ROOT / 'build_specs'

# Create directories
BUILD_DIR.mkdir(exist_ok=True)
DIST_DIR.mkdir(exist_ok=True)
SPEC_DIR.mkdir(exist_ok=True)

# Application metadata
APP_NAME = 'Elite Job Agent'
APP_VERSION = '1.0.0'
AUTHOR = 'Salman'
DESCRIPTION = 'Production-ready job search automation tool'

# PyInstaller spec file content
PYINSTALLER_SPEC = f'''# -*- mode: python ; coding: utf-8 -*-
a = Analysis(
    ['{PROJECT_ROOT / "main.py"}'],
    pathex=[],
    binaries=[],
    datas=[
        ('{PROJECT_ROOT / "requirements.txt"}', '.'),
    ],
    hiddenimports=[
        'nicegui',
        'crewai',
        'cryptography',
        'google.oauth2',
        'google.auth',
        'googleapiclient',
        'groq',
        'requests',
        'bs4',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludedimports=[],
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
    name='Elite Job Agent',
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
    icon='{PROJECT_ROOT / "assets/app_icon.icns"}',
)

app = BUNDLE(
    exe,
    name='Elite Job Agent.app',
    icon='{PROJECT_ROOT / "assets/app_icon.icns"}',
    bundle_identifier='com.salman.elite-job-agent',
    info_plist={{
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': 'True',
        'NSRequiresIPhoneOS': False,
    }},
    entitlements_file=None,
)
'''

def create_spec_file():
    """Create PyInstaller spec file"""
    spec_path = SPEC_DIR / 'elite_job_agent.spec'
    with open(spec_path, 'w') as f:
        f.write(PYINSTALLER_SPEC)
    print(f"✅ Spec file created: {spec_path}")

if __name__ == '__main__':
    create_spec_file()
    print(f"\nBuild configuration initialized:")
    print(f"  App Name: {APP_NAME}")
    print(f"  Version: {APP_VERSION}")
    print(f"  Build Dir: {BUILD_DIR}")
    print(f"  Dist Dir: {DIST_DIR}")
