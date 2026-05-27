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

# ── Config ────────────────────────────────────────────────────────────────────
API_BASE = "https://rainy-backend1-production.up.railway.app"
APP_NAME = "Rainy.solutions Installer"
MASTER_KEY = "29d201e746983999afad5e6783f6b4a6"

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

# ── Automate Zen Studio ───────────────────────────────────────────────────────
def automate_zen_studio(zen_path, gpc_path):
    # Step 1: Open Zen Studio and load the gpc into compiler
    proc = subprocess.Popen([zen_path, gpc_path])

    # Wait for Zen Studio window
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

    # Wait for full load
    time.sleep(4)

    # Bring to front
    try:
        zen_window.activate()
    except:
        pass
    time.sleep(1)

    # Get window position and size
    wx = zen_window.left
    wy = zen_window.top
    ww = zen_window.width
    wh = zen_window.height

    # Step 2: Click Programmer tab
    # Programmer tab is roughly at 50% across, 12% down from window top
    programmer_x = wx + int(ww * 0.50)
    programmer_y = wy + int(wh * 0.095)
    pyautogui.click(programmer_x, programmer_y)
    time.sleep(1.5)

    # Step 3: Click the 3 lines button (left sidebar, roughly 4th button down)
    # Based on screenshot: left sidebar buttons at ~4% across, spaced vertically
    lines_btn_x = wx + int(ww * 0.038)
    lines_btn_y = wy + int(wh * 0.355)
    pyautogui.click(lines_btn_x, lines_btn_y)
    time.sleep(1.5)

    # Step 4: The gpc file should now appear in the list on the right
    # Click it to select it — it appears at roughly 75% across, 25% down
    file_list_x = wx + int(ww * 0.75)
    file_list_y = wy + int(wh * 0.245)
    pyautogui.click(file_list_x, file_list_y)
    time.sleep(0.5)

    # Step 5: Drag from file list to slot 2
    # Slot 2 is roughly at 72% across, 70% down based on screenshot
    slot2_x = wx + int(ww * 0.72)
    slot2_y = wy + int(wh * 0.70)
    pyautogui.moveTo(file_list_x, file_list_y, duration=0.3)
    pyautogui.mouseDown()
    time.sleep(0.3)
    pyautogui.moveTo(slot2_x, slot2_y, duration=0.8)
    pyautogui.mouseUp()
    time.sleep(1.5)

    # Step 6: Click the Play button
    # Play button is on left sidebar, roughly 4% across, 52% down
    play_btn_x = wx + int(ww * 0.038)
    play_btn_y = wy + int(wh * 0.520)
    pyautogui.click(play_btn_x, play_btn_y)
    time.sleep(1)

    # Step 7: Wait for success popup — check window title or just wait
    success = False
    for _ in range(20):
        time.sleep(1)
        # Check for any popup window with "success" or "OK"
        for win in gw.getAllWindows():
            title = win.title.lower()
            if "success" in title or "complete" in title or "ok" in title or "programm" in title:
                success = True
                # Close the popup
                try:
                    win.close()
                except:
                    pass
                break
        if success:
            break

    time.sleep(1)

    # Step 8: Close Zen Studio
    try:
        zen_window.close()
    except:
        pass
    time.sleep(1)
    try:
        proc.terminate()
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
        self._build_ui()

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

        self.install_btn.configure(state="disabled")
        self.progress.start(10)
        threading.Thread(target=self._install, args=(key, script), daemon=True).start()

    def _install(self, key, script):
        tmp_path = None
        try:
            self._set_status("Looking for Zen Studio...", "#4a7a9b")
            zen_path = find_zen_studio()
            if not zen_path:
                self._set_status("Zen Studio not found. Please install Zen Studio first.", "#ff5566")
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
                self._reset_ui()
                return

            if response.status_code != 200:
                self._set_status("Server error. Please try again.", "#ff5566")
                self._reset_ui()
                return

            self._set_status("Decrypting script...", "#4a7a9b")
            encrypted_bytes = response.content
            decrypted = decrypt_script(encrypted_bytes, key)

            tmp_fd, tmp_path = tempfile.mkstemp(suffix=".gpc")
            with os.fdopen(tmp_fd, 'wb') as f:
                f.write(decrypted)

            self._set_status("Installing to your Cronus Zen — please wait...", "#4a7a9b")
            automate_zen_studio(zen_path, tmp_path)

            try:
                os.remove(tmp_path)
                tmp_path = None
            except:
                pass

            self._set_status("✓ Script installed! Your Cronus Zen is ready.", "#44ffaa")

        except requests.exceptions.ConnectionError:
            self._set_status("Cannot connect to server. Check your internet.", "#ff5566")
        except Exception as e:
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
