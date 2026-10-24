"""
9Router Manager — GUI para gerenciar o 9router com Claude Code
Requires: pip install customtkinter
"""

import customtkinter as ctk
import subprocess
import threading
import os
import json
import re
import winreg
import time
import webbrowser
import urllib.request
import urllib.error
from pathlib import Path

# ─────────────────────────────────────────
ROUTER_PORT     = 20128
ROUTER_ENDPOINT = f"http://localhost:{ROUTER_PORT}"
ROUTER_V1       = f"{ROUTER_ENDPOINT}/v1"
CLAUDE_SETTINGS = Path.home() / ".claude" / "settings.json"
ENV_KEY         = "ANTHROPIC_BASE_URL"
STATS_ENDPOINTS = [
    f"{ROUTER_ENDPOINT}/api/stats",
    f"{ROUTER_ENDPOINT}/api/usage",
    f"{ROUTER_ENDPOINT}/stats",
]
TOKEN_PATTERNS = [
    re.compile(r'saved[:\s]+(\d+)\s*token', re.I),
    re.compile(r'(\d+)\s*tokens?\s*saved', re.I),
    re.compile(r'rtk[:\s]+(\d+)', re.I),
    re.compile(r'"tokens_saved"[:\s]+(\d+)', re.I),
]
REQUEST_PATTERNS = [
    re.compile(r'requests?[:\s]+(\d+)', re.I),
    re.compile(r'"(?:total_)?requests?"[:\s]+(\d+)', re.I),
]
# ─────────────────────────────────────────

TEXTS: dict[str, dict[str, str]] = {
    "pt": {
        # Sidebar
        "app_subtitle":    "Gateway Claude Code",
        "nav_dashboard":   "Painel",
        "nav_configure":   "Configurar",
        "nav_logs":        "Logs",
        "version":         "v0.5.x",
        # Dashboard
        "dash_title":      "Painel",
        "status_running":  "Executando",
        "status_stopped":  "Parado",
        "btn_start":       "Iniciar 9Router",
        "btn_stop":        "Parar 9Router",
        "card_port":       "Porta",
        "card_protocol":   "Protocolo",
        "card_env":        "Var. Ambiente",
        "env_active":      "Ativa",
        "env_inactive":    "Inativa",
        "dash_hint":       "Após iniciar o 9Router, ative o roteamento em Configurar para redirecionar o Claude Code pelo gateway.",
        # Token savings
        "savings_title":   "Economia de Tokens",
        "stat_tokens":     "Tokens Economizados",
        "stat_requests":   "Requisições",
        "stat_cost":       "Economia (USD)",
        "stat_unavail":    "Inicie o 9Router para ver as estatísticas",
        "btn_open_dash":   "Abrir Dashboard",
        # Configure
        "conf_title":      "Configurar Claude Code",
        "conf_route_label":"Rotear Claude Code pelo 9Router",
        "conf_on":         "Ativo — {env} = {val}\nReinicie o Claude Code para que a alteração tenha efeito.",
        "conf_off":        "Desativado — {env} não está definido.\nAo ativar, o Claude Code enviará as chamadas de API para {ep}.",
        "conf_settings":   "settings.json do Claude Code",
        "btn_refresh":     "Atualizar",
        # Logs
        "logs_title":      "Logs",
        "btn_clear":       "Limpar",
        "log_starting":    "Iniciando 9Router…",
        "log_stopping":    "Parando 9Router…",
        "log_not_found":   "ERRO: comando '9router' não encontrado. Execute: npm install -g 9router",
        "log_ended":       "Processo 9Router encerrado.",
        "log_cfg_set":     "[Config] Definido {env} = {val}",
        "log_cfg_del":     "[Config] Removido {env}",
    },
    "en": {
        # Sidebar
        "app_subtitle":    "Claude Code Gateway",
        "nav_dashboard":   "Dashboard",
        "nav_configure":   "Configure",
        "nav_logs":        "Logs",
        "version":         "v0.5.x",
        # Dashboard
        "dash_title":      "Dashboard",
        "status_running":  "Running",
        "status_stopped":  "Stopped",
        "btn_start":       "Start 9Router",
        "btn_stop":        "Stop 9Router",
        "card_port":       "Port",
        "card_protocol":   "Protocol",
        "card_env":        "Env Var",
        "env_active":      "Active",
        "env_inactive":    "Inactive",
        "dash_hint":       "After starting 9Router, enable routing in Configure to redirect Claude Code through the gateway.",
        # Token savings
        "savings_title":   "Token Savings",
        "stat_tokens":     "Tokens Saved",
        "stat_requests":   "Requests",
        "stat_cost":       "Savings (USD)",
        "stat_unavail":    "Start 9Router to see statistics",
        "btn_open_dash":   "Open Dashboard",
        # Configure
        "conf_title":      "Configure Claude Code",
        "conf_route_label":"Route Claude Code through 9Router",
        "conf_on":         "Active — {env} = {val}\nRestart Claude Code for changes to take effect.",
        "conf_off":        "Disabled — {env} is not set.\nEnabling this will route Claude Code API calls through {ep}.",
        "conf_settings":   "Claude Code settings.json",
        "btn_refresh":     "Refresh",
        # Logs
        "logs_title":      "Logs",
        "btn_clear":       "Clear",
        "log_starting":    "Starting 9Router…",
        "log_stopping":    "Stopping 9Router…",
        "log_not_found":   "ERROR: '9router' command not found. Run: npm install -g 9router",
        "log_ended":       "9Router process ended.",
        "log_cfg_set":     "[Config] Set {env} = {val}",
        "log_cfg_del":     "[Config] Removed {env}",
    },
}

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
        self.geometry("860x640")
        self.resizable(True, True)
        self.minsize(720, 540)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self._process: subprocess.Popen | None = None
        self._log_thread: threading.Thread | None = None
        self._stats_thread: threading.Thread | None = None
        self._running = False
        self._lang = "pt"
        self._translatable: list[tuple] = []   # (widget, text_key)
        self._stats = {"tokens": 0, "requests": 0, "cost": 0.0}
        self._current_tab = "Dashboard"

        self._build_ui()
        self._refresh_status()

    # ── Translation ───────────────────────────────────────────────────────────

    def t(self, key: str, **kw) -> str:
        text = TEXTS[self._lang].get(key, TEXTS["en"].get(key, key))
        return text.format(**kw) if kw else text

    def _reg(self, widget, key: str):
        """Register a widget for automatic re-translation."""
        self._translatable.append((widget, key))
        return widget

    def _set_lang(self, lang: str):
        self._lang = lang
        for widget, key in self._translatable:
            widget.configure(text=self.t(key))
        # Nav buttons (use internal key → nav_key mapping)
        for tab_key, btn in self._nav_btns.items():
            btn.configure(text=self.t(f"nav_{tab_key.lower()}"))
        # Re-highlight active tab
        self._nav_btns[self._current_tab].configure(fg_color=("#1f538d", "#1f538d"))
        # Language button highlights
        self._btn_pt.configure(fg_color="#1f538d" if lang == "pt" else "transparent")
        self._btn_en.configure(fg_color="#1f538d" if lang == "en" else "transparent")
        # Dynamic widgets
        self._refresh_status()
        self._route_detail.configure(text=self._route_detail_text())
        self._refresh_stats_display()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Sidebar
        sidebar = ctk.CTkFrame(self, width=185, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        ctk.CTkLabel(sidebar, text="9Router", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(24, 4))
        self._reg(
            ctk.CTkLabel(sidebar, text=self.t("app_subtitle"), font=ctk.CTkFont(size=11), text_color="gray"),
            "app_subtitle",
        ).pack(pady=(0, 20))

        self._nav_btns: dict[str, ctk.CTkButton] = {}
        for tab_key in ("Dashboard", "Configure", "Logs"):
            btn = ctk.CTkButton(
                sidebar, text=self.t(f"nav_{tab_key.lower()}"),
                width=155, anchor="w",
                fg_color="transparent", hover_color=("#2b2b2b", "#2b2b2b"),
                command=lambda k=tab_key: self._show_tab(k),
            )
            btn.pack(padx=12, pady=4)
            self._nav_btns[tab_key] = btn

        # Language toggle
        lang_row = ctk.CTkFrame(sidebar, fg_color="transparent")
        lang_row.pack(side="bottom", pady=(0, 8))

        self._btn_pt = ctk.CTkButton(
            lang_row, text="PT", width=62, height=26,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#1f538d", hover_color="#1a4575",
            command=lambda: self._set_lang("pt"),
        )
        self._btn_pt.pack(side="left", padx=(0, 4))

        self._btn_en = ctk.CTkButton(
            lang_row, text="EN", width=62, height=26,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="transparent", hover_color="#1a4575",
            command=lambda: self._set_lang("en"),
        )
        self._btn_en.pack(side="left")

        self._reg(
            ctk.CTkLabel(sidebar, text=self.t("version"), font=ctk.CTkFont(size=10), text_color="gray"),
            "version",
        ).pack(side="bottom", pady=(0, 4))

        # ── Content area
        self._content = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self._content.pack(side="left", fill="both", expand=True, padx=16, pady=16)

        self._tabs: dict[str, ctk.CTkFrame] = {}
        self._build_dashboard()
        self._build_configure()
        self._build_logs()
        self._show_tab("Dashboard")

    def _show_tab(self, name: str):
        self._current_tab = name
        for n, frame in self._tabs.items():
            frame.pack_forget()
            self._nav_btns[n].configure(fg_color="transparent")
        self._tabs[name].pack(fill="both", expand=True)
        self._nav_btns[name].configure(fg_color=("#1f538d", "#1f538d"))

    # ── Dashboard tab ─────────────────────────────────────────────────────────

    def _build_dashboard(self):
        frame = ctk.CTkFrame(self._content, fg_color="transparent")
        self._tabs["Dashboard"] = frame

        self._reg(
            ctk.CTkLabel(frame, text=self.t("dash_title"), font=ctk.CTkFont(size=18, weight="bold")),
            "dash_title",
        ).pack(anchor="w", pady=(0, 10))

        # Status card
        status_card = ctk.CTkFrame(frame)
        status_card.pack(fill="x", pady=(0, 8))

        row = ctk.CTkFrame(status_card, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(12, 6))

        self._status_dot = ctk.CTkLabel(row, text="●", font=ctk.CTkFont(size=22), text_color="#e74c3c", width=30)
        self._status_dot.pack(side="left")
        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", padx=8)
        self._status_label = ctk.CTkLabel(info, text=self.t("status_stopped"), font=ctk.CTkFont(size=14, weight="bold"))
        self._status_label.pack(anchor="w")
        ctk.CTkLabel(info, text=f"Endpoint: {ROUTER_V1}", font=ctk.CTkFont(size=11), text_color="gray").pack(anchor="w")

        btn_row = ctk.CTkFrame(status_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 12))
        self._start_btn = self._reg(
            ctk.CTkButton(btn_row, text=self.t("btn_start"), width=150, command=self._start_router),
            "btn_start",
        )
        self._start_btn.pack(side="left", padx=(0, 8))
        self._stop_btn = self._reg(
            ctk.CTkButton(btn_row, text=self.t("btn_stop"), width=150,
                          fg_color="#c0392b", hover_color="#922b21",
                          command=self._stop_router, state="disabled"),
            "btn_stop",
        )
        self._stop_btn.pack(side="left")

        # Token savings card
        savings_card = ctk.CTkFrame(frame)
        savings_card.pack(fill="x", pady=(0, 8))

        savings_hdr = ctk.CTkFrame(savings_card, fg_color="transparent")
        savings_hdr.pack(fill="x", padx=16, pady=(10, 6))
        self._reg(
            ctk.CTkLabel(savings_hdr, text=self.t("savings_title"), font=ctk.CTkFont(size=13, weight="bold")),
            "savings_title",
        ).pack(side="left")
        self._reg(
            ctk.CTkButton(savings_hdr, text=self.t("btn_open_dash"), width=130, height=26,
                          font=ctk.CTkFont(size=11),
                          command=lambda: webbrowser.open(ROUTER_ENDPOINT)),
            "btn_open_dash",
        ).pack(side="right")

        stat_row = ctk.CTkFrame(savings_card, fg_color="transparent")
        stat_row.pack(fill="x", padx=16, pady=(0, 4))

        self._stat_tokens_lbl = ctk.CTkLabel(stat_row, text="0", font=ctk.CTkFont(size=22, weight="bold"), text_color="#2ecc71")
        self._stat_tokens_lbl.pack(side="left", padx=(0, 2))
        self._reg(ctk.CTkLabel(stat_row, text=self.t("stat_tokens"), font=ctk.CTkFont(size=10), text_color="gray"), "stat_tokens").pack(side="left", padx=(0, 20))

        self._stat_req_lbl = ctk.CTkLabel(stat_row, text="0", font=ctk.CTkFont(size=22, weight="bold"))
        self._stat_req_lbl.pack(side="left", padx=(0, 2))
        self._reg(ctk.CTkLabel(stat_row, text=self.t("stat_requests"), font=ctk.CTkFont(size=10), text_color="gray"), "stat_requests").pack(side="left", padx=(0, 20))

        self._stat_cost_lbl = ctk.CTkLabel(stat_row, text="$0.00", font=ctk.CTkFont(size=22, weight="bold"), text_color="#f39c12")
        self._stat_cost_lbl.pack(side="left", padx=(0, 2))
        self._reg(ctk.CTkLabel(stat_row, text=self.t("stat_cost"), font=ctk.CTkFont(size=10), text_color="gray"), "stat_cost").pack(side="left")

        self._savings_status = self._reg(
            ctk.CTkLabel(savings_card, text=self.t("stat_unavail"), font=ctk.CTkFont(size=10), text_color="gray"),
            "stat_unavail",
        )
        self._savings_status.pack(anchor="w", padx=16, pady=(2, 8))

        # Info cards row
        info_row = ctk.CTkFrame(frame, fg_color="transparent")
        info_row.pack(fill="x", pady=(0, 8))
        self._make_info_card(info_row, "card_port", str(ROUTER_PORT))
        self._make_info_card(info_row, "card_protocol", "OpenAI-compatible")
        self._env_val_label = self._make_info_card(info_row, "card_env", self.t("env_inactive"))

        self._reg(
            ctk.CTkLabel(frame, text=self.t("dash_hint"),
                         font=ctk.CTkFont(size=11), text_color="gray",
                         wraplength=580, justify="left"),
            "dash_hint",
        ).pack(anchor="w", pady=2)

    def _make_info_card(self, parent, title_key: str, value: str) -> ctk.CTkLabel:
        card = ctk.CTkFrame(parent)
        card.pack(side="left", expand=True, fill="x", padx=(0, 8))
        self._reg(
            ctk.CTkLabel(card, text=self.t(title_key), font=ctk.CTkFont(size=10), text_color="gray"),
            title_key,
        ).pack(anchor="w", padx=12, pady=(8, 0))
        val_lbl = ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=12, weight="bold"))
        val_lbl.pack(anchor="w", padx=12, pady=(0, 8))
        return val_lbl

    # ── Configure tab ─────────────────────────────────────────────────────────

    def _build_configure(self):
        frame = ctk.CTkFrame(self._content, fg_color="transparent")
        self._tabs["Configure"] = frame

        self._reg(
            ctk.CTkLabel(frame, text=self.t("conf_title"), font=ctk.CTkFont(size=18, weight="bold")),
            "conf_title",
        ).pack(anchor="w", pady=(0, 16))

        card = ctk.CTkFrame(frame)
        card.pack(fill="x", pady=(0, 12))

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(14, 4))
        self._reg(
            ctk.CTkLabel(top, text=self.t("conf_route_label"), font=ctk.CTkFont(size=13, weight="bold")),
            "conf_route_label",
        ).pack(side="left")

        self._route_switch = ctk.CTkSwitch(top, text="", width=50, command=self._toggle_routing)
        if get_user_env(ENV_KEY):
            self._route_switch.select()
        else:
            self._route_switch.deselect()
        self._route_switch.pack(side="right")

        self._route_detail = ctk.CTkLabel(
            card, text=self._route_detail_text(),
            font=ctk.CTkFont(size=11), text_color="gray",
            wraplength=560, justify="left",
        )
        self._route_detail.pack(anchor="w", padx=16, pady=(0, 14))

        self._reg(
            ctk.CTkLabel(frame, text=self.t("conf_settings"), font=ctk.CTkFont(size=13, weight="bold")),
            "conf_settings",
        ).pack(anchor="w", pady=(8, 4))

        self._settings_box = ctk.CTkTextbox(frame, height=190, font=ctk.CTkFont(family="Consolas", size=11))
        self._settings_box.pack(fill="x")
        self._refresh_settings_view()

        self._reg(
            ctk.CTkButton(frame, text=self.t("btn_refresh"), width=110, command=self._refresh_settings_view),
            "btn_refresh",
        ).pack(anchor="e", pady=(6, 0))

    def _route_detail_text(self) -> str:
        val = get_user_env(ENV_KEY)
        if val:
            return self.t("conf_on", env=ENV_KEY, val=val)
        return self.t("conf_off", env=ENV_KEY, ep=ROUTER_ENDPOINT)

    def _toggle_routing(self):
        if self._route_switch.get():
            set_user_env(ENV_KEY, ROUTER_ENDPOINT)
            self._log(self.t("log_cfg_set", env=ENV_KEY, val=ROUTER_ENDPOINT))
        else:
            delete_user_env(ENV_KEY)
            self._log(self.t("log_cfg_del", env=ENV_KEY))
        self._route_detail.configure(text=self._route_detail_text())
        self._env_val_label.configure(text=self.t("env_active") if get_user_env(ENV_KEY) else self.t("env_inactive"))

    def _refresh_settings_view(self):
        self._settings_box.delete("1.0", "end")
        if CLAUDE_SETTINGS.exists():
            try:
                data = json.loads(CLAUDE_SETTINGS.read_text(encoding="utf-8"))
                self._settings_box.insert("1.0", json.dumps(data, indent=2))
            except Exception as e:
                self._settings_box.insert("1.0", f"Erro: {e}")
        else:
            self._settings_box.insert("1.0", f"Arquivo não encontrado:\n{CLAUDE_SETTINGS}")

    # ── Logs tab ──────────────────────────────────────────────────────────────

    def _build_logs(self):
        frame = ctk.CTkFrame(self._content, fg_color="transparent")
        self._tabs["Logs"] = frame

        hdr = ctk.CTkFrame(frame, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 8))
        self._reg(ctk.CTkLabel(hdr, text=self.t("logs_title"), font=ctk.CTkFont(size=18, weight="bold")), "logs_title").pack(side="left")
        self._reg(ctk.CTkButton(hdr, text=self.t("btn_clear"), width=80, command=self._clear_logs), "btn_clear").pack(side="right")

        self._log_box = ctk.CTkTextbox(frame, font=ctk.CTkFont(family="Consolas", size=11), state="disabled")
        self._log_box.pack(fill="both", expand=True)

    def _log(self, text: str):
        ts = time.strftime("%H:%M:%S")
        self._log_box.configure(state="normal")
        self._log_box.insert("end", f"[{ts}] {text}\n")
        self._log_box.see("end")
        self._log_box.configure(state="disabled")

    def _clear_logs(self):
        self._log_box.configure(state="normal")
        self._log_box.delete("1.0", "end")
        self._log_box.configure(state="disabled")

    # ── Process management ────────────────────────────────────────────────────

    def _install_9router(self) -> bool:
        """Try to install 9router via npm, streaming output to the log."""
        self._log("[install] npm install -g --allow-scripts=9router 9router")
        try:
            proc = subprocess.Popen(
                ["npm", "install", "-g", "--allow-scripts=9router", "9router"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            for line in proc.stdout:
                self._log(f"[npm] {line.rstrip()}")
            proc.wait()
            if proc.returncode == 0:
                self._log("[install] 9router instalado com sucesso!")
                return True
            self._log(f"[install] npm saiu com código {proc.returncode}.")
            return False
        except FileNotFoundError:
            self._log("[install] ERRO: npm não encontrado. Instale Node.js 18+ em https://nodejs.org/")
            return False

    def _start_router(self):
        if self._running:
            return
        self._log(self.t("log_starting"))
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
            self._log(self.t("log_not_found"))
            self._log("[install] Tentando instalar automaticamente…")
            self._show_tab("Logs")  # show logs so user can follow progress
            install_thread = threading.Thread(target=self._install_and_retry, daemon=True)
            install_thread.start()
            return

        self._running = True
        self._stats = {"tokens": 0, "requests": 0, "cost": 0.0}
        self._refresh_status()

        self._log_thread = threading.Thread(target=self._stream_logs, daemon=True)
        self._log_thread.start()

        self._stats_thread = threading.Thread(target=self._poll_stats, daemon=True)
        self._stats_thread.start()

    def _stop_router(self):
        if self._process:
            self._log(self.t("log_stopping"))
            self._process.terminate()
            self._process = None
        self._running = False
        self._refresh_status()

    def _install_and_retry(self):
        """Run in a thread: install 9router then start it."""
        ok = self._install_9router()
        if ok:
            self.after(500, self._start_router)
        else:
            self._log("[install] Instalação falhou. Verifique a conexão e tente novamente.")

    def _stream_logs(self):
        try:
            for line in self._process.stdout:
                line = line.rstrip()
                self._log(line)
                self._parse_log_for_stats(line)
        except Exception:
            pass
        self._running = False
        self.after(0, self._refresh_status)
        self._log(self.t("log_ended"))

    def _parse_log_for_stats(self, line: str):
        """Extract token/request counts from log output."""
        for pattern in TOKEN_PATTERNS:
            m = pattern.search(line)
            if m:
                try:
                    self._stats["tokens"] += int(m.group(1))
                    self.after(0, self._refresh_stats_display)
                    break
                except (ValueError, IndexError):
                    pass
        for pattern in REQUEST_PATTERNS:
            m = pattern.search(line)
            if m:
                try:
                    val = int(m.group(1))
                    if val > self._stats["requests"]:
                        self._stats["requests"] = val
                        self.after(0, self._refresh_stats_display)
                    break
                except (ValueError, IndexError):
                    pass

    def _poll_stats(self):
        """Periodically try 9router API endpoints for live stats."""
        time.sleep(4)
        while self._running:
            for url in STATS_ENDPOINTS:
                try:
                    with urllib.request.urlopen(url, timeout=2) as r:
                        data = json.loads(r.read())
                        self._merge_api_stats(data)
                        break
                except Exception:
                    continue
            time.sleep(15)

    def _merge_api_stats(self, data: dict):
        for k in ("tokens_saved", "tokensSaved", "saved_tokens", "rtk_saved"):
            if k in data:
                try:
                    self._stats["tokens"] = max(self._stats["tokens"], int(data[k]))
                    break
                except (ValueError, TypeError):
                    pass
        for k in ("requests", "total_requests", "requestCount", "count"):
            if k in data:
                try:
                    self._stats["requests"] = max(self._stats["requests"], int(data[k]))
                    break
                except (ValueError, TypeError):
                    pass
        for k in ("cost_saved", "savedCost", "savings_usd", "saved"):
            if k in data:
                try:
                    self._stats["cost"] = max(self._stats["cost"], float(data[k]))
                    break
                except (ValueError, TypeError):
                    pass
        self.after(0, self._refresh_stats_display)

    def _refresh_stats_display(self):
        self._stat_tokens_lbl.configure(text=f"{self._stats['tokens']:,}")
        self._stat_req_lbl.configure(text=str(self._stats["requests"]))
        self._stat_cost_lbl.configure(text=f"${self._stats['cost']:.4f}")
        if self._running:
            self._savings_status.configure(text="")
        else:
            self._savings_status.configure(text=self.t("stat_unavail"))

    def _refresh_status(self):
        if self._running:
            self._status_dot.configure(text_color="#2ecc71")
            self._status_label.configure(text=self.t("status_running"))
            self._start_btn.configure(state="disabled")
            self._stop_btn.configure(state="normal")
            self._savings_status.configure(text="")
        else:
            self._status_dot.configure(text_color="#e74c3c")
            self._status_label.configure(text=self.t("status_stopped"))
            self._start_btn.configure(state="normal")
            self._stop_btn.configure(state="disabled")
            self._savings_status.configure(text=self.t("stat_unavail"))
        self._env_val_label.configure(
            text=self.t("env_active") if get_user_env(ENV_KEY) else self.t("env_inactive")
        )

    def on_close(self):
        self._stop_router()
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
