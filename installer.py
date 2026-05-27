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

# ── HWID ──────────────────────────────────────────────────────────────────────
def get_hwid():
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography")
        machine_guid, _ = winreg.QueryValueEx(key, "MachineGuid")
        return hashlib.sha256(machine_guid.encode()).hexdigest()
    except:
        return hashlib.sha256(str(uuid.getnode()).encode()).hexdigest()

# ── Input lock ────────────────────────────────────────────────────────────────
def lock_input():
    try:
        ctypes.windll.user32.BlockInput(True)
    except:
        pass

def unlock_input():
    try:
        ctypes.windll.user32.BlockInput(False)
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
    if current_tmp_path and os.path.exists(current_tmp_path):
        try:
            os.remove(current_tmp_path)
        except:
            pass
    unlock_input()
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
    zen_window = None
    for _ in range(30):
        time.sleep(1)
        windows = gw.getWindowsWithTitle("ZENSTUDIO")
        if not windows:
            windows = gw.getWindowsWithTitle("Zen Studio")
        if windows:
            zen_window = windows[0]
            break
    if not zen_window:
        proc.kill()
        raise Exception("Zen Studio did not open. Please install Zen Studio first.")
    time.sleep(3)
    try:
        zen_window.activate()
    except:
        pass
    time.sleep(0.5)
    wx = zen_window.left
    wy = zen_window.top
    ww = zen_window.width
    wh = zen_window.height
    lock_input()
    try:
        pyautogui.click(wx + int(ww * 0.50), wy + int(wh * 0.095))
        time.sleep(1)
        pyautogui.click(wx + int(ww * 0.038), wy + int(wh * 0.355))
        time.sleep(1)
        file_x = wx + int(ww * 0.75)
        file_y = wy + int(wh * 0.19)
        pyautogui.click(file_x, file_y)
        time.sleep(0.3)
        slot2_x = wx + int(ww * 0.72)
        slot2_y = wy + int(wh * 0.67)
        pyautogui.moveTo(file_x, file_y, duration=0.2)
        pyautogui.mouseDown()
        time.sleep(0.2)
        pyautogui.moveTo(slot2_x, slot2_y, duration=0.5)
        time.sleep(0.2)
        pyautogui.mouseUp()
        time.sleep(1)
        pyautogui.click(wx + int(ww * 0.038), wy + int(wh * 0.520))
        time.sleep(1)
        for _ in range(15):
            time.sleep(0.5)
            for win in gw.getAllWindows():
                title = win.title.lower()
                if any(word in title for word in ["success", "complete", "ok", "programm", "written"]):
                    try:
                        win.close()
                    except:
                        pass
                    break
            pyautogui.press('enter')
    finally:
        unlock_input()
    try:
        proc.terminate()
    except:
        pass
    time.sleep(0.5)
    try:
        proc.kill()
    except:
        pass

# ── Animated Background Canvas ────────────────────────────────────────────────
class AnimatedBackground(tk.Canvas):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.lines = []
        self._init_lines()
        self._animate()

    def _init_lines(self):
        w, h = 520, 440
        import random
        random.seed(42)
        for _ in range(18):
            x1 = random.randint(-100, w + 100)
            y1 = random.randint(-100, h + 100)
            angle = random.uniform(-30, 30)
            length = random.randint(80, 220)
            speed = random.uniform(0.3, 1.2)
            opacity = random.uniform(0.08, 0.22)
            dx = math.cos(math.radians(angle)) * speed
            dy = math.sin(math.radians(angle)) * speed
            r = int(74 * opacity)
            g = int(184 * opacity)
            b = int(255 * opacity)
            color = f"#{r:02x}{g:02x}{b:02x}"
            line_id = self.create_line(x1, y1, x1 + length, y1 + length,
                                       fill=color, width=1)
            self.lines.append({
                'id': line_id, 'x': x1, 'y': y1,
                'dx': dx, 'dy': dy, 'length': length,
                'angle': angle, 'color': color
            })

    def _animate(self):
        w, h = 520, 440
        for l in self.lines:
            l['x'] += l['dx']
            l['y'] += l['dy']
            # Wrap around
            if l['x'] > w + 120: l['x'] = -120
            if l['x'] < -120: l['x'] = w + 120
            if l['y'] > h + 120: l['y'] = -120
            if l['y'] < -120: l['y'] = h + 120
            ex = l['x'] + math.cos(math.radians(l['angle'])) * l['length']
            ey = l['y'] + math.sin(math.radians(l['angle'])) * l['length']
            self.coords(l['id'], l['x'], l['y'], ex, ey)
        self.after(30, self._animate)

# ── Custom Progress Bar ───────────────────────────────────────────────────────
class ShimmerBar(tk.Canvas):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="#000000", highlightthickness=1,
                         highlightbackground="#1a2d42", **kwargs)
        self._shimmer_x = -200
        self._running = False
        self._bar = self.create_rectangle(0, 0, 0, 0, fill="#000000", outline="")
        self._shimmer = self.create_rectangle(0, 0, 0, 0, fill="#ffffff", outline="")

    def start(self):
        self._running = True
        self._animate()

    def stop(self):
        self._running = False
        self._shimmer_x = -200
        self.coords(self._shimmer, 0, 0, 0, 0)

    def _animate(self):
        if not self._running:
            return
        w = self.winfo_width() or 440
        h = self.winfo_height() or 14
        self._shimmer_x += 6
        if self._shimmer_x > w + 200:
            self._shimmer_x = -200
        # Draw shimmer — white glow moving left to right
        sx = self._shimmer_x
        self.coords(self._shimmer, sx - 60, 2, sx + 60, h - 2)
        # Fade edges with gradient-like effect using multiple rects
        self.after(16, self._animate)

# ── Main App ──────────────────────────────────────────────────────────────────
class RainyInstaller(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("520x440")
        self.resizable(False, False)
        self.configure(bg="#050a0f")
        self.hwid = get_hwid()
        self._installing = False
        self._alpha = 0.0
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build_ui()
        self._fade_in()
        self._check_banned()

    def _fade_in(self):
        self._alpha += 0.06
        if self._alpha <= 1.0:
            self.attributes('-alpha', min(self._alpha, 1.0))
            self.after(20, self._fade_in)

    def _check_banned(self):
        try:
            r = requests.post(f"{API_BASE}/api/check-hwid",
                              json={"hwid": self.hwid}, timeout=5)
            data = r.json()
            if data.get("banned"):
                self._set_status("Your device is banned. Contact @8xgl.", "#ff5566")
                self.install_btn.configure(state="disabled")
        except:
            pass

    def _on_close(self):
        if self._installing:
            threading.Thread(target=emergency_cleanup, args=(self.hwid,), daemon=True).start()
        else:
            self.destroy()

    def _build_ui(self):
        # Animated background
        self.bg_canvas = AnimatedBackground(
            self, width=520, height=440, bg="#050a0f",
            highlightthickness=0
        )
        self.bg_canvas.place(x=0, y=0)

        # Content frame on top of canvas
        content = tk.Frame(self, bg="#050a0f")
        content.place(x=0, y=0, width=520, height=440)

        # Icon
        icon_canvas = tk.Canvas(content, width=52, height=52,
                                bg="#050a0f", highlightthickness=0)
        icon_canvas.pack(pady=(22, 0))
        icon_canvas.create_rectangle(2, 2, 50, 50, fill="#0a1a2a",
                                     outline="#4ab8ff", width=2)
        icon_canvas.create_rectangle(6, 6, 46, 46, fill="#0077cc", outline="")
        icon_canvas.create_text(26, 27, text="R", fill="white",
                                font=("Segoe UI", 20, "bold"))

        # Title
        tk.Label(content, text="Rainy.solutions", bg="#050a0f", fg="#4ab8ff",
                 font=("Segoe UI", 18, "bold")).pack(pady=(6, 1))
        tk.Label(content, text="SCRIPT INSTALLER", bg="#050a0f", fg="#1a4a6a",
                 font=("Segoe UI", 7, "bold")).pack()
        tk.Label(content, text="Close Zen Studio before installing",
                 bg="#050a0f", fg="#2a5a7a", font=("Segoe UI", 8)).pack()

        # Separator line
        sep = tk.Frame(content, bg="#1a2d42", height=1)
        sep.pack(fill="x", padx=40, pady=(12, 0))

        # Form
        form = tk.Frame(content, bg="#050a0f")
        form.pack(pady=12, padx=40, fill="x")

        tk.Label(form, text="LICENSE KEY", bg="#050a0f", fg="#2a5a7a",
                 font=("Segoe UI", 7, "bold")).pack(anchor="w")
        self.key_var = tk.StringVar()
        key_frame = tk.Frame(form, bg="#4ab8ff", padx=1, pady=1)
        key_frame.pack(fill="x", pady=(3, 0))
        self.key_entry = tk.Entry(key_frame, textvariable=self.key_var,
                                  bg="#060e18", fg="#4ab8ff",
                                  insertbackground="#4ab8ff",
                                  relief="flat", font=("Courier New", 12),
                                  bd=0)
        self.key_entry.pack(fill="x", ipady=7, padx=1, pady=1)

        tk.Label(form, text="SCRIPT", bg="#050a0f", fg="#2a5a7a",
                 font=("Segoe UI", 7, "bold")).pack(anchor="w", pady=(10, 0))

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Dark.TCombobox",
                         fieldbackground="#060e18",
                         background="#060e18",
                         foreground="#4ab8ff",
                         selectbackground="#0077cc",
                         selectforeground="white",
                         bordercolor="#4ab8ff",
                         arrowcolor="#4ab8ff")
        self.script_var = tk.StringVar()
        self.script_combo = ttk.Combobox(form, textvariable=self.script_var,
                                          state="readonly", font=("Segoe UI", 10),
                                          style="Dark.TCombobox")
        self.script_combo.pack(fill="x", pady=(3, 0))
        self._load_scripts()

        # Install button
        self.install_btn = tk.Button(content, text="⚡  Install to Zen",
                                      bg="#0077cc", fg="white",
                                      activebackground="#4ab8ff",
                                      activeforeground="#050a0f",
                                      relief="flat",
                                      font=("Segoe UI", 11, "bold"),
                                      cursor="hand2",
                                      command=self._start_install,
                                      bd=0)
        self.install_btn.pack(pady=(8, 0), padx=40, fill="x", ipady=11)

        # Bind hover effects
        self.install_btn.bind("<Enter>", lambda e: self.install_btn.configure(bg="#4ab8ff", fg="#050a0f"))
        self.install_btn.bind("<Leave>", lambda e: self.install_btn.configure(bg="#0077cc", fg="white"))

        # Status
        self.status_var = tk.StringVar(value="Enter your key and click Install to Zen")
        self.status_label = tk.Label(content, textvariable=self.status_var,
                                      bg="#050a0f", fg="#2a5a7a",
                                      font=("Segoe UI", 8), wraplength=440)
        self.status_label.pack(pady=(10, 0))

        # Custom shimmer progress bar
        self.shimmer = ShimmerBar(content, width=440, height=14)
        self.shimmer.pack(pady=(8, 0), padx=40)

        # Footer
        tk.Label(content, text="rainy.solutions", bg="#050a0f", fg="#0d2035",
                 font=("Segoe UI", 7)).pack(side="bottom", pady=8)

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

    def _set_status(self, msg, color="#2a5a7a"):
        self.status_var.set(msg)
        self.status_label.configure(fg=color)

    def _start_install(self):
        key = self.key_var.get().strip().upper()
        script = self.script_var.get()
        if len(key) < 5:
            self._set_status("Please enter your license key.", "#ff5566")
            return
        self._installing = True
        self.install_btn.configure(state="disabled", bg="#0a2a3a")
        self.shimmer.start()
        lock_input()
        threading.Thread(target=self._install, args=(key, script), daemon=True).start()

    def _install(self, key, script):
        global current_tmp_path
        tmp_path = None
        try:
            self._set_status("Looking for Zen Studio...", "#4ab8ff")
            zen_path = find_zen_studio()
            if not zen_path:
                self._set_status("Zen Studio not found. Please install Zen Studio first.", "#ff5566")
                self._installing = False
                self._reset_ui()
                return

            self._set_status("Validating key...", "#4ab8ff")
            response = requests.post(
                f"{API_BASE}/api/redeem",
                json={"key": key, "script": script, "hwid": self.hwid},
                timeout=15
            )

            if response.status_code == 403:
                error = response.json().get("error", "Invalid key.")
                self._set_status(error, "#ff5566")
                self._installing = False
                self._reset_ui()
                return

            if response.status_code != 200:
                self._set_status("Server error. Please try again.", "#ff5566")
                self._installing = False
                self._reset_ui()
                return

            self._set_status("Decrypting script...", "#4ab8ff")
            encrypted_bytes = response.content
            decrypted = decrypt_script(encrypted_bytes, key)

            tmp_fd, tmp_path = tempfile.mkstemp(suffix=".gpc")
            current_tmp_path = tmp_path
            with os.fdopen(tmp_fd, 'wb') as f:
                f.write(decrypted)

            self._set_status("Installing to your Cronus Zen — do not close...", "#4ab8ff")
            automate_zen_studio(zen_path, tmp_path)

            try:
                os.remove(tmp_path)
                tmp_path = None
                current_tmp_path = None
            except:
                pass

            self._installing = False
            self._set_status("✓ Script installed! Your Cronus Zen is ready.", "#44ffaa")

        except requests.exceptions.ConnectionError:
            self._installing = False
            self._set_status("Cannot connect to server. Check your internet.", "#ff5566")
        except Exception as e:
            self._installing = False
            self._set_status(f"Error: {str(e)}", "#ff5566")
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except:
                    pass
            self._reset_ui()

    def _reset_ui(self):
        unlock_input()
        self.shimmer.stop()
        self.install_btn.configure(state="normal", bg="#0077cc", fg="white")


if __name__ == "__main__":
    app = RainyInstaller()
    app.mainloop()
