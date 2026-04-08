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

APP_NAME="Elite Job Agent"
APP_VERSION="1.0.0"
BUNDLE_ID="com.salman.elite-job-agent"

echo "🔨 Building Elite Job Agent for macOS..."
echo "========================================"

# Step 1: Check dependencies
echo "📋 Checking dependencies..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found"
    exit 1
fi

if ! python3 -m pip show pyinstaller &> /dev/null; then
    echo "⚠️  PyInstaller not installed. Installing..."
    python3 -m pip install pyinstaller
fi

if ! command -v create-dmg &> /dev/null; then
    echo "⚠️  create-dmg not found. Install with: brew install create-dmg"
    echo "   Or: npm install -g create-dmg"
fi

# Step 2: Create assets directory if needed
mkdir -p "$ASSETS_DIR"

# Step 3: Check for icon
if [ ! -f "$ASSETS_DIR/app_icon.icns" ]; then
    echo "⚠️  No app_icon.icns found in assets/"
    echo "   Place a 512x512 PNG and run: "
    echo "   python3 -c \"from PIL import Image; img = Image.open('assets/icon.png'); img.save('assets/app_icon.icns')\""
    echo "   Or create using online converter"
fi

# Step 4: Create spec file
echo "📝 Generating PyInstaller spec file..."
python3 build_config.py

# Step 5: Build with PyInstaller
echo "🔨 Running PyInstaller..."
python3 -m PyInstaller \
    --name="Elite Job Agent" \
    --windowed \
    --onedir \
    --icon="$ASSETS_DIR/app_icon.icns" \
    --osx-bundle-identifier="$BUNDLE_ID" \
    --add-data "requirements.txt:." \
    --add-data "README.md:." \
    --add-data ".gitignore:." \
    main.py

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
    echo "⚠️  create-dmg not available. Skipping DMG creation."
    echo "   Install with: brew install create-dmg"
    echo "   Or use macOS Disk Utility to create DMG manually"
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
