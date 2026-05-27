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
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import pyautogui
import pygetwindow as gw

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.05

# ── Config ────────────────────────────────────────────────────────────────────
API_BASE = "https://rainy-backend1-production.up.railway.app"
APP_NAME = "Rainy.solutions Installer"
MASTER_KEY = "29d201e746983999afad5e6783f6b4a6"

# ── Global temp path tracker ──────────────────────────────────────────────────
current_tmp_path = None

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

# ── Cleanup and emergency shutdown ───────────────────────────────────────────
def emergency_cleanup_and_restart():
    global current_tmp_path
    # Delete temp file if it exists
    if current_tmp_path and os.path.exists(current_tmp_path):
        try:
            os.remove(current_tmp_path)
        except:
            pass
    # Show warning message then restart PC
    try:
        subprocess.Popen([
            'msg', '*',
            'Program closed during installation.\n\nIf this was a mistake contact @8xgl for a new key.\n\nYour PC will now restart.'
        ])
    except:
        pass
    time.sleep(2)
    # Restart PC
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

    # Click Programmer tab
    pyautogui.click(wx + int(ww * 0.50), wy + int(wh * 0.095))
    time.sleep(1)

    # Click 3 lines button
    pyautogui.click(wx + int(ww * 0.038), wy + int(wh * 0.355))
    time.sleep(1)

    # Click first file in list
    file_x = wx + int(ww * 0.75)
    file_y = wy + int(wh * 0.19)
    pyautogui.click(file_x, file_y)
    time.sleep(0.3)

    # Drag to slot 2
    slot2_x = wx + int(ww * 0.72)
    slot2_y = wy + int(wh * 0.67)
    pyautogui.moveTo(file_x, file_y, duration=0.2)
    pyautogui.mouseDown()
    time.sleep(0.2)
    pyautogui.moveTo(slot2_x, slot2_y, duration=0.5)
    time.sleep(0.2)
    pyautogui.mouseUp()
    time.sleep(1)

    # Click Play button
    pyautogui.click(wx + int(ww * 0.038), wy + int(wh * 0.520))
    time.sleep(1)

    # Wait for success popup
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

# ── Main App ──────────────────────────────────────────────────────────────────
class RainyInstaller(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("520x420")
        self.resizable(False, False)
        self.configure(bg="#050a0f")
        # Override the close button
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._installing = False
        self._build_ui()

    def _on_close(self):
        if self._installing:
            # Installing in progress — trigger emergency cleanup
            threading.Thread(target=emergency_cleanup_and_restart, daemon=True).start()
        else:
            # Not installing, just close normally
            self.destroy()

    def _build_ui(self):
        tk.Label(self, text="Rainy.solutions", bg="#050a0f", fg="#4ab8ff",
                 font=("Segoe UI", 22, "bold")).pack(pady=(28, 2))
        tk.Label(self, text="Script Installer — Close Zen Studio before installing",
                 bg="#050a0f", fg="#4a7a9b",
                 font=("Segoe UI", 9)).pack()

        frame = tk.Frame(self, bg="#050a0f")
        frame.pack(pady=24, padx=40, fill="x")

        tk.Label(frame, text="LICENSE KEY", bg="#050a0f", fg="#4a7a9b",
                 font=("Segoe UI", 8)).pack(anchor="w")

        self.key_var = tk.StringVar()
        self.key_entry = tk.Entry(frame, textvariable=self.key_var,
                                  bg="#0b1520", fg="#d6eaf8",
                                  insertbackground="#4ab8ff",
                                  relief="flat", font=("Courier New", 13),
                                  bd=0, highlightthickness=1,
                                  highlightbackground="#1a2d42",
                                  highlightcolor="#0077cc")
        self.key_entry.pack(fill="x", ipady=8, pady=(4, 0))

        tk.Label(frame, text="SCRIPT", bg="#050a0f", fg="#4a7a9b",
                 font=("Segoe UI", 8)).pack(anchor="w", pady=(12, 0))

        self.script_var = tk.StringVar()
        self.script_combo = ttk.Combobox(frame, textvariable=self.script_var,
                                          state="readonly", font=("Segoe UI", 10))
        self.script_combo.pack(fill="x", pady=(4, 0))
        self._load_scripts()

        self.install_btn = tk.Button(self, text="Install to Zen",
                                      bg="#0077cc", fg="white",
                                      activebackground="#4ab8ff",
                                      activeforeground="#050a0f",
                                      relief="flat", font=("Segoe UI", 11, "bold"),
                                      cursor="hand2", command=self._start_install)
        self.install_btn.pack(pady=(4, 0), padx=40, fill="x", ipady=10)

        self.status_var = tk.StringVar(value="Enter your key and click Install to Zen")
        self.status_label = tk.Label(self, textvariable=self.status_var,
                                      bg="#050a0f", fg="#4a7a9b",
                                      font=("Segoe UI", 9), wraplength=440)
        self.status_label.pack(pady=(12, 0))

        self.progress = ttk.Progressbar(self, mode="indeterminate", length=400)
        self.progress.pack(pady=(8, 0), padx=40)

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

    def _set_status(self, msg, color="#4a7a9b"):
        self.status_var.set(msg)
        self.status_label.configure(fg=color)

    def _start_install(self):
        key = self.key_var.get().strip().upper()
        script = self.script_var.get()

        if len(key) < 5:
            self._set_status("Please enter your license key.", "#ff5566")
            return

        self._installing = True
        self.install_btn.configure(state="disabled")
        self.progress.start(10)
        threading.Thread(target=self._install, args=(key, script), daemon=True).start()

    def _install(self, key, script):
        global current_tmp_path
        tmp_path = None
        try:
            self._set_status("Looking for Zen Studio...", "#4a7a9b")
            zen_path = find_zen_studio()
            if not zen_path:
                self._set_status("Zen Studio not found. Please install Zen Studio first.", "#ff5566")
                self._installing = False
                self._reset_ui()
                return

            self._set_status("Validating key...", "#4a7a9b")
            response = requests.post(
                f"{API_BASE}/api/redeem",
                json={"key": key, "script": script},
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

            self._set_status("Decrypting script...", "#4a7a9b")
            encrypted_bytes = response.content
            decrypted = decrypt_script(encrypted_bytes, key)

            tmp_fd, tmp_path = tempfile.mkstemp(suffix=".gpc")
            current_tmp_path = tmp_path
            with os.fdopen(tmp_fd, 'wb') as f:
                f.write(decrypted)

            self._set_status("Installing to your Cronus Zen — please wait...", "#4a7a9b")
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
        self.progress.stop()
        self.install_btn.configure(state="normal")


if __name__ == "__main__":
    app = RainyInstaller()
    app.mainloop()
