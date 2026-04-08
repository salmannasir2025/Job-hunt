# Building Elite Job Agent

Complete guide to building standalone applications for macOS, Windows, and Linux.

## Overview

The Elite Job Agent can be packaged as:
- **macOS**: `.app` bundle + `.dmg` installer
- **Windows**: `.exe` standalone executable + optional installer
- **Linux**: AppImage (portable) + standalone executable

Users can then simply **click and run** without needing Python installed.

---

## Prerequisites

### All Platforms
- Python 3.8 or higher
- Git (for cloning repo)

### macOS
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install build tools
brew install python3 create-dmg
```

### Windows
```batch
# Install Python 3.8+ from https://www.python.org/downloads/
# Ensure "Add Python to PATH" is checked during installation

# Install NSIS for installer (optional)
# Download from: https://nsis.sourceforge.io/Download
```

### Linux (Ubuntu/Debian)
```bash
sudo apt-get install python3 python3-pip python3-venv build-essential

# Optional for AppImage
sudo apt-get install appimage-builder
```

### Linux (Fedora)
```bash
sudo dnf install python3 python3-pip gcc gcc-c++ make

# Optional for AppImage
sudo dnf install appimage-builder
```

---

## Quick Build

### macOS
```bash
chmod +x build_macos.sh
./build_macos.sh
```

Output: `dist/Elite Job Agent.dmg` and `dist/Elite Job Agent.app`

### Windows
```batch
build_windows.bat
```

Output: `dist\Elite Job Agent.exe`

### Linux
```bash
chmod +x build_linux.sh
./build_linux.sh
```

Output: 
- `dist/elite-job-agent` (standalone)
- `dist/Elite_Job_Agent-x86_64.AppImage` (portable)

---

## Detailed Build Instructions

### macOS Build

1. **Install dependencies**:
```bash
brew install python3 create-dmg
```

2. **Prepare icon** (optional but recommended):
- Create a 512x512 PNG image named `assets/app_icon.png`
- Convert to `.icns` using online tool or:
```bash
python3 << 'EOF'
from PIL import Image
img = Image.open('assets/app_icon.png')
img.save('assets/app_icon.icns')
EOF
```

3. **Run build**:
```bash
chmod +x build_macos.sh
./build_macos.sh
```

4. **What you get**:
- `dist/Elite Job Agent.app` - Runnable application (double-click to run)
- `dist/Elite Job Agent.dmg` - Installer for distribution

5. **Distribute to users**:
- Share the `.dmg` file
- Users double-click to open
- Drag app to Applications folder
- Click to launch

---

### Windows Build

1. **Install Python 3.8+**:
- Download from https://www.python.org/downloads/
- **Important**: Check "Add Python to PATH"

2. **Install build tool** (optional):
```batch
pip install pyinstaller
```

3. **Run build**:
```batch
build_windows.bat
```

4. **What you get**:
- `dist\Elite Job Agent.exe` - Direct standalone executable

5. **Distribute to users**:
- Share the `.exe` file
- Users double-click to run (no installation needed)
- Everything is bundled inside

**Optional: Create Windows Installer**

For a professional installer with uninstall support, install NSIS:
- Download from: https://nsis.sourceforge.io/Download
- We can create a `.nsi` script for full installer

---

### Linux Build

#### Option 1: Automatic Build (Recommended)

```bash
chmod +x build_linux.sh
./build_linux.sh
```

The script will:
1. Detect your Linux distribution
2. Install system dependencies (asks for permission)
3. Create Python virtual environment
4. Build standalone executable
5. Create AppImage (if appimagetool available)
6. Add desktop launcher

#### Option 2: Manual Build

```bash
# Install dependencies
pip install pyinstaller

# Build executable
python3 -m PyInstaller \
    --name="elite-job-agent" \
    --onefile \
    --windowed \
    main.py

# Run
./dist/elite-job-agent
```

#### Option 3: Using AppImage for Maximum Portability

```bash
# Install appimagetool first
sudo apt-get install appimage-builder  # Ubuntu/Debian
# or
sudo dnf install appimage-builder      # Fedora

# Then run build
./build_linux.sh
```

4. **What you get**:
- `dist/elite-job-agent` - Standalone (no dependencies)
- `dist/Elite_Job_Agent-x86_64.AppImage` - Portable (works on any Linux)

5. **Distribute to users**:

**AppImage (Recommended)**:
```bash
chmod +x Elite_Job_Agent-x86_64.AppImage
./Elite_Job_Agent-x86_64.AppImage
```

**Standalone**:
```bash
./elite-job-agent
```

**From applications menu**:
- Activities → Search "Elite Job Agent"

---

## Install and Use After Download

Once you have built or downloaded a platform-specific package, use the following instructions to install and run the app.

### Windows
- If you built the standalone executable, share `dist\Elite Job Agent.exe`.
- Users simply double-click the file.
- If Windows warns about unknown publisher, click **More info** and **Run anyway**.
- Once the app opens, set up the Vault and authenticate Gmail.

### macOS
- Share `dist/Elite Job Agent.dmg`.
- User opens the `.dmg`, then drags `Elite Job Agent.app` to Applications.
- Optionally, right-click the app and choose **Open** if macOS blocks it on first launch.
- After launching, use the Vault tab to complete API and Gmail setup.

### Linux
- Share `dist/Elite_Job_Agent-x86_64.AppImage` or the standalone binary.
- Make the file executable:
```bash
chmod +x dist/Elite_Job_Agent-x86_64.AppImage
```
- Run it:
```bash
./dist/Elite_Job_Agent-x86_64.AppImage
```
- For the standalone binary:
```bash
chmod +x dist/elite-job-agent
./dist/elite-job-agent
```
- Complete the Vault settings and Gmail auth.

### First Use
- Open the app and go to the **Vault** tab.
- Unlock with the password `admin`.
- Save your Groq API key.
- Save the `client_secret.json` path.
- Click **Authenticate Gmail** and complete the browser popup flow.
- After authentication, start using the Job Hunt tab.

---

## File Structure After Build

```
dist/
├── Elite Job Agent.app/          # macOS app bundle
├── Elite Job Agent.dmg           # macOS installer
├── Elite Job Agent.exe           # Windows executable
├── elite-job-agent               # Linux standalone
└── Elite_Job_Agent-x86_64.AppImage  # Linux portable
```

---

## Configuration for Users

After installation, users:

1. **Launch the app** (click icon)
2. **First run**:
   - Opens The Vault tab
   - Enter password: `admin` ← **CHANGE THIS IN PRODUCTION**
   - Add Groq API key
   - Add `client_secret.json` path
   - Click "Authenticate Gmail" (browser opens for account selection)
   - Done! Ready to search jobs

---

## Troubleshooting

### macOS: "App is damaged, can't be opened"
```bash
# Grant permission
xattr -d com.apple.quarantine "dist/Elite Job Agent.app"
```

### Windows: "Windows protected your PC"
- Click "More info"
- Click "Run anyway"
- Or sign executable with code certificate (production)

### Linux: Permission denied
```bash
chmod +x dist/elite-job-agent
./dist/elite-job-agent
```

### Missing Python on target machine
- Use AppImage (macOS `.dmg`, Windows `.exe` already bundled)
- Everything is self-contained - no Python installation needed

---

## Icon Creation

For professional appearance, create icons:

### Create from PNG
```bash
# macOS (requires PIL)
pip install Pillow
python3 << 'EOF'
from PIL import Image
img = Image.open('assets/icon_512.png')
img.save('assets/app_icon.icns')
EOF
```

### Online Converters
- https://icoconvert.com/ - PNG to ICO/ICNS
- https://convertio.co/png-icns/ - Online converter

### Recommended Specifications
- **PNG**: 512x512 pixels
- **macOS `.icns`**: Converted from PNG
- **Windows `.ico`**: Converted from PNG
- **Linux `.png`**: Use 512x512 directly

---

## Production Considerations

### Code Signing (macOS)
```bash
codesign --deep --force --verify --verbose --sign - "dist/Elite Job Agent.app"
```

### Code Signing (Windows)
- Requires certificate from trusted CA
- Use: `signtool sign /f certificate.pfx app.exe`

### Update Management
Consider adding:
- In-app update checker
- Version file on GitHub
- Auto-download new version

### Security Checklist
- [ ] Change default vault password
- [ ] Remove hardcoded credentials
- [ ] Use environment variables
- [ ] Test on fresh install
- [ ] Verify no Python files exposed
- [ ] Check dependencies are current

---

## Size Reference

Typical build sizes:
- **macOS .dmg**: 200-300 MB
- **Windows .exe**: 150-250 MB
- **Linux AppImage**: 150-250 MB
- **Linux standalone**: 150-250 MB

Sizes vary based on included libraries and assets.

---

## Distribution

### Option 1: GitHub Releases
```bash
gh release create v1.0.0 dist/*
```

### Option 2: Personal Website
- Host `.dmg`, `.exe`, `.AppImage` files
- Users download and run

### Option 3: App Stores (Future)
- Mac App Store
- Microsoft Store
- Snap Store (Linux)

---

## Next Steps

1. **Create icons** for professional appearance
2. **Test builds** on each platform
3. **Create installer script** for Windows (NSIS)
4. **Sign executables** for production
5. **Set up release workflow** on GitHub
6. **Add auto-update** functionality

---

## Support

For issues:
1. Check build logs
2. Verify Python version (3.8+)
3. Ensure dependencies installed
4. Check file permissions
5. Review GitHub issues

---

## Summary

| Platform | Output | Deploy | Size |
|----------|--------|--------|------|
| macOS | .dmg + .app | Users download & drag to Applications | 200-300 MB |
| Windows | .exe | Users download & run | 150-250 MB |
| Linux | AppImage + binary | Users download & run | 150-250 MB |

**End Result**: Users click icon → app runs. No Python needed! 🚀
