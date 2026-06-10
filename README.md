> [!WARNING]
> Usage of this tool is entirely at your own risk. The author assumes no responsibility for any adverse consequences that may arise from its use.

# ExitLag Auto Signup

A tool to automate account creation on ExitLag, with support for multiple plans, automatic language detection, and a self-update system.

## Features

- Automatic account creation for 3-day and 7-day plans
- Supports Chrome, Brave and Opera GX
- Password complexity checker with random password generation
- Proxy support with connectivity test
- Fill speed control (slow, fast, superfast)
- Browser path saved per browser — no need to re-select on next run
- Silent mode (headless) with Ghost Mode — hides the browser window by process ID
- Close after delay control — choose whether the browser closes after each account and with how much delay
- Automatic system language detection (11 languages)
- Configuration saving for reuse
- Automatic update checker
- No webdriver required

## Installation

### Option A — Executable (no Python required)

Download the latest release zip from the [Releases](https://github.com/TDoomX/exitlag-auto-signup-revamp/releases) page, extract everything and run `mainrev.exe` directly. No dependencies needed.

### Option B — Run from source

**1. Clone the repository:**
```shell
git clone https://github.com/TDoomX/exitlag-auto-signup-revamp
```

**2. Install dependencies:**
```shell
pip install -r requirements.txt
```

**3. Run:**
```shell
python main.py
```

## Usage

On startup the app will prompt for:
- Browser (Chrome, Brave or Opera GX)
- Password (or generates one randomly)
- Proxy (optional)
- Number of accounts to create
- Desired plan (3-day trial or 7-day OMEN)
- Fill speed
- Silent mode
- Close after

Generated credentials are automatically saved to `accounts.txt`.

## Supported Languages

Portuguese, English, Spanish, French, German, Italian, Russian, Japanese, Chinese, Vietnamese, Arabic

## Lite Version

Looking for a lightweight CLI version with no graphical interface? Check out [exitlag-auto-signup-revamp-lite](https://github.com/TDoomX/exitlag-auto-signup-revamp-lite).

## Author

Doom — [![Discord](https://img.shields.io/discord/1452848560910368933?label=Discord&logo=discord&color=5865F2)](https://discord.gg/WT5MNusUDX)
