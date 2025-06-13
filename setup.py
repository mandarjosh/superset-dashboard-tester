# setup.py - For building executables with cx_Freeze
from cx_Freeze import setup, Executable
import sys
import os

# Dependencies are automatically detected, but some modules need help
build_options = {
    'packages': [
        'PyQt5', 
        'selenium', 
        'pandas', 
        'requests', 
        'openpyxl',
        'datetime',
        'time',
        'threading',
        'traceback'
    ],
    'excludes': [
        'tkinter',
        'unittest',
        'email',
        'http',
        'urllib',
        'xml',
        'pydoc'
    ],
    'include_files': [
        'resources/',  # Include logo files
        'config.py',
        'superset_performance_tester.py',
        'scenarios.py',
        'ui_connector.py'
    ],
    'zip_include_packages': ['*'],
    'zip_exclude_packages': []
}

# Base for Windows GUI applications
base = None
if sys.platform == "win32":
    base = "Win32GUI"

# Executable configuration
executables = [
    Executable(
        'main.py',
        base=base,
        target_name='SupersetTester.exe' if sys.platform == "win32" else 'SupersetTester',
        icon='resources/app_icon.ico' if os.path.exists('resources/app_icon.ico') else None
    )
]

setup(
    name='Superset Dashboard Tester',
    version='1.0.0',
    description='Performance testing tool for Apache Superset dashboards',
    author='Woodfrog',
    options={'build_exe': build_options},
    executables=executables
)

# ===== PyInstaller spec file alternative =====
# superset_tester.spec - For PyInstaller (recommended for better compatibility)

"""
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('resources', 'resources'),
        ('config.py', '.'),
        ('superset_performance_tester.py', '.'),
        ('scenarios.py', '.'),
        ('ui_connector.py', '.')
    ],
    hiddenimports=[
        'PyQt5.QtCore',
        'PyQt5.QtGui', 
        'PyQt5.QtWidgets',
        'selenium.webdriver.chrome.service',
        'selenium.webdriver.common.by',
        'selenium.webdriver.support.ui',
        'selenium.webdriver.support.expected_conditions',
        'selenium.common.exceptions',
        'pandas._libs.tslibs.timedeltas',
        'openpyxl.cell._writer'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'IPython',
        'jupyter'
    ],
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
    name='SupersetTester',
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
    icon='resources/app_icon.ico'
)

# For macOS app bundle
app = BUNDLE(
    exe,
    name='SupersetTester.app',
    icon='resources/app_icon.icns',
    bundle_identifier='com.woodfrog.supersettester',
    info_plist={
        'NSHighResolutionCapable': 'True',
        'CFBundleShortVersionString': '1.0.0'
    }
)
"""

# ===== Build Scripts =====

# build_windows.bat
"""
@echo off
echo Building Superset Tester for Windows...

REM Install dependencies
pip install -r requirements.txt
pip install pyinstaller

REM Build with PyInstaller
pyinstaller --onefile --windowed --icon=resources/app_icon.ico --add-data "resources;resources" --add-data "*.py;." main.py --name SupersetTester

REM Alternative with cx_Freeze
REM python setup.py build

echo Build completed! Check the dist/ folder.
pause
"""

# build_mac.sh
"""
#!/bin/bash
echo "Building Superset Tester for macOS..."

# Install dependencies
pip install -r requirements.txt
pip install pyinstaller

# Build with PyInstaller
pyinstaller --onefile --windowed --icon=resources/app_icon.icns --add-data "resources:resources" --add-data "*.py:." main.py --name SupersetTester

# Create DMG (requires create-dmg: brew install create-dmg)
if command -v create-dmg &> /dev/null; then
    echo "Creating DMG..."
    create-dmg \
        --volname "Superset Tester" \
        --window-pos 200 120 \
        --window-size 600 300 \
        --icon-size 100 \
        --icon "SupersetTester.app" 175 120 \
        --hide-extension "SupersetTester.app" \
        --app-drop-link 425 120 \
        "SupersetTester.dmg" \
        "dist/"
    echo "DMG created: SupersetTester.dmg"
else
    echo "create-dmg not found. Install with: brew install create-dmg"
    echo "App bundle created in dist/ folder"
fi

echo "Build completed!"
"""