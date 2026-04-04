import asyncio
import re
import warnings
import time
import os
import pickle
import random
import string
import json
import locale

from tqdm import tqdm
from tqdm import TqdmExperimentalWarning
from pydoll.browser import Chrome
from pydoll.browser.options import ChromiumOptions
from pydoll.constants import Key
from DrissionPage import Chromium, ChromiumOptions as DrissionOptions
from lib.lib import Main
from rich.console import Console
from faker import Faker

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
        
        # ==================== OPTION 3: USER AGENT & VIEWPORT ROTATION ====================
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        ]
        
        viewport_sizes = [
            {"width": 1920, "height": 1080},
            {"width": 1366, "height": 768},
            {"width": 1536, "height": 864},
            {"width": 1440, "height": 900},
            {"width": 1280, "height": 720},
        ]
        
        # ==================== OPTION 1: HUMANIZED DELAY FUNCTION ====================
        def human_delay(min_seconds=0.5, max_seconds=3.0):
            """Simulate human reaction time with natural variation"""
            delay = random.uniform(min_seconds, max_seconds)
            time.sleep(delay)
            return delay
        
        # ==================== OPTION 2: MOUSE MOVEMENT EMULATION ====================
        def human_mouse_move(tab, element_selector):
            """Move mouse in a curved path to element with realistic movement"""
            try:
                # Get element position via JavaScript
                element_info = tab.run_js(f"""
                    var elem = document.querySelector('{element_selector}');
                    if (!elem) return null;
                    var rect = elem.getBoundingClientRect();
                    return {{
                        x: rect.left + rect.width/2,
                        y: rect.top + rect.height/2,
                        exists: true
                    }};
                """)
                
                if not element_info or not element_info.get('exists'):
                    return False
                
                target_x = element_info['x']
                target_y = element_info['y']
                
                # Get viewport dimensions
                viewport = tab.run_js("return {width: window.innerWidth, height: window.innerHeight}")
                
                # Generate random start position (different corner each time)
                corners = [
                    (random.randint(50, 200), random.randint(50, 200)),
                    (viewport['width'] - random.randint(50, 200), random.randint(50, 200)),
                    (random.randint(50, 200), viewport['height'] - random.randint(50, 200)),
                    (viewport['width'] - random.randint(50, 200), viewport['height'] - random.randint(50, 200)),
                ]
                start_x, start_y = random.choice(corners)
                
                # Move mouse in steps
                steps = random.randint(20, 40)
                for i in range(steps):
                    t = i / steps
                    eased = t * t * (3 - 2 * t)
                    current_x = start_x + (target_x - start_x) * eased + random.randint(-3, 3)
                    current_y = start_y + (target_y - start_y) * eased + random.randint(-3, 3)
                    
                    tab.run_js(f"""
                        var event = new MouseEvent('mousemove', {{
                            view: window,
                            bubbles: true,
                            cancelable: true,
                            clientX: {current_x},
                            clientY: {current_y}
                        }});
                        document.elementFromPoint({current_x}, {current_y})?.dispatchEvent(event);
                    """)
                    time.sleep(random.uniform(0.008, 0.025))
                
                time.sleep(random.uniform(0.1, 0.3))
                
                offset_x = random.randint(-3, 3)
                offset_y = random.randint(-3, 3)
                tab.run_js(f"""
                    var clickEvent = new MouseEvent('click', {{
                        view: window,
                        bubbles: true,
                        cancelable: true,
                        clientX: {target_x + offset_x},
                        clientY: {target_y + offset_y}
                    }});
                    document.elementFromPoint({target_x + offset_x}, {target_y + offset_y})?.dispatchEvent(clickEvent);
                """)
                
                return True
            except Exception as e:
                return False
        
        # ==================== FIXED: SAFE ELEMENT INTERACTION WITH WAIT ====================
        def safe_input(tab, selector, text, timeout=10):
            """Safely input text into an element with proper waiting"""
            try:
                # Wait for element to be present
                element = tab.ele(selector, timeout=timeout)
                if not element:
                    console.print(f"[red]Element not found: {selector}[/red]")
                    return False
                
                # Clear field first
                element.clear()
                human_delay(0.1, 0.3)
                
                # Input text
                element.input(text)
                human_delay(0.1, 0.3)
                
                return True
            except Exception as e:
                console.print(f"[red]Error inputting to {selector}: {str(e)[:50]}[/red]")
                return False
        
        def safe_click(tab, selector, timeout=10):
            """Safely click an element with proper waiting"""
            try:
                element = tab.ele(selector, timeout=timeout)
                if not element:
                    console.print(f"[red]Element not found: {selector}[/red]")
                    return False
                
                element.click()
                human_delay(0.1, 0.3)
                return True
            except Exception as e:
                console.print(f"[red]Error clicking {selector}: {str(e)[:50]}[/red]")
                return False
        
        # ==================== FIXED: CAPTCHA DETECTION AFTER SUBMIT ====================
        def wait_for_captcha_to_appear(tab, timeout=15):
            """Wait for CAPTCHA to appear after form submission"""
            start_time = time.time()
            while time.time() - start_time < timeout:
                # Check for reCAPTCHA iframe
                has_recaptcha = tab.run_js("""
                    return !!(document.querySelector('iframe[src*="recaptcha"]') 
                        || document.querySelector('.g-recaptcha')
                        || document.querySelector('#captcha')
                        || document.querySelector('[class*="captcha"]'));
                """)
                
                if has_recaptcha:
                    console.print("[yellow]CAPTCHA detected! Waiting for solution...[/yellow]")
                    return True
                
                # Check for error message about CAPTCHA
                error_msg = tab.run_js("""
                    var error = document.querySelector('.alert-danger, .error-message');
                    return error ? error.innerText : null;
                """)
                
                if error_msg and "captcha" in error_msg.lower():
                    console.print(f"[yellow]CAPTCHA required: {error_msg}[/yellow]")
                    return True
                
                # Check if registration succeeded (no CAPTCHA needed)
                url_changed = tab.run_js("return window.location.href.includes('dashboard') || window.location.href.includes('account');")
                if url_changed:
                    console.print("[green]Registration successful - no CAPTCHA required![/green]")
                    return False  # No CAPTCHA, success already
                
                time.sleep(0.5)
            
            return False  # No CAPTCHA appeared within timeout
        
        def wait_for_captcha_solved(tab, timeout=90):
            """Wait for CAPTCHA to be solved after it appears"""
            start_time = time.time()
            last_log = 0
            
            while time.time() - start_time < timeout:
                # Method 1: Check for CAPTCHA response token
                captcha_token = tab.run_js("""
                    var token = document.querySelector('#g-recaptcha-response')?.value;
                    if (token && token.length > 0) return token;
                    
                    // Check for hCaptcha
                    var hcaptcha = document.querySelector('[name="h-captcha-response"]')?.value;
                    if (hcaptcha && hcaptcha.length > 0) return hcaptcha;
                    
                    return null;
                """)
                
                if captcha_token:
                    console.print("[green]CAPTCHA token detected![/green]")
                    return True
                
                # Method 2: Check if CAPTCHA iframe disappeared
                iframe_gone = tab.run_js("""
                    return !document.querySelector('iframe[src*="recaptcha"]') && 
                           !document.querySelector('iframe[src*="hcaptcha"]');
                """)
                
                if iframe_gone:
                    console.print("[green]CAPTCHA iframe removed![/green]")
                    return True
                
                # Method 3: Check for registration success
                success_check = tab.run_js("""
                    return !!(document.location.href.includes('dashboard') || 
                              document.location.href.includes('account') ||
                              document.querySelector('.alert-success'));
                """)
                
                if success_check:
                    console.print("[green]Registration completed after CAPTCHA![/green]")
                    return True
                
                elapsed = int(time.time() - start_time)
                if elapsed - last_log >= 10:
                    console.print(f"[dim]Waiting for CAPTCHA solution... {elapsed}s elapsed[/dim]")
                    last_log = elapsed
                
                time.sleep(1)
            
            console.print(f"[red]CAPTCHA timeout after {timeout}s[/red]")
            return False
        
        # ==================== OPTION 8: DOM MUTATION OBSERVER ====================
        def setup_captcha_observer(tab):
            """Set up DOM observer to detect CAPTCHA completion"""
            tab.run_js("""
                window.captchaResolved = false;
                window.captchaObserver = null;
                
                function initCaptchaObserver() {
                    if (window.captchaObserver) window.captchaObserver.disconnect();
                    
                    window.captchaObserver = new MutationObserver((mutations) => {
                        mutations.forEach((mutation) => {
                            if (mutation.target.id === 'g-recaptcha-response' && mutation.target.value) {
                                window.captchaResolved = true;
                            }
                            if (mutation.target.id === 'h-captcha-response' && mutation.target.value) {
                                window.captchaResolved = true;
                            }
                            if (mutation.removedNodes.length > 0) {
                                mutation.removedNodes.forEach((node) => {
                                    if (node.nodeType === 1 && node.tagName === 'IFRAME') {
                                        if ((node.src && node.src.includes('recaptcha')) ||
                                            (node.src && node.src.includes('hcaptcha'))) {
                                            window.captchaResolved = true;
                                        }
                                    }
                                });
                            }
                        });
                    });
                    
                    window.captchaObserver.observe(document.body, { 
                        childList: true, 
                        subtree: true,
                        attributes: true,
                        attributeFilter: ['value']
                    });
                }
                
                if (document.readyState === 'loading') {
                    document.addEventListener('DOMContentLoaded', initCaptchaObserver);
                } else {
                    initCaptchaObserver();
                }
            """)
        
        def wait_for_captcha_observer(tab, timeout=60):
            """Wait for observer to detect CAPTCHA resolution"""
            start = time.time()
            last_log = 0
            
            while time.time() - start < timeout:
                resolved = tab.run_js("return window.captchaResolved === true;")
                if resolved:
                    console.print("[green]CAPTCHA resolved (observer detected)![/green]")
                    return True
                
                # Also check success directly
                success = tab.run_js("""
                    return !!(document.location.href.includes('dashboard') || 
                              document.location.href.includes('account'));
                """)
                if success:
                    return True
                
                elapsed = int(time.time() - start)
                if elapsed - last_log >= 10:
                    console.print(f"[dim]CAPTCHA observer active... {elapsed}s elapsed[/dim]")
                    last_log = elapsed
                
                time.sleep(0.5)
            
            return False
        
        # ==================== FIXED: RETRY LOGIC WITH SAFE ELEMENT HANDLING ====================
        def fill_and_submit_form(tab, first_name, last_name, email, password):
            """Fill the registration form and submit with safe element handling"""
            try:
                # Wait for page to stabilize
                human_delay(1, 2)
                
                # First Name - with safe input and mouse movement
                human_mouse_move(tab, '#inputFirstName')
                human_delay(0.2, 0.5)
                if not safe_input(tab, '#inputFirstName', first_name, timeout=5):
                    return False, "first_name_field_not_found"
                human_delay(0.3, 0.8)
                
                # Last Name
                human_mouse_move(tab, '#inputLastName')
                human_delay(0.2, 0.5)
                if not safe_input(tab, '#inputLastName', last_name, timeout=5):
                    return False, "last_name_field_not_found"
                human_delay(0.3, 0.8)
                
                # Email
                human_mouse_move(tab, '#inputEmail')
                human_delay(0.2, 0.5)
                if not safe_input(tab, '#inputEmail', email, timeout=5):
                    return False, "email_field_not_found"
                human_delay(0.3, 0.8)
                
                # Password
                human_mouse_move(tab, '#inputNewPassword1')
                human_delay(0.2, 0.5)
                if not safe_input(tab, '#inputNewPassword1', password, timeout=5):
                    return False, "password_field_not_found"
                human_delay(0.3, 0.8)
                
                # Confirm Password
                human_mouse_move(tab, '#inputNewPassword2')
                human_delay(0.2, 0.5)
                if not safe_input(tab, '#inputNewPassword2', password, timeout=5):
                    return False, "confirm_password_field_not_found"
                human_delay(0.4, 1.0)
                
                # Terms Checkbox
                human_mouse_move(tab, ".custom-checkbox--input checkbox")
                human_delay(0.2, 0.5)
                if not safe_click(tab, ".custom-checkbox--input checkbox", timeout=5):
                    # Try alternative selector
                    if not safe_click(tab, "input[type='checkbox']", timeout=3):
                        console.print("[yellow]Could not find terms checkbox, continuing...[/yellow]")
                human_delay(0.5, 1.2)
                
                # Submit Button
                human_mouse_move(tab, '#btnFormRegister')
                human_delay(0.3, 0.8)
                if not safe_click(tab, '#btnFormRegister', timeout=5):
                    return False, "submit_button_not_found"
                
                return True, None
                
            except Exception as e:
                return False, str(e)
        
        def register_with_retry(tab, first_name, last_name, email, password, max_retries=2, progress_callback=None):
            """Attempt registration with retry logic"""
            for attempt in range(max_retries):
                try:
                    if attempt > 0:
                        console.print(f"[dim]Retry attempt {attempt + 1}/{max_retries}...[/dim]")
                        # Refresh page on retry
                        tab.refresh()
                        human_delay(2, 3)
                    
                    # Fill and submit
                    success, error = fill_and_submit_form(tab, first_name, last_name, email, password)
                    
                    if not success:
                        if attempt < max_retries - 1:
                            wait_time = 2 ** attempt
                            console.print(f"[dim]Form fill failed ({error}), retry in {wait_time}s...[/dim]")
                            time.sleep(wait_time)
                            continue
                        return False, error
                    
                    # After submission, wait for CAPTCHA to appear
                    human_delay(1, 2)
                    
                    # Check if CAPTCHA appeared
                    captcha_appeared = wait_for_captcha_to_appear(tab, timeout=10)
                    
                    if captcha_appeared:
                        console.print("[yellow]CAPTCHA detected - please solve it manually or via service[/yellow]")
                        
                        # Setup observer for CAPTCHA resolution
                        setup_captcha_observer(tab)
                        
                        # Wait for CAPTCHA to be solved
                        if not wait_for_captcha_observer(tab, timeout=90):
                            # If observer didn't detect, try direct check
                            if not wait_for_captcha_solved(tab, timeout=30):
                                if attempt < max_retries - 1:
                                    wait_time = 2 ** attempt
                                    console.print(f"[dim]CAPTCHA timeout, retry in {wait_time}s...[/dim]")
                                    time.sleep(wait_time)
                                    continue
                                return False, "captcha_timeout"
                    
                    # Check final success
                    human_delay(2, 3)
                    
                    success_indicator = tab.run_js("""
                        return !!(document.location.href.includes('dashboard') || 
                                  document.location.href.includes('account') ||
                                  document.querySelector('.alert-success') ||
                                  document.querySelector('.success-message'));
                    """)
                    
                    if success_indicator:
                        return True, None
                    
                    # Check for errors
                    error_msg = None
                    try:
                        error_element = tab.ele('.alert-danger, .error-message, .alert-warning', timeout=2)
                        if error_element:
                            error_msg = error_element.text.lower()
                    except:
                        pass
                    
                    if error_msg:
                        if 'captcha' in error_msg:
                            if attempt < max_retries - 1:
                                wait_time = 2 ** attempt
                                console.print(f"[dim]CAPTCHA error, retry in {wait_time}s...[/dim]")
                                time.sleep(wait_time)
                                continue
                            return False, "captcha"
                        elif 'email' in error_msg or 'already' in error_msg:
                            return False, "duplicate"
                        else:
                            return False, error_msg
                    
                    # If no success indicator and no error, assume failure
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        console.print(f"[dim]Unknown result, retry in {wait_time}s...[/dim]")
                        time.sleep(wait_time)
                        continue
                    
                    return False, "unknown_error"
                    
                except Exception as e:
                    console.print(f"[yellow]Attempt {attempt + 1} failed: {str(e)[:50]}[/yellow]")
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        console.print(f"[dim]Retrying in {wait_time}s...[/dim]")
                        time.sleep(wait_time)
                    else:
                        return False, str(e)
            
            return False, "max_retries_exceeded"
        
        # ==================== OPTION 5: COOKIE PERSISTENCE ====================
        def save_cookies(chrome, account_index):
            """Save browser cookies to file"""
            try:
                cookies = chrome.cookies()
                filename = f"session_{account_index}.pkl"
                with open(filename, 'wb') as f:
                    pickle.dump(cookies, f)
                return True
            except:
                return False
        
        def load_cookies(chrome, account_index):
            """Load cookies from file"""
            filename = f"session_{account_index}.pkl"
            if os.path.exists(filename):
                try:
                    with open(filename, 'rb') as f:
                        cookies = pickle.load(f)
                        for cookie in cookies:
                            chrome.set.cookies(cookie)
                    return True
                except:
                    pass
            return False
        
        # ==================== MAIN REGISTRATION LOOP ====================
        for x in range(executionCount):
            console.print(f"\n[bold cyan]{'='*50}[/bold cyan]")
            console.print(f"[bold cyan]Account {x+1}/{executionCount}[/bold cyan]")
            console.print(f"[bold cyan]{'='*50}[/bold cyan]")
            
            # OPTION 3: Rotate User Agent and Viewport
            current_ua = random.choice(user_agents)
            co.set_user_agent(current_ua)
            
            current_viewport = random.choice(viewport_sizes)
            co.set_argument('--window-size', f"{current_viewport['width']},{current_viewport['height']}")
            
            console.print(f"[dim]UA: {current_ua[:50]}...[/dim]")
            console.print(f"[dim]Viewport: {current_viewport['width']}x{current_viewport['height']}[/dim]")
            
            chrome = Chromium(addr_or_opts=co)
            tab = chrome.new_tab()
            tab.set.window.max()
            
            # OPTION 5: Load cookies if available
            if load_cookies(chrome, x):
                console.print("[dim]Loaded previous session cookies[/dim]")
                tab.refresh()
                human_delay(1, 2)
            
            # Create a single progress bar for this account
            bar = tqdm(total=100, colour="cyan", dynamic_ncols=True, position=0, leave=True)
            progress = 0
            
            used_email = gerar_email_aleatorio()
            
            console.print(f"\n[cyan]{tr('signup_process')}[/cyan]")
            console.print(f"[cyan]📧 Email: {used_email}[/cyan]")
            
            tab.get("https://www.exitlag.com/register.php")
            
            # OPTION 1: Human delay after page load
            human_delay(1.5, 3.5)
            progress += 15
            bar.update(15)
            bar.refresh()
            
            first_name = fake.first_name()
            last_name = fake.last_name()
            
            console.print(f"[yellow]{tr('filling_form')}[/yellow]")
            progress += 15
            bar.update(15)
            bar.refresh()
            
            # OPTION 7: Use retry logic for registration
            # Pass progress bar to update it during retries
            success, error_type = register_with_retry(tab, first_name, last_name, used_email, passw, max_retries=2)
            
            # Update progress to completion
            remaining = 100 - bar.n
            if remaining > 0:
                bar.update(remaining)
            bar.close()
            
            if success:
                accounts.append({"email": used_email, "password": passw, "success": True})
                console.print(f"[bold green]✓ {tr('registration_success')}[/bold green]")
                
                # OPTION 5: Save cookies for future sessions
                save_cookies(chrome, x)
                last_chrome = chrome
            else:
                if error_type == "captcha" or error_type == "captcha_timeout":
                    console.print(f"[bold red]✗ CAPTCHA verification failed or timed out[/bold red]")
                elif error_type == "duplicate":
                    console.print(f"[bold red]✗ Email already registered[/bold red]")
                else:
                    console.print(f"[bold red]✗ {tr('error')}: {error_type}[/bold red]")
                accounts.append({"email": used_email, "password": passw, "success": False})
                chrome.quit()
                continue
            
            # OPTION 1: Random delay between accounts
            if x < executionCount - 1:
                delay = random.uniform(5, 10)
                console.print(f"[yellow]{tr('waiting_next_account').format(delay=delay):.0f}s[/yellow]")
                time.sleep(delay)
        
        # Save successful accounts
        with open("accounts.txt", "a") as f:
            for acc in accounts:
                if acc["success"]:
                    f.write(f"{acc['email']} | {acc['password']}\n")
        
        # Clean up cookie files
        for x in range(executionCount):
            filename = f"session_{x}.pkl"
            if os.path.exists(filename):
                try:
                    os.remove(filename)
                except:
                    pass
        
        successful = sum(1 for acc in accounts if acc["success"])
        console.print(f"\n[bold cyan]{'='*50}[/bold cyan]")
        console.print(f"[bold green]✓ {tr('successfully_created_account').format(x=successful, executionCount=executionCount)}[/bold green]")
        console.print(f"[bold green]{tr('credentials_saved')}[/bold green]")
        console.print(f"[bold cyan]{'='*50}[/bold cyan]")

    input(tr("press_enter_to_exit"))


if __name__ == "__main__":
    asyncio.run(main())