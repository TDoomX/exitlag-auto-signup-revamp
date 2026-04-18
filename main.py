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
import ctypes
import math
import queue
from datetime import datetime
import atexit
import random
import string
import locale

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit, QRadioButton,
    QButtonGroup, QFrame, QFileDialog, QScrollArea, QMenu, QDialog,
    QProgressBar, QSizePolicy, QMessageBox
)
from PyQt6.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QObject, QSize, QPoint
)
from PyQt6.QtGui import (
    QFont, QColor, QPainter, QPen, QBrush, QLinearGradient,
    QPainterPath, QAction, QCursor
)

from tqdm import TqdmExperimentalWarning
from pydoll.browser import Chrome
from pydoll.browser.options import ChromiumOptions
from pydoll.constants import Key
from lib.lib import Main
from faker import Faker

warnings.filterwarnings("ignore", category=TqdmExperimentalWarning)

try:
    import psutil
    _PSUTIL_OK = True
except ImportError:
    _PSUTIL_OK = False

# ─── Ghost Mode ──────────────────────────────────────────────────────────────

class GhostModeAPI:
    SW_HIDE = 0

    def __init__(self):
        self.user32 = ctypes.windll.user32
        self._EnumWindowsProc = ctypes.WINFUNCTYPE(
            ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p
        )

    def _hide_by_title(self, title_substring):
        if not _PSUTIL_OK:
            return
        def foreach_window(hwnd, _):
            try:
                buf = ctypes.create_unicode_buffer(256)
                self.user32.GetWindowTextW(hwnd, buf, 256)
                if title_substring in buf.value and self.user32.IsWindowVisible(hwnd):
                    self.user32.ShowWindow(hwnd, self.SW_HIDE)
            except Exception:
                pass
            return True
        self.user32.EnumWindows(self._EnumWindowsProc(foreach_window), 0)

    def _check_if_window_exists(self, title_substring):
        if not _PSUTIL_OK:
            return False
        found = [False]
        def foreach_window(hwnd, _):
            try:
                buf = ctypes.create_unicode_buffer(256)
                self.user32.GetWindowTextW(hwnd, buf, 256)
                if title_substring in buf.value:
                    found[0] = True
            except Exception:
                pass
            return True
        self.user32.EnumWindows(self._EnumWindowsProc(foreach_window), 0)
        return found[0]

    def _force_close_by_title(self, title_substring):
        if not _PSUTIL_OK:
            return
        def foreach_window(hwnd, _):
            try:
                buf = ctypes.create_unicode_buffer(256)
                self.user32.GetWindowTextW(hwnd, buf, 256)
                if title_substring in buf.value:
                    self.user32.PostMessageW(hwnd, 16, 0, 0)
            except Exception:
                pass
            return True
        self.user32.EnumWindows(self._EnumWindowsProc(foreach_window), 0)

    async def auto_cloak_loop(self, title_substring, duration=120, interval=0.4, cancel_event=None):
        elapsed = 0.0
        while elapsed < duration:
            if cancel_event and cancel_event.is_set():
                break
            self._hide_by_title(title_substring)
            await asyncio.sleep(interval)
            elapsed += interval

    def __del__(self):
        try:
            self._force_close_by_title("DOOM_GHOSTAPI")
        except Exception:
            pass

def cleanup_orphaned_browsers():
    try:
        GhostModeAPI()._force_close_by_title("DOOM_GHOSTAPI")
    except Exception:
        pass

atexit.register(cleanup_orphaned_browsers)

# ─── Constants ────────────────────────────────────────────────────────────────

CONFIG_FILE          = "last_config.json"
GITHUB_RAW           = "https://raw.githubusercontent.com/TDoomX/exitlag-auto-signup-revamp/master"
LOCAL_VERSION_FILE   = "version.txt"
TRANSLATIONS_LANGS = ["de", "en", "es", "fr", "it", "ja", "pt", "ru", "zh", "vi", "ar"]

BG       = "#0d0f14"
BG2      = "#13161e"
BG3      = "#1a1e2a"
ACCENT   = "#00c8ff"
ACCENT2  = "#0066ff"
SUCCESS  = "#00e676"
WARNING  = "#ffab00"
ERROR    = "#ff3d71"
TEXT     = "#e8eaf0"
TEXT_DIM = "#6b7280"
BORDER   = "#252a38"

STYLESHEET = f"""
QMainWindow, QDialog, QWidget#root {{
    background-color: {BG};
}}
QWidget {{
    background-color: {BG};
    color: {TEXT};
    font-family: 'Segoe UI';
    font-size: 10pt;
}}

QWidget#menuBar {{
    background-color: {BG2};
    border-bottom: 1px solid {BORDER};
}}
QPushButton#menuBtn {{
    background: transparent;
    color: {TEXT_DIM};
    border: none;
    padding: 4px 12px;
    font-size: 9pt;
}}
QPushButton#menuBtn:hover {{
    color: {ACCENT};
    background-color: {BG3};
}}
QPushButton#loaderBtn {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {ACCENT2}, stop:1 {ACCENT});
    color: white;
    border: none;
    border-radius: 5px;
    padding: 4px 14px;
    font-size: 9pt;
    font-weight: bold;
}}
QPushButton#loaderBtn:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {ACCENT}, stop:1 {ACCENT2});
}}

QLineEdit, QSpinBox {{
    background-color: {BG3};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 8px 10px;
    font-size: 10pt;
    selection-background-color: {ACCENT2};
}}
QLineEdit:focus, QSpinBox:focus {{
    border: 1px solid {ACCENT};
}}
QSpinBox::up-button, QSpinBox::down-button {{
    background-color: {BG2};
    border: none;
    width: 22px;
    subcontrol-origin: border;
}}
QSpinBox::up-button {{
    subcontrol-position: top right;
    border-left: 1px solid {BORDER};
    border-bottom: 1px solid {BORDER};
    border-top-right-radius: 4px;
}}
QSpinBox::down-button {{
    subcontrol-position: bottom right;
    border-left: 1px solid {BORDER};
    border-top: 1px solid {BORDER};
    border-bottom-right-radius: 4px;
}}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
    background-color: {ACCENT2};
}}
QSpinBox::up-arrow {{
    width: 10px;
    height: 10px;
}}
QSpinBox::down-arrow {{
    width: 10px;
    height: 10px;
}}

QPushButton#primary {{
    background-color: {ACCENT2};
    color: {TEXT};
    border: none;
    border-radius: 4px;
    padding: 10px 16px;
    font-size: 10pt;
    font-weight: bold;
}}
QPushButton#primary:hover {{
    background-color: {ACCENT};
}}
QPushButton#primary:disabled {{
    background-color: {BG3};
    color: {TEXT_DIM};
}}
QPushButton#secondary {{
    background-color: {BG3};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 10px 16px;
    font-size: 10pt;
}}
QPushButton#secondary:hover {{
    background-color: {BG2};
    border-color: {ACCENT};
    color: {ACCENT};
}}
QPushButton#secondary:disabled {{
    color: {TEXT_DIM};
    border-color: {BORDER};
}}
QPushButton#danger {{
    background-color: {ERROR};
    color: {BG};
    border: none;
    border-radius: 4px;
    padding: 10px 16px;
    font-size: 10pt;
    font-weight: bold;
}}
QPushButton#danger:hover {{
    background-color: #ff6b93;
}}
QPushButton#danger:disabled {{
    background-color: {BG3};
    color: {TEXT_DIM};
}}
QPushButton#success {{
    background-color: {SUCCESS};
    color: {BG};
    border: none;
    border-radius: 4px;
    padding: 10px 16px;
    font-size: 10pt;
    font-weight: bold;
}}
QPushButton#success:hover {{
    background-color: #33eb91;
}}
QPushButton#warning {{
    background-color: {WARNING};
    color: {BG};
    border: none;
    border-radius: 4px;
    padding: 10px 16px;
    font-size: 10pt;
    font-weight: bold;
}}
QPushButton#warning:hover {{
    background-color: #ffc140;
}}

QRadioButton {{
    color: {TEXT};
    font-size: 10pt;
    spacing: 6px;
}}
QRadioButton::indicator {{
    width: 14px;
    height: 14px;
    border-radius: 7px;
    border: 2px solid {BORDER};
    background-color: {BG3};
}}
QRadioButton::indicator:checked {{
    background-color: {ACCENT2};
    border-color: {ACCENT2};
}}

QTextEdit#logText {{
    background-color: {BG3};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 4px;
    font-family: 'Consolas';
    font-size: 9pt;
    padding: 6px;
    selection-background-color: {BG2};
}}

QLabel#title {{
    color: {ACCENT};
    font-size: 20pt;
    font-weight: bold;
}}
QLabel#subtitle {{
    color: {TEXT_DIM};
    font-size: 9pt;
}}
QLabel#fieldLabel {{
    color: {TEXT_DIM};
    font-size: 9pt;
}}
QLabel#stepLabel {{
    color: {ACCENT};
    font-size: 9pt;
}}
QLabel#progressLabel {{
    color: {TEXT_DIM};
    font-size: 9pt;
}}
QLabel#errorLabel {{
    color: {ERROR};
    font-size: 9pt;
}}

QFrame#separator {{
    background-color: {BORDER};
    max-height: 1px;
}}

QPushButton#spinBtn {{
    background-color: {BG3};
    color: {TEXT};
    border: 1px solid {BORDER};
    font-size: 9pt;
    font-weight: bold;
    padding: 0;
    border-radius: 3px;
}}
QPushButton#spinBtn:hover {{
    background-color: {ACCENT2};
    color: white;
    border-color: {ACCENT2};
}}

QScrollBar:vertical {{
    background: {BG2};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 4px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background: {TEXT_DIM};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QFrame#card {{
    background-color: {BG2};
    border: 1px solid {BORDER};
    border-radius: 6px;
}}

QMenu {{
    background-color: {BG2};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 4px;
}}
QMenu::item {{
    padding: 6px 20px;
    border-radius: 3px;
}}
QMenu::item:selected {{
    background-color: {BG3};
    color: {ACCENT};
}}
"""

# ─── Translations & Config ────────────────────────────────────────────────────

_translation_cache = None
_silent_mode = False

_TR_FALLBACKS = {
    "script_cancelled": "Script cancelled by user.",
    "menu_silent_on":   "Silent ON",
    "menu_silent_off":  "Silent OFF",
}

def get_base():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def get_local_version():
    try:
        with open(os.path.join(get_base(), LOCAL_VERSION_FILE), "r") as f:
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
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        return False

def load_translations():
    LANG_MAP = {
        'pt': 'pt', 'en': 'en', 'es': 'es', 'fr': 'fr',
        'de': 'de', 'it': 'it', 'ru': 'ru', 'ja': 'ja', 'zh': 'zh',
        'vi': 'vi', 'ar': 'ar',

        'portuguese': 'pt', 'english': 'en', 'spanish': 'es',
        'french': 'fr', 'german': 'de', 'italian': 'it',
        'russian': 'ru', 'japanese': 'ja', 'chinese': 'zh',
        'vietnamese': 'vi', 'arabic': 'ar',
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
        translation_path = os.path.join(base, "translations", "en.json")
    with open(translation_path, "r", encoding="utf-8") as f:
        return json.load(f)

def tr(key):
    global _translation_cache
    if _translation_cache is None:
        _translation_cache = load_translations()
    return _translation_cache.get(key, _TR_FALLBACKS.get(key, key))

def save_config(browser_path, password, proxy, execution_count, plan):
    config = {"browser_path": browser_path, "password": password,
               "proxy": proxy, "execution_count": execution_count, "plan": plan}
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
    except Exception:
        pass

def load_config():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return None

def is_valid_password(password):
    if len(password) < 8: return False
    if not re.search(r"[a-z]", password): return False
    if not re.search(r"[A-Z]", password): return False
    if not re.search(r"[0-9]", password): return False
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"|,.<>/?]", password): return False
    return True

def generate_random_password():
    length = 12
    special_chars = "!@#$%^&*()_+-=[]{};':\"|,.<>/?"
    password_chars = [
        random.choice(string.ascii_lowercase),
        random.choice(string.ascii_uppercase),
        random.choice(string.digits),
        random.choice(special_chars),
    ]
    all_chars = string.ascii_letters + string.digits + special_chars
    password_chars.extend(random.choice(all_chars) for _ in range(length - 4))
    random.shuffle(password_chars)
    return ''.join(password_chars)

def gerar_email_aleatorio():
    """Email para plano de 3 dias (trial)"""
    return ''.join(random.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(8)) + "@zylker.com"

def gerar_email_plan2():
    """Email para plano de 7 dias (omen)"""
    return ''.join(random.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(8)) + "@zylker.com"

# ─── Hacker Banner Widget ────────────────────────────────────────────────────

class HackerBannerWidget(QWidget):
    """
    ASCII-art banner estilo warez/demoscene anos 2000.
    Efeitos: glitch de cor, cursor piscante, scanlines, ruído de chars.
    """

    _ASCII = [
        "______ _____  ________  _____   _______ _       ___  _____ ",
        "|  _  \\  _  ||  _  |  \\/  |\\ \\ / /_   _| |     / _ \\|  __ \\",
        "| | | | | | || | | | .  . | \\ V /  | | | |    / /_\\ \\ |  \\/",
        "| | | | | | || | | | |\\/| | /   \\  | | | |    |  _  | | __ ",
        "| |/ /\\ \\_/ /\\ \\_/ / |  | |/ /^\\ \\ | | | |____| | | | |_\\ \\",
        "|___/  \\___/  \\___/\\_|  |_/\\/   \\/ \\_/ \\_____/\\_| |_/\\____/",
    ]

    _NOISE_CHARS = list(r"@#$%&!?\/|<>[]{}01")

    def __init__(self, subtitle="", parent=None):
        super().__init__(parent)
        self._subtitle  = subtitle
        self._tick      = 0
        self._cursor_on = True
        self._noise     = {}          # {(row, col): (char, ttl)}
        self._glitch_x  = 0
        self._glitch_on = False

        self.setFixedHeight(112)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start(80)          # ~12 fps — suficiente pro efeito

    def _on_tick(self):
        self._tick += 1

        # cursor blink a cada 6 ticks (~500 ms)
        if self._tick % 6 == 0:
            self._cursor_on = not self._cursor_on

        # quick glitch every ~2 s
        if self._tick % 25 == 0:
            self._glitch_on = True
            self._glitch_x  = random.randint(-4, 4)
        elif self._tick % 25 == 3:
            self._glitch_on = False
            self._glitch_x  = 0

        # inject random noise
        if self._tick % 4 == 0 and random.random() < 0.6:
            r = random.randrange(len(self._ASCII))
            c = random.randrange(len(self._ASCII[r]))
            self._noise[(r, c)] = (random.choice(self._NOISE_CHARS), 3)

        # decrement noise TTL
        dead = [k for k, (ch, ttl) in self._noise.items() if ttl <= 1]
        for k in dead:
            del self._noise[k]
        for k in list(self._noise):
            if k in self._noise:
                ch, ttl = self._noise[k]
                self._noise[k] = (ch, ttl - 1)

        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        W, H = self.width(), self.height()

        # fundo transparente (herda o BG do app)
        p.fillRect(0, 0, W, H, QColor(0, 0, 0, 0))

        # scanlines sutis
        scan_col = QColor(0, 0, 0, 18)
        for y in range(0, H, 2):
            p.fillRect(0, y, W, 1, scan_col)

        # fonte monospace para o ASCII
        font = QFont("Consolas", 7)
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.5)
        p.setFont(font)

        fm       = p.fontMetrics()
        ch_w     = fm.horizontalAdvance("X")
        ch_h     = fm.height()
        rows     = len(self._ASCII)
        max_cols = max(len(l) for l in self._ASCII)
        total_w  = max_cols * ch_w
        x0       = max(10, (W - total_w) // 2)
        y0       = 12

        # base color cycling — green/cyan like an old terminal
        t        = self._tick
        r_base   = int(0 + 10 * math.sin(t * 0.05))
        g_base   = int(180 + 30 * math.sin(t * 0.03))
        b_base   = int(220 + 35 * math.sin(t * 0.07))
        base_col = QColor(max(0,r_base), min(255,g_base), min(255,b_base))

        glitch_col  = QColor(255, 50,  80)   # vermelho no glitch
        noise_col   = QColor(80,  255, 120)  # bright green for noise
        dim_col     = QColor(0,   100, 130)  # chars apagados

        for row_i, line in enumerate(self._ASCII):
            gx = self._glitch_x if (self._glitch_on and row_i % 3 == 1) else 0
            for col_i, orig_ch in enumerate(line):
                cx = x0 + col_i * ch_w + gx
                cy = y0 + row_i * ch_h

                if (row_i, col_i) in self._noise:
                    ch  = self._noise[(row_i, col_i)][0]
                    col = noise_col
                elif orig_ch == ' ':
                    continue
                elif self._glitch_on and row_i == 2 and col_i % 7 == 0:
                    ch  = orig_ch
                    col = glitch_col
                else:
                    # gradiente horizontal suave
                    t2  = col_i / max(max_cols - 1, 1)
                    rv  = int(r_base * (1 - t2))
                    gv  = int(g_base * (0.6 + 0.4 * t2))
                    bv  = int(b_base * (0.7 + 0.3 * (1 - t2)))
                    col = QColor(max(0,min(255,rv)), max(0,min(255,gv)), max(0,min(255,bv)))
                    ch  = orig_ch

                p.setPen(col)
                p.drawText(cx, cy + ch_h - fm.descent(), ch)

        # decorative line below the ASCII art
        deco_y = y0 + rows * ch_h + 3
        grad = QLinearGradient(x0, deco_y, x0 + total_w, deco_y)
        grad.setColorAt(0.0, QColor(0, 0, 0, 0))
        grad.setColorAt(0.3, base_col)
        grad.setColorAt(0.7, base_col)
        grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setPen(QPen(QBrush(grad), 1))
        p.drawLine(x0, deco_y, x0 + total_w, deco_y)

        # subtitle + cursor piscante
        if self._subtitle:
            sfont = QFont("Consolas", 8)
            sfont.setStyleHint(QFont.StyleHint.Monospace)
            p.setFont(sfont)
            sfm     = p.fontMetrics()
            cursor  = "_" if self._cursor_on else " "
            txt     = f">> {self._subtitle}{cursor}"
            tw      = sfm.horizontalAdvance(txt)
            sx      = max(10, (W - tw) // 2)
            sy      = deco_y + 14
            # glow shadow
            glow    = QColor(0, 200, 255, 40)
            p.setPen(glow)
            for dx in (-1, 0, 1):
                p.drawText(sx + dx, sy + 1, txt)
            p.setPen(QColor(0, 200, 220))
            p.drawText(sx, sy, txt)

        p.end()

    def closeEvent(self, event):
        self._timer.stop()
        super().closeEvent(event)


# ─── Loader ───────────────────────────────────────────────────────────────────

def open_loader():
    base_dir = get_base()
    loader_path = os.path.join(base_dir, "Exitloader.exe")
    dll_path    = os.path.join(base_dir, "ExitLag.dll")
    missing = []
    if not os.path.exists(loader_path):
        missing.append("Exitloader.exe")
    if not os.path.exists(dll_path):
        missing.append("ExitLag.dll")
    if missing:
        QMessageBox.critical(
            None, tr("loader_missing_title"),
            tr("loader_missing_body") + "\n".join(f"  • {m}" for m in missing)
        )
        return
    ctypes.windll.shell32.ShellExecuteW(None, "runas", loader_path, None, base_dir, 1)

# ─── Browser Automation ───────────────────────────────────────────────────────


# ─── Plan configs ─────────────────────────────────────────────────────────────

PLAN_CONFIGS = {
    "1": {
        "url":         "https://www.exitlag.com/lp/trial",
        "email_fn":    "gerar_email_aleatorio",
        "selectors": {
            "first":    "#inputFirstName",
            "last":     "#inputLastName",
            "email":    "#inputEmail",
            "password": "#inputNewPassword",
            "confirm":  "#inputNewPassword2",
            "tos":      "#hero-terms-check",
        },
        "pre_click":   "#heroSocialFlow > button",
        "pre_delay":   1.0,
        "success_url": "exitlag.com/lp/trial/success",
        "success_txt": "your account has been created",
        "submit_fn":   "onLpRegister",
    },
    "2": {
        "url":         "https://www.exitlag.com/lp/omen",
        "email_fn":    "gerar_email_plan2",
        "selectors": {
            "first":    "#firstName",
            "last":     "#lastName",
            "email":    "#email",
            "password": "#password",
            "confirm":  "#confirmPassword",
            "tos":      "#acceptTos",
        },
        "pre_click":   None,
        "pre_delay":   0.0,
        "success_url": "account_created=1",
        "success_txt": "soon you will recieve an e-mail from exitlag",
        "submit_fn":   None,
    },
}

_EMAIL_FNS = {
    "gerar_email_aleatorio": lambda: gerar_email_aleatorio(),
    "gerar_email_plan2":     lambda: gerar_email_plan2(),
}

# ─── Browser Automation ───────────────────────────────────────────────────────

class BrowserAutomation:
    """Classe unificada para todos os planos — comportamento injetado via PLAN_CONFIGS."""

    def __init__(self, plan_config: dict):
        self.cfg   = plan_config
        self.fake  = Faker()
        self.ghost = None

    # ── helpers ───────────────────────────────────────────────────────────────

    async def fill_field_instantly(self, tab, selector, text):
        await tab.execute_script(f"document.querySelector('{selector}').focus();")
        await asyncio.sleep(0.1)
        escaped_text = text.replace("\\", "\\\\").replace('"', '\\"')
        await tab.execute_script(
            f"document.querySelector('{selector}').value = \"{escaped_text}\";"
        )
        await tab.execute_script(
            f"document.querySelector('{selector}').dispatchEvent(new Event('input', {{ bubbles: true }}));"
        )
        await asyncio.sleep(0.05)

    async def _interruptible_sleep(self, seconds, cancel_event):
        elapsed = 0.0
        while elapsed < seconds:
            if cancel_event and cancel_event.is_set():
                return True
            await asyncio.sleep(0.2)
            elapsed += 0.2
        return False

    async def _setup_ghost_mode(self, tab, log_cb, cancel_event):
        try:
            await tab.execute_script('document.title = "DOOM_GHOSTAPI";')
            self.ghost = GhostModeAPI()
            self.ghost._hide_by_title("DOOM_GHOSTAPI")
            asyncio.create_task(
                self.ghost.auto_cloak_loop("DOOM_GHOSTAPI", duration=120, cancel_event=cancel_event)
            )
            if not _PSUTIL_OK:
                log_cb(tr("psutil_missing"), "warning")
        except Exception as e:
            log_cb(tr("ghost_hide_error").format(e=str(e)[:50]), "warning")

    # ── main entry point ──────────────────────────────────────────────────────

    async def register_account(self, password, browser_path, log_cb, step_cb,
                                headless=False, cancel_event=None):
        cfg        = self.cfg
        sel        = cfg["selectors"]
        email      = _EMAIL_FNS[cfg["email_fn"]]()
        first_name = self.fake.first_name()
        last_name  = self.fake.last_name()

        options = ChromiumOptions()
        options.browser_preferences = {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_settings.popups": 0,
        }
        if headless:
            options.add_argument("--window-position=30000,30000")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-blink-features=AutomationControlled")
        if browser_path:
            options.binary_location = browser_path

        browser = Chrome(options=options)
        tab     = await browser.start()
        if headless:
            await self._setup_ghost_mode(tab, log_cb, cancel_event)

        def _early_exit():
            log_cb(f"⚠ {tr('btn_cancel')}", "warning")

        async def _safe_stop():
            try:
                await browser.stop()
            except Exception:
                pass

        try:
            log_cb(f"📧 Email: {email}", "info")
            step_cb(tr('opening_browser'))
            await tab.go_to(cfg["url"])

            if await self._interruptible_sleep(2, cancel_event):
                _early_exit(); await _safe_stop()
                return {"email": email, "password": password, "success": False}

            step_cb(tr('filling_form'))
            log_cb(tr('filling_form'), "info")

            # pre_click: extra button the trial page requires before showing the form
            if cfg["pre_click"]:
                await tab.execute_script(
                    f"document.querySelector('{cfg['pre_click']}').click();"
                )
                await asyncio.sleep(cfg["pre_delay"])

            await self.fill_field_instantly(tab, sel["first"],    first_name)
            await self.fill_field_instantly(tab, sel["last"],     last_name)
            await self.fill_field_instantly(tab, sel["email"],    email)
            await self.fill_field_instantly(tab, sel["password"], password)
            await self.fill_field_instantly(tab, sel["confirm"],  password)
            await asyncio.sleep(0.2)
            await tab.execute_script(f"document.querySelector('{sel['tos']}').click();")

            step_cb(tr('waiting_captcha'))
            log_cb(tr('waiting_captcha'), "warning")
            if await self._interruptible_sleep(5, cancel_event):
                _early_exit(); await _safe_stop()
                return {"email": email, "password": password, "success": False}

            step_cb(tr('submitting_form'))
            log_cb(tr('submitting_form'), "info")
            _submit_fn = cfg.get("submit_fn")
            if _submit_fn:
                # Button uses reCAPTCHA callback — calling it directly ensures the submit
                await tab.execute_script(f"document.querySelector('#registerButton').click();")
                await asyncio.sleep(0.5)
                await tab.execute_script(f"if(typeof {_submit_fn}==='function') {_submit_fn}('dummy-token');")
            else:
                await tab.execute_script("document.querySelector('#registerButton').click();")

            if await self._interruptible_sleep(5, cancel_event):
                _early_exit(); await _safe_stop()
                return {"email": email, "password": password, "success": False}

            try:
                def _extract(result):
                    if isinstance(result, dict):
                        try:    return result["result"]["result"]["value"]
                        except (KeyError, TypeError): return None
                    return result

                current_url   = _extract(await tab.execute_script("return window.location.href;"))
                page_title    = _extract(await tab.execute_script("return document.title;"))
                page_body_txt = _extract(await tab.execute_script(
                    "return document.body ? document.body.innerText : '';"
                ))

                error_text = _extract(await tab.execute_script("""
                    const errorSelectors = ['.error', '.alert-danger', '[data-error]',
                        '[class*="invalid-feedback"]', '.form-error', '[class*="error-msg"]',
                        '[class*="alert-error"]'];
                    for (const sel of errorSelectors) {
                        const error = document.querySelector(sel);
                        if (error && error.offsetParent !== null && error.textContent.trim()) {
                            return error.textContent.trim();
                        }
                    }
                    return null;
                """))

                success_el = _extract(await tab.execute_script("""
                    const s = document.querySelector(
                        '.success, .alert-success, [class*="success"], [class*="thank"],' +
                        '[class*="confirm"], [class*="complete"], [class*="registered"],' +
                        '[id*="success"], [id*="confirm"], [id*="complete"]'
                    );
                    return s ? s.textContent.trim() : null;
                """))

                error_text    = str(error_text).strip()    if error_text    not in (None, "None", "") else None
                success_el    = str(success_el).strip()    if success_el    not in (None, "None", "") else None
                current_url   = str(current_url)           if current_url   else ""
                page_title    = str(page_title).lower()    if page_title    else ""
                page_body_txt = str(page_body_txt).lower() if page_body_txt else ""

                # exact plan signals — highest priority
                _success_url = cfg.get("success_url", "").lower()
                _success_txt = cfg.get("success_txt", "").lower()
                url_lower    = current_url.lower()
                body_lower   = page_body_txt.lower()

                exact_url = bool(_success_url and _success_url in url_lower)
                exact_txt = bool(_success_txt and _success_txt in body_lower)

                # generic fallback
                SUCCESS_KEYWORDS = ("success", "thank", "confirm", "complete",
                                    "registered", "account-created", "welcome",
                                    "obrigado", "cadastro")
                success_by_url   = any(k in url_lower  for k in SUCCESS_KEYWORDS)
                success_by_title = any(k in page_title for k in SUCCESS_KEYWORDS)
                success_by_body  = any(k in body_lower for k in (
                    "thank you", "successfully created", "account created",
                    "registration complete", "bem-vindo", "cadastro realizado"
                ))

                success = False
                if exact_url or exact_txt or success_el or success_by_url or success_by_title or success_by_body:
                    success = True
                    step_cb(tr('step_done'))
                    log_cb(f"✓ {tr('registration_success')}", "success")
                    log_cb(f"   📧 {email}",    "success")
                    log_cb(f"   🔑 {password}", "success")
                elif error_text and "captcha" in error_text.lower():
                    log_cb(f"✗ {tr('captcha_failed')}", "error")
                    step_cb(tr('step_failed'))
                elif error_text:
                    log_cb(f"✗ {tr('error_fill_form').format(e=error_text)}", "error")
                    step_cb(tr('step_failed'))
                else:
                    step_cb(tr('step_failed'))

                try:
                    await browser.stop()
                    await asyncio.sleep(0.5)
                    if headless and self.ghost:
                        if self.ghost._check_if_window_exists("DOOM_GHOSTAPI"):
                            log_cb(tr("browser_still_open"), "warning")
                            self.ghost._force_close_by_title("DOOM_GHOSTAPI")
                            await asyncio.sleep(0.5)
                        else:
                            log_cb(tr("browser_closed_ok"), "info")
                except Exception:
                    pass

                return {"email": email, "password": password, "success": success}

            except Exception as e:
                log_cb(f"✗ {tr('error_fill_form').format(e=str(e)[:80])}", "error")
                step_cb(tr('step_failed'))
                await _safe_stop()
                return {"email": email, "password": password, "success": False}

        except Exception as e:
            log_cb(f"✗ {tr('error_fill_form').format(e=str(e)[:80])}", "error")
            await _safe_stop()
            return {"email": email, "password": password, "success": False}


async def run_accounts(plan, passw, count, browser_path, log_cb, step_cb, done_cb,
                       cancel_event=None, headless=False):
    """Executa criação de contas — uma única instância de BrowserAutomation por run."""
    accounts   = []
    automation = BrowserAutomation(PLAN_CONFIGS.get(plan, PLAN_CONFIGS["1"]))

    for x in range(count):
        if cancel_event and cancel_event.is_set():
            log_cb(f"\n⚠ {tr('script_cancelled')}", "warning")
            break
        log_cb(f"\n{'─'*40}", "dim")
        log_cb(tr('account_counter').format(x=x+1, count=count), 'accent')
        log_cb(f"{'─'*40}", "dim")

        result = await automation.register_account(
            passw, browser_path, log_cb, step_cb,
            headless=headless, cancel_event=cancel_event,
        )
        result["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        accounts.append(result)

        if result.get("success"):
            with open("accounts.txt", "a", encoding="utf-8") as f:
                f.write(f"{result['email']} | {result['password']} | {result['created_at']}\n")

        if cancel_event and cancel_event.is_set():
            log_cb(f"\n⚠ {tr('script_cancelled')}", "warning")
            break

        if x < count - 1:
            delay = 3
            log_cb(tr('waiting_next_account').format(delay=delay), "warning")
            elapsed = 0.0
            while elapsed < delay:
                if cancel_event and cancel_event.is_set():
                    break
                await asyncio.sleep(0.2)
                elapsed += 0.2

    successful = sum(1 for acc in accounts if acc["success"])
    log_cb(f"\n{'═'*40}", "dim")
    log_cb(f"✓ {tr('successfully_created_account').format(x=successful, executionCount=count)}", "success")
    log_cb(tr('credentials_saved'), "success")
    done_cb(accounts)


# ─── PyQt6 Segmented Progress Bar ────────────────────────────────────────────

class SegmentedBarWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(16)
        self._pct = 0.0
        self._target = 0.0
        self._pulse_t = 0.0
        self._completed = False

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(33)

    def set_pct(self, value):
        self._target = max(0.0, min(1.0, value))
        if self._target >= 1.0:
            self._completed = True

    def _tick(self):
        self._pct += (self._target - self._pct) * 0.12
        self._pulse_t += 0.08
        self.update()

    def stop(self):
        self._timer.stop()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        W = self.width()
        H = self.height()
        p = self._pct
        C = 6

        NUM_SEGS = 20
        SEG_GAP  = 3
        BAR_PAD  = 3

        BG_COL     = QColor("#1a1e2a")
        BORDER_COL = QColor("#00c8ff")
        SEG_DIM    = QColor("#003a4a")
        CHECK_COL  = QColor("#00e676")

        path = QPainterPath()
        path.addRoundedRect(0, 0, W, H, C, C)
        painter.fillPath(path, BG_COL)
        painter.setPen(QPen(BORDER_COL if not self._completed else CHECK_COL, 1))
        painter.drawPath(path)

        if self._completed and p >= 0.99:
            painter.setPen(QPen(CHECK_COL, 2))
            cx, cy = W // 2, H // 2
            s = H * 0.28
            painter.drawLine(int(cx - s), cy,
                             int(cx - s * 0.2), int(cy + s * 0.8))
            painter.drawLine(int(cx - s * 0.2), int(cy + s * 0.8),
                             int(cx + s), int(cy - s * 0.7))
            return

        import math
        pulse = 0.7 + 0.3 * math.sin(self._pulse_t)
        filled = int(p * NUM_SEGS)

        inner_x0 = C + 2
        inner_x1 = W - C - 2
        inner_w   = inner_x1 - inner_x0
        seg_total = (inner_w + SEG_GAP) / NUM_SEGS
        seg_w     = seg_total - SEG_GAP

        painter.setPen(Qt.PenStyle.NoPen)
        for i in range(NUM_SEGS):
            x0 = int(inner_x0 + i * seg_total)
            x1 = int(x0 + seg_w)
            y0 = BAR_PAD
            y1 = H - BAR_PAD
            if i < filled:
                fade = 0.6 + 0.4 * (i / max(filled - 1, 1))
                b_val = min(255, int(0xff * fade * pulse))
                g_val = min(255, int(0xc8 * fade * pulse))
                color = QColor(0, g_val, b_val)
                painter.fillRect(x0, y0, x1 - x0, y1 - y0, color)
                painter.setPen(QPen(QColor("#5ae8ff"), 1))
                painter.drawLine(x0, y0, x1, y0)
                painter.setPen(Qt.PenStyle.NoPen)
            else:
                painter.fillRect(x0, y0, x1 - x0, y1 - y0, SEG_DIM)

        painter.end()

# ─── Worker thread for async automation ───────────────────────────────────────

class AutomationWorker(QObject):
    log_signal  = pyqtSignal(str, str)
    step_signal = pyqtSignal(str)
    done_signal = pyqtSignal(list)

    def __init__(self, plan, passw, count, browser_path, cancel_event, headless):
        super().__init__()
        self.plan         = plan
        self.passw        = passw
        self.count        = count
        self.browser_path = browser_path
        self.cancel_event = cancel_event
        self.headless     = headless

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_accounts(
            self.plan, self.passw, self.count, self.browser_path,
            lambda msg, lvl="info": self.log_signal.emit(msg, lvl),
            lambda msg: self.step_signal.emit(msg),
            lambda accounts: self.done_signal.emit(accounts),
            cancel_event=self.cancel_event,
            headless=self.headless,
        ))
        loop.close()

# ─── Reusable UI helpers ──────────────────────────────────────────────────────

class NumberSpinBox(QWidget):
    """Spinbox customizado: QLineEdit + botões − e + sem depender do QSpinBox nativo."""
    valueChanged = pyqtSignal(int)

    def __init__(self, min_val=1, max_val=100, value=1, parent=None):
        super().__init__(parent)
        self._min = min_val
        self._max = max_val
        self._value = value

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._edit = QLineEdit(str(value))
        self._edit.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self._edit.setFixedWidth(70)
        self._edit.textEdited.connect(self._on_text_edited)
        outer.addWidget(self._edit)

        btn_col = QVBoxLayout()
        btn_col.setContentsMargins(0, 0, 0, 0)
        btn_col.setSpacing(1)

        for symbol, delta in [("+", 1), ("−", -1)]:
            btn = QPushButton(symbol)
            btn.setObjectName("spinBtn")
            btn.setFixedSize(24, 18)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.clicked.connect(lambda _, d=delta: self._step(d))
            btn_col.addWidget(btn)

        outer.addLayout(btn_col)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def _step(self, delta):
        self.setValue(self._value + delta)

    def _on_text_edited(self, text):
        try:
            v = int(text)
            if self._min <= v <= self._max:
                self._value = v
                self.valueChanged.emit(v)
        except ValueError:
            pass

    def setValue(self, v):
        self._value = max(self._min, min(self._max, v))
        self._edit.setText(str(self._value))
        self.valueChanged.emit(self._value)

    def value(self):
        try:
            v = int(self._edit.text())
            return max(self._min, min(self._max, v))
        except ValueError:
            return self._value


def make_separator():
    line = QFrame()
    line.setObjectName("separator")
    line.setFrameShape(QFrame.Shape.HLine)
    return line

def make_field_label(text):
    lbl = QLabel(text)
    lbl.setObjectName("fieldLabel")
    return lbl

def make_input(placeholder=""):
    w = QLineEdit()
    if placeholder:
        w.setPlaceholderText(placeholder)
    return w

def make_btn(text, style="primary"):
    b = QPushButton(text)
    b.setObjectName(style)
    b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
    return b

# ─── Accounts Dialog ──────────────────────────────────────────────────────────

class AccountsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr('window_accounts'))
        self.resize(640, 520)
        self.setStyleSheet(STYLESHEET)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(0)

        hdr = QHBoxLayout()
        title = QLabel(tr('saved_accounts_title'))
        title.setStyleSheet(f"color: {ACCENT}; font-size: 14pt; font-weight: bold;")
        hdr.addWidget(title)
        hdr.addStretch()
        refresh = make_btn(tr('btn_refresh'), "secondary")
        refresh.clicked.connect(self._load)
        hdr.addWidget(refresh)
        layout.addLayout(hdr)
        layout.addSpacing(10)
        layout.addWidget(make_separator())
        layout.addSpacing(10)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._container = QWidget()
        self._vbox = QVBoxLayout(self._container)
        self._vbox.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._scroll.setWidget(self._container)
        layout.addWidget(self._scroll, 1)

        self._count_label = QLabel("")
        self._count_label.setObjectName("subtitle")
        self._count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._count_label)

        self._load()

    def _load(self):
        while self._vbox.count():
            item = self._vbox.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        accounts = []
        acc_file = os.path.join(get_base(), "accounts.txt")
        if os.path.exists(acc_file):
            with open(acc_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    parts = [p.strip() for p in line.split("|")]
                    email    = parts[0] if len(parts) > 0 else ""
                    password = parts[1] if len(parts) > 1 else ""
                    created  = parts[2] if len(parts) > 2 else "—"
                    if email:
                        accounts.append({"email": email, "password": password, "created_at": created})

        self._count_label.setText(tr("accounts_saved_count").format(count=len(accounts)))

        if not accounts:
            lbl = QLabel(tr('no_accounts_saved'))
            lbl.setObjectName("subtitle")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._vbox.addWidget(lbl)
            return

        for i, acc in enumerate(accounts):
            card = QFrame()
            card.setObjectName("card")
            cl = QVBoxLayout(card)
            cl.setContentsMargins(14, 10, 14, 10)
            cl.setSpacing(2)

            num = QLabel(f"#{i+1}")
            num.setStyleSheet(f"color: {TEXT_DIM}; font-size: 9pt; font-weight: bold;")

            email_lbl = QLabel(f"📧  {acc['email']}")
            pass_lbl  = QLabel(f"🔑  {acc['password']}")
            pass_lbl.setStyleSheet(f"color: {TEXT_DIM};")
            time_lbl  = QLabel(f"🕐  {acc['created_at']}")
            time_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 9pt;")

            cl.addWidget(num)
            cl.addWidget(email_lbl)
            cl.addWidget(pass_lbl)
            cl.addWidget(time_lbl)

            btn_row = QHBoxLayout()
            btn_row.setSpacing(6)
            for label, val, style in [
                (tr('btn_copy_all'),      f"{acc['email']} | {acc['password']}", "primary"),
                (tr('btn_copy_email'),    acc['email'],                           "secondary"),
                (tr('btn_copy_password'), acc['password'],                        "secondary"),
            ]:
                b = make_btn(label, style)
                b.clicked.connect(lambda _, v=val: QApplication.clipboard().setText(v))
                btn_row.addWidget(b)
            btn_row.addStretch()
            cl.addLayout(btn_row)

            self._vbox.addWidget(card)
            self._vbox.addSpacing(6)

# ─── Update Dialog ────────────────────────────────────────────────────────────

class UpdateDialog(QDialog):
    status_signal = pyqtSignal(str, str)
    exit_signal   = pyqtSignal(str)  # payload: 'exe' | 'py' | 'py:<path>'

    def __init__(self, local, remote, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr('window_update'))
        self.setFixedSize(420, 280)
        self.setStyleSheet(STYLESHEET)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 20)
        layout.setSpacing(8)

        title = QLabel(tr("update_available_title"))
        title.setStyleSheet(f"color: {WARNING}; font-size: 16pt; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        layout.addWidget(QLabel(tr('update_arrow').format(local=local, remote=remote)))

        note = QLabel(tr('update_auto_dl'))
        note.setObjectName("subtitle")
        note.setWordWrap(True)
        layout.addWidget(note)

        self._prog = QProgressBar()
        self._prog.setRange(0, 0)
        self._prog.setFixedHeight(6)
        self._prog.setStyleSheet(f"""
            QProgressBar {{ background: {BG3}; border-radius: 3px; border: none; }}
            QProgressBar::chunk {{ background: {ACCENT2}; border-radius: 3px; }}
        """)
        self._prog.setVisible(False)
        layout.addWidget(self._prog)

        self._status = QLabel("")
        self._status.setObjectName("stepLabel")
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._status)

        btn = make_btn(tr('btn_update_now'), "warning")
        btn.clicked.connect(lambda: self._do_update(local, remote))
        layout.addWidget(btn)

        self.status_signal.connect(self._on_status)
        self.exit_signal.connect(self._on_exit)

    def _on_exit(self, mode):
        QApplication.instance().closeAllWindows()
        if mode == 'exe':
            pass  # bat already launched, just quit
        elif mode.startswith('py:'):
            subprocess.Popen([sys.executable, mode[3:]])
        QApplication.instance().quit()

    def _on_status(self, text, color):
        self._status.setText(text)
        self._status.setStyleSheet(f"color: {color};")

    def _do_update(self, local, remote):
        self._prog.setVisible(True)
        def run():
            base = get_base()
            success = True
            steps = []
            if getattr(sys, 'frozen', False):
                new_exe_path = os.path.join(base, "mainrev_new.exe")
                steps.append((tr('downloading_exe'),
                    "https://github.com/TDoomX/exitlag-auto-signup-revamp/releases/latest/download/mainrev.exe",
                    new_exe_path))
            steps.append((tr('downloading_main'), f"{GITHUB_RAW}/main.py", os.path.join(base, "main.py")))
            os.makedirs(os.path.join(base, "translations"), exist_ok=True)
            for lang in TRANSLATIONS_LANGS:
                steps.append((tr('downloading_translation').format(lang=lang),
                    f"{GITHUB_RAW}/translations/{lang}.json",
                    os.path.join(base, "translations", f"{lang}.json")))
            steps.append(("version.txt", f"{GITHUB_RAW}/version.txt", os.path.join(base, "version.txt")))
            steps.append(("lib/lib.py", f"{GITHUB_RAW}/lib/lib.py", os.path.join(base, "lib", "lib.py")))
            steps.append(("requirements.txt", f"{GITHUB_RAW}/requirements.txt", os.path.join(base, "requirements.txt")))

            for label, url, dest in steps:
                self.status_signal.emit(label, ACCENT)
                if not download_file(url, dest):
                    success = False

            if not success:
                self.status_signal.emit(tr('update_some_failed'), ERROR)
                if getattr(sys, 'frozen', False) and os.path.exists(new_exe_path):
                    os.remove(new_exe_path)
                QTimer.singleShot(2000, self.close)
                return

            self.status_signal.emit(tr('update_complete'), SUCCESS)
            if getattr(sys, 'frozen', False):
                exe_path = os.path.join(base, "mainrev.exe")
                new_exe  = os.path.join(base, "mainrev_new.exe")
                bat_path = os.path.join(base, "update.bat")
                bat_content = (
                    "@echo off\r\n"
                    "timeout /t 2 /nobreak > nul\r\n"
                    f"move /y \"{new_exe}\" \"{exe_path}\"\r\n"
                    f"explorer.exe \"{exe_path}\"\r\n"
                    "del \"%~f0\"\r\n"
                )
                with open(bat_path, "w", encoding="utf-8") as f:
                    f.write(bat_content)
                time.sleep(0.5)
                subprocess.Popen(bat_path, shell=True)
                self.exit_signal.emit('exe')
            else:
                req_path = os.path.join(base, "requirements.txt")
                if os.path.exists(req_path):
                    self.status_signal.emit(tr("installing_dependencies"), ACCENT)
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", "-r", req_path],
                        capture_output=True
                    )
                self.exit_signal.emit(f'py:{os.path.join(base, "main.py")}')

        threading.Thread(target=run, daemon=True).start()

# ─── Main Window ──────────────────────────────────────────────────────────────

class App(QMainWindow):
    _update_signal = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle(tr('app_title'))
        self.setFixedSize(600, 700)
        self.setStyleSheet(STYLESHEET)
        self.lib = Main()
        self._silent_mode = False
        self._bar_widget = None
        self._log_queue = queue.Queue()
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._poll_log)
        self._cancel_event = None
        self._completed = 0
        self._total = 0
        self._current_screen = (None, None)
        # Detect initial language from system locale
        try:
            import locale as _lc
            _lc.setlocale(_lc.LC_ALL, '')
            _lt = _lc.getlocale()
            _raw = _lt[0].split('_')[0].lower() if _lt and _lt[0] else 'en'
            _LMAP = {'pt':'pt','en':'en','es':'es','fr':'fr','de':'de',
                     'it':'it','ru':'ru','ja':'ja','zh':'zh',
                     'portuguese':'pt','english':'en','spanish':'es',
                     'french':'fr','german':'de','italian':'it',
                     'russian':'ru','japanese':'ja','chinese':'zh'}
            self._current_lang = _LMAP.get(_raw, 'en')
        except Exception:
            self._current_lang = "en"
        self._center()
        self._update_signal.connect(self._show_update)
        self._check_updates_bg()
        self._download_missing_langs()
        self._check_missing_deps()
        self._show_config()

    def _center(self):
        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width() - 600) // 2, (screen.height() - 700) // 2)

    # ── Header ────────────────────────────────────────────────────────────────

    def _build_header(self, central, subtitle=""):
        # Menu bar
        menu_bar = QWidget()
        menu_bar.setObjectName("menuBar")
        menu_bar.setFixedHeight(32)
        mb_layout = QHBoxLayout(menu_bar)
        mb_layout.setContentsMargins(4, 0, 4, 0)
        mb_layout.setSpacing(0)

        def menu_btn(text, slot, obj="menuBtn"):
            b = QPushButton(text)
            b.setObjectName(obj)
            b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            if slot is not None:
                b.clicked.connect(slot)
            return b

        mb_layout.addWidget(menu_btn(tr('menu_accounts'), self._show_accounts))

        last = load_config()
        if last:
            mb_layout.addWidget(menu_btn(tr('menu_last_config'),
                                         lambda: self._show_last_config(last)))

        mb_layout.addStretch()

        # Silent toggle
        self._silent_btn = menu_btn("", self._toggle_silent)
        self._update_silent_btn()
        mb_layout.addWidget(self._silent_btn)

        # Language menu
        LANG_FLAGS = {
            "pt": "🇧🇷", "en": "🇺🇸", "es": "🇪🇸", "fr": "🇫🇷",
            "de": "🇩🇪", "it": "🇮🇹", "ru": "🇷🇺", "ja": "🇯🇵", "zh": "🇨🇳",
            "vi": "🇻🇳", "ar": "🇸🇦",
        }
        flag = LANG_FLAGS.get(self._current_lang, "🌐")
        lang_btn = menu_btn(f"{flag}  {tr('menu_language')}", None)
        lang_btn.setFont(QFont("Segoe UI Emoji", 10))
        lang_btn.clicked.connect(lambda: self._show_lang_menu(lang_btn))
        mb_layout.addWidget(lang_btn)

        central.addWidget(menu_bar)

        # Title area — hacker banner
        banner = HackerBannerWidget(subtitle)
        central.addWidget(banner)
        central.addWidget(make_separator())
        central.addSpacing(10)

    def _toggle_silent(self):
        self._silent_mode = not self._silent_mode
        self._update_silent_btn()

    def _update_silent_btn(self):
        if self._silent_mode:
            self._silent_btn.setText(f"🔇 {tr('menu_silent_on')}")
            self._silent_btn.setStyleSheet(f"color: {ACCENT}; background: transparent; border: none; padding: 4px 12px; font-size: 9pt;")
        else:
            self._silent_btn.setText(f"🔊 {tr('menu_silent_off')}")
            self._silent_btn.setStyleSheet("")

    def _show_lang_menu(self, btn):
        LANG_OPTIONS = [
            ("🇧🇷  Português", "pt"), ("🇺🇸  English",  "en"),
            ("🇪🇸  Español",   "es"), ("🇫🇷  Français", "fr"),
            ("🇩🇪  Deutsch",   "de"), ("🇮🇹  Italiano", "it"),
            ("🇷🇺  Русский",   "ru"), ("🇯🇵  日本語",   "ja"),
            ("🇨🇳  中文",      "zh"),
            ("🇻🇳  Tiếng Việt", "vi"),
            ("🇸🇦  العربية",   "ar"),
        ]
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1e2130;
                border: 1px solid #2e3250;
                padding: 4px 0;
                font-family: 'Segoe UI Emoji', 'Segoe UI', sans-serif;
                font-size: 10pt;
            }
            QMenu::item {
                padding: 7px 20px 7px 12px;
                color: #e0e0e0;
                background: transparent;
            }
            QMenu::item:selected {
                background-color: #2e3250;
                color: #ffffff;
                border-radius: 3px;
            }
            QMenu::item:checked {
                color: #00e5ff;
                font-weight: bold;
            }
        """)

        for lbl, code in LANG_OPTIONS:
            active = (code == self._current_lang)
            text = ("✓  " if active else "     ") + lbl
            action = menu.addAction(text)
            action.setCheckable(True)
            action.setChecked(active)
            action.triggered.connect(lambda checked, c=code: self._set_lang(c))

        pos = btn.mapToGlobal(QPoint(0, btn.height()))
        menu.exec(pos)

    def _set_lang(self, code):
        global _translation_cache
        self._current_lang = code
        base = get_base()
        path = os.path.join(base, "translations", f"{code}.json")
        if not os.path.exists(path):
            url = f"{GITHUB_RAW}/translations/{code}.json"
            download_file(url, path)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                _translation_cache = json.load(f)
        screen = self._current_screen
        if screen[0] == "last_config":
            self._show_last_config(screen[1])
        elif screen[0] == "log":
            self._show_log(*screen[1])
        else:
            self._show_config()

    # ── Clear central widget ──────────────────────────────────────────────────

    def _clear(self):
        if self._bar_widget:
            self._bar_widget.stop()
            self._bar_widget = None
        self._poll_timer.stop()
        cw = QWidget()
        cw.setObjectName("root")
        self.setCentralWidget(cw)

    def _make_scroll_content(self):
        """Returns (central_vbox, scroll_vbox, central_widget)"""
        central = QWidget()
        central.setObjectName("root")
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        return main_layout

    # ── Config Screen ─────────────────────────────────────────────────────────

    def _show_config(self):
        self._current_screen = ("config", None)
        main = self._make_scroll_content()
        self._build_header(main, tr('new_config_title'))

        body = QWidget()
        bl = QVBoxLayout(body)
        bl.setContentsMargins(30, 0, 30, 30)
        bl.setSpacing(6)

        # Browser path
        bl.addWidget(make_field_label(tr("browser_executable_path")))
        browser_row = QHBoxLayout()
        browser_entry = make_input(tr("browser_path_prompt"))
        browser_row.addWidget(browser_entry)
        browse_btn = make_btn(tr('btn_browse'), "secondary")
        browse_btn.setFixedWidth(100)
        def browse():
            path, _ = QFileDialog.getOpenFileName(self, tr("browse_dialog_title"), "", "Executable (*.exe)")
            if path:
                browser_entry.setText(path)
        browse_btn.clicked.connect(browse)
        browser_row.addWidget(browse_btn)
        bl.addLayout(browser_row)
        bl.addSpacing(4)

        # Password
        bl.addWidget(make_field_label(tr("password_label")))
        pass_row = QHBoxLayout()
        pass_entry = make_input()
        pass_row.addWidget(pass_entry)
        gen_btn = make_btn(tr('btn_generate'), "secondary")
        gen_btn.setFixedWidth(100)
        gen_btn.clicked.connect(lambda: pass_entry.setText(generate_random_password()))
        pass_row.addWidget(gen_btn)
        bl.addLayout(pass_row)
        bl.addSpacing(4)

        # Proxy
        bl.addWidget(make_field_label(tr("proxy_label") + " (optional)"))
        proxy_entry = make_input("http://host:port")
        bl.addWidget(proxy_entry)
        bl.addSpacing(4)

        # Account count + Loader side by side
        bl.addWidget(make_field_label(tr("number_of_accounts_prompt")))
        spin_loader_row = QHBoxLayout()
        spin_loader_row.setSpacing(10)
        count_spin = NumberSpinBox(1, 100, 1)
        count_spin.setFixedHeight(38)
        spin_loader_row.addWidget(count_spin)
        spin_loader_row.addStretch()
        loader_btn = QPushButton("⚡ Loader")
        loader_btn.setObjectName("loaderBtn")
        loader_btn.setFixedHeight(38)
        loader_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        loader_btn.clicked.connect(open_loader)
        spin_loader_row.addWidget(loader_btn)
        bl.addLayout(spin_loader_row)
        bl.addSpacing(4)

        # Plan
        bl.addWidget(make_field_label(tr("plan_selection_title")))
        plan_row = QHBoxLayout()
        plan_group = QButtonGroup(self)
        rb1 = QRadioButton(tr('plan_option_3days'))
        rb2 = QRadioButton(tr('plan_option_7days'))
        rb1.setChecked(True)
        plan_group.addButton(rb1, 1)
        plan_group.addButton(rb2, 2)
        plan_row.addWidget(rb1)
        plan_row.addWidget(rb2)
        plan_row.addStretch()
        bl.addLayout(plan_row)
        bl.addSpacing(4)

        # Error label
        err_label = QLabel("")
        err_label.setObjectName("errorLabel")
        bl.addWidget(err_label)

        bl.addStretch()

        # Start button
        start_btn = make_btn(tr('btn_start'), "primary")
        def start():
            browser = browser_entry.text().strip()
            if browser == tr("browser_path_prompt"):
                browser = ""
            browser = browser.replace('"', '').replace("'", '')
            if browser and not os.path.exists(browser):
                err_label.setText(tr("invalid_path"))
                return
            passw = pass_entry.text().strip()
            if not passw:
                passw = generate_random_password()
            elif not is_valid_password(passw):
                err_label.setText(tr("password_not_meeting_requirements"))
                return
            proxy = proxy_entry.text().strip()
            if proxy == "http://host:port":
                proxy = ""
            if proxy:
                ok, msg = self.lib.testProxy(proxy)
                if not ok:
                    err_label.setText(str(msg))
                    return
            count = count_spin.value()
            plan = "2" if plan_group.checkedId() == 2 else "1"
            save_config(browser, passw, proxy, count, plan)
            self._show_log(browser, passw, proxy, count, plan)
        start_btn.clicked.connect(start)
        bl.addWidget(start_btn)

        main.addWidget(body, 1)

    # ── Last Config Screen ────────────────────────────────────────────────────

    def _show_last_config(self, cfg):
        self._current_screen = ("last_config", cfg)
        main = self._make_scroll_content()
        self._build_header(main, tr('last_config_title'))

        body = QWidget()
        bl = QVBoxLayout(body)
        bl.setContentsMargins(30, 0, 30, 30)
        bl.setSpacing(0)

        card = QFrame()
        card.setObjectName("card")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(20, 10, 20, 10)

        rows = [
            (tr("browser_label"),          cfg.get("browser_path") or tr("default_browser")),
            (tr("password_label_display"), cfg.get("password", "")),
            (tr("proxy_label_display"),    cfg.get("proxy") or tr("no_proxy")),
            (tr("accounts_label"),         str(cfg.get("execution_count", 1))),
            (tr("plan_label"),             tr("seven_days") if cfg.get("plan") == "2" else tr("three_days")),
        ]
        for label, val in rows:
            row = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setFixedWidth(160)
            lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 9pt;")
            val_lbl = QLabel(val)
            row.addWidget(lbl)
            row.addWidget(val_lbl)
            row.addStretch()
            cl.addLayout(row)

        bl.addWidget(card)
        bl.addSpacing(16)

        use_btn = make_btn(tr('btn_use_last_config'), "success")
        use_btn.clicked.connect(lambda: self._start_with_config(cfg))
        bl.addWidget(use_btn)
        bl.addSpacing(8)

        new_btn = make_btn(tr('btn_new_configuration'), "secondary")
        new_btn.clicked.connect(self._show_config)
        bl.addWidget(new_btn)
        bl.addStretch()

        main.addWidget(body, 1)

    def _start_with_config(self, cfg):
        self._show_log(
            cfg.get("browser_path", ""), cfg.get("password", ""),
            cfg.get("proxy", ""), cfg.get("execution_count", 1), cfg.get("plan", "1")
        )

    # ── Log Screen ────────────────────────────────────────────────────────────

    def _cleanup_thread(self):
        """Encerra o thread anterior com segurança, tolerando objeto C++ já deletado."""
        thread = getattr(self, '_thread', None)
        if thread is not None:
            try:
                if thread.isRunning():
                    cancel = getattr(self, '_cancel_event', None)
                    if cancel:
                        cancel.set()
                    thread.quit()
                    thread.wait(5000)
            except RuntimeError:
                pass  # C++ object already deleted by deleteLater — expected
        self._thread = None
        self._worker = None

    def _show_log(self, browser_path, passw, proxy, count, plan):
        self._current_screen = ("log", (browser_path, passw, proxy, count, plan))
        plan_name = tr("plan_option_7days") if plan == "2" else tr("plan_option_3days")
        main = self._make_scroll_content()
        self._build_header(main, tr('running_header').format(plan_name=plan_name, count=count))

        body = QWidget()
        bl = QVBoxLayout(body)
        bl.setContentsMargins(30, 0, 30, 20)
        bl.setSpacing(6)

        # Segmented progress bar
        self._bar_widget = SegmentedBarWidget()
        bl.addWidget(self._bar_widget)

        # Step / progress row
        step_row = QHBoxLayout()
        self._step_label = QLabel(tr('step_starting'))
        self._step_label.setObjectName("stepLabel")
        step_row.addWidget(self._step_label)
        step_row.addStretch()
        self._progress_label = QLabel(f"0 / {count}")
        self._progress_label.setObjectName("progressLabel")
        step_row.addWidget(self._progress_label)
        bl.addLayout(step_row)

        # Log text
        self._log_text = QTextEdit()
        self._log_text.setObjectName("logText")
        self._log_text.setReadOnly(True)
        bl.addWidget(self._log_text, 1)

        # Button row
        btn_row = QHBoxLayout()
        self._btn_cancel = make_btn(tr('btn_cancel'), "danger")
        self._cancel_event = threading.Event()
        def _cancel():
            self._cancel_event.set()
            self._btn_cancel.setText(tr('btn_cancelling'))
            self._btn_cancel.setEnabled(False)
        self._btn_cancel.clicked.connect(_cancel)
        btn_row.addWidget(self._btn_cancel)
        btn_row.addStretch()

        self._btn_save = make_btn(tr('btn_save_config'), "secondary")
        self._btn_save.setEnabled(False)
        self._btn_save.clicked.connect(lambda: save_config(browser_path, passw, proxy, count, plan))
        btn_row.addWidget(self._btn_save)

        self._btn_new = make_btn(tr('btn_new_config'), "secondary")
        self._btn_new.setEnabled(False)
        self._btn_new.clicked.connect(self._show_config)
        btn_row.addWidget(self._btn_new)

        bl.addLayout(btn_row)
        main.addWidget(body, 1)

        # Color map for log levels
        self._log_colors = {
            "info":    TEXT,
            "success": SUCCESS,
            "warning": WARNING,
            "error":   ERROR,
            "accent":  ACCENT,
            "dim":     TEXT_DIM,
        }

        self._completed = 0
        self._total = count
        self._log_queue = queue.Queue()
        self._poll_timer.start(100)

        STEPS_PER_ACCOUNT = 5
        total_steps = count * STEPS_PER_ACCOUNT
        self._step_counter = 0
        self._prog_maximum = total_steps

        STEP_MAP = {
            tr('opening_browser'): 1,
            tr('filling_form'):    1,
            tr('waiting_captcha'): 1,
            tr('submitting_form'): 1,
        }
        self._step_map = STEP_MAP

        # Stop previous thread if still running
        self._cleanup_thread()

        # Launch worker thread
        self._worker = AutomationWorker(plan, passw, count, browser_path,
                                        self._cancel_event, self._silent_mode)
        self._thread = QThread()
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.log_signal.connect(lambda m, l: self._log_queue.put(("log", m, l)))
        self._worker.step_signal.connect(lambda m: self._log_queue.put(("step", m, None)))
        self._worker.done_signal.connect(lambda a: self._log_queue.put(("done", a, None)))
        # Clean thread shutdown when worker finishes
        self._worker.done_signal.connect(self._thread.quit)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    def _poll_log(self):
        try:
            while True:
                item = self._log_queue.get_nowait()
                kind = item[0]
                if kind == "log":
                    _, msg, level = item
                    self._append_log(msg, level)
                    if level == "success" and "✓" in msg and tr('registration_success') in msg:
                        self._completed += 1
                        self._progress_label.setText(f"{self._completed} / {self._total}")
                        if self._bar_widget:
                            self._bar_widget.set_pct(self._completed * 5 / max(self._prog_maximum, 1))
                elif kind == "step":
                    _, msg, _ = item
                    self._step_label.setText(msg)
                    step_map = getattr(self, '_step_map', {})
                    if msg in step_map:
                        self._step_counter += step_map[msg]
                        if self._bar_widget:
                            self._bar_widget.set_pct(self._step_counter / max(self._prog_maximum, 1))
                elif kind == "done":
                    _, successful_accounts, _ = item
                    self._poll_timer.stop()
                    if self._bar_widget:
                        self._bar_widget.set_pct(1.0)
                    self._step_label.setText(tr('step_all_done'))
                    self._step_label.setStyleSheet(f"color: {SUCCESS};")
                    self._btn_cancel.setEnabled(False)
                    self._btn_new.setEnabled(True)
                    self._btn_save.setEnabled(True)
                    self._show_results(successful_accounts)
                    return
        except queue.Empty:
            pass

    def _append_log(self, msg, level="info"):
        color = self._log_colors.get(level, TEXT)
        self._log_text.setTextColor(QColor(color))
        self._log_text.append(msg)
        self._log_text.verticalScrollBar().setValue(
            self._log_text.verticalScrollBar().maximum()
        )

    def _show_results(self, successful_accounts):
        if not successful_accounts:
            return
        self._append_log(f"\n{'═'*40}", "dim")
        self._append_log(f"  {tr('accounts_created')} {len(successful_accounts)}", "accent")
        self._append_log(f"{'═'*40}", "dim")
        for acc in successful_accounts:
            self._append_log(f"  📧 {tr('email_label')} {acc['email']}", "success")
            self._append_log(f"  🔑 {tr('password_display_label')} {acc['password']}", "success")
            self._append_log("", "info")

    # ── Accounts / Update ─────────────────────────────────────────────────────

    def _show_accounts(self):
        dlg = AccountsDialog(self)
        dlg.exec()

    def _check_updates_bg(self):
        def run():
            old_exe = os.path.join(get_base(), "mainrev_old.exe")
            if os.path.exists(old_exe):
                try: os.remove(old_exe)
                except: pass
            remote = get_remote_version()
            if remote is None:
                return
            local = get_local_version()
            if remote != local:
                self._update_signal.emit(local, remote)
        threading.Thread(target=run, daemon=True).start()

    def _check_missing_deps(self):
        def run():
            base = get_base()
            req_path = os.path.join(base, "requirements.txt")
            if not os.path.exists(req_path):
                return
            try:
                import importlib.metadata as meta
            except ImportError:
                import importlib_metadata as meta

            with open(req_path, "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f if l.strip() and not l.startswith("#")]

            missing = []
            for line in lines:
                pkg = line.split("==")[0].split(">=")[0].split("<=")[0].split("!=")[0].split("~=")[0].strip()
                try:
                    meta.version(pkg)
                except Exception:
                    try:
                        meta.version(pkg.replace("-", "_"))
                    except Exception:
                        missing.append(line)

            if missing:
                # Use the real Python interpreter, not the frozen exe
                if getattr(sys, "frozen", False):
                    python = os.path.join(os.path.dirname(sys.executable), "python.exe")
                    if not os.path.exists(python):
                        return  # can't pip install in frozen env without Python
                else:
                    python = sys.executable
                subprocess.run(
                    [python, "-m", "pip", "install"] + missing,
                    capture_output=True
                )
        threading.Thread(target=run, daemon=True).start()

    def _download_missing_langs(self):
        def run():
            base = get_base()
            for lang in TRANSLATIONS_LANGS:
                path = os.path.join(base, "translations", f"{lang}.json")
                if not os.path.exists(path):
                    url = f"{GITHUB_RAW}/translations/{lang}.json"
                    download_file(url, path)
        threading.Thread(target=run, daemon=True).start()

    def _show_update(self, local, remote):
        dlg = UpdateDialog(local, remote, self)
        dlg.exec()


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = App()
    window.show()
    sys.exit(app.exec())