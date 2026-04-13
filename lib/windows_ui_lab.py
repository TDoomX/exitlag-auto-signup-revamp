import os
import glob
import time
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

try:
    import winreg
except ImportError:
    winreg = None

from pywinauto import Application, Desktop


class WindowsUILab:
    """
    Helper genérico e seguro para automação/inspeção de janelas Windows
    dos seus próprios apps de teste ou utilitários locais.
    Inclui suporte completo para ExitLag.
    """

    REGISTRY_PATHS = [
        (getattr(winreg, "HKEY_LOCAL_MACHINE", None), r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (getattr(winreg, "HKEY_LOCAL_MACHINE", None), r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (getattr(winreg, "HKEY_CURRENT_USER", None), r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]

    COMMON_INSTALL_DIRS = [
        r"C:\Program Files",
        r"C:\Program Files (x86)",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs"),
        os.path.expandvars(r"%LOCALAPPDATA%"),
        os.path.expandvars(r"%APPDATA%"),
    ]

    def __init__(self, logger: Optional[logging.Logger] = None, backend: str = "uia"):
        self.logger = logger or logging.getLogger("WindowsUILab")
        self.backend = backend
        self.app: Optional[Application] = None
        self.main_window = None

    def log(self, msg: str):
        try:
            self.logger.info(msg)
        except Exception:
            pass

    def _normalize_exe_path(self, raw_value: str) -> Optional[str]:
        if not raw_value:
            return None

        value = str(raw_value).strip().strip('"')

        if ".exe" in value.lower():
            idx = value.lower().find(".exe")
            value = value[:idx + 4]

        value = os.path.expandvars(value)

        if os.path.isfile(value):
            return os.path.abspath(value)

        return None

    def find_executable(self, exe_names: List[str]) -> Optional[str]:
        exe_names_lower = {x.lower() for x in exe_names}
        self.log(f"[WindowsUILab] procurando executável: {exe_names}")

        if winreg is not None:
            for hive, root_path in self.REGISTRY_PATHS:
                if hive is None:
                    continue

                try:
                    with winreg.OpenKey(hive, root_path) as root:
                        sub_count = winreg.QueryInfoKey(root)[0]

                        for i in range(sub_count):
                            try:
                                subkey_name = winreg.EnumKey(root, i)
                                with winreg.OpenKey(root, subkey_name) as subkey:
                                    for value_name in ("DisplayIcon", "InstallLocation", "UninstallString"):
                                        try:
                                            raw, _ = winreg.QueryValueEx(subkey, value_name)
                                        except FileNotFoundError:
                                            continue
                                        except Exception:
                                            continue

                                        normalized = self._normalize_exe_path(raw)
                                        if normalized and Path(normalized).name.lower() in exe_names_lower:
                                            self.log(f"[WindowsUILab] encontrado no registry ({value_name}): {normalized}")
                                            return normalized

                                        if value_name == "InstallLocation":
                                            install_dir = os.path.expandvars(str(raw).strip())
                                            if os.path.isdir(install_dir):
                                                for exe in exe_names:
                                                    candidate = os.path.join(install_dir, exe)
                                                    if os.path.isfile(candidate):
                                                        candidate = os.path.abspath(candidate)
                                                        self.log(f"[WindowsUILab] encontrado em InstallLocation: {candidate}")
                                                        return candidate
                            except Exception:
                                continue
                except Exception:
                    continue

        for base in self.COMMON_INSTALL_DIRS:
            if not base or not os.path.isdir(base):
                continue

            for exe in exe_names:
                patterns = [
                    os.path.join(base, exe),
                    os.path.join(base, "*", exe),
                    os.path.join(base, "*", "*", exe),
                ]

                for pattern in patterns:
                    try:
                        for match in glob.glob(pattern):
                            if os.path.isfile(match):
                                match = os.path.abspath(match)
                                self.log(f"[WindowsUILab] encontrado em caminhos comuns: {match}")
                                return match
                    except Exception:
                        continue

        self.log("[WindowsUILab] executável não encontrado")
        return None

    def find_exitlag(self) -> Optional[str]:
        """Specifically find ExitLag executable using multiple strategies."""
        known_paths = [
            r"C:\Program Files\ExitLag\ExitLag.exe",
            r"C:\Program Files (x86)\ExitLag\ExitLag.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\ExitLag\ExitLag.exe"),
        ]
        for path in known_paths:
            if os.path.isfile(path):
                self.log(f"[ExitLag] found at: {path}")
                return path
        
        result = self.find_executable(["ExitLag.exe", "ExitLag"])
        if result:
            return result
        
        self.log("[ExitLag] executable not found")
        return None

    def launch_or_attach(self, exe_path: str):
        self.log(f"[WindowsUILab] iniciando/conectando: {exe_path}")

        try:
            self.app = Application(backend=self.backend).start(f'"{exe_path}"')
            self.log("[WindowsUILab] processo iniciado com sucesso")
            return self.app
        except Exception as e:
            msg = str(e)
            self.log(f"[WindowsUILab] falha ao iniciar; tentando attach: {msg}")

            if "740" in msg or "requires elevation" in msg.lower():
                raise RuntimeError(
                    "O executável selecionado requer privilégios de administrador para iniciar. "
                    "Abra o aplicativo manualmente como administrador e depois tente conectar, "
                    "ou use um aplicativo de teste sem elevação."
                )

        self.app = Application(backend=self.backend).connect(path=exe_path)
        self.log("[WindowsUILab] conectado a processo existente")
        return self.app

    def connect_by_pid(self, pid: int):
        self.app = Application(backend=self.backend).connect(process=pid)
        self.log(f"[WindowsUILab] conectado ao PID {pid}")
        return self.app

    def get_top_window(self, timeout: float = 5.0):
        """Get the top window of the application."""
        if not self.app:
            return None
        try:
            self.main_window = self.app.top_window()
            self.main_window.wait('visible', timeout=timeout)
            return self.main_window
        except Exception as e:
            self.log(f"Error getting top window: {e}")
            return None

    def focus_window(self, window=None):
        """Bring window to foreground."""
        target = window or self.main_window
        if not target:
            return False
        try:
            target.set_focus()
            time.sleep(0.2)
            return True
        except Exception:
            return False

    def wait_window(self, title_re: str, timeout: float = 15.0):
        self.log(f"[WindowsUILab] aguardando janela: {title_re}")
        end = time.time() + timeout

        while time.time() < end:
            try:
                win = Desktop(backend=self.backend).window(title_re=title_re)
                if win.exists(timeout=0.5):
                    self.main_window = win
                    self.log("[WindowsUILab] janela localizada")
                    return win
            except Exception:
                pass
            time.sleep(0.4)

        raise RuntimeError(f"janela não encontrada: {title_re}")

    def dump_controls(self, window=None, depth: int = 4):
        window = window or self.main_window
        if window is None:
            raise RuntimeError("nenhuma janela conectada")
        self.log("[WindowsUILab] dump de controles")
        window.print_control_identifiers(depth=depth)

    def list_controls(self, window=None) -> List[Dict[str, Any]]:
        window = window or self.main_window
        if window is None:
            raise RuntimeError("nenhuma janela conectada")

        items = []
        try:
            for d in window.descendants():
                try:
                    info = d.element_info
                    items.append({
                        "name": getattr(info, "name", ""),
                        "control_type": getattr(info, "control_type", ""),
                        "automation_id": getattr(info, "automation_id", ""),
                        "class_name": getattr(info, "class_name", ""),
                    })
                except Exception:
                    continue
        except Exception as e:
            self.log(f"[WindowsUILab] erro listando controles: {e}")

        return items

    def find_control(
        self,
        window=None,
        *,
        title: Optional[str] = None,
        title_re: Optional[str] = None,
        auto_id: Optional[str] = None,
        control_type: Optional[str] = None,
        class_name: Optional[str] = None,
        timeout: float = 1.0,
    ):
        window = window or self.main_window
        if window is None:
            raise RuntimeError("nenhuma janela conectada")

        kwargs = {}
        if title is not None:
            kwargs["title"] = title
        if title_re is not None:
            kwargs["title_re"] = title_re
        if auto_id is not None:
            kwargs["auto_id"] = auto_id
        if control_type is not None:
            kwargs["control_type"] = control_type
        if class_name is not None:
            kwargs["class_name"] = class_name

        ctrl = window.child_window(**kwargs)
        if ctrl.exists(timeout=timeout):
            return ctrl
        return None

    def find_first(self, window=None, selectors: Optional[List[Dict[str, Any]]] = None):
        window = window or self.main_window
        selectors = selectors or []

        for sel in selectors:
            try:
                ctrl = self.find_control(window=window, **sel)
                if ctrl is not None:
                    self.log(f"[WindowsUILab] controle encontrado via fallback: {sel}")
                    return ctrl
            except Exception:
                continue

        return None

    def set_text(self, control, value: str):
        control.set_focus()

        try:
            control.type_keys("^a{BACKSPACE}", set_foreground=True)
        except Exception:
            pass

        try:
            control.set_edit_text(value)
        except Exception:
            control.type_keys(value, with_spaces=True, set_foreground=True)

        self.log("[WindowsUILab] texto preenchido")

    def click(self, control):
        try:
            control.click_input()
        except Exception:
            control.invoke()

        self.log("[WindowsUILab] controle acionado")

    # ─── ExitLag Specific Methods ─────────────────────────────────────────

    def exitlag_logout(self, window=None) -> bool:
        """
        Attempt to logout from ExitLag if an account is active.
        Looks for logout button or menu item.
        """
        window = window or self.main_window
        if not window:
            self.log("[ExitLag] no window to perform logout")
            return False
        
        logout_selectors = [
            {"title": "Logout", "control_type": "Button"},
            {"title": "Sair", "control_type": "Button"},
            {"title_re": ".*Logout.*", "control_type": "Button"},
            {"title_re": ".*Sair.*", "control_type": "Button"},
            {"auto_id": "LogoutButton"},
            {"auto_id": "btnLogout"},
            {"class_name": "LogoutButton"},
        ]
        
        for selector in logout_selectors:
            try:
                logout_btn = self.find_control(window, **selector, timeout=0.5)
                if logout_btn and logout_btn.exists():
                    self.log("[ExitLag] logout button found, clicking...")
                    self.click(logout_btn)
                    time.sleep(1.5)
                    return True
            except Exception:
                continue
        
        try:
            profile_menu = self.find_control(
                window, 
                control_type="MenuItem",
                title_re=".*Profile.*|.*Conta.*",
                timeout=0.5
            )
            if profile_menu:
                self.click(profile_menu)
                time.sleep(0.5)
                logout_option = self.find_control(
                    window,
                    title_re=".*Logout.*|.*Sair.*",
                    timeout=0.5
                )
                if logout_option:
                    self.click(logout_option)
                    time.sleep(1.0)
                    return True
        except Exception:
            pass
        
        self.log("[ExitLag] could not find logout button — maybe already logged out")
        return False

    def exitlag_add_account(self, email: str, password: str, window=None) -> bool:
        """
        Add a new account to ExitLag.
        Assumes user is on the main screen.
        """
        window = window or self.main_window
        if not window:
            self.log("[ExitLag] no window to add account")
            return False
        
        add_selectors = [
            {"title": "Add Account", "control_type": "Button"},
            {"title": "Adicionar Conta", "control_type": "Button"},
            {"title_re": ".*Add.*Account.*", "control_type": "Button"},
            {"auto_id": "AddAccountButton"},
            {"class_name": "AddAccountButton"},
        ]
        
        add_btn = None
        for selector in add_selectors:
            add_btn = self.find_control(window, **selector, timeout=0.5)
            if add_btn and add_btn.exists():
                break
        
        if not add_btn:
            self.log("[ExitLag] could not find Add Account button")
            return False
        
        self.click(add_btn)
        time.sleep(0.8)
        
        email_selectors = [
            {"control_type": "Edit", "title_re": ".*Email.*|.*E-mail.*"},
            {"control_type": "Edit", "title_re": ".*Username.*|.*Usuário.*"},
            {"auto_id": "EmailBox"},
            {"auto_id": "UsernameBox"},
        ]
        
        email_field = self.find_first(window, email_selectors)
        if not email_field:
            self.log("[ExitLag] could not find email field")
            return False
        
        pass_selectors = [
            {"control_type": "Edit", "title_re": ".*Password.*|.*Senha.*"},
            {"auto_id": "PasswordBox"},
        ]
        
        all_edits = []
        try:
            all_edits = [c for c in window.descendants() if c.element_info.control_type == "Edit"]
            if len(all_edits) >= 2:
                pass_field = all_edits[1]
            else:
                pass_field = self.find_first(window, pass_selectors)
        except Exception:
            pass_field = self.find_first(window, pass_selectors)
        
        if not pass_field:
            self.log("[ExitLag] could not find password field")
            return False
        
        self.set_text(email_field, email)
        time.sleep(0.2)
        self.set_text(pass_field, password)
        time.sleep(0.2)
        
        login_selectors = [
            {"title": "Login", "control_type": "Button"},
            {"title": "Save", "control_type": "Button"},
            {"title": "Adicionar", "control_type": "Button"},
            {"title": "Sign In", "control_type": "Button"},
            {"auto_id": "LoginButton"},
            {"auto_id": "SaveButton"},
        ]
        
        login_btn = self.find_first(window, login_selectors)
        if login_btn:
            self.click(login_btn)
            time.sleep(1.0)
            self.log(f"[ExitLag] account added successfully for {email}")
            return True
        
        try:
            pass_field.type_keys("{ENTER}")
            time.sleep(1.0)
            self.log(f"[ExitLag] account added (Enter pressed) for {email}")
            return True
        except Exception:
            pass
        
        self.log("[ExitLag] could not complete account addition")
        return False

    def exitlag_full_login_flow(self, email: str, password: str, auto_logout: bool = True) -> bool:
        """
        Complete ExitLag login flow:
        1. Find/attach to ExitLag window
        2. Optionally logout existing account
        3. Add new account with credentials
        """
        exe_path = self.find_exitlag()
        if not exe_path:
            self.log("[ExitLag] executable not found")
            return False
        
        try:
            self.launch_or_attach(exe_path)
            time.sleep(1.5)
            
            self.main_window = self.get_top_window()
            if not self.main_window:
                self.log("[ExitLag] could not get main window")
                return False
            
            self.focus_window()
            time.sleep(0.5)
            
            if auto_logout:
                self.exitlag_logout()
                time.sleep(1.0)
            
            success = self.exitlag_add_account(email, password)
            return success
            
        except Exception as e:
            self.log(f"[ExitLag] error in full login flow: {e}")
            return False