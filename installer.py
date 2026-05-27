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
BG       = "#0a0a12"
SURFACE  = "#12121e"
BORDER   = "#2a1f4a"
ACCENT   = "#7c3aed"
ACCENT2  = "#a855f7"
TEXT     = "#e2e8f0"
MUTED    = "#4a4a6a"
SUCCESS  = "#44ffaa"
ERROR    = "#ff5566"

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
    common_paths = [
        r"C:\Program Files\Zen Studio\ZenStudio.exe",
        r"C:\Program Files (x86)\Zen Studio\ZenStudio.exe",
        r"C:\Program Files\Cronus\Zen Studio\ZenStudio.exe",
        r"C:\Program Files (x86)\Cronus\Zen Studio\ZenStudio.exe",
    ]
    for p in common_paths:
        if os.path.exists(p):
            return p
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                             r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
        for i in range(winreg.QueryInfoKey(key)[0]):
            try:
                subkey_name = winreg.EnumKey(key, i)
                subkey = winreg.OpenKey(key, subkey_name)
                name, _ = winreg.QueryValueEx(subkey, "DisplayName")
                if "zen" in name.lower():
                    install_loc, _ = winreg.QueryValueEx(subkey, "InstallLocation")
                    candidate = os.path.join(install_loc, "ZenStudio.exe")
                    if os.path.exists(candidate):
                        return candidate
            except:
                continue
    except:
        pass
    drives = ["C:", "D:", "E:"]
    for drive in drives:
        results = glob.glob(f"{drive}\\**\\ZenStudio.exe", recursive=True)
        if results:
            return results[0]
    return None

# ── Emergency cleanup ─────────────────────────────────────────────────────────
def emergency_cleanup(hwid):
    global current_tmp_path
    unlock_input()
    if current_tmp_path and os.path.exists(current_tmp_path):
        try:
            os.remove(current_tmp_path)
        except:
            pass
    try:
        requests.post(f"{API_BASE}/api/ban-hwid",
                      json={"hwid": hwid, "reason": "Closed installer during installation"},
                      timeout=5)
    except:
        pass
    ctypes.windll.user32.MessageBoxW(
        0,
        "Program closed during installation.\n\nYour device has been banned.\nIf this was a mistake contact @8xgl for a new key.\n\nYour PC will now restart.",
        "Installation Cancelled",
        0x10
    )
    time.sleep(2)
    os.system("shutdown /r /t 0")

# ── Automate Zen Studio ───────────────────────────────────────────────────────
def automate_zen_studio(zen_path, gpc_path):
    proc = subprocess.Popen([zen_path, gpc_path])

    # Wait for ANY window containing "zen" in title
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

    # Bring to front and maximize to get consistent coords
    try:
        zen_window.activate()
        time.sleep(0.5)
        zen_window.maximize()
        time.sleep(1)
    except:
        pass

    # Re-get window after maximize
    for win in gw.getAllWindows():
        if "zen" in win.title.lower() and win.width > 200:
            zen_window = win
            break

    wx = zen_window.left
    wy = zen_window.top
    ww = zen_window.width
    wh = zen_window.height

    # Click Programmer tab
    pyautogui.click(wx + int(ww * 0.50), wy + int(wh * 0.095))
    time.sleep(1.5)

    # Click 3 lines button
    pyautogui.click(wx + int(ww * 0.038), wy + int(wh * 0.355))
    time.sleep(1.5)

    # Click first file in list
    file_x = wx + int(ww * 0.75)
    file_y = wy + int(wh * 0.19)
    pyautogui.click(file_x, file_y)
    time.sleep(0.5)

    # Drag to slot 2
    slot2_x = wx + int(ww * 0.72)
    slot2_y = wy + int(wh * 0.67)
    pyautogui.moveTo(file_x, file_y, duration=0.3)
    pyautogui.mouseDown()
    time.sleep(0.3)
    pyautogui.moveTo(slot2_x, slot2_y, duration=0.6)
    time.sleep(0.3)
    pyautogui.mouseUp()
    time.sleep(1.5)

    # Click Play button
    pyautogui.click(wx + int(ww * 0.038), wy + int(wh * 0.520))
    time.sleep(1)

    # Wait for success popup
    for _ in range(40):
        time.sleep(0.5)
        for win in gw.getAllWindows():
            title = win.title.lower()
            if any(word in title for word in ["success", "complete", "programm", "written", "ok"]):
                try:
                    win.close()
                except:
                    pass
                break
        pyautogui.press('enter')

    # Force close Zen Studio
    try:
        proc.terminate()
    except:
        pass
    time.sleep(0.5)
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
            r = int(124 * alpha * 3)
            g = int(58 * alpha * 3)
            b = int(237 * alpha * 3)
            r = min(r, 255); g = min(g, 255); b = min(b, 255)
            color = f"#{r:02x}{g:02x}{b:02x}"
            lid = self.create_line(x1, y1, x1+length, y1+length,
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
            c.create_text(18, 18, text="✓", fill="white", font=("Segoe UI", 12, "bold"))
        elif self._active:
            c.create_oval(2, 2, 34, 34, fill=ACCENT, outline=ACCENT2, width=2)
            c.create_text(18, 18, text=str(self.number), fill="white", font=("Segoe UI", 10, "bold"))
        else:
            c.create_oval(2, 2, 34, 34, fill="#1a1a2e", outline=BORDER, width=1)
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
        c.create_oval(2, 2, 34, 34, fill="#3a0a0a", outline=ERROR, width=1)
        c.create_text(18, 18, text="✕", fill=ERROR, font=("Segoe UI", 12, "bold"))

# ── Main App ──────────────────────────────────────────────────────────────────
class RainyInstaller(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("680x580")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.attributes('-alpha', 0.0)
        self.hwid = get_hwid()
        self._installing = False
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build_ui()
        self._fade_in()
        self.after(500, self._check_banned)

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
            unlock_input()
            self.destroy()

    def _build_ui(self):
        W, H = 680, 580

        # Animated background
        self.bg = AnimatedBackground(self, W, H)
        self.bg.place(x=0, y=0)

        # Content overlay
        content = tk.Frame(self, bg=BG)
        content.place(x=0, y=0, width=W, height=H)

        # ── Header ──
        header = tk.Frame(content, bg=BG)
        header.pack(pady=(28, 0))

        tk.Label(header, text="RAINY.SOLUTIONS", bg=BG, fg=ACCENT2,
                 font=("Segoe UI", 16, "bold")).pack(pady=(6, 0))
        tk.Label(header, text="I N S T A L L E R", bg=BG, fg=MUTED,
                 font=("Segoe UI", 8, "bold")).pack()
        tk.Label(header, text="Enhance your experience. Install. Inject. Dominate.",
                 bg=BG, fg=MUTED, font=("Segoe UI", 8)).pack(pady=(2, 0))

        # ── Main card ──
        card = tk.Frame(content, bg=SURFACE,
                        highlightthickness=1, highlightbackground=BORDER)
        card.pack(padx=40, pady=18, fill="x")

        # Key input
        key_frame = tk.Frame(card, bg=SURFACE)
        key_frame.pack(fill="x", padx=24, pady=(18, 0))
        tk.Label(key_frame, text="LICENSE KEY", bg=SURFACE, fg=MUTED,
                 font=("Segoe UI", 7, "bold")).pack(anchor="w")
        entry_wrap = tk.Frame(key_frame, bg=ACCENT, padx=1, pady=1)
        entry_wrap.pack(fill="x", pady=(4, 0))
        self.key_var = tk.StringVar()
        self.key_entry = tk.Entry(entry_wrap, textvariable=self.key_var,
                                   bg="#0d0d1a", fg=ACCENT2,
                                   insertbackground=ACCENT2,
                                   relief="flat", font=("Courier New", 12), bd=0)
        self.key_entry.pack(fill="x", ipady=8, padx=1, pady=1)

        # Script selector
        script_frame = tk.Frame(card, bg=SURFACE)
        script_frame.pack(fill="x", padx=24, pady=(12, 0))
        tk.Label(script_frame, text="SCRIPT", bg=SURFACE, fg=MUTED,
                 font=("Segoe UI", 7, "bold")).pack(anchor="w")
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("P.TCombobox",
                         fieldbackground="#0d0d1a", background="#0d0d1a",
                         foreground=ACCENT2, selectbackground=ACCENT,
                         selectforeground="white", bordercolor=ACCENT,
                         arrowcolor=ACCENT2)
        self.script_var = tk.StringVar()
        self.script_combo = ttk.Combobox(script_frame, textvariable=self.script_var,
                                          state="readonly", font=("Segoe UI", 10),
                                          style="P.TCombobox")
        self.script_combo.pack(fill="x", pady=(4, 0))
        self._load_scripts()

        # Divider
        tk.Frame(card, bg=BORDER, height=1).pack(fill="x", padx=24, pady=16)

        # Steps
        steps_frame = tk.Frame(card, bg=SURFACE)
        steps_frame.pack(fill="x", padx=24, pady=(0, 4))

        self.step1 = StepRow(steps_frame, 1, "Preparing", "Checking system compatibility...")
        self.step1.pack(fill="x", pady=4)
        tk.Frame(steps_frame, bg=BORDER, width=2, height=16).pack(anchor="w", padx=17)

        self.step2 = StepRow(steps_frame, 2, "Validating", "Validating your license key...")
        self.step2.pack(fill="x", pady=4)
        tk.Frame(steps_frame, bg=BORDER, width=2, height=16).pack(anchor="w", padx=17)

        self.step3 = StepRow(steps_frame, 3, "Installing", "Programming your Cronus Zen...")
        self.step3.pack(fill="x", pady=4)
        tk.Frame(steps_frame, bg=BORDER, width=2, height=16).pack(anchor="w", padx=17)

        self.step4 = StepRow(steps_frame, 4, "Finalizing", "Cleaning up and finishing...")
        self.step4.pack(fill="x", pady=(4, 18))

        # ── Install button ──
        self.install_btn = tk.Button(content, text="⚡   Install to Zen",
                                      bg=ACCENT, fg="white",
                                      activebackground=ACCENT2,
                                      activeforeground="white",
                                      relief="flat", font=("Segoe UI", 11, "bold"),
                                      cursor="hand2", command=self._start_install, bd=0)
        self.install_btn.pack(padx=40, fill="x", ipady=12)
        self.install_btn.bind("<Enter>", lambda e: self.install_btn.configure(bg=ACCENT2))
        self.install_btn.bind("<Leave>", lambda e: self.install_btn.configure(bg=ACCENT))

        # ── Footer badge ──
        badge = tk.Frame(content, bg=BG)
        badge.pack(pady=(10, 0))
        tk.Label(badge, text="🛡  Safe  •  Secure  •  Undetected",
                 bg=BG, fg=ACCENT2, font=("Segoe UI", 8, "bold")).pack()
        tk.Label(badge, text="Your system is protected.",
                 bg=BG, fg=MUTED, font=("Segoe UI", 7)).pack()

        # ── Bottom status bar ──
        bottom = tk.Frame(content, bg="#080810")
        bottom.pack(side="bottom", fill="x")

        self.status_var = tk.StringVar(value="Ready to install")
        self.status_lbl = tk.Label(bottom, textvariable=self.status_var,
                                    bg="#080810", fg=MUTED,
                                    font=("Segoe UI", 8), anchor="w")
        self.status_lbl.pack(side="left", padx=12, pady=6)

        self.shimmer = ShimmerBar(bottom)
        self.shimmer.pack(side="bottom", fill="x")

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
        lock_input()
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
            unlock_input()
            automate_zen_studio(zen_path, tmp_path)
            lock_input()
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
        unlock_input()
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
