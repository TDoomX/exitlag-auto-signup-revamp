"""
DOOMXTLAG - Public Release (Placeholder)
==========================================
This is the public version of the DOOMXTLAG script.

Browser automation (account registration) requires the 'pydoll' library
and additional internal modules that are not included in this release.
The full version is distributed as a compiled executable (mainrev.exe)
and is automatically downloaded by the updater below.

To get the full version, simply run this script and it will update itself.
"""

import asyncio
import re
import warnings
import time
import os
import sys
import json
import urllib.request
import subprocess
import threading
import locale
import random
import string

from tqdm import tqdm
from tqdm import TqdmExperimentalWarning
from rich.console import Console
from faker import Faker

console = Console()
warnings.filterwarnings("ignore", category=TqdmExperimentalWarning)

CONFIG_FILE = "last_config.json"

GITHUB_RAW = "https://raw.githubusercontent.com/TDoomX/exitlag-auto-signup-revamp/master"
LOCAL_VERSION_FILE = "version.txt"
TRANSLATIONS_LANGS = ["de", "en", "es", "fr", "it", "ja", "pt", "ru", "zh", "vi", "ar"]


# ---------------------------------------------------------------------------
# Base / version helpers
# ---------------------------------------------------------------------------

def get_base():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def get_local_version():
    version_path = os.path.join(get_base(), LOCAL_VERSION_FILE)
    try:
        with open(version_path, "r") as f:
            return f.read().strip()
    except Exception:
        return "0.0.0"


def _ssl_ctx():
    import ssl
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def get_remote_version():
    try:
        url = f"{GITHUB_RAW}/{LOCAL_VERSION_FILE}"
        with urllib.request.urlopen(url, timeout=5, context=_ssl_ctx()) as r:
            return r.read().decode().strip()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Downloader — retry + backoff + HTML response guard
# ---------------------------------------------------------------------------

def download_file(url, dest_path, retries=3, backoff=2):
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    tmp_path = dest_path + ".tmp"
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(url, timeout=30, context=_ssl_ctx()) as r:
                data = r.read()
            # Reject HTML error pages served with 200 (e.g. GitHub CDN)
            if url.endswith(('.exe', '.dll', '.py', '.json', '.css', '.b64', '.txt')):
                if data[:5] in (b'<!DOC', b'<html', b'<HTML'):
                    raise ValueError("Unexpected HTML response")
            with open(tmp_path, "wb") as f:
                f.write(data)
            os.replace(tmp_path, dest_path)
            return True
        except Exception as e:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
            if attempt < retries:
                time.sleep(backoff ** attempt)
    console.print(f"[red]Failed to download: {url}[/red]")
    return False


def verify_sha256(file_path, expected_hex):
    import hashlib
    h = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                h.update(chunk)
        return h.hexdigest().lower() == expected_hex.lower()
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Updater
# ---------------------------------------------------------------------------

_THEME_FILES = (
    'logo.b64', 'minecraft.css', 'minecraft_font.b64',
    'mojangles.b64', 'valorant.css', 'winxp.css',
)

_LIB_FILES = ('__init__.py', 'lib.py', 'windows_ui_lab.py')

_LIB_DLLS = (
    'audit_monitor.dll', 'cx_core.dll', 'cxcrypt32_helper.dll',
    'cxevtlog.dll', 'cxmem_alloc.dll', 'cxreg_cache.dll',
    'cxwinsys.dll', 'd3dcompat_layer.dll', 'ntdll_bridge.dll',
    'vcruntime_ext.dll',
)

RELEASE_BASE = "https://github.com/TDoomX/exitlag-auto-signup-revamp/releases/latest/download"


def _download_all_files(base, include_exe=True):
    """Download the full file set required to run mainrev.exe.

    Returns True if all downloads succeeded, False otherwise.
    Sets new_exe_path on success when include_exe=True.
    """
    success = True
    new_exe_path = os.path.join(base, "mainrev_new.exe")

    # --- mainrev.exe (with SHA256 integrity check) ---
    if include_exe:
        console.print("[cyan]Downloading mainrev.exe...[/cyan]")
        sha256_url  = f"{RELEASE_BASE}/mainrev.sha256"
        sha256_path = new_exe_path + ".sha256"
        if not download_file(f"{RELEASE_BASE}/mainrev.exe", new_exe_path):
            return False
        if download_file(sha256_url, sha256_path):
            try:
                with open(sha256_path, "r") as sf:
                    expected = sf.read().strip().split()[0]
                if not verify_sha256(new_exe_path, expected):
                    console.print("[bold red]Download corrupted — please try again.[/bold red]")
                    os.remove(new_exe_path)
                    return False
            except Exception:
                pass
            finally:
                try:
                    os.remove(sha256_path)
                except Exception:
                    pass

    # --- translations (11 languages) ---
    os.makedirs(os.path.join(base, "translations"), exist_ok=True)
    for lang in TRANSLATIONS_LANGS:
        console.print(f"[cyan]Downloading translations/{lang}.json...[/cyan]")
        if not download_file(
            f"{GITHUB_RAW}/translations/{lang}.json",
            os.path.join(base, "translations", f"{lang}.json")
        ):
            success = False

    # --- version.txt ---
    if not download_file(f"{GITHUB_RAW}/version.txt", os.path.join(base, "version.txt")):
        success = False

    # --- themes/ ---
    os.makedirs(os.path.join(base, "themes"), exist_ok=True)
    for theme_file in _THEME_FILES:
        console.print(f"[cyan]Downloading themes/{theme_file}...[/cyan]")
        if not download_file(
            f"{GITHUB_RAW}/themes/{theme_file}",
            os.path.join(base, "themes", theme_file)
        ):
            success = False

    # --- lib/ Python files ---
    os.makedirs(os.path.join(base, "lib"), exist_ok=True)
    for lib_file in _LIB_FILES:
        console.print(f"[cyan]Downloading lib/{lib_file}...[/cyan]")
        if not download_file(
            f"{GITHUB_RAW}/lib/{lib_file}",
            os.path.join(base, "lib", lib_file)
        ):
            success = False

    # --- lib/__pycache__/ DLLs ---
    os.makedirs(os.path.join(base, "lib", "__pycache__"), exist_ok=True)
    for dll in _LIB_DLLS:
        console.print(f"[cyan]Downloading lib/__pycache__/{dll}...[/cyan]")
        if not download_file(
            f"{GITHUB_RAW}/lib/__pycache__/{dll}",
            os.path.join(base, "lib", "__pycache__", dll)
        ):
            success = False

    return success


def check_for_updates():
    console.print(f"[cyan]{tr('checking_updates')}[/cyan]")

    # Clean up leftover old exe from previous update
    old_exe = os.path.join(get_base(), "mainrev_old.exe")
    if os.path.exists(old_exe):
        try:
            os.remove(old_exe)
        except Exception:
            pass

    remote_version = get_remote_version()
    if remote_version is None:
        console.print(f"[yellow]{tr('update_check_failed')}[/yellow]")
        return

    local_version = get_local_version()
    base = get_base()
    frozen = getattr(sys, 'frozen', False)

    # --- First install: running as .py, mainrev.exe not present yet ---
    # Download everything from scratch and launch the exe.
    if not frozen and not os.path.exists(os.path.join(base, "mainrev.exe")):
        console.print("\n[bold cyan]First install detected — downloading full package...[/bold cyan]")
        console.print("[yellow]Please do not close this window.[/yellow]\n")

        if not _download_all_files(base, include_exe=True):
            console.print("\n[bold red]Some files failed to download. Please try again.[/bold red]")
            return

        console.print("\n[bold green]Download complete! Launching mainrev.exe...[/bold green]")
        exe_path = os.path.join(base, "mainrev.exe")
        new_exe  = os.path.join(base, "mainrev_new.exe")
        # Rename the downloaded exe to its final name
        try:
            if os.path.exists(new_exe):
                os.replace(new_exe, exe_path)
        except Exception as e:
            console.print(f"[bold red]Could not rename exe: {e}[/bold red]")
            return
        subprocess.Popen([exe_path])
        sys.exit(0)

    # --- Already up to date ---
    if remote_version == local_version:
        console.print(f"[green]{tr('up_to_date').format(local_version=local_version)}[/green]")
        return

    # --- Normal update ---
    console.print(f"\n[bold cyan]{'='*50}[/bold cyan]")
    console.print(f"[bold yellow]{tr('update_available')}[/bold yellow]")
    console.print(f"[cyan]{tr('current_version').format(local_version=local_version)}[/cyan]")
    console.print(f"[cyan]{tr('new_version').format(remote_version=remote_version)}[/cyan]")
    console.print(f"[bold cyan]{'='*50}[/bold cyan]")
    console.print(f"[yellow]{tr('update_downloading')}[/yellow]")
    console.print(f"[yellow]{tr('update_dont_close')}[/yellow]\n")

    new_exe_path = os.path.join(base, "mainrev_new.exe")

    if not _download_all_files(base, include_exe=frozen):
        console.print(f"\n[bold red]{tr('update_partial_fail')}[/bold red]")
        if frozen and os.path.exists(new_exe_path):
            try:
                os.remove(new_exe_path)
            except Exception:
                pass
        return

    console.print(f"\n[bold green]{tr('update_complete')}[/bold green]")
    console.print(f"[bold yellow]{tr('update_reopening')}[/bold yellow]")
    console.print(f"[dim]{tr('update_skip_countdown')}[/dim]\n")

    skip = threading.Event()

    def wait_for_enter():
        try:
            input()
        except Exception:
            pass
        skip.set()

    threading.Thread(target=wait_for_enter, daemon=True).start()

    for i in range(5, 0, -1):
        if skip.is_set():
            break
        console.print(f"[cyan]{tr('update_countdown').format(i=i)}[/cyan]", end="\r")
        time.sleep(1)

    console.print()

    if frozen:
        exe_path = os.path.join(base, "mainrev.exe")
        new_exe  = os.path.join(base, "mainrev_new.exe")
        bat_path = os.path.join(base, "update.bat")
        bat_content = (
            "@echo off\r\n"
            "timeout /t 3 /nobreak > nul\r\n"
            "move /y \"" + new_exe + "\" \"" + exe_path + "\"\r\n"
            "if errorlevel 1 (\r\n"
            "    if exist \"" + new_exe + "\" del /f /q \"" + new_exe + "\"\r\n"
            "    if exist \"" + exe_path + "\" start \"\" \"" + exe_path + "\"\r\n"
            "    del \"%~f0\"\r\n"
            "    exit /b 1\r\n"
            ")\r\n"
            "start \"\" \"" + exe_path + "\" --updated\r\n"
            "del \"%~f0\"\r\n"
        )
        with open(bat_path, "w", encoding="utf-8") as f:
            f.write(bat_content)
        subprocess.Popen(["cmd.exe", "/c", bat_path], shell=False)
        time.sleep(0.5)
    else:
        subprocess.Popen([sys.executable, os.path.join(base, "main.py")])

    sys.exit(0)


# ---------------------------------------------------------------------------
# Translations
# ---------------------------------------------------------------------------

def load_translations():
    LANG_MAP = {
        'pt': 'pt', 'en': 'en', 'es': 'es', 'fr': 'fr',
        'de': 'de', 'it': 'it', 'ru': 'ru',
        'portuguese': 'pt', 'english': 'en', 'spanish': 'es',
        'french': 'fr', 'german': 'de', 'italian': 'it', 'russian': 'ru',
    }
    try:
        locale.setlocale(locale.LC_ALL, '')
        lang_tuple = locale.getlocale()
        raw  = lang_tuple[0].split('_')[0].lower() if lang_tuple and lang_tuple[0] else 'en'
        lang = LANG_MAP.get(raw, 'en')
    except Exception:
        lang = 'en'

    base = get_base()
    translation_path = os.path.join(base, "translations", f"{lang}.json")
    if not os.path.exists(translation_path):
        translation_path = os.path.join(base, "translations", "en.json")

    with open(translation_path, "r", encoding="utf-8") as f:
        return json.load(f)


_translation_cache = None

def tr(key):
    global _translation_cache
    if _translation_cache is None:
        _translation_cache = load_translations()
    return _translation_cache.get(key, key)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def save_config(browser_path: str, password: str, proxy: str, execution_count: int):
    config = {
        "browser_path": browser_path,
        "password": password,
        "proxy": proxy,
        "execution_count": execution_count,
    }
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        console.print(f"[yellow]Could not save config: {e}[/yellow]")


def load_config():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        console.print(f"[yellow]Could not load config: {e}[/yellow]")
    return None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def is_valid_password(password):
    return (
        len(password) >= 8
        and re.search(r"[a-z]", password)
        and re.search(r"[A-Z]", password)
        and re.search(r"[0-9]", password)
        and re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"|,.<>/?]", password)
    )


def generate_random_password():
    while True:
        length = 12
        chars = (
            random.choice(string.ascii_lowercase)
            + random.choice(string.ascii_uppercase)
            + random.choice(string.digits)
            + random.choice("!@#$%^&*()_+-=[]{};':\"|,.<>/?")
        )
        rest = ''.join(
            random.choice(string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{};':\"|,.<>/?")
            for _ in range(length - 4)
        )
        password = ''.join(random.sample(chars + rest, length))
        if is_valid_password(password):
            return password


def generate_random_email():
    name = ''.join(random.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(8))
    return f"{name}@zylker.com"


def display_accounts(accounts: list):
    successful = [acc for acc in accounts if acc["success"]]
    if not successful:
        return
    console.print(f"\n[bold cyan]{'='*50}[/bold cyan]")
    console.print(f"[bold cyan]{tr('accounts_created')}[/bold cyan]")
    console.print(f"[bold cyan]{'='*50}[/bold cyan]")
    for acc in successful:
        console.print(f"[cyan]{tr('email_label')}[/cyan]")
        console.print(f"[cyan]{acc['email']}[/cyan]")
        console.print(f"[cyan]{tr('password_display_label')}[/cyan]")
        console.print(f"[cyan]{acc['password']}[/cyan]")
        console.print("")
    console.print(f"[bold cyan]{'='*50}[/bold cyan]\n")


# ---------------------------------------------------------------------------
# Account registration
# NOTE: Browser automation requires pydoll (pip install pydoll-python) and
# the internal lib/ modules included in the full release. This public version
# stubs out the automation layer — the full logic runs inside mainrev.exe.
# ---------------------------------------------------------------------------

class AccountAutomation:

    def __init__(self):
        self.fake = Faker()

    async def fill_field(self, tab, selector, text):
        # Requires pydoll tab object from the full version.
        # Full version: focuses element, sets value, dispatches input event.
        raise NotImplementedError("Browser automation requires the full version (mainrev.exe)")

    async def register_account(self, password: str, browser_path: str = None) -> dict:
        email      = generate_random_email()
        first_name = self.fake.first_name()
        last_name  = self.fake.last_name()

        console.print(f"\n[cyan]{tr('signup_process')}[/cyan]")
        console.print(f"[cyan]📧 Email: {email}[/cyan]")

        # Browser automation requires pydoll and the full internal lib.
        # The full version launches a Chromium/Opera GX instance here,
        # navigates to https://www.exitlag.com/lp/trial, fills the form,
        # handles reCAPTCHA and submits.
        console.print(f"[bold red]Browser automation is not available in this public release.[/bold red]")
        console.print(f"[yellow]Please run mainrev.exe (downloaded automatically by the updater).[/yellow]")

        return {"email": email, "password": password, "success": False, "error": "pydoll not available"}


async def register_accounts(passw: str, execution_count: int, browser_path: str = None):
    accounts   = []
    automation = AccountAutomation()

    for x in range(execution_count):
        console.print(f"\n[bold cyan]{'='*50}[/bold cyan]")
        console.print(f"[bold cyan]Account {x+1}/{execution_count}[/bold cyan]")
        console.print(f"[bold cyan]{'='*50}[/bold cyan]")

        result = await automation.register_account(passw, browser_path)
        accounts.append(result)

        if x < execution_count - 1:
            delay = random.uniform(5, 10)
            console.print(f"[yellow]{tr('waiting_next_account').format(delay=delay):.0f}s[/yellow]")
            await asyncio.sleep(delay)

    with open("accounts.txt", "a") as f:
        for acc in accounts:
            if acc["success"]:
                f.write(f"{acc['email']} | {acc['password']}\n")

    successful = sum(1 for acc in accounts if acc["success"])
    console.print(f"\n[bold cyan]{'='*50}[/bold cyan]")
    console.print(f"[bold green]✓ {tr('successfully_created_account').format(x=successful, executionCount=execution_count)}[/bold green]")
    console.print(f"[bold green]{tr('credentials_saved')}[/bold green]")
    console.print(f"[bold cyan]{'='*50}[/bold cyan]")

    display_accounts(accounts)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    check_for_updates()

    last_config = load_config()

    if last_config:
        console.print(f"\n[bold cyan]{'='*50}[/bold cyan]")
        console.print(f"[bold cyan]{tr('last_config_found')}[/bold cyan]")
        console.print(f"[bold cyan]{'='*50}[/bold cyan]")
        console.print(f"[cyan]{tr('browser_label')}{last_config.get('browser_path', tr('default_browser'))}[/cyan]")
        console.print(f"[cyan]{tr('password_label_display')}{last_config.get('password', '')}[/cyan]")
        console.print(f"[cyan]{tr('proxy_label_display')}{last_config.get('proxy', tr('no_proxy'))}[/cyan]")
        console.print(f"[cyan]{tr('accounts_label')}{last_config.get('execution_count', 1)}[/cyan]")
        console.print(f"[bold cyan]{'='*50}[/bold cyan]\n")

        use_last = input(tr("use_last_config_prompt")).strip().lower()

        if use_last in ('y', 's', 'o', 'j', 'д'):
            browser_path    = last_config.get('browser_path', '')
            passw           = last_config.get('password', '')
            proxy           = last_config.get('proxy', '')
            execution_count = last_config.get('execution_count', 1)
        else:
            last_config = None

    if not last_config:
        browser_path = ""
        while True:
            browser_path = input(
                f"\033[1m{tr('browser_path_prompt')}\033[0m\n"
                f"{tr('browser_path_info')}\n{tr('supported_browsers')}\n- Chrome\n- Brave\n"
                f"{tr('browser_executable_path')}"
            ).replace('"', '').replace("'", '')
            if browser_path == "" or os.path.exists(browser_path):
                break
            console.print(f"[bold red]{tr('invalid_path')}[/bold red]")

        while True:
            passw = input(
                f"\033[1m{tr('password_prompt')}\033[0m\n"
                f"{tr('password_info')}\n{tr('password_label')}"
            )
            if passw == "":
                passw = generate_random_password()
                console.print(f"[bold green]{tr('random_password_generated').format(passw=passw)}[/bold green]")
                break
            if not is_valid_password(passw):
                console.print(f"[bold red]{tr('password_not_meeting_requirements')}[/bold red]")
                continue
            break

        proxy = input(f"\n{tr('proxy_prompt')}\n{tr('proxy_info')}\n{tr('proxy_label')}: ")

        while True:
            raw_count = input(f"\n{tr('number_of_accounts_prompt')}")
            try:
                execution_count = int(raw_count) if raw_count else 1
                break
            except ValueError:
                console.print(f"[bold red]{tr('invalid_number')}[/bold red]")

        save_config(browser_path, passw, proxy, execution_count)

    console.print(f"\n[bold cyan]{tr('account_generation_process')}[/bold cyan]\n")
    await register_accounts(passw, execution_count, browser_path)

    input(tr("press_enter_to_exit"))


if __name__ == "__main__":
    asyncio.run(main())
