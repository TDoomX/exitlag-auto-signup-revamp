import asyncio
import re
import warnings
import time
import os

from tqdm import tqdm
from tqdm import TqdmExperimentalWarning
from pydoll.browser import Chrome
from pydoll.browser.options import ChromiumOptions
from pydoll.constants import Key
from DrissionPage import Chromium, ChromiumOptions as DrissionOptions
from lib.lib import Main
from rich.console import Console
from faker import Faker
import random
import string
import json
import locale

console = Console()
warnings.filterwarnings("ignore", category=TqdmExperimentalWarning)


def load_translations():
    try:
        locale.setlocale(locale.LC_ALL, '')
        lang_tuple = locale.getlocale()  
        lang = lang_tuple[0].split('_')[0] if lang_tuple and lang_tuple[0] else 'en'
    except Exception:
        lang = 'en'

    translation_path = f"translations/{lang}.json"
    if not os.path.exists(translation_path):
        lang = 'en'
        translation_path = f"translations/{lang}.json"

    with open(translation_path, "r", encoding="utf-8") as f:
        return json.load(f)


_translation_cache = None

def tr(key):
    global _translation_cache
    if _translation_cache is None:
        _translation_cache = load_translations()
    return _translation_cache.get(key, key)


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


async def main():
    lib = Main()
    co = DrissionOptions()
    co.incognito().auto_port().mute(True)
    
    browserPath = ""

    while True:
        browserPath = input(
            f"\033[1m{tr('browser_path_prompt')}\033[0m\n"
            f"{tr('browser_path_info')}\n{tr('supported_browsers')}\n- Chrome\n- Brave\n"
            f"{tr('browser_executable_path')}"
        ).replace('"', '').replace("'", '')
        if browserPath != "":
            if os.path.exists(browserPath):
                co.set_browser_path(browserPath)
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
        if lib.testProxy(proxyUsage)[0]:
            co.set_proxy(proxyUsage)
        else:
            console.print(lib.testProxy(proxyUsage)[1])

    fake = Faker()

    console.print(f"\n{tr('plan_selection_title')}", style="bold cyan")
    console.print(f"1 - {tr('plan_option_3days')}")
    console.print(f"2 - {tr('plan_option_7days')}")

    escolha_plano = await asyncio.to_thread(input, tr("plan_input_prompt"))
    escolha_plano = escolha_plano.strip() or "1"

    if escolha_plano == "2":
        console.print(f"\n[bold cyan]{tr('account_generation_process')} - {tr('plan_option_7days')}[/bold cyan]\n")
        await register_plan2_accounts(passw, executionCount, browserPath)

    else:
        console.print(f"\n[bold cyan]{tr('account_generation_process')} - {tr('plan_option_3days')}[/bold cyan]\n")
        accounts = []
        last_chrome = None

        for x in range(executionCount):
            console.print(f"\n[bold cyan]{'='*50}[/bold cyan]")
            console.print(f"[bold cyan]Account {x+1}/{executionCount}[/bold cyan]")
            console.print(f"[bold cyan]{'='*50}[/bold cyan]")

            chrome = Chromium(addr_or_opts=co)
            tab = chrome.new_tab()
            tab.set.window.max()

            bar = tqdm(total=100, colour="cyan", dynamic_ncols=True)
            progress = 0

            used_email = gerar_email_aleatorio()

            console.print(f"\n[cyan]{tr('signup_process')}[/cyan]")
            console.print(f"[cyan]📧 Email: {used_email}[/cyan]")

            tab.get("https://www.exitlag.com/register.php")

            time.sleep(2)
            progress += 30
            bar.n = progress
            bar.refresh()

            first_name = fake.first_name()
            last_name = fake.last_name()

            try:
                tab.ele('#inputFirstName', timeout=0).input(first_name)
                tab.ele('#inputLastName', timeout=0).input(last_name)
                tab.ele('#inputEmail', timeout=0).input(used_email)
                tab.ele('#inputNewPassword1', timeout=0).input(passw)
                tab.ele('#inputNewPassword2', timeout=0).input(passw)
                tab.ele(".custom-checkbox--input checkbox", timeout=0).click()
                tab.ele('#btnFormRegister', timeout=0).click()

                progress = 100
                bar.n = progress
                bar.refresh()
                bar.close()

                accounts.append({"email": used_email, "password": passw, "success": True})
                console.print(f"[bold green]✓ {tr('registration_success')}[/bold green]")

                last_chrome = chrome

            except Exception as e:
                console.print(f"[bold red]{tr('error')}: {e}[/bold red]")
                bar.close()
                accounts.append({"email": used_email, "password": passw, "success": False})
                chrome.quit()
                continue

            if x < executionCount - 1:
                delay = random.uniform(5, 10)
                console.print(f"[yellow]{tr('waiting_next_account').format(delay=delay):.0f}s[/yellow]")
                time.sleep(delay)

        with open("accounts.txt", "a") as f:
            for acc in accounts:
                if acc["success"]:
                    f.write(f"{acc['email']} | {acc['password']}\n")

        successful = sum(1 for acc in accounts if acc["success"])
        console.print(f"\n[bold cyan]{'='*50}[/bold cyan]")
        console.print(f"[bold green]✓ {tr('successfully_created_account').format(x=successful, executionCount=executionCount)}[/bold green]")
        console.print(f"[bold green]{tr('credentials_saved')}[/bold green]")
        console.print(f"[bold cyan]{'='*50}[/bold cyan]")

    input(tr("press_enter_to_exit"))


if __name__ == "__main__":
    asyncio.run(main())