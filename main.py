import asyncio
import re
import warnings
import time
import os
import sys
import json
import subprocess
import threading
import ctypes
import math
import queue
from datetime import datetime
import atexit
import random
import urllib.request
import string
import locale
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QTextEdit, QRadioButton, QButtonGroup, QFrame, QFileDialog, QScrollArea, QMenu, QDialog, QProgressBar, QSizePolicy, QMessageBox
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QObject, QSize, QPoint
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QBrush, QLinearGradient, QPainterPath, QAction, QCursor
from tqdm import TqdmExperimentalWarning
from pydoll.browser import Chrome
from pydoll.browser.options import ChromiumOptions
from pydoll.constants import Key
from lib.lib import Main
from faker import Faker
warnings.filterwarnings('ignore', category=TqdmExperimentalWarning)
try:
    import psutil
    _PSUTIL_OK = True
except ImportError:
    _PSUTIL_OK = False

class GhostModeAPI:
    SW_HIDE = 0

    def __init__(self):
        self.user32 = ctypes.windll.user32
        self._EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

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

    def _watch_and_hide(self, title_substrings, timeout=8.0, interval=0.03, stop_event=None):
        import time
        elapsed = 0.0
        if isinstance(title_substrings, str):
            title_substrings = [title_substrings]
        while elapsed < timeout:
            if stop_event and stop_event.is_set():
                break
            for ts in title_substrings:
                self._hide_by_title(ts)
            time.sleep(interval)
            elapsed += interval

    def _watch_and_hide_by_pid(self, pid, timeout=60.0, interval=0.03, stop_event=None):
        import time, ctypes as _ct
        if not _PSUTIL_OK:
            return
        elapsed = 0.0
        _EnumProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        while elapsed < timeout:
            if stop_event and stop_event.is_set():
                break
            try:

                def foreach_window(hwnd, _):
                    try:
                        pid_out = _ct.c_ulong(0)
                        _ct.windll.user32.GetWindowThreadProcessId(hwnd, _ct.byref(pid_out))
                        if pid_out.value == pid and self.user32.IsWindowVisible(hwnd):
                            self.user32.ShowWindow(hwnd, self.SW_HIDE)
                    except Exception:
                        pass
                    return True
                self.user32.EnumWindows(_EnumProc(foreach_window), 0)
            except Exception:
                pass
            time.sleep(interval)
            elapsed += interval

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
            self._force_close_by_title('DOOM_GHOSTAPI')
        except Exception:
            pass

def cleanup_orphaned_browsers():
    try:
        GhostModeAPI()._force_close_by_title('DOOM_GHOSTAPI')
    except Exception:
        pass
atexit.register(cleanup_orphaned_browsers)
CONFIG_FILE = 'last_config.json'
BROWSERS_FILE = 'saved_browsers.json'
GITHUB_RAW = 'https://raw.githubusercontent.com/TDoomX/exitlag-auto-signup-revamp/master'
LOCAL_VERSION_FILE = 'version.txt'
TRANSLATIONS_LANGS = ['de', 'en', 'es', 'fr', 'it', 'ja', 'pt', 'ru', 'zh', 'vi', 'ar']
BG = '#0d0f14'
BG2 = '#13161e'
BG3 = '#1a1e2a'
ACCENT = '#00c8ff'
ACCENT2 = '#0066ff'
SUCCESS = '#00e676'
WARNING = '#ffab00'
ERROR = '#ff3d71'
TEXT = '#e8eaf0'
TEXT_DIM = '#6b7280'
BORDER = '#252a38'
STYLESHEET = f"\nQMainWindow, QDialog, QWidget#root {{\n    background-color: {BG};\n}}\nQWidget {{\n    background-color: {BG};\n    color: {TEXT};\n    font-family: 'Segoe UI';\n    font-size: 10pt;\n}}\n\nQWidget#menuBar {{\n    background-color: {BG2};\n    border-bottom: 1px solid {BORDER};\n}}\nQPushButton#menuBtn {{\n    background: transparent;\n    color: {TEXT_DIM};\n    border: none;\n    padding: 4px 12px;\n    font-size: 9pt;\n}}\nQPushButton#menuBtn:hover {{\n    color: {ACCENT};\n    background-color: {BG3};\n}}\nQPushButton#loaderBtn {{\n    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,\n        stop:0 {ACCENT2}, stop:1 {ACCENT});\n    color: white;\n    border: none;\n    border-radius: 5px;\n    padding: 4px 14px;\n    font-size: 9pt;\n    font-weight: bold;\n}}\nQPushButton#loaderBtn:hover {{\n    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,\n        stop:0 {ACCENT}, stop:1 {ACCENT2});\n}}\n\nQLineEdit, QSpinBox {{\n    background-color: {BG3};\n    color: {TEXT};\n    border: 1px solid {BORDER};\n    border-radius: 4px;\n    padding: 8px 10px;\n    font-size: 10pt;\n    selection-background-color: {ACCENT2};\n}}\nQLineEdit:focus, QSpinBox:focus {{\n    border: 1px solid {ACCENT};\n}}\nQSpinBox::up-button, QSpinBox::down-button {{\n    background-color: {BG2};\n    border: none;\n    width: 22px;\n    subcontrol-origin: border;\n}}\nQSpinBox::up-button {{\n    subcontrol-position: top right;\n    border-left: 1px solid {BORDER};\n    border-bottom: 1px solid {BORDER};\n    border-top-right-radius: 4px;\n}}\nQSpinBox::down-button {{\n    subcontrol-position: bottom right;\n    border-left: 1px solid {BORDER};\n    border-top: 1px solid {BORDER};\n    border-bottom-right-radius: 4px;\n}}\nQSpinBox::up-button:hover, QSpinBox::down-button:hover {{\n    background-color: {ACCENT2};\n}}\nQSpinBox::up-arrow {{\n    width: 10px;\n    height: 10px;\n}}\nQSpinBox::down-arrow {{\n    width: 10px;\n    height: 10px;\n}}\n\nQPushButton#primary {{\n    background-color: {ACCENT2};\n    color: {TEXT};\n    border: none;\n    border-radius: 4px;\n    padding: 10px 16px;\n    font-size: 10pt;\n    font-weight: bold;\n}}\nQPushButton#primary:hover {{\n    background-color: {ACCENT};\n}}\nQPushButton#primary:disabled {{\n    background-color: {BG3};\n    color: {TEXT_DIM};\n}}\nQPushButton#secondary {{\n    background-color: {BG3};\n    color: {TEXT};\n    border: 1px solid {BORDER};\n    border-radius: 4px;\n    padding: 10px 16px;\n    font-size: 10pt;\n}}\nQPushButton#secondary:hover {{\n    background-color: {BG2};\n    border-color: {ACCENT};\n    color: {ACCENT};\n}}\nQPushButton#secondary:disabled {{\n    color: {TEXT_DIM};\n    border-color: {BORDER};\n}}\nQPushButton#danger {{\n    background-color: {ERROR};\n    color: {BG};\n    border: none;\n    border-radius: 4px;\n    padding: 10px 16px;\n    font-size: 10pt;\n    font-weight: bold;\n}}\nQPushButton#danger:hover {{\n    background-color: #ff6b93;\n}}\nQPushButton#danger:disabled {{\n    background-color: {BG3};\n    color: {TEXT_DIM};\n}}\nQPushButton#success {{\n    background-color: {SUCCESS};\n    color: {BG};\n    border: none;\n    border-radius: 4px;\n    padding: 10px 16px;\n    font-size: 10pt;\n    font-weight: bold;\n}}\nQPushButton#success:hover {{\n    background-color: #33eb91;\n}}\nQPushButton#warning {{\n    background-color: {WARNING};\n    color: {BG};\n    border: none;\n    border-radius: 4px;\n    padding: 10px 16px;\n    font-size: 10pt;\n    font-weight: bold;\n}}\nQPushButton#warning:hover {{\n    background-color: #ffc140;\n}}\n\nQRadioButton {{\n    color: {TEXT};\n    font-size: 10pt;\n    spacing: 6px;\n}}\nQRadioButton::indicator {{\n    width: 14px;\n    height: 14px;\n    border-radius: 7px;\n    border: 2px solid {BORDER};\n    background-color: {BG3};\n}}\nQRadioButton::indicator:checked {{\n    background-color: {ACCENT2};\n    border-color: {ACCENT2};\n}}\n\nQTextEdit#logText {{\n    background-color: {BG3};\n    color: {TEXT};\n    border: 1px solid {BORDER};\n    border-radius: 4px;\n    font-family: 'Consolas';\n    font-size: 9pt;\n    padding: 6px;\n    selection-background-color: {BG2};\n}}\n\nQLabel#title {{\n    color: {ACCENT};\n    font-size: 20pt;\n    font-weight: bold;\n}}\nQLabel#subtitle {{\n    color: {TEXT_DIM};\n    font-size: 9pt;\n}}\nQLabel#fieldLabel {{\n    color: {TEXT_DIM};\n    font-size: 9pt;\n}}\nQLabel#stepLabel {{\n    color: {ACCENT};\n    font-size: 9pt;\n}}\nQLabel#progressLabel {{\n    color: {TEXT_DIM};\n    font-size: 9pt;\n}}\nQLabel#errorLabel {{\n    color: {ERROR};\n    font-size: 9pt;\n}}\n\nQFrame#separator {{\n    background-color: {BORDER};\n    max-height: 1px;\n}}\n\nQPushButton#spinBtn {{\n    background-color: {BG3};\n    color: {TEXT};\n    border: 1px solid {BORDER};\n    font-size: 9pt;\n    font-weight: bold;\n    padding: 0;\n    border-radius: 3px;\n}}\nQPushButton#spinBtn:hover {{\n    background-color: {ACCENT2};\n    color: white;\n    border-color: {ACCENT2};\n}}\n\nQScrollBar:vertical {{\n    background: {BG2};\n    width: 8px;\n    border-radius: 4px;\n}}\nQScrollBar::handle:vertical {{\n    background: {BORDER};\n    border-radius: 4px;\n    min-height: 20px;\n}}\nQScrollBar::handle:vertical:hover {{\n    background: {TEXT_DIM};\n}}\nQScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{\n    height: 0px;\n}}\n\nQFrame#card {{\n    background-color: {BG2};\n    border: 1px solid {BORDER};\n    border-radius: 6px;\n}}\n\nQMenu {{\n    background-color: {BG2};\n    color: {TEXT};\n    border: 1px solid {BORDER};\n    border-radius: 4px;\n    padding: 4px;\n}}\nQMenu::item {{\n    padding: 6px 20px;\n    border-radius: 3px;\n}}\nQMenu::item:selected {{\n    background-color: {BG3};\n    color: {ACCENT};\n}}\n"
_translation_cache = None
_silent_mode = False
_TR_FALLBACKS = {'script_cancelled': 'Script cancelled by user.', 'menu_silent_on': 'Silent ON', 'menu_silent_off': 'Silent OFF'}

def get_base():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def get_local_version():
    try:
        with open(os.path.join(get_base(), LOCAL_VERSION_FILE), 'r') as f:
            return f.read().strip()
    except Exception:
        return '0.0.0'

def get_remote_version():
    try:
        url = f'{GITHUB_RAW}/{LOCAL_VERSION_FILE}'
        with urllib.request.urlopen(url, timeout=5) as r:
            return r.read().decode().strip()
    except Exception:
        return None

def download_file(url, dest_path):
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    tmp_path = dest_path + '.tmp'
    try:
        urllib.request.urlretrieve(url, tmp_path)
        os.replace(tmp_path, dest_path)
        return True
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        return False

def load_translations():
    LANG_MAP = {'pt': 'pt', 'en': 'en', 'es': 'es', 'fr': 'fr', 'de': 'de', 'it': 'it', 'ru': 'ru', 'ja': 'ja', 'zh': 'zh', 'vi': 'vi', 'ar': 'ar', 'portuguese': 'pt', 'english': 'en', 'spanish': 'es', 'french': 'fr', 'german': 'de', 'italian': 'it', 'russian': 'ru', 'japanese': 'ja', 'chinese': 'zh', 'vietnamese': 'vi', 'arabic': 'ar'}
    try:
        locale.setlocale(locale.LC_ALL, '')
        lang_tuple = locale.getlocale()
        raw = lang_tuple[0].split('_')[0].lower() if lang_tuple and lang_tuple[0] else 'en'
        lang = LANG_MAP.get(raw, 'en')
    except Exception:
        lang = 'en'
    base = get_base()
    translation_path = os.path.join(base, 'translations', f'{lang}.json')
    if not os.path.exists(translation_path):
        translation_path = os.path.join(base, 'translations', 'en.json')
    with open(translation_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def tr(key):
    global _translation_cache
    if _translation_cache is None:
        _translation_cache = load_translations()
    return _translation_cache.get(key, _TR_FALLBACKS.get(key, key))

def save_config(browser_path, password, proxy, execution_count, plan):
    config = {'browser_path': browser_path, 'password': password, 'proxy': proxy, 'execution_count': execution_count, 'plan': plan}
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
    except Exception:
        pass

def load_config():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return None

def save_browser_path(key, path):
    try:
        data = load_browser_paths()
        data[key] = path
        with open(BROWSERS_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception:
        pass

def load_browser_paths():
    try:
        if os.path.exists(BROWSERS_FILE):
            with open(BROWSERS_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def is_valid_password(password):
    if len(password) < 8:
        return False
    if not re.search('[a-z]', password):
        return False
    if not re.search('[A-Z]', password):
        return False
    if not re.search('[0-9]', password):
        return False
    if not re.search('[!@#$%^&*()_+\\-=\\[\\]{};\':\\"|,.<>/?]', password):
        return False
    return True

def generate_random_password():
    length = 12
    special_chars = '!@#$%^&*()_+-=[]{};\':"|,.<>/?'
    password_chars = [random.choice(string.ascii_lowercase), random.choice(string.ascii_uppercase), random.choice(string.digits), random.choice(special_chars)]
    all_chars = string.ascii_letters + string.digits + special_chars
    password_chars.extend((random.choice(all_chars) for _ in range(length - 4)))
    random.shuffle(password_chars)
    return ''.join(password_chars)

def gerar_email_aleatorio():
    return ''.join((random.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(8))) + '@juno.com'

def gerar_email_plan2():
    return ''.join((random.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(8))) + '@juno.com'

class HackerBannerWidget(QWidget):
    _ASCII = ['______ _____  ________  _____   _______ _       ___  _____ ', '|  _  \\  _  ||  _  |  \\/  |\\ \\ / /_   _| |     / _ \\|  __ \\', '| | | | | | || | | | .  . | \\ V /  | | | |    / /_\\ \\ |  \\/', '| | | | | | || | | | |\\/| | /   \\  | | | |    |  _  | | __ ', '| |/ /\\ \\_/ /\\ \\_/ / |  | |/ /^\\ \\ | | | |____| | | | |_\\ \\', '|___/  \\___/  \\___/\\_|  |_/\\/   \\/ \\_/ \\_____/\\_| |_/\\____/']
    _NOISE_CHARS = list('@#$%&!?\\/|<>[]{}01')

    def __init__(self, subtitle='', parent=None):
        super().__init__(parent)
        self._subtitle = subtitle
        self._tick = 0
        self._cursor_on = True
        self._noise = {}
        self._glitch_x = 0
        self._glitch_on = False
        self.setFixedHeight(112)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start(80)

    def _on_tick(self):
        self._tick += 1
        if self._tick % 6 == 0:
            self._cursor_on = not self._cursor_on
        if self._tick % 25 == 0:
            self._glitch_on = True
            self._glitch_x = random.randint(-4, 4)
        elif self._tick % 25 == 3:
            self._glitch_on = False
            self._glitch_x = 0
        if self._tick % 4 == 0 and random.random() < 0.6:
            r = random.randrange(len(self._ASCII))
            c = random.randrange(len(self._ASCII[r]))
            self._noise[r, c] = (random.choice(self._NOISE_CHARS), 3)
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
        W, H = (self.width(), self.height())
        p.fillRect(0, 0, W, H, QColor(0, 0, 0, 0))
        scan_col = QColor(0, 0, 0, 18)
        for y in range(0, H, 2):
            p.fillRect(0, y, W, 1, scan_col)
        font = QFont('Consolas', 7)
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.5)
        p.setFont(font)
        fm = p.fontMetrics()
        ch_w = fm.horizontalAdvance('X')
        ch_h = fm.height()
        rows = len(self._ASCII)
        max_cols = max((len(l) for l in self._ASCII))
        total_w = max_cols * ch_w
        x0 = max(10, (W - total_w) // 2)
        y0 = 12
        t = self._tick
        r_base = int(0 + 10 * math.sin(t * 0.05))
        g_base = int(180 + 30 * math.sin(t * 0.03))
        b_base = int(220 + 35 * math.sin(t * 0.07))
        base_col = QColor(max(0, min(255, r_base)), max(0, min(255, g_base)), max(0, min(255, b_base)))
        glitch_col = QColor(255, 50, 80)
        noise_col = QColor(80, 255, 120)
        dim_col = QColor(0, 100, 130)
        for row_i, line in enumerate(self._ASCII):
            gx = self._glitch_x if self._glitch_on and row_i % 3 == 1 else 0
            for col_i, orig_ch in enumerate(line):
                cx = x0 + col_i * ch_w + gx
                cy = y0 + row_i * ch_h
                if (row_i, col_i) in self._noise:
                    ch = self._noise[row_i, col_i][0]
                    col = noise_col
                elif orig_ch == ' ':
                    continue
                elif self._glitch_on and row_i == 2 and (col_i % 7 == 0):
                    ch = orig_ch
                    col = glitch_col
                else:
                    t2 = col_i / max(max_cols - 1, 1)
                    rv = int(r_base * (1 - t2))
                    gv = int(g_base * (0.6 + 0.4 * t2))
                    bv = int(b_base * (0.7 + 0.3 * (1 - t2)))
                    col = QColor(max(0, min(255, rv)), max(0, min(255, gv)), max(0, min(255, bv)))
                    ch = orig_ch
                p.setPen(col)
                p.drawText(cx, cy + ch_h - fm.descent(), ch)
        deco_y = y0 + rows * ch_h + 3
        grad = QLinearGradient(x0, deco_y, x0 + total_w, deco_y)
        grad.setColorAt(0.0, QColor(0, 0, 0, 0))
        grad.setColorAt(0.3, base_col)
        grad.setColorAt(0.7, base_col)
        grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setPen(QPen(QBrush(grad), 1))
        p.drawLine(x0, deco_y, x0 + total_w, deco_y)
        if self._subtitle:
            sfont = QFont('Consolas', 8)
            sfont.setStyleHint(QFont.StyleHint.Monospace)
            p.setFont(sfont)
            sfm = p.fontMetrics()
            cursor = '_' if self._cursor_on else ' '
            txt = f'>> {self._subtitle}{cursor}'
            tw = sfm.horizontalAdvance(txt)
            sx = max(10, (W - tw) // 2)
            sy = deco_y + 14
            glow = QColor(0, 200, 255, 40)
            p.setPen(glow)
            for dx in (-1, 0, 1):
                p.drawText(sx + dx, sy + 1, txt)
            p.setPen(QColor(0, 200, 220))
            p.drawText(sx, sy, txt)
        p.end()

    def closeEvent(self, event):
        self._timer.stop()
        super().closeEvent(event)

def open_loader():
    base_dir = get_base()
    loader_path = os.path.join(base_dir, 'Exitloader.exe')
    dll_path = os.path.join(base_dir, 'ExitLag.dll')
    missing = []
    if not os.path.exists(loader_path):
        missing.append('Exitloader.exe')
    if not os.path.exists(dll_path):
        missing.append('ExitLag.dll')
    if missing:
        QMessageBox.critical(None, tr('loader_missing_title'), tr('loader_missing_body') + '\n'.join((f'  • {m}' for m in missing)))
        return
    ctypes.windll.shell32.ShellExecuteW(None, 'runas', loader_path, None, base_dir, 1)
PLAN_CONFIGS = {'1': {'url': 'https://www.exitlag.com/lp/trial', 'email_fn': 'gerar_email_aleatorio', 'selectors': {'first': '#inputFirstName', 'last': '#inputLastName', 'email': '#inputEmail', 'password': '#inputNewPassword', 'confirm': '#inputNewPassword2', 'tos': '#hero-terms-check'}, 'pre_click': 'button.btn-signup-email', 'pre_delay': 1.0, 'success_url': 'exitlag.com/lp/trial/success', 'success_txt': 'your account has been created', 'submit_fn': 'onLpRegister'}, '2': {'url': 'https://www.exitlag.com/lp/omen', 'email_fn': 'gerar_email_plan2', 'selectors': {'first': '#firstName', 'last': '#lastName', 'email': '#email', 'password': '#password', 'confirm': '#confirmPassword', 'tos': '#acceptTos'}, 'pre_click': None, 'pre_delay': 0.0, 'success_url': 'account_created=1', 'success_txt': 'soon you will recieve an e-mail from exitlag', 'submit_fn': None}}
_EMAIL_FNS = {'gerar_email_aleatorio': lambda: gerar_email_aleatorio(), 'gerar_email_plan2': lambda: gerar_email_plan2()}

class BrowserAutomation:

    def __init__(self, plan_config: dict):
        self.cfg = plan_config
        self.fake = Faker()
        self.ghost = None

    async def fill_field_instantly(self, tab, selector, text):
        import json as _json
        sel_json = _json.dumps(selector)
        text_json = _json.dumps(text)
        await tab.execute_script(f"\n            (function() {{\n                var el = document.querySelector({sel_json});\n                if (!el) return;\n                el.focus();\n                el.dispatchEvent(new MouseEvent('click', {{bubbles:true}}));\n                // Usa o setter nativo para garantir que frameworks React/Vue detectem\n                var nativeSetter = Object.getOwnPropertyDescriptor(\n                    Object.getPrototypeOf(el), 'value').set;\n                if (nativeSetter) {{\n                    nativeSetter.call(el, {text_json});\n                }} else {{\n                    el.value = {text_json};\n                }}\n                el.dispatchEvent(new Event('input',  {{bubbles:true}}));\n                el.dispatchEvent(new Event('change', {{bubbles:true}}));\n            }})();\n        ")
        await asyncio.sleep(0.05 + random.random() * 0.08)

    async def _inject_antidetect(self, tab):
        try:
            await tab.execute_script("\n                // Remove webdriver flag\n                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});\n\n                // Plugins realistas\n                Object.defineProperty(navigator, 'plugins', {\n                    get: () => [\n                        {name:'Chrome PDF Plugin', filename:'internal-pdf-viewer'},\n                        {name:'Chrome PDF Viewer', filename:'mhjfbmdgcfjbbpaeojofohoefgiehjai'},\n                        {name:'Native Client',     filename:'internal-nacl-plugin'}\n                    ]\n                });\n\n                // Languages\n                Object.defineProperty(navigator, 'languages', {\n                    get: () => ['pt-BR','pt','en-US','en']\n                });\n\n                // hardwareConcurrency realista\n                Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});\n\n                // deviceMemory\n                Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});\n\n                // Canvas noise leve\n                const _toDataURL = HTMLCanvasElement.prototype.toDataURL;\n                HTMLCanvasElement.prototype.toDataURL = function(type) {\n                    const ctx = this.getContext('2d');\n                    if (ctx) {\n                        const img = ctx.getImageData(0, 0, this.width, this.height);\n                        for (let i = 0; i < img.data.length; i += 100) {\n                            img.data[i] ^= (Math.random() * 2) | 0;\n                        }\n                        ctx.putImageData(img, 0, 0);\n                    }\n                    return _toDataURL.apply(this, arguments);\n                };\n\n                // WebGL vendor/renderer realistas\n                const _getParam = WebGLRenderingContext.prototype.getParameter;\n                WebGLRenderingContext.prototype.getParameter = function(param) {\n                    if (param === 37445) return 'Google Inc. (NVIDIA)';\n                    if (param === 37446) return 'ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0)';\n                    return _getParam.call(this, param);\n                };\n            ")
        except Exception:
            pass

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
            self.ghost._hide_by_title('DOOM_GHOSTAPI')
            asyncio.create_task(self.ghost.auto_cloak_loop('DOOM_GHOSTAPI', duration=120, cancel_event=cancel_event))
            if not _PSUTIL_OK:
                log_cb(tr('psutil_missing'), 'warning')
        except Exception as e:
            log_cb(tr('ghost_hide_error').format(e=str(e)[:50]), 'warning')

    async def register_account(self, password, browser_path, log_cb, step_cb, headless=False, cancel_event=None, close_after=True, close_after_delay=5, worker=None, fill_speed='slow'):
        cfg = self.cfg
        sel = cfg['selectors']
        email = _EMAIL_FNS[cfg['email_fn']]()
        first_name = self.fake.first_name()
        last_name = self.fake.last_name()
        options = ChromiumOptions()
        options.browser_preferences = {'profile.default_content_setting_values.notifications': 2, 'profile.default_content_settings.popups': 0}
        _is_opera = 'opera' in (browser_path or '').lower()
        if headless:
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--disable-blink-features=AutomationControlled')
            if not _is_opera:
                options.add_argument('--window-position=30000,30000')
        elif _is_opera:
            options.add_argument(cfg['url'])
        if browser_path:
            options.binary_location = browser_path
        browser = Chrome(options=options)
        _watcher_stop = threading.Event()
        _is_opera = 'opera' in (browser_path or '').lower()
        _ghost_watcher = None
        _existing_opera_pids: set = set()
        if headless and _is_opera and _PSUTIL_OK:
            try:
                import psutil as _psu
                _opera_bin = (browser_path or '').lower()
                for _proc in _psu.process_iter(['pid', 'exe']):
                    try:
                        _exe = (_proc.info['exe'] or '').lower()
                        if _opera_bin and _opera_bin in _exe:
                            _existing_opera_pids.add(_proc.info['pid'])
                    except Exception:
                        pass
            except Exception:
                pass
        if _is_opera and _PSUTIL_OK:
            try:
                import psutil
                _opera_bin = (browser_path or '').lower()
                for _proc in psutil.process_iter(['pid', 'exe', 'status']):
                    try:
                        _exe = (_proc.info['exe'] or '').lower()
                        if _opera_bin and _exe == _opera_bin and (_proc.info['status'] in (psutil.STATUS_ZOMBIE, psutil.STATUS_STOPPED, psutil.STATUS_DEAD)):
                            _proc.kill()
                    except Exception:
                        pass
            except Exception:
                pass
        try:
            tab = await asyncio.wait_for(browser.start(), timeout=30.0)
        except asyncio.TimeoutError:
            try:
                await browser.stop()
            except Exception:
                pass
            return {'email': email, 'password': password, 'success': False}
        if headless and _PSUTIL_OK:
            if not _ghost_watcher:
                _ghost_watcher = GhostModeAPI()
            try:
                _bp = browser._browser_process_manager._process
                _browser_pid = _bp.pid if _bp else None
                if _browser_pid and _browser_pid not in _existing_opera_pids:
                    threading.Thread(target=_ghost_watcher._watch_and_hide_by_pid, args=(_browser_pid,), kwargs={'timeout': 60.0, 'interval': 0.03, 'stop_event': _watcher_stop}, daemon=True).start()
            except Exception:
                pass
        if worker:
            try:
                _bp = browser._browser_process_manager._process
                worker.active_browser_pid = _bp.pid if _bp else None
                worker.watcher_stop = _watcher_stop
            except Exception:
                pass

        def _early_exit():
            log_cb(f'⚠ {tr('btn_cancel')}', 'warning')

        async def _safe_stop(force=False):
            try:
                if force or close_after or (not success):
                    _watcher_stop.set()
                    if worker:
                        worker.active_browser_pid = None
                    await browser.stop()
            except Exception:
                pass
        try:
            log_cb(f'📧 Email: {email}', 'info')
            step_cb(tr('opening_browser'))
            await self._inject_antidetect(tab)
            try:
                _ua_brand = 'Opera' if _is_opera else 'Brave' if 'brave' in (browser_path or '').lower() else 'Google Chrome'
                await tab.execute_script(f"\n                    Object.defineProperty(navigator, 'userAgentData', {{\n                        get: () => ({{\n                            brands: [\n                                {{brand: 'Chromium',      version: '124'}},\n                                {{brand: '{_ua_brand}',   version: '124'}},\n                                {{brand: 'Not-A.Brand',   version: '99'}}\n                            ],\n                            mobile: false,\n                            platform: 'Windows'\n                        }})\n                    }});\n                ")
            except Exception:
                pass
            _is_opera = 'opera' in (browser_path or '').lower()
            if _is_opera and (not headless):
                _target_url = cfg['url'].lower().split('?')[0]
                _deadline, _elapsed = (30.0, 0.0)
                _found_tab = None
                while _elapsed < _deadline:
                    if cancel_event and cancel_event.is_set():
                        _early_exit()
                        await _safe_stop(force=True)
                        return {'email': email, 'password': password, 'success': False}
                    try:
                        _tabs = await browser.get_opened_tabs()
                        for _t in _tabs:
                            try:
                                _cur = (await _t.current_url or '').lower()
                                if _target_url in _cur:
                                    _found_tab = _t
                                    break
                            except Exception:
                                pass
                        if _found_tab:
                            tab = _found_tab
                            break
                    except Exception:
                        pass
                    await asyncio.sleep(0.3)
                    _elapsed += 0.3
            elif _is_opera and headless:
                try:
                    await tab.go_to(cfg['url'])
                except Exception as _e:
                    if 'ERR_ABORTED' in str(_e) or 'net::' in str(_e):
                        _target_url = cfg['url'].lower().split('?')[0]
                        _deadline, _elapsed = (30.0, 0.0)
                        while _elapsed < _deadline:
                            if cancel_event and cancel_event.is_set():
                                break
                            await asyncio.sleep(0.3)
                            _elapsed += 0.3
                            try:
                                for _t in await browser.get_opened_tabs():
                                    try:
                                        _cur = (await _t.current_url or '').lower()
                                        if _target_url in _cur:
                                            tab = _t
                                            break
                                    except Exception:
                                        pass
                                else:
                                    continue
                                break
                            except Exception:
                                pass
                    else:
                        raise
            else:
                try:
                    await asyncio.wait_for(tab.go_to(cfg['url']), timeout=15.0)
                except asyncio.TimeoutError:
                    pass
            if headless:
                if _is_opera and _ghost_watcher:
                    _browser_pid_check = None
                    try:
                        _bp2 = browser._browser_process_manager._process
                        _browser_pid_check = _bp2.pid if _bp2 else None
                    except Exception:
                        pass
                    _confirm_deadline, _confirm_elapsed = (3.0, 0.0)
                    while _confirm_elapsed < _confirm_deadline:
                        _any_visible = False
                        if _browser_pid_check:
                            try:
                                _EnumProc2 = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
                                _vis = [False]

                                def _chk_vis(hwnd, _, _pid=_browser_pid_check):
                                    try:
                                        _pid2 = ctypes.c_ulong(0)
                                        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(_pid2))
                                        if _pid2.value == _pid and ctypes.windll.user32.IsWindowVisible(hwnd):
                                            _vis[0] = True
                                    except Exception:
                                        pass
                                    return True
                                ctypes.windll.user32.EnumWindows(_EnumProc2(_chk_vis), 0)
                                _any_visible = _vis[0]
                            except Exception:
                                pass
                        if not _any_visible:
                            break
                        await asyncio.sleep(0.1)
                        _confirm_elapsed += 0.1
                _watcher_stop.set()
            if cfg['pre_click']:
                _sel_esc = cfg['pre_click'].replace("'", "\\'")
                _deadline_pc, _elapsed_pc = (15.0, 0.0)
                while _elapsed_pc < _deadline_pc:
                    if cancel_event and cancel_event.is_set():
                        _early_exit()
                        await _safe_stop(force=True)
                        return {'email': email, 'password': password, 'success': False}
                    try:
                        _exists = await tab.execute_script(f"return !!document.querySelector('{_sel_esc}');")
                        if _exists:
                            break
                    except Exception:
                        pass
                    await asyncio.sleep(0.3)
                    _elapsed_pc += 0.3
                await tab.execute_script('\n                    window.__cfRLUnblockHandlers = true;\n                ')
                await asyncio.sleep(0.2)
                await tab.execute_script("\n                    (function() {\n                        var btn = document.querySelector('button.btn-signup-email')\n                                  || document.querySelector('#heroSocialFlow > button');\n                        if (!btn) return;\n                        var rect = btn.getBoundingClientRect();\n                        var cx = rect.left + rect.width / 2 + (Math.random() * 4 - 2);\n                        var cy = rect.top + rect.height / 2 + (Math.random() * 4 - 2);\n                        var evts = ['mouseover','mouseenter','mousemove','mousedown','mouseup','click'];\n                        var i = 0;\n                        function next() {\n                            if (i >= evts.length) return;\n                            btn.dispatchEvent(new MouseEvent(evts[i++], {\n                                bubbles: true, cancelable: true,\n                                view: window, clientX: cx, clientY: cy\n                            }));\n                            setTimeout(next, 30 + Math.random() * 60);\n                        }\n                        next();\n                    })();\n                ")
                await asyncio.sleep(cfg['pre_delay'])
                _first_sel_esc = sel['first'].replace("'", "\\'")
                _deadline_form, _elapsed_form = (15.0, 0.0)
                while _elapsed_form < _deadline_form:
                    if cancel_event and cancel_event.is_set():
                        _early_exit()
                        await _safe_stop(force=True)
                        return {'email': email, 'password': password, 'success': False}
                    try:
                        _form_ready = await tab.execute_script(f"return !!document.querySelector('{_first_sel_esc}');")
                        if _form_ready:
                            break
                    except Exception:
                        pass
                    await asyncio.sleep(0.1)
                    _elapsed_form += 0.1
            step_cb(tr('filling_form'))
            log_cb(tr('filling_form'), 'info')
            if fill_speed == 'superfast':
                import json as _json
                _fields = [(sel['first'], first_name), (sel['last'], last_name), (sel['email'], email), (sel['password'], password), (sel['confirm'], password)]
                _fill_js = ''
                for _s, _v in _fields:
                    _sel_j = _json.dumps(_s)
                    _val_j = _json.dumps(_v)
                    _fill_js += '(function(){var el=document.querySelector(' + _sel_j + ');if(el){el.value=' + _val_j + ";el.dispatchEvent(new Event('input',{bubbles:true}));el.dispatchEvent(new Event('change',{bubbles:true}));}})();"
                await tab.execute_script(_fill_js)
                await asyncio.sleep(0.05 + random.random() * 0.1)
                await self.fill_field_instantly(tab, sel['first'], first_name)
                await self.fill_field_instantly(tab, sel['last'], last_name)
                await self.fill_field_instantly(tab, sel['email'], email)
                await self.fill_field_instantly(tab, sel['password'], password)
                await self.fill_field_instantly(tab, sel['confirm'], password)
            else:
                await self.fill_field_instantly(tab, sel['first'], first_name)
                await asyncio.sleep(0.2 + random.random() * 0.3)
                await self.fill_field_instantly(tab, sel['last'], last_name)
                await asyncio.sleep(0.2 + random.random() * 0.3)
                await self.fill_field_instantly(tab, sel['email'], email)
                await asyncio.sleep(0.2 + random.random() * 0.3)
                await self.fill_field_instantly(tab, sel['password'], password)
                await asyncio.sleep(0.2 + random.random() * 0.3)
                await self.fill_field_instantly(tab, sel['confirm'], password)
            await asyncio.sleep(0.2)
            await tab.execute_script(f"document.querySelector('{sel['tos']}').click();")
            step_cb(tr('waiting_captcha'))
            log_cb(tr('waiting_captcha'), 'warning')
            if await self._interruptible_sleep(5, cancel_event):
                _early_exit()
                await _safe_stop()
                return {'email': email, 'password': password, 'success': False}
            step_cb(tr('submitting_form'))
            log_cb(tr('submitting_form'), 'info')
            _submit_fn = cfg.get('submit_fn')
            if _submit_fn:
                await tab.execute_script(f"document.querySelector('#registerButton').click();")
                await asyncio.sleep(0.5)
                await tab.execute_script(f"if(typeof {_submit_fn}==='function') {_submit_fn}('dummy-token');")
            else:
                await tab.execute_script("document.querySelector('#registerButton').click();")
            _post_submit_deadline = asyncio.get_event_loop().time() + 15
            while asyncio.get_event_loop().time() < _post_submit_deadline:
                if cancel_event and cancel_event.is_set():
                    _early_exit()
                    await _safe_stop()
                    return {'email': email, 'password': password, 'success': False}
                await asyncio.sleep(0.4)
                _url_now = None
                try:
                    _url_now = await tab.execute_script('return window.location.href;')
                    if isinstance(_url_now, dict):
                        try:
                            _url_now = _url_now['result']['result']['value']
                        except (KeyError, TypeError):
                            _url_now = None
                except Exception:
                    pass
                _url_now = str(_url_now or '').lower()
                _success_url_cfg = cfg.get('success_url', '').lower()
                if _success_url_cfg and _success_url_cfg in _url_now:
                    break
                if any((k in _url_now for k in ('success', 'account_created', 'register-success', 'signup-complete'))):
                    break
                _err_quick = None
                try:
                    _err_quick = await tab.execute_script('\n                        const s=[\'.alert-danger\',\'[class*="invalid-feedback"]\',\'[class*="error-msg"]\',\'[class*="alert-error"]\'];\n                        for(const sel of s){const e=document.querySelector(sel);\n                        if(e&&e.offsetParent!==null&&e.textContent.trim())return e.textContent.trim();}\n                        return null;\n                    ')
                    if isinstance(_err_quick, dict):
                        try:
                            _err_quick = _err_quick['result']['result']['value']
                        except (KeyError, TypeError):
                            _err_quick = None
                except Exception:
                    pass
                if _err_quick and str(_err_quick).strip() not in (None, 'None', ''):
                    break
            try:

                def _extract(result):
                    if isinstance(result, dict):
                        try:
                            return result['result']['result']['value']
                        except (KeyError, TypeError):
                            return None
                    return result
                current_url = _extract(await tab.execute_script('return window.location.href;'))
                page_title = _extract(await tab.execute_script('return document.title;'))
                page_body_txt = _extract(await tab.execute_script("return document.body ? document.body.innerText : '';"))
                error_text = _extract(await tab.execute_script('\n                    const errorSelectors = [\'.alert-danger\', \'[data-error]\',\n                        \'[class*="invalid-feedback"]\', \'.form-error\', \'[class*="error-msg"]\',\n                        \'[class*="alert-error"]\'];\n                    for (const sel of errorSelectors) {\n                        const error = document.querySelector(sel);\n                        if (error && error.offsetParent !== null && error.textContent.trim()) {\n                            return error.textContent.trim();\n                        }\n                    }\n                    return null;\n                '))
                success_el = _extract(await tab.execute_script('\n                    const s = document.querySelector(\n                        \'.success, .alert-success, [class*="success"], [class*="thank"],\' +\n                        \'[class*="confirm"], [class*="complete"], [class*="registered"],\' +\n                        \'[id*="success"], [id*="confirm"], [id*="complete"]\'\n                    );\n                    return s ? s.textContent.trim() : null;\n                '))
                error_text = str(error_text).strip() if error_text not in (None, 'None', '') else None
                success_el = str(success_el).strip() if success_el not in (None, 'None', '') else None
                current_url = str(current_url) if current_url else ''
                page_title = str(page_title).lower() if page_title else ''
                page_body_txt = str(page_body_txt).lower() if page_body_txt else ''
                ERROR_BODY_KEYWORDS = ('invalid email', 'email already', 'already registered', 'already in use', 'email taken', 'this email is', 'password is too', 'password must', 'senha inválida', 'e-mail já', 'email já', 'já cadastrado', 'captcha', 'robot', 'automated', 'unusual traffic', 'too many requests', 'rate limit', 'blocked')
                hard_error = bool(error_text)
                body_error = any((k in page_body_txt for k in ERROR_BODY_KEYWORDS))
                if hard_error or body_error:
                    _err_reason = error_text or next((k for k in ERROR_BODY_KEYWORDS if k in page_body_txt), 'unknown error')
                    if 'captcha' in _err_reason.lower() or 'robot' in _err_reason.lower() or 'automated' in _err_reason.lower():
                        log_cb(f'✗ {tr('captcha_failed')}', 'error')
                    else:
                        log_cb(f'✗ {tr('error_fill_form').format(e=_err_reason)}', 'error')
                    step_cb(tr('step_failed'))
                    if close_after:
                        try:
                            _watcher_stop.set()
                            if worker:
                                worker.active_browser_pid = None
                            await browser.stop()
                        except Exception:
                            pass
                    return {'email': email, 'password': password, 'success': False}
                _success_url = cfg.get('success_url', '').lower()
                _success_txt = cfg.get('success_txt', '').lower()
                url_lower = current_url.lower()
                body_lower = page_body_txt.lower()
                exact_url = bool(_success_url and _success_url in url_lower)
                exact_txt = bool(_success_txt and _success_txt in body_lower)
                has_success_el = bool(success_el)
                FALLBACK_BODY = ('thank you for registering', 'thank you for signing up', 'successfully created', 'account created', 'registration complete', 'registration successful', 'bem-vindo', 'cadastro realizado com sucesso')
                FALLBACK_URL = ('account_created', 'registration-success', 'signup-complete', 'register-success')
                fallback_body = any((k in body_lower for k in FALLBACK_BODY))
                fallback_url = any((k in url_lower for k in FALLBACK_URL))
                success = exact_url or exact_txt or has_success_el or fallback_body or fallback_url
                if success:
                    step_cb(tr('step_done'))
                    log_cb(f'✓ {tr('registration_success')}', 'success')
                    log_cb(f'   📧 {email}', 'success')
                    log_cb(f'   🔑 {password}', 'success')
                else:
                    step_cb(tr('step_failed'))
                if close_after:
                    try:
                        if success and close_after_delay > 0:
                            await asyncio.sleep(close_after_delay)
                        _watcher_stop.set()
                        if worker:
                            worker.active_browser_pid = None
                        await browser.stop()
                        await asyncio.sleep(0.5)
                        if headless and self.ghost:
                            if self.ghost._check_if_window_exists('DOOM_GHOSTAPI'):
                                log_cb(tr('browser_still_open'), 'warning')
                                self.ghost._force_close_by_title('DOOM_GHOSTAPI')
                                await asyncio.sleep(0.5)
                            else:
                                log_cb(tr('browser_closed_ok'), 'info')
                    except Exception:
                        pass
                return {'email': email, 'password': password, 'success': success}
            except Exception as e:
                log_cb(f'✗ {tr('error_fill_form').format(e=str(e)[:80])}', 'error')
                step_cb(tr('step_failed'))
                await _safe_stop()
                return {'email': email, 'password': password, 'success': False}
        except Exception as e:
            log_cb(f'✗ {tr('error_fill_form').format(e=str(e)[:80])}', 'error')
            await _safe_stop()
            return {'email': email, 'password': password, 'success': False}

async def run_accounts(plan, passw, count, browser_path, log_cb, step_cb, done_cb, cancel_event=None, headless=False, close_after=True, close_after_delay=5, fill_speed='slow'):
    accounts = []
    automation = BrowserAutomation(PLAN_CONFIGS.get(plan, PLAN_CONFIGS['1']))
    for x in range(count):
        if cancel_event and cancel_event.is_set():
            log_cb(f'\n⚠ {tr('script_cancelled')}', 'warning')
            break
        log_cb(f'\n{'─' * 40}', 'dim')
        log_cb(tr('account_counter').format(x=x + 1, count=count), 'accent')
        log_cb(f'{'─' * 40}', 'dim')
        result = await automation.register_account(passw, browser_path, log_cb, step_cb, headless=headless, cancel_event=cancel_event, close_after=close_after, close_after_delay=close_after_delay, fill_speed=fill_speed)
        result['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        accounts.append(result)
        if result.get('success'):
            with open('accounts.txt', 'a', encoding='utf-8') as f:
                f.write(f'{result['email']} | {result['password']} | {result['created_at']}\n')
        if cancel_event and cancel_event.is_set():
            log_cb(f'\n⚠ {tr('script_cancelled')}', 'warning')
            break
        if x < count - 1:
            delay = 3
            log_cb(tr('waiting_next_account').format(delay=delay), 'warning')
            elapsed = 0.0
            while elapsed < delay:
                if cancel_event and cancel_event.is_set():
                    break
                await asyncio.sleep(0.2)
                elapsed += 0.2
    successful = sum((1 for acc in accounts if acc['success']))
    log_cb(f'\n{'═' * 40}', 'dim')
    log_cb(f'✓ {tr('successfully_created_account').format(x=successful, executionCount=count)}', 'success')
    log_cb(tr('credentials_saved'), 'success')
    cancelled = cancel_event and cancel_event.is_set()
    done_cb([acc for acc in accounts if acc.get('success')], cancelled)

class SegmentedBarWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(16)
        self._pct = 0.0
        self._target = 0.0
        self._pulse_t = 0.0
        self._state = 'idle'
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(33)

    def set_pct(self, value):
        self._target = max(0.0, min(1.0, value))

    def set_state(self, state: str):
        self._state = state
        if state == 'success':
            self._target = 1.0
        elif state in ('error', 'cancelled'):
            self._target = 1.0
        self.update()

    def _tick(self):
        self._pct += (self._target - self._pct) * 0.12
        self._pulse_t += 0.08
        self.update()

    def stop(self):
        self._timer.stop()

    def paintEvent(self, event):
        import math
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        W = self.width()
        H = self.height()
        p = self._pct
        C = 6
        NUM_SEGS = 20
        SEG_GAP = 3
        BAR_PAD = 3
        BG_COL = QColor('#1a1e2a')
        if self._state == 'error':
            BORDER_COL = QColor('#ff4444')
            SEG_LIT = QColor('#cc0000')
            SEG_TOP = QColor('#ff6666')
            ICON_COL = QColor('#ff4444')
        elif self._state == 'cancelled':
            BORDER_COL = QColor('#ffaa00')
            SEG_LIT = QColor('#aa6600')
            SEG_TOP = QColor('#ffcc55')
            ICON_COL = QColor('#ffaa00')
        elif self._state == 'success':
            BORDER_COL = QColor('#00e676')
            SEG_LIT = None
            SEG_TOP = QColor('#5ae8ff')
            ICON_COL = QColor('#00e676')
        else:
            BORDER_COL = QColor('#00c8ff')
            SEG_LIT = None
            SEG_TOP = QColor('#5ae8ff')
            ICON_COL = None
        SEG_DIM = QColor('#003a4a')
        path = QPainterPath()
        path.addRoundedRect(0, 0, W, H, C, C)
        painter.fillPath(path, BG_COL)
        painter.setPen(QPen(BORDER_COL, 1))
        painter.drawPath(path)
        if self._state in ('success', 'error', 'cancelled') and p >= 0.97:
            painter.setPen(QPen(ICON_COL, 2))
            cx, cy = (W // 2, H // 2)
            s = H * 0.28
            if self._state == 'success':
                painter.drawLine(int(cx - s), cy, int(cx - s * 0.2), int(cy + s * 0.8))
                painter.drawLine(int(cx - s * 0.2), int(cy + s * 0.8), int(cx + s), int(cy - s * 0.7))
            elif self._state == 'error':
                painter.drawLine(int(cx - s), int(cy - s), int(cx + s), int(cy + s))
                painter.drawLine(int(cx + s), int(cy - s), int(cx - s), int(cy + s))
            elif self._state == 'cancelled':
                painter.drawLine(int(cx - s), cy, int(cx + s), cy)
            painter.end()
            return
        pulse = 0.7 + 0.3 * math.sin(self._pulse_t)
        filled = int(p * NUM_SEGS)
        inner_x0 = C + 2
        inner_x1 = W - C - 2
        inner_w = inner_x1 - inner_x0
        seg_total = (inner_w + SEG_GAP) / NUM_SEGS
        seg_w = seg_total - SEG_GAP
        painter.setPen(Qt.PenStyle.NoPen)
        for i in range(NUM_SEGS):
            x0 = int(inner_x0 + i * seg_total)
            x1 = int(x0 + seg_w)
            y0 = BAR_PAD
            y1 = H - BAR_PAD
            if i < filled:
                if SEG_LIT:
                    color = SEG_LIT
                else:
                    fade = 0.6 + 0.4 * (i / max(filled - 1, 1))
                    b_val = min(255, int(255 * fade * pulse))
                    g_val = min(255, int(200 * fade * pulse))
                    color = QColor(0, g_val, b_val)
                painter.fillRect(x0, y0, x1 - x0, y1 - y0, color)
                painter.setPen(QPen(SEG_TOP, 1))
                painter.drawLine(x0, y0, x1, y0)
                painter.setPen(Qt.PenStyle.NoPen)
            else:
                painter.fillRect(x0, y0, x1 - x0, y1 - y0, SEG_DIM)
        painter.end()

class AutomationWorker(QObject):
    log_signal = pyqtSignal(str, str)
    step_signal = pyqtSignal(str)
    done_signal = pyqtSignal(list, bool)

    def __init__(self, plan, passw, count, browser_path, cancel_event, headless, close_after, close_after_delay, fill_speed):
        super().__init__()
        self.plan = plan
        self.passw = passw
        self.count = count
        self.browser_path = browser_path
        self.cancel_event = cancel_event
        self.headless = headless
        self.close_after = close_after
        self.close_after_delay = close_after_delay
        self.fill_speed = fill_speed

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_accounts(self.plan, self.passw, self.count, self.browser_path, lambda msg, lvl='info': self.log_signal.emit(msg, lvl), lambda msg: self.step_signal.emit(msg), lambda accounts, cancelled: self.done_signal.emit(accounts, cancelled), cancel_event=self.cancel_event, headless=self.headless, close_after=self.close_after, close_after_delay=self.close_after_delay, fill_speed=self.fill_speed))
        loop.close()

class NumberSpinBox(QWidget):
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
        for symbol, delta in [('+', 1), ('−', -1)]:
            btn = QPushButton(symbol)
            btn.setObjectName('spinBtn')
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
    line.setObjectName('separator')
    line.setFrameShape(QFrame.Shape.HLine)
    return line

def make_field_label(text):
    lbl = QLabel(text)
    lbl.setObjectName('fieldLabel')
    return lbl

def make_input(placeholder=''):
    w = QLineEdit()
    if placeholder:
        w.setPlaceholderText(placeholder)
    return w

def make_btn(text, style='primary'):
    b = QPushButton(text)
    b.setObjectName(style)
    b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
    return b

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
        title.setStyleSheet(f'color: {ACCENT}; font-size: 14pt; font-weight: bold;')
        hdr.addWidget(title)
        hdr.addStretch()
        refresh = make_btn(tr('btn_refresh'), 'secondary')
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
        self._count_label = QLabel('')
        self._count_label.setObjectName('subtitle')
        self._count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._count_label)
        self._load()

    def _load(self):
        while self._vbox.count():
            item = self._vbox.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        accounts = []
        acc_file = os.path.join(get_base(), 'accounts.txt')
        if os.path.exists(acc_file):
            with open(acc_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    parts = [p.strip() for p in line.split('|')]
                    email = parts[0] if len(parts) > 0 else ''
                    password = parts[1] if len(parts) > 1 else ''
                    created = parts[2] if len(parts) > 2 else '—'
                    if email:
                        accounts.append({'email': email, 'password': password, 'created_at': created})
        self._count_label.setText(tr('accounts_saved_count').format(count=len(accounts)))
        if not accounts:
            lbl = QLabel(tr('no_accounts_saved'))
            lbl.setObjectName('subtitle')
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._vbox.addWidget(lbl)
            return
        for i, acc in enumerate(accounts):
            card = QFrame()
            card.setObjectName('card')
            cl = QVBoxLayout(card)
            cl.setContentsMargins(14, 10, 14, 10)
            cl.setSpacing(2)
            num = QLabel(f'#{i + 1}')
            num.setStyleSheet(f'color: {TEXT_DIM}; font-size: 9pt; font-weight: bold;')
            email_lbl = QLabel(f'📧  {acc['email']}')
            pass_lbl = QLabel(f'🔑  {acc['password']}')
            pass_lbl.setStyleSheet(f'color: {TEXT_DIM};')
            time_lbl = QLabel(f'🕐  {acc['created_at']}')
            time_lbl.setStyleSheet(f'color: {TEXT_DIM}; font-size: 9pt;')
            cl.addWidget(num)
            cl.addWidget(email_lbl)
            cl.addWidget(pass_lbl)
            cl.addWidget(time_lbl)
            btn_row = QHBoxLayout()
            btn_row.setSpacing(6)
            for label, val, style in [(tr('btn_copy_all'), f'{acc['email']} | {acc['password']}', 'primary'), (tr('btn_copy_email'), acc['email'], 'secondary'), (tr('btn_copy_password'), acc['password'], 'secondary')]:
                b = make_btn(label, style)
                b.clicked.connect(lambda _, v=val: QApplication.clipboard().setText(v))
                btn_row.addWidget(b)
            btn_row.addStretch()
            cl.addLayout(btn_row)
            self._vbox.addWidget(card)
            self._vbox.addSpacing(6)

class UpdateDialog(QDialog):
    status_signal = pyqtSignal(str, str)
    exit_signal = pyqtSignal(str)

    def __init__(self, local, remote, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr('window_update'))
        self.setFixedSize(420, 280)
        self.setStyleSheet(STYLESHEET)
        self.setModal(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 20)
        layout.setSpacing(8)
        title = QLabel(tr('update_available_title'))
        title.setStyleSheet(f'color: {WARNING}; font-size: 16pt; font-weight: bold;')
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        layout.addWidget(QLabel(tr('update_arrow').format(local=local, remote=remote)))
        note = QLabel(tr('update_auto_dl'))
        note.setObjectName('subtitle')
        note.setWordWrap(True)
        layout.addWidget(note)
        self._prog = QProgressBar()
        self._prog.setRange(0, 0)
        self._prog.setFixedHeight(6)
        self._prog.setStyleSheet(f'\n            QProgressBar {{ background: {BG3}; border-radius: 3px; border: none; }}\n            QProgressBar::chunk {{ background: {ACCENT2}; border-radius: 3px; }}\n        ')
        self._prog.setVisible(False)
        layout.addWidget(self._prog)
        self._status = QLabel('')
        self._status.setObjectName('stepLabel')
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._status)
        btn = make_btn(tr('btn_update_now'), 'warning')
        btn.clicked.connect(lambda: self._do_update(local, remote))
        layout.addWidget(btn)
        self.status_signal.connect(self._on_status)
        self.exit_signal.connect(self._on_exit)

    def _on_exit(self, mode):
        QApplication.instance().closeAllWindows()
        if mode == 'exe':
            pass
        elif mode.startswith('py:'):
            subprocess.Popen([sys.executable, mode[3:]])
        QApplication.instance().quit()
        os._exit(0)

    def _on_status(self, text, color):
        self._status.setText(text)
        self._status.setStyleSheet(f'color: {color};')

    def _do_update(self, local, remote):
        self._prog.setVisible(True)

        def run():
            base = get_base()
            success = True
            steps = []
            if getattr(sys, 'frozen', False):
                new_exe_path = os.path.join(base, 'mainrev_new.exe')
                steps.append((tr('downloading_exe'), 'https://github.com/TDoomX/exitlag-auto-signup-revamp/releases/latest/download/mainrev.exe', new_exe_path))
            steps.append((tr('downloading_main'), f'{GITHUB_RAW}/main.py', os.path.join(base, 'main.py')))
            os.makedirs(os.path.join(base, 'translations'), exist_ok=True)
            for lang in TRANSLATIONS_LANGS:
                steps.append((tr('downloading_translation').format(lang=lang), f'{GITHUB_RAW}/translations/{lang}.json', os.path.join(base, 'translations', f'{lang}.json')))
            steps.append(('version.txt', f'{GITHUB_RAW}/version.txt', os.path.join(base, 'version.txt')))
            steps.append(('lib/lib.py', f'{GITHUB_RAW}/lib/lib.py', os.path.join(base, 'lib', 'lib.py')))
            steps.append(('requirements.txt', f'{GITHUB_RAW}/requirements.txt', os.path.join(base, 'requirements.txt')))
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
                exe_path = os.path.join(base, 'mainrev.exe')
                new_exe = os.path.join(base, 'mainrev_new.exe')
                bat_path = os.path.join(base, 'update.bat')
                bat_content = f'@echo off\r\ntimeout /t 2 /nobreak > nul\r\nmove /y "{new_exe}" "{exe_path}"\r\nexplorer.exe "{exe_path}"\r\ndel "%~f0"\r\n'
                with open(bat_path, 'w', encoding='utf-8') as f:
                    f.write(bat_content)
                time.sleep(0.5)
                subprocess.Popen(bat_path, shell=True)
                self.exit_signal.emit('exe')
            else:
                req_path = os.path.join(base, 'requirements.txt')
                if os.path.exists(req_path):
                    self.status_signal.emit(tr('installing_dependencies'), ACCENT)
                    subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', req_path], capture_output=True)
                self.exit_signal.emit(f'py:{os.path.join(base, 'main.py')}')
        threading.Thread(target=run, daemon=True).start()

class App(QMainWindow):
    _update_signal = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle(tr('app_title'))
        self.setFixedSize(600, 700)
        self.setStyleSheet(STYLESHEET)
        self.lib = Main()
        self._silent_mode = False
        self._close_after = False
        self._close_after_delay = 5
        self._selected_plan = 1
        self._fill_speed = 'slow'
        self._delay_container = None
        self._bar_widget = None
        self._log_queue = queue.Queue()
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._poll_log)
        self._cancel_event = None
        self._completed = 0
        self._total = 0
        self._current_screen = (None, None)
        try:
            import locale as _lc
            _lc.setlocale(_lc.LC_ALL, '')
            _lt = _lc.getlocale()
            _raw = _lt[0].split('_')[0].lower() if _lt and _lt[0] else 'en'
            _LMAP = {'pt': 'pt', 'en': 'en', 'es': 'es', 'fr': 'fr', 'de': 'de', 'it': 'it', 'ru': 'ru', 'ja': 'ja', 'zh': 'zh', 'portuguese': 'pt', 'english': 'en', 'spanish': 'es', 'french': 'fr', 'german': 'de', 'italian': 'it', 'russian': 'ru', 'japanese': 'ja', 'chinese': 'zh'}
            self._current_lang = _LMAP.get(_raw, 'en')
        except Exception:
            self._current_lang = 'en'
        self._center()
        self._update_signal.connect(self._show_update)
        self._check_updates_bg()
        self._download_missing_langs()
        self._check_missing_deps()
        self._show_config()

    def _center(self):
        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width() - 600) // 2, (screen.height() - 700) // 2)

    def _build_header(self, central, subtitle=''):
        self._delay_container = None
        menu_bar = QWidget()
        self._menu_bar = menu_bar
        menu_bar.setObjectName('menuBar')
        menu_bar.setFixedHeight(32)
        mb_layout = QHBoxLayout(menu_bar)
        mb_layout.setContentsMargins(4, 0, 4, 0)
        mb_layout.setSpacing(0)

        def menu_btn(text, slot, obj='menuBtn'):
            b = QPushButton(text)
            b.setObjectName(obj)
            b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            if slot is not None:
                b.clicked.connect(slot)
            return b
        mb_layout.addWidget(menu_btn(tr('menu_accounts'), self._show_accounts))
        last = load_config()
        if last:
            mb_layout.addWidget(menu_btn(tr('menu_last_config'), lambda: self._show_last_config(last)))
        mb_layout.addStretch()
        self._silent_btn = menu_btn('', self._toggle_silent)
        self._update_silent_btn()
        mb_layout.addWidget(self._silent_btn)
        self._close_after_btn = menu_btn('', self._toggle_close_after)
        self._update_close_after_btn()
        mb_layout.addWidget(self._close_after_btn)
        LANG_FLAGS = {'pt': '🇧🇷', 'en': '🇺🇸', 'es': '🇪🇸', 'fr': '🇫🇷', 'de': '🇩🇪', 'it': '🇮🇹', 'ru': '🇷🇺', 'ja': '🇯🇵', 'zh': '🇨🇳', 'vi': '🇻🇳', 'ar': '🇸🇦'}
        flag = LANG_FLAGS.get(self._current_lang, '🌐')
        lang_btn = menu_btn(f'{flag}  {tr('menu_language')}', None)
        lang_btn.setFont(QFont('Segoe UI Emoji', 10))
        lang_btn.clicked.connect(lambda: self._show_lang_menu(lang_btn))
        mb_layout.addWidget(lang_btn)
        central.addWidget(menu_bar)
        banner = HackerBannerWidget(subtitle)
        central.addWidget(banner)
        central.addWidget(make_separator())
        central.addSpacing(10)

    def _toggle_silent(self):
        self._silent_mode = not self._silent_mode
        self._update_silent_btn()
        if self._silent_mode:
            self._close_after = True
            self._update_close_after_btn()
            self._close_after_btn.setEnabled(False)
        else:
            self._close_after_btn.setEnabled(True)

    def _update_silent_btn(self):
        if self._silent_mode:
            self._silent_btn.setText(f'🔇 {tr('menu_silent_on')}')
            self._silent_btn.setStyleSheet(f'color: {ACCENT}; background: transparent; border: none; padding: 4px 12px; font-size: 9pt;')
        else:
            self._silent_btn.setText(f'🔊 {tr('menu_silent_off')}')
            self._silent_btn.setStyleSheet('')

    def _toggle_close_after(self):
        self._close_after = not self._close_after
        self._update_close_after_btn()

    def _update_close_after_btn(self):
        if self._close_after:
            self._close_after_btn.setText(f'🔒 {tr('menu_close_after_on')}')
            self._close_after_btn.setStyleSheet(f'color: {ACCENT}; background: transparent; border: none; padding: 4px 12px; font-size: 9pt;')
        else:
            self._close_after_btn.setText(f'🔓 {tr('menu_close_after_off')}')
            self._close_after_btn.setStyleSheet('')
        self._close_after_btn.setEnabled(not self._silent_mode)
        if self._delay_container is not None:
            self._delay_container.setVisible(self._close_after)

    def _show_lang_menu(self, btn):
        LANG_OPTIONS = [('🇧🇷  Português', 'pt'), ('🇺🇸  English', 'en'), ('🇪🇸  Español', 'es'), ('🇫🇷  Français', 'fr'), ('🇩🇪  Deutsch', 'de'), ('🇮🇹  Italiano', 'it'), ('🇷🇺  Русский', 'ru'), ('🇯🇵  日本語', 'ja'), ('🇨🇳  中文', 'zh'), ('🇻🇳  Tiếng Việt', 'vi'), ('🇸🇦  العربية', 'ar')]
        menu = QMenu(self)
        menu.setStyleSheet("\n            QMenu {\n                background-color: #1e2130;\n                border: 1px solid #2e3250;\n                padding: 4px 0;\n                font-family: 'Segoe UI Emoji', 'Segoe UI', sans-serif;\n                font-size: 10pt;\n            }\n            QMenu::item {\n                padding: 7px 20px 7px 12px;\n                color: #e0e0e0;\n                background: transparent;\n            }\n            QMenu::item:selected {\n                background-color: #2e3250;\n                color: #ffffff;\n                border-radius: 3px;\n            }\n            QMenu::item:checked {\n                color: #00e5ff;\n                font-weight: bold;\n            }\n        ")
        for lbl, code in LANG_OPTIONS:
            active = code == self._current_lang
            text = ('✓  ' if active else '     ') + lbl
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
        path = os.path.join(base, 'translations', f'{code}.json')
        if not os.path.exists(path):
            url = f'{GITHUB_RAW}/translations/{code}.json'
            download_file(url, path)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                _translation_cache = json.load(f)
        screen = self._current_screen
        if screen[0] == 'last_config':
            self._show_last_config(screen[1])
        elif screen[0] == 'log':
            self._show_log(*screen[1])
        else:
            self._show_config()

    def _clear(self):
        if self._bar_widget:
            self._bar_widget.stop()
            self._bar_widget = None
        self._poll_timer.stop()
        cw = QWidget()
        cw.setObjectName('root')
        self.setCentralWidget(cw)

    def _make_scroll_content(self):
        central = QWidget()
        central.setObjectName('root')
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        return main_layout

    def _show_config(self):
        self._current_screen = ('config', None)
        main = self._make_scroll_content()
        self._build_header(main, tr('new_config_title'))
        body = QWidget()
        bl = QVBoxLayout(body)
        bl.setContentsMargins(30, 0, 30, 30)
        bl.setSpacing(6)
        bl.addWidget(make_field_label(tr('browser_executable_path')))
        _saved_browsers = load_browser_paths()
        BROWSERS = [('chrome', 'Chrome', '🌐'), ('brave', 'Brave', '🦁'), ('operagx', 'Opera GX', '🎮')]
        browser_entry = make_input(tr('browser_path_prompt'))
        _last_cfg = load_config()
        if _last_cfg and _last_cfg.get('browser_path') and os.path.exists(_last_cfg['browser_path']):
            browser_entry.setText(_last_cfg['browser_path'])

        def _pick_browser(key, label):
            saved = load_browser_paths().get(key)
            if saved and os.path.exists(saved):
                browser_entry.setText(saved)
                return
            path, _ = QFileDialog.getOpenFileName(self, f'{tr('browse_dialog_title')} — {label}', '', 'Executable (*.exe)')
            if path:
                save_browser_path(key, path)
                browser_entry.setText(path)
                _refresh_browser_btns()

        def _browser_context_menu(btn, key, label):
            saved = load_browser_paths().get(key)
            if not (saved and os.path.exists(saved)):
                _pick_browser(key, label)
                return
            menu = QMenu(btn)
            act_change = menu.addAction(tr('browser_ctx_change'))
            act_remove = menu.addAction(tr('browser_ctx_remove'))
            chosen = menu.exec(btn.mapToGlobal(btn.rect().bottomLeft()))
            if chosen == act_change:
                path, _ = QFileDialog.getOpenFileName(self, f'{tr('browse_dialog_title')} — {label}', '', 'Executable (*.exe)')
                if path:
                    save_browser_path(key, path)
                    browser_entry.setText(path)
                    _refresh_browser_btns()
            elif chosen == act_remove:
                data = load_browser_paths()
                data.pop(key, None)
                try:
                    with open(BROWSERS_FILE, 'w') as f:
                        json.dump(data, f, indent=4)
                except Exception:
                    pass
                if browser_entry.text() == saved:
                    browser_entry.setText('')
                _refresh_browser_btns()
        browser_btns_row = QHBoxLayout()
        browser_btns_row.setSpacing(6)
        _browser_btns = {}

        def _refresh_browser_btns():
            saved = load_browser_paths()
            current = browser_entry.text().strip()
            for k, btn in _browser_btns.items():
                path = saved.get(k, '')
                has = bool(path and os.path.exists(path))
                selected = has and path == current
                if selected:
                    btn.setStyleSheet(f'font-size: 9pt; padding: 0 10px; border-radius: 6px;background: #00cc6622; color: #00cc66; border: 1px solid #00cc6655;')
                elif has:
                    btn.setStyleSheet(f'font-size: 9pt; padding: 0 10px; border-radius: 6px;background: {ACCENT}22; color: {ACCENT}; border: 1px solid {ACCENT}55;')
                else:
                    btn.setStyleSheet(f'font-size: 9pt; padding: 0 10px; border-radius: 6px;')
                btn.setToolTip(tr('browser_ctx_tip') if has else tr('browser_pick_tip'))
        for _key, _label, _icon in BROWSERS:
            _btn = QPushButton(f'{_icon}  {_label}')
            _btn.setFixedHeight(32)
            _btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            _btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            _browser_btns[_key] = _btn
            browser_btns_row.addWidget(_btn)
            _btn.clicked.connect(lambda checked=False, k=_key, l=_label: _pick_browser(k, l))
            _btn.customContextMenuRequested.connect(lambda pos, b=_btn, k=_key, l=_label: _browser_context_menu(b, k, l))
        browser_btns_row.addStretch()
        _refresh_browser_btns()

        def _update_silent_for_browser(path):
            _refresh_browser_btns()
            self._silent_btn.setEnabled(True)
            self._silent_btn.setToolTip('')
            self._update_silent_btn()
        browser_entry.textChanged.connect(_update_silent_for_browser)
        _update_silent_for_browser(browser_entry.text())
        bl.addLayout(browser_btns_row)
        bl.addSpacing(4)
        browser_row = QHBoxLayout()
        browser_row.addWidget(browser_entry)
        browse_btn = make_btn(tr('btn_browse'), 'secondary')
        browse_btn.setFixedWidth(100)

        def browse():
            path, _ = QFileDialog.getOpenFileName(self, tr('browse_dialog_title'), '', 'Executable (*.exe)')
            if path:
                browser_entry.setText(path)
        browse_btn.clicked.connect(browse)
        browser_row.addWidget(browse_btn)
        bl.addLayout(browser_row)
        bl.addSpacing(4)
        bl.addWidget(make_field_label(tr('password_label')))
        pass_row = QHBoxLayout()
        pass_entry = make_input()
        pass_row.addWidget(pass_entry)
        gen_btn = make_btn(tr('btn_generate'), 'secondary')
        gen_btn.setFixedWidth(100)
        gen_btn.clicked.connect(lambda: pass_entry.setText(generate_random_password()))
        pass_row.addWidget(gen_btn)
        bl.addLayout(pass_row)
        bl.addSpacing(4)
        bl.addWidget(make_field_label(tr('proxy_label') + ' (optional)'))
        proxy_entry = make_input('http://host:port')
        bl.addWidget(proxy_entry)
        bl.addSpacing(4)
        bl.addWidget(make_field_label(tr('fill_speed_label')))
        speed_row = QHBoxLayout()
        speed_group = QButtonGroup(self)
        _speeds = [('slow', tr('fill_speed_slow')), ('fast', tr('fill_speed_fast')), ('superfast', tr('fill_speed_superfast'))]
        _speed_rbs = {}
        for _sid, _slabel in _speeds:
            _rb = QRadioButton(_slabel)
            _rb.setChecked(self._fill_speed == _sid)
            speed_group.addButton(_rb)
            _speed_rbs[_sid] = _rb
            speed_row.addWidget(_rb)
        speed_row.addStretch()

        def _on_speed_changed():
            for _sid, _rb in _speed_rbs.items():
                if _rb.isChecked():
                    self._fill_speed = _sid
                    break
        for _rb in _speed_rbs.values():
            _rb.toggled.connect(lambda _: _on_speed_changed())
        bl.addLayout(speed_row)
        bl.addSpacing(4)
        counts_row = QHBoxLayout()
        counts_row.setSpacing(16)
        counts_row.setAlignment(Qt.AlignmentFlag.AlignTop)
        count_block = QVBoxLayout()
        count_block.setSpacing(2)
        count_block.setContentsMargins(0, 0, 0, 0)
        count_block.addWidget(make_field_label(tr('number_of_accounts_prompt')))
        count_spin = NumberSpinBox(1, 100, 1)
        count_spin.setFixedHeight(38)
        count_block.addWidget(count_spin)
        count_container = QWidget()
        count_container.setLayout(count_block)
        counts_row.addWidget(count_container)
        delay_block = QVBoxLayout()
        delay_block.setSpacing(2)
        delay_block.setContentsMargins(0, 0, 0, 0)
        delay_block.addWidget(make_field_label(tr('close_after_delay_label')))
        delay_spin = NumberSpinBox(1, 60, self._close_after_delay)
        delay_spin.setFixedHeight(38)

        def _on_delay_changed(val):
            self._close_after_delay = val
        delay_spin.valueChanged.connect(_on_delay_changed)
        delay_block.addWidget(delay_spin)
        delay_container = QWidget()
        delay_container.setLayout(delay_block)
        delay_container.setVisible(self._close_after)
        counts_row.addWidget(delay_container)
        self._delay_container = delay_container
        counts_row.addStretch()
        loader_btn = QPushButton('⚡ Loader')
        loader_btn.setObjectName('loaderBtn')
        loader_btn.setFixedHeight(38)
        loader_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        loader_btn.clicked.connect(open_loader)
        counts_row.addWidget(loader_btn, 0, Qt.AlignmentFlag.AlignBottom)
        bl.addLayout(counts_row)
        bl.addSpacing(4)
        bl.addWidget(make_field_label(tr('plan_selection_title')))
        plan_row = QHBoxLayout()
        plan_group = QButtonGroup(self)
        rb1 = QRadioButton(tr('plan_option_3days'))
        rb2 = QRadioButton(tr('plan_option_7days'))
        rb1.setChecked(self._selected_plan == 1)
        rb2.setChecked(self._selected_plan == 2)
        plan_group.addButton(rb1, 1)
        plan_group.addButton(rb2, 2)
        plan_row.addWidget(rb1)
        plan_row.addWidget(rb2)
        plan_row.addStretch()
        bl.addLayout(plan_row)

        def _on_plan_changed(btn_id):
            self._selected_plan = btn_id
        plan_group.idClicked.connect(_on_plan_changed)
        bl.addSpacing(4)
        err_label = QLabel('')
        err_label.setObjectName('errorLabel')
        bl.addWidget(err_label)
        bl.addStretch()
        start_btn = make_btn(tr('btn_start'), 'primary')

        def start():
            browser = browser_entry.text().strip()
            if browser == tr('browser_path_prompt'):
                browser = ''
            browser = browser.replace('"', '').replace("'", '')
            if browser and (not os.path.exists(browser)):
                err_label.setText(tr('invalid_path'))
                return
            passw = pass_entry.text().strip()
            if not passw:
                passw = generate_random_password()
            elif not is_valid_password(passw):
                err_label.setText(tr('password_not_meeting_requirements'))
                return
            proxy = proxy_entry.text().strip()
            if proxy == 'http://host:port':
                proxy = ''
            if proxy:
                ok, msg = self.lib.testProxy(proxy)
                if not ok:
                    err_label.setText(str(msg))
                    return
            count = count_spin.value()
            plan = '2' if plan_group.checkedId() == 2 else '1'
            save_config(browser, passw, proxy, count, plan)
            self._show_log(browser, passw, proxy, count, plan)
        start_btn.clicked.connect(start)
        bl.addWidget(start_btn)
        main.addWidget(body, 1)

    def _show_last_config(self, cfg):
        self._current_screen = ('last_config', cfg)
        main = self._make_scroll_content()
        self._build_header(main, tr('last_config_title'))
        body = QWidget()
        bl = QVBoxLayout(body)
        bl.setContentsMargins(30, 0, 30, 30)
        bl.setSpacing(0)
        card = QFrame()
        card.setObjectName('card')
        cl = QVBoxLayout(card)
        cl.setContentsMargins(20, 10, 20, 10)
        rows = [(tr('browser_label'), cfg.get('browser_path') or tr('default_browser')), (tr('password_label_display'), cfg.get('password', '')), (tr('proxy_label_display'), cfg.get('proxy') or tr('no_proxy')), (tr('accounts_label'), str(cfg.get('execution_count', 1))), (tr('plan_label'), tr('seven_days') if cfg.get('plan') == '2' else tr('three_days'))]
        for label, val in rows:
            row = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setFixedWidth(160)
            lbl.setStyleSheet(f'color: {TEXT_DIM}; font-size: 9pt;')
            val_lbl = QLabel(val)
            row.addWidget(lbl)
            row.addWidget(val_lbl)
            row.addStretch()
            cl.addLayout(row)
        bl.addWidget(card)
        bl.addSpacing(16)
        use_btn = make_btn(tr('btn_use_last_config'), 'success')
        use_btn.clicked.connect(lambda: self._start_with_config(cfg))
        bl.addWidget(use_btn)
        bl.addSpacing(8)
        new_btn = make_btn(tr('btn_new_configuration'), 'secondary')
        new_btn.clicked.connect(self._show_config)
        bl.addWidget(new_btn)
        bl.addStretch()
        main.addWidget(body, 1)

    def _start_with_config(self, cfg):
        self._show_log(cfg.get('browser_path', ''), cfg.get('password', ''), cfg.get('proxy', ''), cfg.get('execution_count', 1), cfg.get('plan', '1'))

    def _cleanup_thread(self):
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
                pass
        self._thread = None
        self._worker = None

    def _show_log(self, browser_path, passw, proxy, count, plan):
        self._current_screen = ('log', (browser_path, passw, proxy, count, plan))
        plan_name = tr('plan_option_7days') if plan == '2' else tr('plan_option_3days')
        self._current_plan_label = plan_name
        self._current_browser_label = os.path.basename(browser_path) if browser_path else ''
        main = self._make_scroll_content()
        self._build_header(main, tr('running_header').format(plan_name=plan_name, count=count))
        body = QWidget()
        bl = QVBoxLayout(body)
        bl.setContentsMargins(30, 0, 30, 20)
        bl.setSpacing(6)
        self._bar_widget = SegmentedBarWidget()
        bl.addWidget(self._bar_widget)
        step_row = QHBoxLayout()
        self._step_label = QLabel(tr('step_starting'))
        self._step_label.setObjectName('stepLabel')
        step_row.addWidget(self._step_label)
        step_row.addStretch()
        self._progress_label = QLabel(f'0 / {count}')
        self._progress_label.setObjectName('progressLabel')
        step_row.addWidget(self._progress_label)
        bl.addLayout(step_row)
        self._log_text = QTextEdit()
        self._log_text.setObjectName('logText')
        self._log_text.setReadOnly(True)
        bl.addWidget(self._log_text, 1)
        btn_row = QHBoxLayout()
        self._btn_cancel = make_btn(tr('btn_cancel'), 'danger')
        self._cancel_event = threading.Event()

        def _cancel():
            self._cancel_event.set()
            self._btn_cancel.setText(tr('btn_cancelling'))
            self._btn_cancel.setEnabled(False)
        self._btn_cancel.clicked.connect(_cancel)
        btn_row.addWidget(self._btn_cancel)
        btn_row.addStretch()
        self._btn_save = make_btn(tr('btn_save_config'), 'secondary')
        self._btn_save.setEnabled(False)
        self._btn_save.clicked.connect(lambda: save_config(browser_path, passw, proxy, count, plan))
        btn_row.addWidget(self._btn_save)
        self._btn_new = make_btn(tr('btn_new_config'), 'secondary')
        self._btn_new.setEnabled(False)
        self._btn_new.clicked.connect(self._show_config)
        btn_row.addWidget(self._btn_new)
        bl.addLayout(btn_row)
        main.addWidget(body, 1)
        self._log_colors = {'info': TEXT, 'success': SUCCESS, 'warning': WARNING, 'error': ERROR, 'accent': ACCENT, 'dim': TEXT_DIM}
        self._completed = 0
        self._total = count
        self._log_queue = queue.Queue()
        self._poll_timer.start(100)
        STEPS_PER_ACCOUNT = 5
        total_steps = count * STEPS_PER_ACCOUNT
        self._step_counter = 0
        self._prog_maximum = total_steps
        STEP_MAP = {tr('opening_browser'): 1, tr('filling_form'): 1, tr('waiting_captcha'): 1, tr('submitting_form'): 1}
        self._step_map = STEP_MAP
        self._cleanup_thread()
        self._worker = AutomationWorker(plan, passw, count, browser_path, self._cancel_event, self._silent_mode, self._close_after, self._close_after_delay, self._fill_speed)
        self._thread = QThread()
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.log_signal.connect(lambda m, l: self._log_queue.put(('log', m, l)))
        self._worker.step_signal.connect(lambda m: self._log_queue.put(('step', m, None)))
        self._worker.done_signal.connect(lambda a, c: self._log_queue.put(('done', a, c)))
        self._worker.done_signal.connect(self._thread.quit)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()
        if hasattr(self, '_menu_bar') and self._menu_bar:
            self._menu_bar.setEnabled(False)
            self._menu_bar.setStyleSheet('QWidget { color: rgba(255,255,255,0.25); }')

    def _poll_log(self):
        try:
            while True:
                item = self._log_queue.get_nowait()
                kind = item[0]
                if kind == 'log':
                    _, msg, level = item
                    self._append_log(msg, level)
                    if level == 'success' and '✓' in msg and (tr('registration_success') in msg):
                        self._completed += 1
                        self._progress_label.setText(f'{self._completed} / {self._total}')
                        if self._bar_widget:
                            self._bar_widget.set_pct(self._completed * 5 / max(self._prog_maximum, 1))
                elif kind == 'step':
                    _, msg, _ = item
                    self._step_label.setText(msg)
                    step_map = getattr(self, '_step_map', {})
                    if msg in step_map:
                        self._step_counter += step_map[msg]
                        if self._bar_widget:
                            self._bar_widget.set_pct(self._step_counter / max(self._prog_maximum, 1))
                elif kind == 'done':
                    _, successful_accounts, cancelled = item
                    self._poll_timer.stop()
                    all_failed = not cancelled and len(successful_accounts) == 0
                    if self._bar_widget:
                        self._bar_widget.set_pct(1.0)
                        if cancelled:
                            self._bar_widget.set_state('cancelled')
                        elif all_failed:
                            self._bar_widget.set_state('error')
                        else:
                            self._bar_widget.set_state('success')
                    if cancelled:
                        self._step_label.setText(tr('script_cancelled'))
                        self._step_label.setStyleSheet(f'color: {WARNING};')
                    else:
                        self._step_label.setText(tr('step_all_done'))
                        self._step_label.setStyleSheet(f'color: {SUCCESS};')
                    self._btn_cancel.setEnabled(False)
                    self._btn_new.setEnabled(True)
                    self._btn_save.setEnabled(True)
                    if hasattr(self, '_menu_bar') and self._menu_bar:
                        self._menu_bar.setEnabled(True)
                        self._menu_bar.setStyleSheet('')
                    self._show_results(successful_accounts)
                    return
        except queue.Empty:
            pass

    def _append_log(self, msg, level='info'):
        color = self._log_colors.get(level, TEXT)
        self._log_text.setTextColor(QColor(color))
        self._log_text.append(msg)
        self._log_text.verticalScrollBar().setValue(self._log_text.verticalScrollBar().maximum())

    def _show_results(self, successful_accounts):
        if not successful_accounts:
            return
        self._append_log(f'\n{'═' * 40}', 'dim')
        self._append_log(f'  {tr('accounts_created')} {len(successful_accounts)}', 'accent')
        self._append_log(f'{'═' * 40}', 'dim')
        for acc in successful_accounts:
            self._append_log(f'  📧 {tr('email_label')} {acc['email']}', 'success')
            self._append_log(f'  🔑 {tr('password_display_label')} {acc['password']}', 'success')
            self._append_log('', 'info')

    def _show_accounts(self):
        dlg = AccountsDialog(self)
        dlg.exec()

    def _check_updates_bg(self):

        def run():
            old_exe = os.path.join(get_base(), 'mainrev_old.exe')
            if os.path.exists(old_exe):
                try:
                    os.remove(old_exe)
                except:
                    pass
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
            req_path = os.path.join(base, 'requirements.txt')
            if not os.path.exists(req_path):
                return
            try:
                import importlib.metadata as meta
            except ImportError:
                import importlib_metadata as meta
            with open(req_path, 'r', encoding='utf-8') as f:
                lines = [l.strip() for l in f if l.strip() and (not l.startswith('#'))]
            missing = []
            for line in lines:
                pkg = line.split('==')[0].split('>=')[0].split('<=')[0].split('!=')[0].split('~=')[0].strip()
                try:
                    meta.version(pkg)
                except Exception:
                    try:
                        meta.version(pkg.replace('-', '_'))
                    except Exception:
                        missing.append(line)
            if missing:
                if getattr(sys, 'frozen', False):
                    python = os.path.join(os.path.dirname(sys.executable), 'python.exe')
                    if not os.path.exists(python):
                        return
                else:
                    python = sys.executable
                subprocess.run([python, '-m', 'pip', 'install'] + missing, capture_output=True)
        threading.Thread(target=run, daemon=True).start()

    def _download_missing_langs(self):

        def run():
            base = get_base()
            for lang in TRANSLATIONS_LANGS:
                path = os.path.join(base, 'translations', f'{lang}.json')
                if not os.path.exists(path):
                    url = f'{GITHUB_RAW}/translations/{lang}.json'
                    download_file(url, path)
        threading.Thread(target=run, daemon=True).start()

    def _show_update(self, local, remote):
        dlg = UpdateDialog(local, remote, self)
        dlg.exec()
if __name__ == '__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = App()
    window.show()
    sys.exit(app.exec())