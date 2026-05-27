import tkinter as tk
from tkinter import ttk
import requests
import hashlib
import os
import sys
import subprocess
import tempfile
import threading
import winreg
import glob
import time
import uuid
import ctypes
import math
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import pyautogui
import pygetwindow as gw
import win32gui
import win32api
import win32con

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.05

# ── Force Admin ───────────────────────────────────────────────────────────────
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    ctypes.windll.user32.MessageBoxW(
        0,
        "You must run this program as Administrator.\n\nRight-click RainyInstaller.exe and select 'Run as administrator'.",
        "Administrator Required",
        0x10
    )
    sys.exit()

# ── Config ────────────────────────────────────────────────────────────────────
API_BASE = "https://rainy-backend1-production.up.railway.app"
APP_NAME = "Rainy.solutions Installer"
MASTER_KEY = "29d201e746983999afad5e6783f6b4a6"
current_tmp_path = None

# ── Colors ────────────────────────────────────────────────────────────────────
BG       = "#080808"
SURFACE  = "#111111"
BORDER   = "#222222"
BORDER2  = "#2a2a2a"
ACCENT   = "#ffffff"
ACCENT2  = "#cccccc"
TEXT     = "#f0f0f0"
MUTED    = "#555555"
MUTED2   = "#888888"
SUCCESS  = "#44ff88"
ERROR    = "#ff4444"

# ── HWID ──────────────────────────────────────────────────────────────────────
def get_hwid():
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography")
        machine_guid, _ = winreg.QueryValueEx(key, "MachineGuid")
        return hashlib.sha256(machine_guid.encode()).hexdigest()
    except:
        return hashlib.sha256(str(uuid.getnode()).encode()).hexdigest()

# ── Input lock ────────────────────────────────────────────────────────────────
_input_locked = False

def lock_input():
    global _input_locked
    try:
        ctypes.windll.user32.BlockInput(True)
        _input_locked = True
    except:
        pass

def unlock_input():
    global _input_locked
    try:
        ctypes.windll.user32.BlockInput(False)
        _input_locked = False
    except:
        pass

# ── Decryption ────────────────────────────────────────────────────────────────
def decrypt_script(encrypted_bytes, license_key):
    digest = hashlib.sha256((MASTER_KEY + license_key.upper()).encode()).digest()
    iv = encrypted_bytes[:16]
    auth_tag = encrypted_bytes[16:32]
    ciphertext = encrypted_bytes[32:]
    decryptor = Cipher(
        algorithms.AES(digest),
        modes.GCM(iv, auth_tag),
        backend=default_backend()
    ).decryptor()
    return decryptor.update(ciphertext) + decryptor.finalize()

# ── Find Zen Studio ───────────────────────────────────────────────────────────
def find_zen_studio():
    user_profile = os.environ.get('USERPROFILE', os.path.expanduser('~'))
    desktop = os.path.join(user_profile, 'Desktop')
    downloads = os.path.join(user_profile, 'Downloads')
    appdata = os.environ.get('APPDATA', '')
    localappdata = os.environ.get('LOCALAPPDATA', '')
    sep = os.sep
    pf = 'C:' + sep + 'Program Files'
    pf86 = 'C:' + sep + 'Program Files (x86)'
    common_paths = [
        pf + sep + 'Zen Studio' + sep + 'ZenStudio.exe',
        pf86 + sep + 'Zen Studio' + sep + 'ZenStudio.exe',
        pf + sep + 'Cronus' + sep + 'Zen Studio' + sep + 'ZenStudio.exe',
        pf86 + sep + 'Cronus' + sep + 'Zen Studio' + sep + 'ZenStudio.exe',
        pf + sep + 'CronusZen' + sep + 'ZenStudio.exe',
        pf86 + sep + 'CronusZen' + sep + 'ZenStudio.exe',
        'C:' + sep + 'ZenStudio' + sep + 'ZenStudio.exe',
        'C:' + sep + 'Cronus' + sep + 'Zen Studio' + sep + 'ZenStudio.exe',
        os.path.join(desktop, 'ZenStudio.exe'),
        os.path.join(desktop, 'Zen Studio', 'ZenStudio.exe'),
        os.path.join(desktop, 'Cronus Zen', 'ZenStudio.exe'),
        os.path.join(downloads, 'ZenStudio.exe'),
        os.path.join(downloads, 'Zen Studio', 'ZenStudio.exe'),
        os.path.join(appdata, 'ZenStudio', 'ZenStudio.exe'),
        os.path.join(localappdata, 'ZenStudio', 'ZenStudio.exe'),
        os.path.join(localappdata, 'Cronus', 'Zen Studio', 'ZenStudio.exe'),
    ]
    for p in common_paths:
        if p and os.path.exists(p):
            return p
    try:
        for hive in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
            for reg_path in [
                'SOFTWARE' + sep + 'Microsoft' + sep + 'Windows' + sep + 'CurrentVersion' + sep + 'Uninstall',
                'SOFTWARE' + sep + 'WOW6432Node' + sep + 'Microsoft' + sep + 'Windows' + sep + 'CurrentVersion' + sep + 'Uninstall',
            ]:
                try:
                    key = winreg.OpenKey(hive, reg_path)
                    for i in range(winreg.QueryInfoKey(key)[0]):
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            subkey = winreg.OpenKey(key, subkey_name)
                            try:
                                name, _ = winreg.QueryValueEx(subkey, 'DisplayName')
                                if 'zen' in name.lower() or 'cronus' in name.lower():
                                    try:
                                        install_loc, _ = winreg.QueryValueEx(subkey, 'InstallLocation')
                                        candidate = os.path.join(install_loc, 'ZenStudio.exe')
                                        if os.path.exists(candidate):
                                            return candidate
                                    except:
                                        pass
                                    try:
                                        exe, _ = winreg.QueryValueEx(subkey, 'DisplayIcon')
                                        exe = exe.split(',')[0].strip('"')
                                        if os.path.exists(exe) and 'zen' in exe.lower():
                                            return exe
                                    except:
                                        pass
                            except:
                                pass
                        except:
                            continue
                except:
                    pass
    except:
        pass
    drives = ['C:', 'D:', 'E:', 'F:']
    for drive in drives:
        try:
            results = glob.glob(drive + sep + '**' + sep + 'ZenStudio.exe', recursive=True)
            if results:
                return results[0]
        except:
            pass
    return None


def find_zen_hwnd():
    """Find Zen Studio window handle."""
    result = []
    def callback(hwnd, _):
        title = win32gui.GetWindowText(hwnd)
        if "zen" in title.lower() and win32gui.IsWindowVisible(hwnd):
            rect = win32gui.GetWindowRect(hwnd)
            w = rect[2] - rect[0]
            if w > 200:
                result.append(hwnd)
    win32gui.EnumWindows(callback, None)
    return result[0] if result else None


# ── Automate Zen Studio ───────────────────────────────────────────────────────
def automate_zen_studio(zen_path, gpc_path):
    proc = subprocess.Popen([zen_path, gpc_path])

    # Wait for Zen Studio window
    zen_window = None
    for _ in range(30):
        time.sleep(1)
        for win in gw.getAllWindows():
            if "zen" in win.title.lower() and win.width > 200:
                zen_window = win
                break
        if zen_window:
            break

    if not zen_window:
        proc.kill()
        raise Exception("Zen Studio did not open. Please install Zen Studio first.")

    # Wait for full load
    time.sleep(4)

    # Force maximize using win32 directly
    try:
        hwnd = win32gui.FindWindow(None, zen_window.title)
        win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
        time.sleep(1.5)
        # Re-get window after maximize
        for win in gw.getAllWindows():
            if "zen" in win.title.lower() and win.width > 200:
                zen_window = win
                break
    except:
        try:
            zen_window.maximize()
            time.sleep(1.5)
        except:
            pass

    # Bring to front
    try:
        zen_window.activate()
        time.sleep(0.5)
    except:
        pass

    wx = zen_window.left
    wy = zen_window.top
    ww = zen_window.width
    wh = zen_window.height

    # ── Helpers defined INSIDE the function with correct indentation ──
    def locked_click(x, y):
        pyautogui.moveTo(x, y, duration=0.15)
        time.sleep(0.1)
        pyautogui.click(x, y)
        time.sleep(0.1)

    def locked_drag(x1, y1, x2, y2):
        pyautogui.moveTo(x1, y1, duration=0.2)
        pyautogui.mouseDown()
        time.sleep(0.2)
        pyautogui.moveTo(x2, y2, duration=0.5)
        time.sleep(0.2)
        pyautogui.mouseUp()

    try:
        # Click Programmer tab
        locked_click(wx + int(ww * 0.50), wy + int(wh * 0.095))
        time.sleep(1.5)

        # Click 3 lines button
        locked_click(wx + int(ww * 0.038), wy + int(wh * 0.355))
        time.sleep(1.5)

        # Click first file in list
        file_x = wx + int(ww * 0.75)
        file_y = wy + int(wh * 0.19)
        locked_click(file_x, file_y)
        time.sleep(0.5)

        # Drag to slot 2
        slot2_x = wx + int(ww * 0.72)
        slot2_y = wy + int(wh * 0.67)
        locked_drag(file_x, file_y, slot2_x, slot2_y)
        time.sleep(1.5)

        # Click Play button
        locked_click(wx + int(ww * 0.038), wy + int(wh * 0.520))
        time.sleep(1)

        # Wait for success popup
        for _ in range(20):
            time.sleep(0.5)
            for win in gw.getAllWindows():
                title = win.title.lower()
                if any(word in title for word in ["success", "complete", "programm", "written", "ok"]):
                    try:
                        win.close()
                    except:
                        pass
                    break
            pyautogui.press("enter")

    except Exception as e:
        unlock_input()
        raise e

    # Force close Zen Studio
    try:
        hwnd = win32gui.FindWindow(None, zen_window.title)
        win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
    except:
        pass
    time.sleep(0.2)
    try:
        proc.terminate()
    except:
        pass
    try:
        proc.kill()
    except:
        pass


# ── Animated Background ───────────────────────────────────────────────────────
class AnimatedBackground(tk.Canvas):
    def __init__(self, parent, w, h, **kwargs):
        super().__init__(parent, width=w, height=h, bg=BG,
                         highlightthickness=0, **kwargs)
        self.w = w
        self.h = h
        self.lines = []
        self._init_lines()
        self._animate()

    def _init_lines(self):
        import random
        random.seed(99)
        for _ in range(40):
            x1 = random.randint(-100, self.w + 100)
            y1 = random.randint(-100, self.h + 100)
            angle = random.uniform(-45, 45)
            length = random.randint(60, 180)
            speed = random.uniform(0.8, 2.5)
            alpha = random.uniform(0.05, 0.18)
            dx = math.cos(math.radians(angle)) * speed
            dy = math.sin(math.radians(angle)) * speed
            v = int(255 * alpha * 2.5)
            v = min(v, 255)
            color = f"#{v:02x}{v:02x}{v:02x}"
            lid = self.create_line(x1, y1, x1 + length, y1 + length,
                                   fill=color, width=1)
            self.lines.append({'id': lid, 'x': x1, 'y': y1,
                                'dx': dx, 'dy': dy, 'length': length,
                                'angle': angle})

    def _animate(self):
        for l in self.lines:
            l['x'] += l['dx']
            l['y'] += l['dy']
            if l['x'] > self.w + 120: l['x'] = -120
            if l['x'] < -120: l['x'] = self.w + 120
            if l['y'] > self.h + 120: l['y'] = -120
            if l['y'] < -120: l['y'] = self.h + 120
            ex = l['x'] + math.cos(math.radians(l['angle'])) * l['length']
            ey = l['y'] + math.sin(math.radians(l['angle'])) * l['length']
            self.coords(l['id'], l['x'], l['y'], ex, ey)
        self.after(16, self._animate)


# ── Shimmer Progress Bar ──────────────────────────────────────────────────────
class ShimmerBar(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, height=4, bg="#0d0d1a", **kwargs)
        self._running = False
        self._bright = False

    def start(self):
        self._running = True
        self._loop()

    def stop(self):
        self._running = False
        self.configure(bg="#0d0d1a")

    def _loop(self):
        if not self._running:
            return
        self._bright = not self._bright
        self.configure(bg="white" if self._bright else "#0d0d1a")
        self.after(60, self._loop)


# ── Step Widget ───────────────────────────────────────────────────────────────
class StepRow(tk.Frame):
    def __init__(self, parent, number, title, subtitle, **kwargs):
        super().__init__(parent, bg=SURFACE, **kwargs)
        self.number = number
        self.title = title
        self.subtitle = subtitle
        self._active = False
        self._done = False
        self._build()

    def _build(self):
        self.num_canvas = tk.Canvas(self, width=36, height=36,
                                     bg=SURFACE, highlightthickness=0)
        self.num_canvas.pack(side="left", padx=(0, 12))
        self._draw_num()

        text_frame = tk.Frame(self, bg=SURFACE)
        text_frame.pack(side="left", fill="x", expand=True)
        self.title_lbl = tk.Label(text_frame, text=self.title.upper(),
                                   bg=SURFACE, fg=MUTED,
                                   font=("Segoe UI", 8, "bold"))
        self.title_lbl.pack(anchor="w")
        self.sub_lbl = tk.Label(text_frame, text=self.subtitle,
                                 bg=SURFACE, fg=MUTED,
                                 font=("Segoe UI", 8))
        self.sub_lbl.pack(anchor="w")

    def _draw_num(self):
        c = self.num_canvas
        c.delete("all")
        if self._done:
            c.create_oval(2, 2, 34, 34, fill=ACCENT, outline="")
            c.create_text(18, 18, text="✓", fill=BG, font=("Segoe UI", 12, "bold"))
        elif self._active:
            c.create_oval(2, 2, 34, 34, fill=ACCENT, outline=ACCENT2, width=2)
            c.create_text(18, 18, text=str(self.number), fill=BG, font=("Segoe UI", 10, "bold"))
        else:
            c.create_oval(2, 2, 34, 34, fill="#141414", outline=BORDER, width=1)
            c.create_text(18, 18, text=str(self.number), fill=MUTED, font=("Segoe UI", 10))

    def set_active(self, subtitle=None):
        self._active = True
        self._done = False
        self.title_lbl.configure(fg=ACCENT2)
        self.sub_lbl.configure(fg=TEXT)
        if subtitle:
            self.sub_lbl.configure(text=subtitle)
        self._draw_num()

    def set_done(self):
        self._active = False
        self._done = True
        self.title_lbl.configure(fg=SUCCESS)
        self.sub_lbl.configure(fg=SUCCESS)
        self._draw_num()

    def set_error(self, msg=None):
        self._active = False
        self.title_lbl.configure(fg=ERROR)
        self.sub_lbl.configure(fg=ERROR)
        if msg:
            self.sub_lbl.configure(text=msg)
        self.num_canvas.delete("all")
        c = self.num_canvas
        c.create_oval(2, 2, 34, 34, fill="#1a0a0a", outline=ERROR, width=1)
        c.create_text(18, 18, text="✕", fill=ERROR, font=("Segoe UI", 12, "bold"))


# ── Main App ──────────────────────────────────────────────────────────────────
class RainyInstaller(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("920x760")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.attributes('-alpha', 0.0)
        self.hwid = get_hwid()
        self._installing = False
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build_ui()
        self._block_clipboard()
        self._fade_in()
        self.after(500, self._check_banned)

    def _block_clipboard(self):
        self.bind_all('<Control-c>', lambda e: 'break')
        self.bind_all('<Control-v>', lambda e: 'break')
        self.bind_all('<Control-x>', lambda e: 'break')
        self.bind_all('<Control-a>', lambda e: 'break')
        self.bind_all('<Button-3>', lambda e: 'break')
        self.bind_all('<Control-Insert>', lambda e: 'break')
        self.bind_all('<Shift-Insert>', lambda e: 'break')

    def _fade_in(self):
        a = self.attributes('-alpha')
        if a < 1.0:
            self.attributes('-alpha', min(a + 0.07, 1.0))
            self.after(18, self._fade_in)

    def _check_banned(self):
        threading.Thread(target=self._check_banned_bg, daemon=True).start()

    def _check_banned_bg(self):
        try:
            r = requests.post(f"{API_BASE}/api/check-hwid",
                              json={"hwid": self.hwid}, timeout=5)
            data = r.json()
            if data.get("banned"):
                self.after(0, lambda: self.step1.set_error("Your device is banned. Contact @8xgl."))
                self.after(0, lambda: self.install_btn.configure(state="disabled"))
        except:
            pass

    def _on_close(self):
        if self._installing:
            threading.Thread(target=emergency_cleanup,
                             args=(self.hwid,), daemon=True).start()
        else:
            self.destroy()

    def _build_ui(self):
        W, H = 920, 760
        self.geometry(f"{W}x{H}")

        # Animated background
        self.bg = AnimatedBackground(self, W, H)
        self.bg.place(x=0, y=0)

        # Content overlay
        content = tk.Frame(self, bg=BG)
        content.place(x=0, y=0, width=W, height=H)

        # ── Header ──
        header = tk.Frame(content, bg=BG)
        header.pack(pady=(28, 0))

        tk.Label(header, text="RAINY.SOLUTIONS",
                 bg=BG, fg=ACCENT,
                 font=("Segoe UI", 18, "bold")).pack()
        tk.Label(header, text="S C R I P T   I N S T A L L E R",
                 bg=BG, fg=MUTED,
                 font=("Segoe UI", 7)).pack(pady=(3, 0))

        # ── Thin divider ──
        tk.Frame(content, bg=BORDER, height=1).pack(fill="x", padx=40, pady=(14, 0))

        # ── Main card ──
        card = tk.Frame(content, bg=SURFACE,
                        highlightthickness=1, highlightbackground=BORDER)
        card.pack(padx=40, pady=16, fill="x")

        # Key + script row
        top_row = tk.Frame(card, bg=SURFACE)
        top_row.pack(fill="x", padx=20, pady=(16, 0))

        # Key input - left
        key_col = tk.Frame(top_row, bg=SURFACE)
        key_col.pack(side="left", fill="x", expand=True, padx=(0, 8))
        tk.Label(key_col, text="LICENSE KEY", bg=SURFACE, fg=MUTED,
                 font=("Segoe UI", 7)).pack(anchor="w")
        self.key_var = tk.StringVar()
        self.key_entry = tk.Entry(key_col, textvariable=self.key_var,
                                   bg="#0d0d0d", fg=ACCENT,
                                   insertbackground=ACCENT,
                                   relief="flat", font=("Courier New", 11),
                                   bd=0, highlightthickness=1,
                                   highlightbackground=BORDER2,
                                   highlightcolor=ACCENT)
        self.key_entry.pack(fill="x", ipady=7, pady=(4, 0))

        # Script - right
        script_col = tk.Frame(top_row, bg=SURFACE)
        script_col.pack(side="right", padx=(8, 0))
        tk.Label(script_col, text="SCRIPT", bg=SURFACE, fg=MUTED,
                 font=("Segoe UI", 7)).pack(anchor="w")
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("BW.TCombobox",
                         fieldbackground="#0d0d0d",
                         background="#0d0d0d",
                         foreground=ACCENT,
                         selectbackground="#222222",
                         selectforeground=ACCENT,
                         bordercolor=BORDER2,
                         arrowcolor=MUTED2)
        self.script_var = tk.StringVar()
        self.script_combo = ttk.Combobox(script_col, textvariable=self.script_var,
                                          state="readonly", font=("Segoe UI", 9),
                                          style="BW.TCombobox", width=16)
        self.script_combo.pack(pady=(4, 0), ipady=5)
        self._load_scripts()

        # Divider
        tk.Frame(card, bg=BORDER, height=1).pack(fill="x", padx=20, pady=14)

        # Steps
        steps_frame = tk.Frame(card, bg=SURFACE)
        steps_frame.pack(fill="x", padx=20, pady=(0, 4))

        self.step1 = StepRow(steps_frame, 1, "Preparing", "Checking system compatibility...")
        self.step1.pack(fill="x", pady=3)
        tk.Frame(steps_frame, bg=BORDER2, width=1, height=12).pack(anchor="w", padx=17)

        self.step2 = StepRow(steps_frame, 2, "Validating", "Validating your license key...")
        self.step2.pack(fill="x", pady=3)
        tk.Frame(steps_frame, bg=BORDER2, width=1, height=12).pack(anchor="w", padx=17)

        self.step3 = StepRow(steps_frame, 3, "Installing", "Programming your Cronus Zen...")
        self.step3.pack(fill="x", pady=3)
        tk.Frame(steps_frame, bg=BORDER2, width=1, height=12).pack(anchor="w", padx=17)

        self.step4 = StepRow(steps_frame, 4, "Finalizing", "Cleaning up and finishing...")
        self.step4.pack(fill="x", pady=(3, 16))

        # ── Install button ──
        self.install_btn = tk.Button(content, text="Install to Zen",
                                      bg=ACCENT, fg=BG,
                                      activebackground=ACCENT2,
                                      activeforeground=BG,
                                      relief="flat", font=("Segoe UI", 10, "bold"),
                                      cursor="hand2", command=self._start_install, bd=0)
        self.install_btn.pack(padx=40, fill="x", ipady=12)
        self.install_btn.bind("<Enter>", lambda e: self.install_btn.configure(bg=ACCENT2))
        self.install_btn.bind("<Leave>", lambda e: self.install_btn.configure(bg=ACCENT))

        # ── Bottom status bar ──
        bottom = tk.Frame(content, bg="#050505")
        bottom.pack(side="bottom", fill="x")

        self.shimmer = ShimmerBar(bottom)
        self.shimmer.pack(side="bottom", fill="x")

        status_row = tk.Frame(bottom, bg="#050505")
        status_row.pack(fill="x", padx=16, pady=(6, 6))

        self.status_var = tk.StringVar(value="Ready to install")
        self.status_lbl = tk.Label(status_row, textvariable=self.status_var,
                                    bg="#050505", fg=MUTED,
                                    font=("Segoe UI", 8), anchor="w")
        self.status_lbl.pack(side="left")

        tk.Label(status_row, text="rainy.solutions",
                 bg="#050505", fg=BORDER2,
                 font=("Segoe UI", 7)).pack(side="right")

    def _load_scripts(self):
        try:
            r = requests.get(f"{API_BASE}/api/scripts", timeout=5)
            scripts = r.json().get("scripts", [])
            self.script_combo["values"] = scripts
            if scripts:
                self.script_combo.current(0)
        except:
            self.script_combo["values"] = ["default"]
            self.script_combo.current(0)

    def _set_status(self, msg, color=None):
        self.after(0, lambda: self.status_var.set(msg))
        self.after(0, lambda: self.status_lbl.configure(fg=color or MUTED))

    def _start_install(self):
        key = self.key_var.get().strip().upper()
        script = self.script_var.get()
        if len(key) < 5:
            self._set_status("Please enter your license key.", ERROR)
            return
        self._installing = True
        self.install_btn.configure(state="disabled", bg="#3a1a6a")
        self.shimmer.start()
        threading.Thread(target=self._install, args=(key, script), daemon=True).start()

    def _install(self, key, script):
        global current_tmp_path
        tmp_path = None
        try:
            # Step 1: Find Zen Studio
            self.after(0, lambda: self.step1.set_active("Checking system compatibility..."))
            self._set_status("Looking for Zen Studio...", ACCENT2)
            zen_path = find_zen_studio()
            if not zen_path:
                self.after(0, lambda: self.step1.set_error("Zen Studio not found. Please install it first."))
                self._set_status("Zen Studio not found.", ERROR)
                self.after(0, lambda: self._done(success=False))
                return
            self.after(0, self.step1.set_done)

            # Step 2: Validate key
            self.after(0, lambda: self.step2.set_active("Validating your license key..."))
            self._set_status("Validating key...", ACCENT2)
            response = requests.post(
                f"{API_BASE}/api/redeem",
                json={"key": key, "script": script, "hwid": self.hwid},
                timeout=15
            )
            if response.status_code == 403:
                error = response.json().get("error", "Invalid key.")
                self.after(0, lambda: self.step2.set_error(error))
                self._set_status(error, ERROR)
                self.after(0, lambda: self._done(success=False))
                return
            if response.status_code != 200:
                self.after(0, lambda: self.step2.set_error("Server error. Please try again."))
                self._set_status("Server error.", ERROR)
                self.after(0, lambda: self._done(success=False))
                return
            self.after(0, self.step2.set_done)

            # Step 3: Install
            self.after(0, lambda: self.step3.set_active("Programming your Cronus Zen..."))
            self._set_status("Installing to your Cronus Zen — do not close...", ACCENT2)
            encrypted_bytes = response.content
            decrypted = decrypt_script(encrypted_bytes, key)
            tmp_fd, tmp_path = tempfile.mkstemp(suffix=".gpc")
            current_tmp_path = tmp_path
            with os.fdopen(tmp_fd, 'wb') as f:
                f.write(decrypted)
            automate_zen_studio(zen_path, tmp_path)
            self.after(0, self.step3.set_done)

            # Step 4: Cleanup
            self.after(0, lambda: self.step4.set_active("Cleaning up..."))
            self._set_status("Finalizing...", ACCENT2)
            try:
                os.remove(tmp_path)
                tmp_path = None
                current_tmp_path = None
            except:
                pass
            time.sleep(0.5)
            self.after(0, self.step4.set_done)

            self._set_status("✓ Script installed! Your Cronus Zen is ready.", SUCCESS)
            self.after(0, lambda: self._done(success=True))

        except requests.exceptions.ConnectionError:
            self._set_status("Cannot connect to server. Check your internet.", ERROR)
            self.after(0, lambda: self._done(success=False))
        except Exception as e:
            self._set_status(f"Error: {str(e)}", ERROR)
            self.after(0, lambda: self._done(success=False))
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except:
                    pass

    def _done(self, success=True):
        self._installing = False
        self.shimmer.stop()
        if success:
            self.install_btn.configure(state="disabled", bg="#1a3a1a",
                                        fg=SUCCESS, text="✓  Installation Complete")
        else:
            self.install_btn.configure(state="normal", bg=ACCENT, fg="white",
                                        text="⚡   Install to Zen")


if __name__ == "__main__":
    app = RainyInstaller()
    app.mainloop()
