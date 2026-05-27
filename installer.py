import tkinter as tk
from tkinter import ttk, messagebox
import requests
import hashlib
import os
import sys
import subprocess
import tempfile
import threading
import winreg
import glob

# ── Config ────────────────────────────────────────────────────────────────────
API_BASE = "https://rainy-backend1-production.up.railway.app"
APP_NAME = "Rainy.solutions Installer"
MASTER_KEY = "29d201e746983999afad5e6783f6b4a6"  # Must match server

# ── Decryption (mirrors server encryption) ────────────────────────────────────
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import secrets

def decrypt_script(encrypted_bytes, license_key):
    """Decrypt the script blob received from the server."""
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.backends import default_backend

    # Derive the same key as the server
    digest = hashlib.sha256((MASTER_KEY + license_key.upper()).encode()).digest()

    # Extract iv (16), authTag (16), ciphertext (rest)
    iv = encrypted_bytes[:16]
    auth_tag = encrypted_bytes[16:32]
    ciphertext = encrypted_bytes[32:]

    # Decrypt using AES-256-GCM
    # GCM auth tag is appended to ciphertext for the cryptography library
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    decryptor = Cipher(
        algorithms.AES(digest),
        modes.GCM(iv, auth_tag),
        backend=default_backend()
    ).decryptor()

    return decryptor.update(ciphertext) + decryptor.finalize()

# ── Find Zen Studio ────────────────────rainy-backend1-production.up.railway.app───────────────────────────────────────
def find_zen_studio():
    """Try to find Zen Studio executable on this PC."""
    # Common install locations
    common_paths = [
        r"C:\Program Files\Zen Studio\ZenStudio.exe",
        r"C:\Program Files (x86)\Zen Studio\ZenStudio.exe",
        r"C:\Program Files\Cronus\Zen Studio\ZenStudio.exe",
        r"C:\Program Files (x86)\Cronus\Zen Studio\ZenStudio.exe",
    ]

    for p in common_paths:
        if os.path.exists(p):
            return p

    # Search registry
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

    # Glob search as last resort
    drives = ["C:", "D:", "E:"]
    for drive in drives:
        results = glob.glob(f"{drive}\\**\\ZenStudio.exe", recursive=True)
        if results:
            return results[0]

    return None

# ── Main App ──────────────────────────────────────────────────────────────────
class RainyInstaller(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("520x420")
        self.resizable(False, False)
        self.configure(bg="#050a0f")
        self.iconbitmap(default='') if sys.platform == 'win32' else None

        self._build_ui()

    def _build_ui(self):
        # Header
        tk.Label(self, text="Rainy.solutions", bg="#050a0f", fg="#4ab8ff",
                 font=("Segoe UI", 22, "bold")).pack(pady=(28, 2))
        tk.Label(self, text="Script Installer", bg="#050a0f", fg="#4a7a9b",
                 font=("Segoe UI", 10)).pack()

        # Key entry
        frame = tk.Frame(self, bg="#050a0f")
        frame.pack(pady=24, padx=40, fill="x")

        tk.Label(frame, text="LICENSE KEY", bg="#050a0f", fg="#4a7a9b",
                 font=("Segoe UI", 8)).pack(anchor="w")

        self.key_var = tk.StringVar()
        self.key_var.trace("w", self._format_key)
        self.key_entry = tk.Entry(frame, textvariable=self.key_var,
                                  bg="#0b1520", fg="#d6eaf8",
                                  insertbackground="#4ab8ff",
                                  relief="flat", font=("Courier New", 13),
                                  bd=0, highlightthickness=1,
                                  highlightbackground="#1a2d42",
                                  highlightcolor="#0077cc")
        self.key_entry.pack(fill="x", ipady=8, pady=(4, 0))

        # Script selector
        tk.Label(frame, text="SCRIPT", bg="#050a0f", fg="#4a7a9b",
                 font=("Segoe UI", 8)).pack(anchor="w", pady=(12, 0))

        self.script_var = tk.StringVar()
        self.script_combo = ttk.Combobox(frame, textvariable=self.script_var,
                                          state="readonly", font=("Segoe UI", 10))
        self.script_combo.pack(fill="x", pady=(4, 0))
        self._load_scripts()

        # Install button
        self.install_btn = tk.Button(self, text="Install to Zen",
                                      bg="#0077cc", fg="white",
                                      activebackground="#4ab8ff",
                                      activeforeground="#050a0f",
                                      relief="flat", font=("Segoe UI", 11, "bold"),
                                      cursor="hand2", command=self._start_install)
        self.install_btn.pack(pady=(4, 0), padx=40, fill="x", ipady=10)

        # Status label
        self.status_var = tk.StringVar(value="Enter your key and click Install to Zen")
        self.status_label = tk.Label(self, textvariable=self.status_var,
                                      bg="#050a0f", fg="#4a7a9b",
                                      font=("Segoe UI", 9), wraplength=400)
        self.status_label.pack(pady=(12, 0))

        # Progress bar
        self.progress = ttk.Progressbar(self, mode="indeterminate", length=400)
        self.progress.pack(pady=(8, 0), padx=40)

    def _format_key(self, *args):
    # Don't reformat — just uppercase
    val = self.key_var.get().upper()
    self.key_var.trace_vdelete("w", self._trace_id) if hasattr(self, '_trace_id') else None
    self.key_entry.delete(0, tk.END)
    self.key_entry.insert(0, val)
    self._trace_id = self.key_var.trace("w", self._format_key)

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

        if len(key.replace("-", "")) < 10:
            self._set_status("Please enter your full license key.", "#ff5566")
            return

        self.install_btn.configure(state="disabled")
        self.progress.start(10)
        threading.Thread(target=self._install, args=(key, script), daemon=True).start()

    def _install(self, key, script):
        tmp_path = None
        try:
            # Step 1: Find Zen Studio
            self._set_status("Looking for Zen Studio...", "#4a7a9b")
            zen_path = find_zen_studio()
            if not zen_path:
                self._set_status(
                    "Zen Studio not found. Please install Zen Studio first.",
                    "#ff5566"
                )
                self._reset_ui()
                return

            # Step 2: Redeem key and get encrypted script
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

            # Step 3: Decrypt in memory
            self._set_status("Decrypting script...", "#4a7a9b")
            encrypted_bytes = response.content
            decrypted = decrypt_script(encrypted_bytes, key)

            # Step 4: Write to temp file (only exists for seconds)
            self._set_status("Programming your Cronus Zen...", "#4a7a9b")
            tmp_fd, tmp_path = tempfile.mkstemp(suffix=".gpc")
            with os.fdopen(tmp_fd, 'wb') as f:
                f.write(decrypted)

            # Step 5: Call Zen Studio silently to compile and program
            result = subprocess.run(
                [zen_path, "--compile", tmp_path, "--program"],
                capture_output=True,
                timeout=30
            )

            # Step 6: Delete temp file immediately
            try:
                os.remove(tmp_path)
                tmp_path = None
            except:
                pass

            if result.returncode == 0:
                self._set_status(
                    "✓ Script installed successfully! Your Cronus Zen is ready.",
                    "#44ffaa"
                )
            else:
                # Zen Studio may not support CLI args — open it with the file instead
                subprocess.Popen([zen_path, tmp_path])
                self._set_status(
                    "✓ Zen Studio opened — click Compile & Program to finish.",
                    "#44ffaa"
                )

        except requests.exceptions.ConnectionError:
            self._set_status("Cannot connect to server. Check your internet.", "#ff5566")
        except Exception as e:
            self._set_status(f"Error: {str(e)}", "#ff5566")
        finally:
            # Always clean up temp file
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
