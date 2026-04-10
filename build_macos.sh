#!/bin/bash

# macOS Build Script for Elite Job Agent
# Builds .app bundle and .dmg installer for macOS
# Usage: bash build_macos.sh

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$PROJECT_ROOT/build"
DIST_DIR="$PROJECT_ROOT/dist"
ASSETS_DIR="$PROJECT_ROOT/assets"
SPEC_DIR="$PROJECT_ROOT/build_specs"
LOGO_PNG="$PROJECT_ROOT/logo.png"

APP_NAME="Elite Job Agent"
PYTHON_EXECUTABLE="${PYTHON_EXECUTABLE:-$(cd "$PROJECT_ROOT" && \
    if [ -x .venv_stable/bin/python ]; then printf '%s' "$PROJECT_ROOT/.venv_stable/bin/python"; \
    elif [ -x .venv/bin/python ]; then printf '%s' "$PROJECT_ROOT/.venv/bin/python"; \
    elif [ -x .venv_automated/bin/python ]; then printf '%s' "$PROJECT_ROOT/.venv_automated/bin/python"; \
    elif command -v python3 &> /dev/null; then command -v python3; \
    else command -v python; fi)}"

echo "🔍 Running System Alignment Check..."
"$PYTHON_EXECUTABLE" system_validator.py || { echo "❌ System alignment failed"; exit 1; }

if [ -z "$PYTHON_EXECUTABLE" ]; then
    echo "❌ Python 3 not found"
    exit 1
fi

if ! "$PYTHON_EXECUTABLE" -m pip show pyinstaller &> /dev/null; then
    echo "⚠️  PyInstaller not installed. Installing..."
    "$PYTHON_EXECUTABLE" -m pip install pyinstaller Pillow
fi

if ! command -v create-dmg &> /dev/null; then
    echo "⚠️  create-dmg not found. Install with: brew install create-dmg"
    echo "   Or: npm install -g create-dmg"
fi

# Step 2: Create assets directory if needed
mkdir -p "$ASSETS_DIR"

# Step 3: Create app icon from logo.png if missing
if [ ! -f "$ASSETS_DIR/app_icon.icns" ]; then
    if [ -f "$LOGO_PNG" ]; then
        echo "🖼️ Generating app_icon.icns from logo.png..."
        ICONSET_DIR="$ASSETS_DIR/app_icon.iconset"
        rm -rf "$ICONSET_DIR"
        mkdir -p "$ICONSET_DIR"

        "$PYTHON_EXECUTABLE" - <<PY
from pathlib import Path
from PIL import Image
base = Path('$LOGO_PNG')
iconset = Path('$ICONSET_DIR')
img = Image.open(base).convert('RGBA')
if img.width != img.height:
    size = max(img.width, img.height)
    background = Image.new('RGBA', (size, size), (0,0,0,0))
    background.paste(img, ((size-img.width)//2, (size-img.height)//2), img)
    img = background
sizes = [16, 32, 64, 128, 256, 512, 1024]
for size in sizes:
    for suffix in ['', '@2x']:
        actual = size * (2 if suffix == '@2x' else 1)
        icon_file = iconset / f'icon_{size}x{size}{suffix}.png'
        img.resize((actual, actual), Image.LANCZOS).save(icon_file)
PY
        if command -v iconutil &> /dev/null; then
            iconutil -c icns "$ICONSET_DIR" -o "$ASSETS_DIR/app_icon.icns"
            echo "✅ Generated $ASSETS_DIR/app_icon.icns"
            rm -rf "$ICONSET_DIR"
        else
            echo "⚠️  iconutil not available; please install Xcode command line tools or provide assets/app_icon.icns"
        fi
    else
        echo "⚠️  logo.png found but app_icon.icns could not be generated"
    fi
else
    echo "✅ App icon exists: $ASSETS_DIR/app_icon.icns"
fi

# Step 4: Create spec file
echo "📝 Generating PyInstaller spec file..."
"$PYTHON_EXECUTABLE" build_config.py

# Step 5: Build with PyInstaller
echo "🔨 Running PyInstaller..."
"$PYTHON_EXECUTABLE" -m PyInstaller \
    --clean \
    --noconfirm \
    --workpath="$BUILD_DIR" \
    --distpath="$DIST_DIR" \
    "build_specs/elite_job_agent.spec"

# Step 6: Remove old build artifacts
rm -rf "$DIST_DIR/Elite Job Agent.dmg" 2>/dev/null || true

# Step 7: Create DMG installer
echo "📦 Creating .dmg installer..."
if command -v create-dmg &> /dev/null; then
    create-dmg \
        --volname "Elite Job Agent Installer" \
        --volicon "$ASSETS_DIR/app_icon.icns" \
        --window-pos 200 120 \
        --window-size 800 400 \
        --icon-size 100 \
        --icon "Elite Job Agent.app" 200 190 \
        --hide-extension "Elite Job Agent.app" \
        --app-drop-link 600 190 \
        "$DIST_DIR/Elite Job Agent.dmg" \
        "$DIST_DIR/Elite Job Agent.app"
    echo "✅ DMG created: $DIST_DIR/Elite Job Agent.dmg"
else
    echo "⚠️  create-dmg not available. Falling back to hdiutil..."
    hdiutil create -volname "Elite Job Agent Installer" -srcfolder "$DIST_DIR/Elite Job Agent.app" -ov -format UDZO "$DIST_DIR/Elite Job Agent.dmg"
    if [ -f "$DIST_DIR/Elite Job Agent.dmg" ]; then
        echo "✅ DMG created using hdiutil: $DIST_DIR/Elite Job Agent.dmg"
    else
        echo "❌ DMG creation failed."
    fi
fi

# Step 8: Verify build
if [ -d "$DIST_DIR/Elite Job Agent.app" ]; then
    echo "✅ App bundle created successfully!"
    echo "   Location: $DIST_DIR/Elite Job Agent.app"
    echo ""
    echo "📊 Build Summary:"
    echo "   - App Name: $APP_NAME"
    echo "   - Version: $APP_VERSION"
    echo "   - Bundle ID: $BUNDLE_ID"
    echo ""
    echo "🚀 To run the app:"
    echo "   open '$DIST_DIR/Elite Job Agent.app'"
    echo ""
    echo "📦 To distribute:"
    echo "   1. Users download and open Elite Job Agent.dmg"
    echo "   2. Drag Elite Job Agent.app to Applications folder"
    echo "   3. Click Applications → Elite Job Agent.app to launch"
else
    echo "❌ Build failed!"
    exit 1
fi
