# Job Agent

## Overview
A production-ready Python application for automated job search using a multi-agent AI system. Features secure encrypted storage, web scraping, legitimacy checks, and Gmail integration for email drafting.

## Features
- **Secure Vault**: Encrypted storage for API keys and sensitive data.
- **Multi-Agent System**: Researcher, Auditor, Ghostwriter, and Manager agents using CrewAI.
- **GUI**: Modern interface with NiceGUI.
- **Bounce Recovery**: Automatic handling of bounced emails.
- **Human-Style Emails**: AI-generated emails following strict guidelines.

## Setup
1. Clone or download the project.
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application: `python main.py`
4. In the GUI, go to 'The Vault' tab, unlock with password 'admin', and set your API keys and client_secret.json path.
5. Authorize Gmail when prompted.

## Requirements
- Python 3.8+
- API keys for Groq or other LLMs
- Google OAuth client_secret.json for Gmail access

## Security
- All sensitive data is encrypted in vault.dat using hardware-bound keys.
- vault.dat, token.json, and .env are gitignored.

## Usage
- Use 'Job Hunt' tab to research jobs.
- Monitor status in 'Dashboard'.
- Manage blacklists in 'Blacklist' tab.
- Adjust communication tone with the slider.
