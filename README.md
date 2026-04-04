> [!WARNING]
> Usage of this tool is entirely at your own risk. The author assumes no responsibility for any adverse consequences that may arise from its use.

# ExitLag Auto Signup

A tool to automate account creation on ExitLag, with support for multiple plans, automatic language detection, and a self-update system.

## Features

- Automatic account creation for 3-day and 7-day plans
- Supports any Chromium-based browser (Chrome, Brave, etc.)
- Password complexity checker with random password generation
- Proxy support with connectivity test
- Automatic system language detection
- Configuration saving for reuse
- Automatic update checker
- No webdriver required

## Installation

**1. Clone the repository:**
```shell
git clone https://github.com/TDoomX/exitlag-auto-signup-revamp
```

**2. Install dependencies:**
```shell
pip install -r requirements.txt
playwright install
```

**3. Run:**
```shell
python main.py
```

## Usage

On startup, the script will prompt for:
- Browser path (Chrome or Brave)
- Password (or generates one randomly)
- Proxy (optional)
- Number of accounts to create
- Desired plan (3 or 7 days)

Generated credentials are automatically saved to `accounts.txt`.

## Supported Languages

Portuguese, English, Spanish, French, German, Italian, Russian

## Author

Doom — https://github.com/TDoomX
