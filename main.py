import asyncio
import re
import warnings
import time
import os
import sys
import json
import urllib.request
import subprocess
import ctypes

from tqdm import tqdm
from tqdm import TqdmExperimentalWarning
from pydoll.browser import Chrome
from pydoll.browser.options import ChromiumOptions
from pydoll.constants import Key
from lib.lib import Main
from rich.console import Console
from faker import Faker
import random
import string
import locale

console = Console()
warnings.filterwarnings("ignore", category=TqdmExperimentalWarning)

CONFIG_FILE = "last_config.json"

GITHUB_RAW = "https://raw.githubusercontent.com/TDoomX/exitlag-auto-signup-revamp/master"
LOCAL_VERSION_FILE = "version.txt"
TRANSLATIONS_LANGS = ["de", "en", "es", "fr", "it", "pt", "ru"]


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


def get_remote_version():
    try:
        url = f"{GITHUB_RAW}/{LOCAL_VERSION_FILE}"
        with urllib.request.urlopen(url, timeout=5) as r:
            return r.read().decode().strip()
    except Exception:
        return None


def download_file(url, dest_path):
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    tmp_path = dest_path + ".tmp"
    try:
        urllib.request.urlretrieve(url, tmp_path)
        os.replace(tmp_path, dest_path)
        return True
    except Exception as e:
        console.print(f"[red]Erro ao baixar {url}: {e}[/red]")
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        return False


def check_for_updates():
    console.print(f"[cyan]Verificando atualizações...[/cyan]")

    old_exe = os.path.join(get_base(), "mainrev_old.exe")
    if os.path.exists(old_exe):
        try:
            os.remove(old_exe)
        except Exception:
            pass

    remote_version = get_remote_version()
    if remote_version is None:
        console.print(f"[yellow]Não foi possível verificar atualizações. Continuando...[/yellow]")
        return

    local_version = get_local_version()

    if remote_version == local_version:
        console.print(f"[green]Você está na versão mais recente ({local_version}).[/green]")
        return

    console.print(f"\n[bold cyan]{'='*50}[/bold cyan]")
    console.print(f"[bold yellow]⚡ Atualização disponível![/bold yellow]")
    console.print(f"[cyan]  Versão atual:  {local_version}[/cyan]")
    console.print(f"[cyan]  Nova versão:   {remote_version}[/cyan]")
    console.print(f"[bold cyan]{'='*50}[/bold cyan]")
    console.print(f"[yellow]O programa irá baixar a atualização, fechar e reabrir automaticamente.[/yellow]")
    console.print(f"[yellow]Não feche o terminal durante o processo.[/yellow]\n")

    base = get_base()
    success = True

    # Baixar main.exe (somente se estiver rodando como .exe)
    if getattr(sys, 'frozen', False):
        console.print(f"[cyan]Baixando mainrev.exe...[/cyan]")
        new_exe_path = os.path.join(base, "mainrev_new.exe")
        ok = download_file("https://github.com/TDoomX/exitlag-auto-signup-revamp/releases/latest/download/mainrev.exe", new_exe_path)
        if not ok:
            success = False

    # Baixar main.py
    console.print(f"[cyan]Baixando main.py...[/cyan]")
    ok = download_file(f"{GITHUB_RAW}/main.py", os.path.join(base, "main.py"))
    if not ok:
        success = False

    # Baixar translations
    os.makedirs(os.path.join(base, "translations"), exist_ok=True)
    for lang in TRANSLATIONS_LANGS:
        console.print(f"[cyan]Baixando translations/{lang}.json...[/cyan]")
        ok = download_file(
            f"{GITHUB_RAW}/translations/{lang}.json",
            os.path.join(base, "translations", f"{lang}.json")
        )
        if not ok:
            success = False

    # Baixar version.txt
    ok = download_file(f"{GITHUB_RAW}/version.txt", os.path.join(base, "version.txt"))
    if not ok:
        success = False

    if not success:
        console.print(f"\n[bold red]Alguns arquivos não puderam ser baixados. Continuando com a versão atual.[/bold red]")
        return

    console.print(f"\n[bold green]✓ Atualização concluída![/bold green]")
    console.print(f"[bold yellow]Esta janela irá fechar e o programa abrirá novamente automaticamente.[/bold yellow]")
    console.print(f"[dim]Pressione Enter para pular a contagem.[/dim]\n")

    import threading
    skip = threading.Event()

    def wait_for_enter():
        input()
        skip.set()

    t = threading.Thread(target=wait_for_enter, daemon=True)
    t.start()

    for i in range(5, 0, -1):
        if skip.is_set():
            break
        console.print(f"[cyan]Reabrindo em {i}s...[/cyan]", end="\r")
        time.sleep(1)

    console.print()

    # Reiniciar
    if getattr(sys, 'frozen', False):
        exe_path = os.path.join(base, "mainrev.exe")
        old_exe = os.path.join(base, "mainrev_old.exe")
        new_exe = os.path.join(base, "mainrev_new.exe")
        try:
            if os.path.exists(new_exe):
                if os.path.exists(old_exe):
                    os.remove(old_exe)
                os.rename(exe_path, old_exe)
                os.rename(new_exe, exe_path)
            ctypes.windll.shell32.ShellExecuteW(None, "open", exe_path, None, None, 1)
        except Exception as e:
            console.print(f"[red]Erro ao reabrir: {e}[/red]")
            if os.path.exists(old_exe) and not os.path.exists(exe_path):
                os.rename(old_exe, exe_path)
    else:
        subprocess.Popen([sys.executable, os.path.join(base, "main.py")])

    sys.exit(0)


def load_translations():
    LANG_MAP = {
        'pt': 'pt', 'en': 'en', 'es': 'es', 'fr': 'fr', 'de': 'de', 'it': 'it', 'ru': 'ru',
        'portuguese': 'pt',
        'english':    'en',
        'spanish':    'es',
        'french':     'fr',
        'german':     'de',
        'italian':    'it',
        'russian':    'ru',
    }

    try:
        locale.setlocale(locale.LC_ALL, '')
        lang_tuple = locale.getlocale()
        raw = lang_tuple[0].split('_')[0].lower() if lang_tuple and lang_tuple[0] else 'en'
        lang = LANG_MAP.get(raw, 'en')
    except Exception:
        lang = 'en'

    base = get_base()
    translation_path = os.path.join(base, "translations", f"{lang}.json")
    if not os.path.exists(translation_path):
        lang = 'en'
        translation_path = os.path.join(base, "translations", "en.json")

    with open(translation_path, "r", encoding="utf-8") as f:
        return json.load(f)


_translation_cache = None

def tr(key):
    global _translation_cache
    if _translation_cache is None:
        _translation_cache = load_translations()
    return _translation_cache.get(key, key)


def save_config(browser_path: str, password: str, proxy: str, execution_count: int, plan: str):
    config = {
        "browser_path": browser_path,
        "password": password,
        "proxy": proxy,
        "execution_count": execution_count,
        "plan": plan
    }
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        console.print(f"[yellow]Could not save config: {str(e)}[/yellow]")


def load_config():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        console.print(f"[yellow]Could not load config: {str(e)}[/yellow]")
    return None


def is_valid_password(password):
    if len(password) < 8:
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[0-9]", password):
        return False
    if not re.search(r"[!@#$%^&*()_+\-=[\]{};':\"|,.<>/?]", password):
        return False
    return True


def generate_random_password():
    while True:
        length = 12
        password_chars = (
            random.choice(string.ascii_lowercase) +
            random.choice(string.ascii_uppercase) +
            random.choice(string.digits) +
            random.choice("!@#$%^&*()_+-=[]{};':\"|,.<>/?")
        )
        remaining = ''.join(
            random.choice(string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{};':\"|,.<>/?")
            for _ in range(length - 4)
        )
        password = ''.join(random.sample(password_chars + remaining, length))
        if is_valid_password(password):
            return password


def gerar_email_aleatorio():
    nome = ''.join(random.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(8))
    return f"{nome}@zylker.com"


def gerar_email_plan2():
    nome = ''.join(random.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(8))
    dominio = "zylker.com"
    return f"{nome}@{dominio}"


def display_accounts(accounts: list):
    successful_accounts = [acc for acc in accounts if acc["success"]]
    
    if not successful_accounts:
        return
    
    console.print(f"\n[bold cyan]{'='*50}[/bold cyan]")
    console.print(f"[bold cyan]{tr('accounts_created')}[/bold cyan]")
    console.print(f"[bold cyan]{'='*50}[/bold cyan]")
    
    for acc in successful_accounts:
        console.print(f"[cyan]{tr('email_label')}[/cyan]")
        console.print(f"[cyan]{acc['email']}[/cyan]")
        console.print(f"[cyan]{tr('password_display_label')}[/cyan]")
        console.print(f"[cyan]{acc['password']}[/cyan]")
        console.print("")
    
    console.print(f"[bold cyan]{'='*50}[/bold cyan]\n")


class HumanizedBrowserAutomation:
    
    def __init__(self):
        self.fake = Faker()
    
    async def add_random_pauses(self, min_time=0.5, max_time=2.0):
        await asyncio.sleep(random.uniform(min_time, max_time))
    
    async def fill_field_instantly(self, tab, selector, text):
        await tab.execute_script(f"document.querySelector('{selector}').focus();")
        await asyncio.sleep(0.1)
        
        escaped_text = text.replace("\\", "\\\\").replace('"', '\\"')
        await tab.execute_script(f"document.querySelector('{selector}').value = \"{escaped_text}\";")
        await tab.execute_script(f"document.querySelector('{selector}').dispatchEvent(new Event('input', {{ bubbles: true }}));")
        
        await asyncio.sleep(0.05)
    
    async def register_account(self, password: str, browser_path: str = None) -> dict:
        
        email = gerar_email_plan2()
        first_name = self.fake.first_name()
        last_name = self.fake.last_name()
        
        options = ChromiumOptions()
        options.headless = False
        options.browser_preferences = {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_settings.popups": 0,
        }
        
        if browser_path:
            options.binary_location = browser_path
        
        browser = Chrome(options=options)
        tab = await browser.start()
        
        try:
            console.print(f"\n[cyan]{tr('signup_process')}[/cyan]")
            console.print(f"[cyan]📧 Email: {email}[/cyan]")
            
            await tab.go_to("https://www.exitlag.com/lp/omen")
            await asyncio.sleep(2)
            
            console.print(f"[yellow]{tr('filling_form')}[/yellow]")
            
            await self.fill_field_instantly(tab, '#firstName', first_name)
            await self.fill_field_instantly(tab, '#lastName', last_name)
            await self.fill_field_instantly(tab, '#email', email)
            await self.fill_field_instantly(tab, '#password', password)
            await self.fill_field_instantly(tab, '#confirmPassword', password)
            
            await asyncio.sleep(0.2)
            await tab.execute_script("document.querySelector('#acceptTos').click();")
            
            console.print(f"[yellow]{tr('waiting_captcha')}[/yellow]")
            await asyncio.sleep(5)
            
            console.print(f"[cyan]{tr('submitting_form')}[/cyan]")
            await tab.execute_script("document.querySelector('#registerButton').click();")
            
            await asyncio.sleep(3)
            
            try:
                error_text = await tab.execute_script("""
                    const error = document.querySelector('.error, .alert-danger, [data-error]');
                    return error ? error.textContent : null;
                """)
                
                if error_text and "captcha" in error_text.lower():
                    console.print(f"[bold red]✗ {tr('captcha_failed')}: {error_text}[/bold red]")
                    return {"email": email, "password": password, "success": False, "error": "Captcha failed", "browser": browser, "tab": tab}
                elif error_text:
                    console.print(f"[bold red]✗ {tr('error_fill_form').format(e=error_text)}[/bold red]")
                    return {"email": email, "password": password, "success": False, "error": error_text, "browser": browser, "tab": tab}
            except:
                pass
            
            console.print(f"[bold green]✓ {tr('registration_success')}[/bold green]")
            return {"email": email, "password": password, "success": True, "browser": browser, "tab": tab}
        
        except Exception as e:
            console.print(f"[bold red]✗ {tr('error')}: {str(e)[:100]}[/bold red]")
            return {"email": email, "password": password, "success": False, "error": str(e), "browser": browser, "tab": tab}


async def register_plan2_accounts(passw: str, executionCount: int, browser_path: str = None):
    
    accounts = []
    automation = HumanizedBrowserAutomation()
    last_browser = None
    last_tab = None
    
    for x in range(executionCount):
        console.print(f"\n[bold cyan]{'='*50}[/bold cyan]")
        console.print(f"[bold cyan]Account {x+1}/{executionCount}[/bold cyan]")
        console.print(f"[bold cyan]{'='*50}[/bold cyan]")
        
        result = await automation.register_account(passw, browser_path)
        
        if "browser" in result:
            last_browser = result.pop("browser")
            last_tab = result.pop("tab")
        
        accounts.append(result)
        
        if x < executionCount - 1:
            delay = random.uniform(5, 10)
            console.print(f"[yellow]{tr('waiting_next_account').format(delay=delay):.0f}s[/yellow]")
            await asyncio.sleep(delay)
    
    with open("accounts.txt", "a") as f:
        for acc in accounts:
            if acc["success"]:
                f.write(f"{acc['email']} | {acc['password']}\n")
    
    successful = sum(1 for acc in accounts if acc["success"])
    console.print(f"\n[bold cyan]{'='*50}[/bold cyan]")
    console.print(f"[bold green]✓ {tr('successfully_created_account').format(x=successful, executionCount=executionCount)}[/bold green]")
    console.print(f"[bold green]{tr('credentials_saved')}[/bold green]")
    console.print(f"[bold cyan]{'='*50}[/bold cyan]")
    
    display_accounts(accounts)


class Plan1BrowserAutomation:
    
    def __init__(self):
        self.fake = Faker()
    
    async def fill_field_instantly(self, tab, selector, text):
        await tab.execute_script(f"document.querySelector('{selector}').focus();")
        await asyncio.sleep(0.1)
        
        escaped_text = text.replace("\\", "\\\\").replace('"', '\\"')
        await tab.execute_script(f"document.querySelector('{selector}').value = \"{escaped_text}\";")
        await tab.execute_script(f"document.querySelector('{selector}').dispatchEvent(new Event('input', {{ bubbles: true }}));")
        
        await asyncio.sleep(0.05)
    
    async def register_account(self, password: str, browser_path: str = None) -> dict:
        
        email = gerar_email_aleatorio()
        first_name = self.fake.first_name()
        last_name = self.fake.last_name()
        
        options = ChromiumOptions()
        options.headless = False
        options.browser_preferences = {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_settings.popups": 0,
        }
        
        if browser_path:
            options.binary_location = browser_path
        
        browser = Chrome(options=options)
        tab = await browser.start()
        
        try:
            console.print(f"\n[cyan]{tr('signup_process')}[/cyan]")
            console.print(f"[cyan]📧 Email: {email}[/cyan]")
            
            await tab.go_to("https://www.exitlag.com/lp/trial")
            await asyncio.sleep(2)
            
            console.print(f"[yellow]{tr('filling_form')}[/yellow]")
            
            await tab.execute_script("document.querySelector('#heroSocialFlow > button').click();")
            await asyncio.sleep(1)
            
            await self.fill_field_instantly(tab, '#inputFirstName', first_name)
            await self.fill_field_instantly(tab, '#inputLastName', last_name)
            await self.fill_field_instantly(tab, '#inputEmail', email)
            await self.fill_field_instantly(tab, '#inputNewPassword', password)
            await self.fill_field_instantly(tab, '#inputNewPassword2', password)
            
            await asyncio.sleep(0.2)
            
            await tab.execute_script("document.querySelector('#hero-terms-check').click();")
            
            console.print(f"[yellow]{tr('waiting_captcha')}[/yellow]")
            await asyncio.sleep(5)
            
            console.print(f"[cyan]{tr('submitting_form')}[/cyan]")
            await tab.execute_script("document.querySelector('#registerButton').click();")
            
            await asyncio.sleep(3)
            
            try:
                error_text = await tab.execute_script("""
                    const error = document.querySelector('.error, .alert-danger, [data-error]');
                    return error ? error.textContent : null;
                """)
                
                if error_text and "captcha" in error_text.lower():
                    console.print(f"[bold red]✗ {tr('captcha_failed')}: {error_text}[/bold red]")
                    return {"email": email, "password": password, "success": False, "error": "Captcha failed", "browser": browser, "tab": tab}
                elif error_text:
                    console.print(f"[bold red]✗ {tr('error_fill_form').format(e=error_text)}[/bold red]")
                    return {"email": email, "password": password, "success": False, "error": error_text, "browser": browser, "tab": tab}
            except:
                pass
            
            console.print(f"[bold green]✓ {tr('registration_success')}[/bold green]")
            return {"email": email, "password": password, "success": True, "browser": browser, "tab": tab}
        
        except Exception as e:
            console.print(f"[bold red]✗ {tr('error')}: {str(e)[:100]}[/bold red]")
            return {"email": email, "password": password, "success": False, "error": str(e), "browser": browser, "tab": tab}


async def register_plan1_accounts(passw: str, executionCount: int, browser_path: str = None):
    
    accounts = []
    automation = Plan1BrowserAutomation()
    last_browser = None
    last_tab = None
    
    for x in range(executionCount):
        console.print(f"\n[bold cyan]{'='*50}[/bold cyan]")
        console.print(f"[bold cyan]Account {x+1}/{executionCount}[/bold cyan]")
        console.print(f"[bold cyan]{'='*50}[/bold cyan]")
        
        result = await automation.register_account(passw, browser_path)
        
        if "browser" in result:
            last_browser = result.pop("browser")
            last_tab = result.pop("tab")
        
        accounts.append(result)
        
        if x < executionCount - 1:
            delay = random.uniform(5, 10)
            console.print(f"[yellow]{tr('waiting_next_account').format(delay=delay):.0f}s[/yellow]")
            await asyncio.sleep(delay)
    
    with open("accounts.txt", "a") as f:
        for acc in accounts:
            if acc["success"]:
                f.write(f"{acc['email']} | {acc['password']}\n")
    
    successful = sum(1 for acc in accounts if acc["success"])
    console.print(f"\n[bold cyan]{'='*50}[/bold cyan]")
    console.print(f"[bold green]✓ {tr('successfully_created_account').format(x=successful, executionCount=executionCount)}[/bold green]")
    console.print(f"[bold green]{tr('credentials_saved')}[/bold green]")
    console.print(f"[bold cyan]{'='*50}[/bold cyan]")
    
    display_accounts(accounts)


async def main():
    check_for_updates()

    lib = Main()

    last_config = load_config()
    
    if last_config:
        console.print(f"\n[bold cyan]{'='*50}[/bold cyan]")
        console.print(f"[bold cyan]{tr('last_config_found')}[/bold cyan]")
        console.print(f"[bold cyan]{'='*50}[/bold cyan]")
        console.print(f"[cyan]{tr('browser_label')}{last_config.get('browser_path', tr('default_browser'))}[/cyan]")
        console.print(f"[cyan]{tr('password_label_display')}{last_config.get('password', '')}[/cyan]")
        console.print(f"[cyan]{tr('proxy_label_display')}{last_config.get('proxy', tr('no_proxy'))}[/cyan]")
        console.print(f"[cyan]{tr('accounts_label')}{last_config.get('execution_count', 1)}[/cyan]")
        plan_name = tr("seven_days") if last_config.get('plan') == '2' else tr("three_days")
        console.print(f"[cyan]{tr('plan_label')}{plan_name}[/cyan]")
        console.print(f"[bold cyan]{'='*50}[/bold cyan]\n")
        
        use_last = input(tr("use_last_config_prompt")).strip().lower()
        
        if use_last in ('y', 's', 'o', 'j', 'д'):
            browserPath = last_config.get('browser_path', '')
            passw = last_config.get('password', '')
            proxyUsage = last_config.get('proxy', '')
            executionCount = last_config.get('execution_count', 1)
            escolha_plano = last_config.get('plan', '1')
            
            if proxyUsage:
                if lib.testProxy(proxyUsage)[0]:
                    pass
        else:
            last_config = None
    
    if not last_config:
        browserPath = ""

        while True:
            browserPath = input(
                f"\033[1m{tr('browser_path_prompt')}\033[0m\n"
                f"{tr('browser_path_info')}\n{tr('supported_browsers')}\n- Chrome\n- Brave\n"
                f"{tr('browser_executable_path')}"
            ).replace('"', '').replace("'", '')
            if browserPath != "":
                if os.path.exists(browserPath):
                    break
                else:
                    console.print(f"[bold red]{tr('invalid_path')}[/bold red]")
            else:
                break

        while True:
            passw = input(
                f"\033[1m{tr('password_prompt')}\033[0m\n"
                f"{tr('password_info')}\n{tr('password_label')}"
            )
            if passw == "":
                passw = generate_random_password()
                console.print(f"[bold green]{tr('random_password_generated').format(passw=passw)}[/bold green]")
                break
            else:
                if not is_valid_password(passw):
                    console.print(f"[bold red]{tr('password_not_meeting_requirements')}[/bold red]")
                    continue
                break

        proxyUsage = input(f"\n{tr('proxy_prompt')}\n{tr('proxy_info')}\n{tr('proxy_label')}: ")

        while True:
            executionCount = input(f"\n{tr('number_of_accounts_prompt')}")
            try:
                executionCount = int(executionCount)
                break
            except ValueError:
                if executionCount == "":
                    executionCount = 1
                    break
                else:
                    console.print(f"[bold red]{tr('invalid_number')}[/bold red]")

        if proxyUsage != "":
            if not lib.testProxy(proxyUsage)[0]:
                console.print(lib.testProxy(proxyUsage)[1])

        fake = Faker()

        console.print(f"\n{tr('plan_selection_title')}", style="bold cyan")
        console.print(f"1 - {tr('plan_option_3days')}")
        console.print(f"2 - {tr('plan_option_7days')}")

        escolha_plano = await asyncio.to_thread(input, tr("plan_input_prompt"))
        escolha_plano = escolha_plano.strip() or "1"
        
        save_config(browserPath, passw, proxyUsage, executionCount, escolha_plano)

    if escolha_plano == "2":
        console.print(f"\n[bold cyan]{tr('account_generation_process')} - {tr('plan_option_7days')}[/bold cyan]\n")
        await register_plan2_accounts(passw, executionCount, browserPath)
    else:
        console.print(f"\n[bold cyan]{tr('account_generation_process')} - {tr('plan_option_3days')}[/bold cyan]\n")
        await register_plan1_accounts(passw, executionCount, browserPath)

    input(tr("press_enter_to_exit"))


if __name__ == "__main__":
    asyncio.run(main())