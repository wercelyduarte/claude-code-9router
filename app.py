"""
9Router Manager — GUI for managing 9router with Claude Code
Requires: pip install customtkinter
"""

import customtkinter as ctk
import subprocess
import threading
import os
import json
import winreg
import time
from pathlib import Path

# ─────────────────────────────────────────
ROUTER_PORT = 20128
ROUTER_ENDPOINT = f"http://localhost:{ROUTER_PORT}"
ROUTER_V1 = f"{ROUTER_ENDPOINT}/v1"
CLAUDE_SETTINGS = Path.home() / ".claude" / "settings.json"
ENV_KEY = "ANTHROPIC_BASE_URL"
# ─────────────────────────────────────────

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


def get_user_env(name: str) -> str | None:
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_READ)
        val, _ = winreg.QueryValueEx(key, name)
        winreg.CloseKey(key)
        return val
    except FileNotFoundError:
        return None


def set_user_env(name: str, value: str):
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE)
    winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)
    winreg.CloseKey(key)
    # Broadcast the env change to running processes
    import ctypes
    ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001A, 0, "Environment", 0x0002, 5000, None)


def delete_user_env(name: str):
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, name)
        winreg.CloseKey(key)
        import ctypes
        ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001A, 0, "Environment", 0x0002, 5000, None)
    except FileNotFoundError:
        pass


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("9Router Manager")
        self.geometry("820x560")
        self.resizable(True, True)
        self.minsize(700, 480)

        self._process: subprocess.Popen | None = None
        self._log_thread: threading.Thread | None = None
        self._running = False

        self._build_ui()
        self._refresh_status()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        # Sidebar
        sidebar = ctk.CTkFrame(self, width=180, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        ctk.CTkLabel(sidebar, text="9Router", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(24, 4))
        ctk.CTkLabel(sidebar, text="Claude Code Gateway", font=ctk.CTkFont(size=11), text_color="gray").pack(pady=(0, 24))

        self._nav_btns = {}
        for label in ("Dashboard", "Configure", "Logs"):
            btn = ctk.CTkButton(
                sidebar, text=label, width=150, anchor="w",
                fg_color="transparent", hover_color=("#2b2b2b", "#2b2b2b"),
                command=lambda l=label: self._show_tab(l),
            )
            btn.pack(padx=12, pady=4)
            self._nav_btns[label] = btn

        ctk.CTkLabel(sidebar, text="v0.5.x", font=ctk.CTkFont(size=10), text_color="gray").pack(side="bottom", pady=12)

        # Main content area
        self._content = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self._content.pack(side="left", fill="both", expand=True, padx=16, pady=16)

        self._tabs: dict[str, ctk.CTkFrame] = {}
        self._build_dashboard()
        self._build_configure()
        self._build_logs()

        self._show_tab("Dashboard")

    def _show_tab(self, name: str):
        for n, frame in self._tabs.items():
            frame.pack_forget()
            self._nav_btns[n].configure(fg_color="transparent")
        self._tabs[name].pack(fill="both", expand=True)
        self._nav_btns[name].configure(fg_color=("#1f538d", "#1f538d"))

    # ── Dashboard tab ─────────────────────────────────────────────────────────

    def _build_dashboard(self):
        frame = ctk.CTkFrame(self._content, fg_color="transparent")
        self._tabs["Dashboard"] = frame

        ctk.CTkLabel(frame, text="Dashboard", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", pady=(0, 16))

        status_card = ctk.CTkFrame(frame)
        status_card.pack(fill="x", pady=(0, 12))

        row = ctk.CTkFrame(status_card, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=12)

        self._status_dot = ctk.CTkLabel(row, text="●", font=ctk.CTkFont(size=22), text_color="red", width=30)
        self._status_dot.pack(side="left")

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", padx=8)
        self._status_label = ctk.CTkLabel(info, text="Stopped", font=ctk.CTkFont(size=14, weight="bold"))
        self._status_label.pack(anchor="w")
        ctk.CTkLabel(info, text=f"Endpoint: {ROUTER_V1}", font=ctk.CTkFont(size=11), text_color="gray").pack(anchor="w")

        btn_row = ctk.CTkFrame(status_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 12))

        self._start_btn = ctk.CTkButton(btn_row, text="Start 9Router", width=140, command=self._start_router)
        self._start_btn.pack(side="left", padx=(0, 8))

        self._stop_btn = ctk.CTkButton(
            btn_row, text="Stop 9Router", width=140,
            fg_color="#c0392b", hover_color="#922b21",
            command=self._stop_router, state="disabled"
        )
        self._stop_btn.pack(side="left")

        # Info cards
        info_row = ctk.CTkFrame(frame, fg_color="transparent")
        info_row.pack(fill="x", pady=(0, 12))

        self._make_info_card(info_row, "Port", str(ROUTER_PORT), "left")
        self._make_info_card(info_row, "Protocol", "OpenAI-compatible", "left")
        self._make_info_card(info_row, "Env Var", self._routing_status_text(), "left")

        self._env_card_label = None  # refreshed later

        ctk.CTkLabel(
            frame,
            text="After starting 9Router, enable routing in the Configure tab to redirect Claude Code through the gateway.",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            wraplength=560,
            justify="left",
        ).pack(anchor="w", pady=8)

    def _make_info_card(self, parent, title, value, side):
        card = ctk.CTkFrame(parent)
        card.pack(side=side, expand=True, fill="x", padx=(0, 8))
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=10), text_color="gray").pack(anchor="w", padx=12, pady=(8, 0))
        ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=12, pady=(0, 8))

    def _routing_status_text(self):
        val = get_user_env(ENV_KEY)
        return "Active" if val else "Inactive"

    # ── Configure tab ─────────────────────────────────────────────────────────

    def _build_configure(self):
        frame = ctk.CTkFrame(self._content, fg_color="transparent")
        self._tabs["Configure"] = frame

        ctk.CTkLabel(frame, text="Configure Claude Code", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", pady=(0, 16))

        card = ctk.CTkFrame(frame)
        card.pack(fill="x", pady=(0, 12))

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(14, 4))

        ctk.CTkLabel(top, text="Route Claude Code through 9Router", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")

        current = get_user_env(ENV_KEY)
        self._route_switch = ctk.CTkSwitch(
            top, text="", width=50,
            command=self._toggle_routing,
        )
        if current:
            self._route_switch.select()
        else:
            self._route_switch.deselect()
        self._route_switch.pack(side="right")

        self._route_detail = ctk.CTkLabel(
            card,
            text=self._route_detail_text(),
            font=ctk.CTkFont(size=11),
            text_color="gray",
            wraplength=560,
            justify="left",
        )
        self._route_detail.pack(anchor="w", padx=16, pady=(0, 14))

        # Settings.json viewer
        ctk.CTkLabel(frame, text="Claude Code settings.json", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(8, 4))

        self._settings_box = ctk.CTkTextbox(frame, height=180, font=ctk.CTkFont(family="Consolas", size=11))
        self._settings_box.pack(fill="x")
        self._refresh_settings_view()

        ctk.CTkButton(frame, text="Refresh", width=100, command=self._refresh_settings_view).pack(anchor="e", pady=(6, 0))

    def _route_detail_text(self):
        val = get_user_env(ENV_KEY)
        if val:
            return f"Active — {ENV_KEY} = {val}\nRestart Claude Code for changes to take effect."
        return (
            f"Disabled — {ENV_KEY} is not set.\n"
            "Enabling this will set the environment variable at the Windows user level so Claude Code "
            f"routes API calls through {ROUTER_ENDPOINT}."
        )

    def _toggle_routing(self):
        if self._route_switch.get():
            set_user_env(ENV_KEY, ROUTER_ENDPOINT)
            self._log(f"[Config] Set {ENV_KEY} = {ROUTER_ENDPOINT}")
        else:
            delete_user_env(ENV_KEY)
            self._log(f"[Config] Removed {ENV_KEY}")
        self._route_detail.configure(text=self._route_detail_text())

    def _refresh_settings_view(self):
        self._settings_box.delete("1.0", "end")
        if CLAUDE_SETTINGS.exists():
            try:
                data = json.loads(CLAUDE_SETTINGS.read_text(encoding="utf-8"))
                self._settings_box.insert("1.0", json.dumps(data, indent=2))
            except Exception as e:
                self._settings_box.insert("1.0", f"Error reading file: {e}")
        else:
            self._settings_box.insert("1.0", f"File not found:\n{CLAUDE_SETTINGS}")

    # ── Logs tab ──────────────────────────────────────────────────────────────

    def _build_logs(self):
        frame = ctk.CTkFrame(self._content, fg_color="transparent")
        self._tabs["Logs"] = frame

        hdr = ctk.CTkFrame(frame, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(hdr, text="Logs", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left")
        ctk.CTkButton(hdr, text="Clear", width=80, command=self._clear_logs).pack(side="right")

        self._log_box = ctk.CTkTextbox(
            frame,
            font=ctk.CTkFont(family="Consolas", size=11),
            state="disabled",
        )
        self._log_box.pack(fill="both", expand=True)

    def _log(self, text: str):
        ts = time.strftime("%H:%M:%S")
        line = f"[{ts}] {text}\n"
        self._log_box.configure(state="normal")
        self._log_box.insert("end", line)
        self._log_box.see("end")
        self._log_box.configure(state="disabled")

    def _clear_logs(self):
        self._log_box.configure(state="normal")
        self._log_box.delete("1.0", "end")
        self._log_box.configure(state="disabled")

    # ── Process management ────────────────────────────────────────────────────

    def _start_router(self):
        if self._running:
            return
        self._log("Starting 9Router…")
        try:
            self._process = subprocess.Popen(
                ["9router"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        except FileNotFoundError:
            self._log("ERROR: '9router' command not found. Run: npm install -g 9router")
            return

        self._running = True
        self._refresh_status()

        self._log_thread = threading.Thread(target=self._stream_logs, daemon=True)
        self._log_thread.start()

    def _stop_router(self):
        if self._process:
            self._log("Stopping 9Router…")
            self._process.terminate()
            self._process = None
        self._running = False
        self._refresh_status()

    def _stream_logs(self):
        try:
            for line in self._process.stdout:
                self._log(line.rstrip())
        except Exception:
            pass
        self._running = False
        self.after(0, self._refresh_status)
        self._log("9Router process ended.")

    def _refresh_status(self):
        if self._running:
            self._status_dot.configure(text_color="#2ecc71")
            self._status_label.configure(text="Running")
            self._start_btn.configure(state="disabled")
            self._stop_btn.configure(state="normal")
        else:
            self._status_dot.configure(text_color="#e74c3c")
            self._status_label.configure(text="Stopped")
            self._start_btn.configure(state="normal")
            self._stop_btn.configure(state="disabled")

    def on_close(self):
        self._stop_router()
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
