# Job Agent

## Overview
A production-ready Python application for automated job search using a multi-agent AI system. Features secure encrypted storage, web scraping, legitimacy checks, and Gmail integration for email drafting.

## Features
- **Secure Vault**: Encrypted storage for API keys and sensitive data.
- **Multi-Agent System**: Researcher, Auditor, Ghostwriter, and Manager agents using CrewAI.
- **Multi-Portal Search**: Covers Indeed, Bayt, GulfTalent, LinkedIn, and All Portals mode.
- **Verified Contacts**: Contact email discovery and audit before draft creation.
- **GUI**: Modern interface with NiceGUI.
- **Bounce Recovery**: Automatic handling of bounced emails.
- **Human-Style Emails**: AI-generated emails following strict guidelines.

## Setup
1. Clone or download the project.
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application: `python main.py`
4. In the GUI, go to 'The Vault' tab, unlock with password 'admin', and set your API keys and client_secret.json path.
5. Authorize Gmail when prompted.

## Cross-Platform Builds
For platform-specific installers, use the provided build tools:
- `build_macos.sh` for macOS `.dmg`/`.app`
- `build_windows.bat` for Windows `.exe`
- `build_linux.sh` for Linux standalone or AppImage
- `build.py` detects your OS and runs the correct build script

The project `logo.png` is now used to generate installer icons and app launcher icons for all supported platforms when the build scripts run.

See `BUILD.md` and `RELEASES.md` for full build, packaging, and distribution instructions.

## Installation and Use
After you build or download a platform-specific installer, follow these steps:

### Windows
1. Download `Elite Job Agent.exe`.
2. Double-click the file to launch.
3. If Windows warns you, choose **More info** → **Run anyway**.
4. In the Vault tab, unlock with password `admin`, save credentials, and authenticate Gmail.

### macOS
1. Download `Elite Job Agent.dmg`.
2. Double-click the `.dmg` file to open.
3. Drag `Elite Job Agent.app` into the Applications folder.
4. Open the app from Applications.
5. Use the Vault tab to save keys and authenticate Gmail.

### Linux
1. Download `Elite_Job_Agent-x86_64.AppImage` or the standalone binary.
2. Make it executable: `chmod +x Elite_Job_Agent-x86_64.AppImage`.
3. Run: `./Elite_Job_Agent-x86_64.AppImage` or `./dist/elite-job-agent`.
4. Complete Vault setup and Gmail authentication.

## Requirements
- Python 3.8+
- API keys for Groq or other LLMs
- Google OAuth client_secret.json for Gmail access

## Security
- All sensitive data is encrypted in vault.dat using hardware-bound keys.
- vault.dat, token.json, and .env are gitignored.
- Local Bandit security scan passed on core source files with no issues found.

## Usage
- Use 'Job Hunt' tab to research jobs.
- Monitor status in 'Dashboard'.
- Manage blacklists in 'Blacklist' tab.
- Adjust communication tone with the slider.
