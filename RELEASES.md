# Release and Distribution Guide

This document explains how to package the application for Windows, macOS, and Linux, and how to distribute it safely without committing built binaries directly to the GitHub source repository.

## Licensing and Commercial Distribution

The project is currently licensed under the **MIT License**.
- MIT allows both free and paid use.
- You can earn money by selling the software or offering it as a service.
- MIT does not prevent others from redistributing or modifying the code.

If you want stronger commercial control, consider applying a proprietary or dual license later.

## Recommended Release Strategy

### 1. Build platform-specific installers
Use the provided build scripts for each OS:
- macOS: `build_macos.sh`
- Windows: `build_windows.bat`
- Linux: `build_linux.sh`
- Universal: `build.py`

### 2. Keep source repo clean
Do not commit large binaries or installers into the repository.
The GitHub repository should remain source-only and contain build scripts and docs.

### 3. Publish binaries as assets
Preferred distribution channels:
- **Google Drive** (your preferred hosting)
- **GitHub Releases** (recommended for versioned builds)

Example structure on Google Drive:
```
Elite Job Agent/
├── windows/
│   └── Elite Job Agent.exe
├── mac/
│   └── Elite Job Agent.dmg
└── linux/
    └── Elite_Job_Agent-x86_64.AppImage
```

### 4. Use GitHub Releases if possible
Create a release for each version and upload installers as release assets.
This keeps the source repo clean and the download links stable.

## Build Workflow

### Build for macOS
1. Run:
```bash
chmod +x build_macos.sh
./build_macos.sh
```
2. Output:
- `dist/Elite Job Agent.app`
- `dist/Elite Job Agent.dmg`

### Build for Windows
1. Run:
```batch
build_windows.bat
```
2. Output:
- `dist\Elite Job Agent.exe`

### Build for Linux
1. Run:
```bash
chmod +x build_linux.sh
./build_linux.sh
```
2. Output:
- `dist/elite-job-agent`
- `dist/Elite_Job_Agent-x86_64.AppImage`

## Hosting on Google Drive

Upload the built installer files to Google Drive and share them with customers.
- Keep separate folders per platform
- Use versioned file names, e.g. `Elite_Job_Agent_v1.0.dmg`
- Do not upload `vault.dat`, `token.json`, or `.env`

## GitHub Best Practice

- Keep source code and build scripts in the repo
- Do not add compiled apps or installers to git
- Use release tags and release assets for published installers
- Keep `README.md`, `BUILD.md`, and `RELEASES.md` updated

## Monetization Notes

If you sell the software:
- You can charge for distribution, support, or installation
- MIT lets you sell the project, but it also allows buyers to share it
- A proprietary license would be required if you want to restrict resale or redistribution

## Example Release Process

1. Build installers on the appropriate OS
2. Test each built artifact
3. Create a GitHub release: `v1.0.0`
4. Upload `.dmg`, `.exe`, and `.AppImage` as assets
5. Add release notes and download links to `README.md`
6. Optionally upload the same files to Google Drive for direct customer download

## GitHub Release Workflow

### Using GitHub UI
1. Navigate to the GitHub repository.
2. Click **Releases** → **Draft a new release**.
3. Tag the release (e.g. `v1.0.0`) and give it a title.
4. Add a short changelog or release notes.
5. Upload the platform-specific build assets:
   - `Elite Job Agent.dmg`
   - `Elite Job Agent.exe`
   - `Elite_Job_Agent-x86_64.AppImage`
6. Publish the release.

### Using GitHub CLI
```bash
gh release create v1.0.0 \
  dist/Elite\ Job\ Agent.dmg \
  dist/Elite\ Job\ Agent.exe \
  dist/Elite_Job_Agent-x86_64.AppImage \
  --title "Elite Job Agent v1.0.0" \
  --notes "Initial cross-platform release with macOS, Windows, and Linux installers."
```

### What this gives you
- Stable versioned download links
- Cleaner repo with no binary history
- A professional distribution channel for paying customers

## Security and Compliance

- Do not publish your own API keys, secrets, or local credentials.
- Keep the encrypted vault data private.
- Use the Vault tab to manage keys securely.
- If you accept payments, handle customer data with privacy in mind.
