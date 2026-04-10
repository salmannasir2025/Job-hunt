#!/bin/bash

# Linux Build Script for Elite Job Agent
# Builds standalone executable and AppImage for Linux
# Usage: bash build_linux.sh
# Supports: Ubuntu, Debian, Fedora, Arch, and other Linux distros

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$PROJECT_ROOT/build"
DIST_DIR="$PROJECT_ROOT/dist"
ASSETS_DIR="$PROJECT_ROOT/assets"
SPEC_DIR="$PROJECT_ROOT/build_specs"

APP_NAME="Elite Job Agent"
APP_VERSION="1.0.0"
BUNDLE_ID="com.salman.elite-job-agent"
APPIMAGE_DIR="$BUILD_DIR/AppImage"

echo "🐧 Linux Build System"
echo "🔨 Building Elite Job Agent for Linux..."
echo "========================================"

# Detect Python Executable
PYTHON_EXECUTABLE=$(if [ -x .venv_stable/bin/python ]; then printf '%s' ".venv_stable/bin/python"; \
    elif [ -x .venv/bin/python ]; then printf '%s' ".venv/bin/python"; \
    elif [ -x .venv_automated/bin/python ]; then printf '%s' ".venv_automated/bin/python"; \
    elif [ -x venv/bin/python ]; then printf '%s' "venv/bin/python"; \
    elif command -v python3 &> /dev/null; then command -v python3; \
    else command -v python; fi)

echo "🔍 Running System Alignment Check..."
"$PYTHON_EXECUTABLE" system_validator.py || { echo "❌ System alignment failed"; exit 1; }

# Step 1: Detect Linux distribution
echo "📋 Detecting Linux distribution..."
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO=$ID
    DISTRO_NAME=$NAME
else
    echo "⚠️  Could not detect Linux distribution"
    DISTRO="linux"
    DISTRO_NAME="Linux"
fi
echo "✅ Distribution: $DISTRO_NAME"

# Step 2: Check and install system dependencies
echo ""
echo "📦 Checking system dependencies..."

install_dependencies() {
    case $DISTRO in
        ubuntu|debian)
            echo "🔧 Installing dependencies for Ubuntu/Debian..."
            sudo apt-get update
            sudo apt-get install -y \
                python3-dev \
                python3-pip \
                python3-venv \
                libssl-dev \
                libffi-dev \
                build-essential \
                libdbus-1-dev \
                libgtk-3-dev \
                libappindicator3-dev
            ;;
        fedora|rhel)
            echo "🔧 Installing dependencies for Fedora/RHEL..."
            sudo dnf install -y \
                python3-devel \
                libssl-devel \
                libffi-devel \
                gcc \
                gcc-c++ \
                dbus-devel \
                gtk3-devel
            ;;
        arch)
            echo "🔧 Installing dependencies for Arch Linux..."
            sudo pacman -S --noconfirm \
                python \
                base-devel \
                libffi \
                openssl \
                dbus \
                gtk3
            ;;
        opensuse*)
            echo "🔧 Installing dependencies for openSUSE..."
            sudo zypper install -y \
                python3-devel \
                openssl-devel \
                libffi-devel \
                gcc \
                gcc-c++ \
                dbus-1-devel \
                gtk3-devel
            ;;
        *)
            echo "⚠️  Unknown distribution. Please ensure these are installed:"
            echo "   - Python 3.8+"
            echo "   - Build tools (gcc, make)"
            echo "   - OpenSSL dev"
            echo "   - GTK3 dev (optional, for better UI)"
            ;;
    esac
}

# Ask user if they want to install system dependencies
read -p "Install system dependencies? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    install_dependencies
else
    echo "⚠️  Skipping system dependency installation"
fi

# Step 3: Create virtual environment
echo ""
echo "🐍 Setting up Python virtual environment..."
if [ ! -d "$PROJECT_ROOT/venv" ]; then
    python3 -m venv "$PROJECT_ROOT/venv"
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
source "$PROJECT_ROOT/venv/bin/activate"

# Step 4: Install Python dependencies
echo ""
echo "📚 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller
pip install linuxdeploy
pip install pillow

echo "✅ Dependencies installed"

# Step 5: Create directories
mkdir -p "$BUILD_DIR" "$DIST_DIR" "$ASSETS_DIR" "$SPEC_DIR"

# Step 6: Create icon from logo.png if missing
if [ ! -f "$ASSETS_DIR/app_icon.png" ]; then
    if [ -f "$PROJECT_ROOT/logo.png" ]; then
        echo "🖼️ Generating app_icon.png from logo.png..."
        python3 - <<'PY'
from pathlib import Path
from PIL import Image
logo = Path('$PROJECT_ROOT/logo.png')
icon = Path('$ASSETS_DIR/app_icon.png')
img = Image.open(logo).convert('RGBA')
img = img.resize((512, 512), Image.LANCZOS)
icon.parent.mkdir(parents=True, exist_ok=True)
img.save(icon)
PY
        if [ -f "$ASSETS_DIR/app_icon.png" ]; then
            echo "✅ Generated $ASSETS_DIR/app_icon.png from logo.png"
        else
            echo "⚠️  Failed to generate $ASSETS_DIR/app_icon.png"
        fi
    else
        echo "⚠️  No app_icon.png found in assets/"
        echo "   Place a 512x512 PNG icon there for better appearance"
    fi
else
    echo "✅ Icon found: $ASSETS_DIR/app_icon.png"
fi

# Step 7: Build with PyInstaller (standalone)
echo ""
echo "🔨 Building standalone executable with PyInstaller..."
python3 -m PyInstaller \
    --name="elite-job-agent" \
    --onefile \
    --windowed \
    --icon="$ASSETS_DIR/app_icon.png" \
    --add-data "requirements.txt:." \
    --add-data "README.md:." \
    --add-data ".gitignore:." \
    --hidden-import=nicegui \
    --hidden-import=crewai \
    --hidden-import=cryptography \
    --hidden-import=google.oauth2 \
    --hidden-import=googleapiclient \
    --hidden-import=groq \
    main.py

echo "✅ Standalone executable built"

# Step 8: Create AppImage (portable across all Linux distros)
echo ""
echo "📦 Creating AppImage (portable Linux app)..."

# Create AppImage directory structure
APPIMAGE_BUILD="$APPIMAGE_DIR/Elite_Job_Agent"
mkdir -p "$APPIMAGE_BUILD/usr/bin"
mkdir -p "$APPIMAGE_BUILD/usr/share/applications"
mkdir -p "$APPIMAGE_BUILD/usr/share/icons/hicolor/512x512/apps"

# Copy executable
cp "$DIST_DIR/elite-job-agent" "$APPIMAGE_BUILD/usr/bin/"
chmod +x "$APPIMAGE_BUILD/usr/bin/elite-job-agent"

# Create desktop entry
cat > "$APPIMAGE_BUILD/usr/share/applications/elite-job-agent.desktop" << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=Elite Job Agent
Comment=Production-ready job search automation tool
Exec=elite-job-agent
Icon=elite-job-agent
Categories=Office;Utility;
Terminal=false
X-AppImage-Version=1.0.0
EOF

# Copy icon if available
if [ -f "$ASSETS_DIR/app_icon.png" ]; then
    cp "$ASSETS_DIR/app_icon.png" "$APPIMAGE_BUILD/usr/share/icons/hicolor/512x512/apps/elite-job-agent.png"
fi

# Create AppImage if appimagetool is available
if command -v appimagetool &> /dev/null; then
    echo "   Using appimagetool to create AppImage..."
    appimagetool "$APPIMAGE_BUILD" "$DIST_DIR/Elite_Job_Agent-x86_64.AppImage"
    chmod +x "$DIST_DIR/Elite_Job_Agent-x86_64.AppImage"
    echo "✅ AppImage created: $DIST_DIR/Elite_Job_Agent-x86_64.AppImage"
else
    echo "⚠️  appimagetool not found"
    echo "   AppImage creation requires appimagetool:"
    echo "   Ubuntu/Debian: sudo apt-get install appimage-builder"
    echo "   Or download from: https://github.com/AppImage/AppImageKit/releases"
    echo ""
    echo "   Standalone executable is available in: $DIST_DIR/elite-job-agent"
fi

# Step 9: Create desktop launcher for convenience
echo ""
echo "🖥️  Creating desktop launcher..."
LAUNCHER_DIR="$HOME/.local/share/applications"
mkdir -p "$LAUNCHER_DIR"

cat > "$LAUNCHER_DIR/elite-job-agent.desktop" << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=Elite Job Agent
Comment=Job search automation tool
Exec=elite-job-agent
Icon=elite-job-agent
Categories=Office;Utility;
Terminal=false
EOF

chmod +x "$LAUNCHER_DIR/elite-job-agent.desktop"

# Step 10: Verify build
echo ""
echo "✅ Build completed successfully!"
echo ""
echo "📊 Build Summary:"
echo "   - App Name: $APP_NAME"
echo "   - Version: $APP_VERSION"
echo "   - Distribution: $DISTRO_NAME"
echo ""
echo "📁 Output Files:"
echo "   - Standalone: $DIST_DIR/elite-job-agent"

if [ -f "$DIST_DIR/Elite_Job_Agent-x86_64.AppImage" ]; then
    echo "   - AppImage: $DIST_DIR/Elite_Job_Agent-x86_64.AppImage"
fi

echo ""
echo "🚀 To run the application:"
echo ""
echo "   Option 1 - Standalone executable:"
echo "   $ $DIST_DIR/elite-job-agent"
echo ""
echo "   Option 2 - From applications menu:"
echo "   Click Activities → Search 'Elite Job Agent'"
echo ""

if [ -f "$DIST_DIR/Elite_Job_Agent-x86_64.AppImage" ]; then
    echo "   Option 3 - Run AppImage (portable):"
    echo "   $ $DIST_DIR/Elite_Job_Agent-x86_64.AppImage"
    echo ""
    echo "   Make portable (no reinstall needed on any Linux):"
    echo "   $ chmod +x $DIST_DIR/Elite_Job_Agent-x86_64.AppImage"
    echo "   $ mv $DIST_DIR/Elite_Job_Agent-x86_64.AppImage ~/Elite_Job_Agent"
    echo ""
fi

echo "📦 To share with others:"
echo "   - Share the AppImage file (works on any Linux)"
echo "   - Or the standalone executable"
echo "   - No dependencies needed - it's self-contained!"
echo ""

# Deactivate virtual environment
deactivate
