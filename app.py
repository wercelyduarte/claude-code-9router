"""
9Router Manager — GUI para gerenciar o 9router e conectar ferramentas de IA
Requires: pip install customtkinter
"""

import customtkinter as ctk
import subprocess
import threading
import os
import json
import sqlite3
import winreg
import time
import webbrowser
import socket
from pathlib import Path

# ─────────────────────────────────────────
ROUTER_PORT     = 20128
ROUTER_ENDPOINT = f"http://localhost:{ROUTER_PORT}"
ROUTER_LOCAL    = f"http://127.0.0.1:{ROUTER_PORT}"
ROUTER_V1       = f"{ROUTER_ENDPOINT}/v1"
DASH            = f"{ROUTER_ENDPOINT}/dashboard"
ROUTER_DB       = Path(os.environ.get("APPDATA", "")) / "9router" / "db" / "data.sqlite"
DEFAULT_PASSWORD = "123456"
ENV_KEY         = "ANTHROPIC_BASE_URL"   # set by older versions of this app; migrated away on start
# --log skips the interactive menu (which exits without a keyboard); 127.0.0.1 keeps it off the LAN
ROUTER_CMD      = f"9router --host 127.0.0.1 --port {ROUTER_PORT} --no-browser --log --skip-update"
NO_WINDOW       = subprocess.CREATE_NO_WINDOW
# ─────────────────────────────────────────

TEXTS: dict[str, dict[str, str]] = {
    "pt": {
        "app_subtitle":    "Gateway de IA",
        "nav_dashboard":   "Painel",
        "nav_tools":       "Ferramentas",
        "nav_logs":        "Logs",
        "version":         "v0.5.x",
        # Dashboard
        "dash_title":      "Painel",
        "status_running":  "Executando",
        "status_stopped":  "Parado",
        "btn_start":       "Iniciar 9Router",
        "btn_stop":        "Parar 9Router",
        "card_port":       "Porta",
        "card_tools":      "Ferramentas conectadas",
        "card_password":   "Senha do dashboard",
        "pw_unknown":      "—",
        "pw_default":      "Padrão (123456)",
        "pw_custom":       "Criada ✓",
        "pw_warn":         "Você ainda não criou uma senha: o 9Router está usando a padrão 123456. Crie a sua no dashboard.",
        "btn_password":    "Criar / alterar senha",
        "dash_hint":       "Depois de iniciar, conecte suas ferramentas de IA na aba Ferramentas.",
        # Usage
        "savings_title":   "Uso e Economia",
        "stat_tokens":     "Tokens",
        "stat_requests":   "Requisições",
        "stat_cost":       "Custo (USD)",
        "stat_empty":      "Nenhum uso registrado ainda. Os números aparecem quando alguma ferramenta usar o 9Router.",
        "btn_open_dash":   "Abrir Dashboard",
        "btn_token_saver": "Economia de Tokens",
        # Tools
        "tools_title":     "Ferramentas de IA",
        "tools_cli":       "Ferramentas de linha de comando — configuradas automaticamente",
        "btn_connect":     "Conectar",
        "btn_remove":      "Remover",
        "btn_connect_all": "Conectar todas",
        "btn_refresh":     "Atualizar",
        "tool_on":         "Conectado — {url}",
        "tool_off":        "Não conectado",
        "tools_loading":   "Carregando…",
        "tools_hint":      "Reinicie a ferramenta depois de conectar ou remover. A senha pedida é a do dashboard do 9Router; ela fica só na memória enquanto o app estiver aberto.",
        "tools_need_server": "Inicie o 9Router primeiro (aba Painel).",
        "tools_busy":      "Executando…",
        "tools_done":      "Concluído. Detalhes na aba Logs.",
        "tools_failed":    "Falhou. Detalhes na aba Logs.",
        "tools_dash_title":"Pelo dashboard do 9Router",
        "kiro_prov_title": "Kiro AI — provedor gratuito",
        "kiro_prov_text":  "Use os modelos do Kiro em todas as ferramentas acima: Providers → Connect Kiro AI → faça login com sua conta Kiro.",
        "btn_open_providers": "Abrir Providers",
        "mitm_title":      "Kiro IDE, Cursor e GitHub Copilot",
        "mitm_text":       "Essas IDEs passam pelo 9Router por interceptação (MITM). Abra a página MITM, ative e siga as instruções — pode ser pedido para instalar um certificado.",
        "btn_open_mitm":   "Abrir MITM",
        # Password dialog
        "pw_dialog_title": "Senha do dashboard",
        "pw_dialog_text":  "Digite a senha do dashboard do 9Router.\nSe você nunca criou uma, a senha é 123456.\nAtenção: após 5 tentativas erradas o login é bloqueado.",
        "btn_ok":          "OK",
        "btn_cancel":      "Cancelar",
        # Logs
        "logs_title":      "Logs",
        "btn_clear":       "Limpar",
        "log_starting":    "Iniciando 9Router…",
        "log_stopping":    "Parando 9Router…",
        "log_not_found":   "ERRO: comando '9router' não encontrado.",
        "log_ended":       "Processo 9Router encerrado.",
        "log_old_env":     "[Config] Removida a variável ANTHROPIC_BASE_URL criada por uma versão antiga. Conecte o Claude Code pela aba Ferramentas.",
    },
    "en": {
        "app_subtitle":    "AI Gateway",
        "nav_dashboard":   "Dashboard",
        "nav_tools":       "Tools",
        "nav_logs":        "Logs",
        "version":         "v0.5.x",
        # Dashboard
        "dash_title":      "Dashboard",
        "status_running":  "Running",
        "status_stopped":  "Stopped",
        "btn_start":       "Start 9Router",
        "btn_stop":        "Stop 9Router",
        "card_port":       "Port",
        "card_tools":      "Connected tools",
        "card_password":   "Dashboard password",
        "pw_unknown":      "—",
        "pw_default":      "Default (123456)",
        "pw_custom":       "Created ✓",
        "pw_warn":         "You haven't created a password yet: 9Router is using the default 123456. Create your own in the dashboard.",
        "btn_password":    "Create / change password",
        "dash_hint":       "After starting, connect your AI tools in the Tools tab.",
        # Usage
        "savings_title":   "Usage and Savings",
        "stat_tokens":     "Tokens",
        "stat_requests":   "Requests",
        "stat_cost":       "Cost (USD)",
        "stat_empty":      "No usage recorded yet. Numbers appear once a tool sends requests through 9Router.",
        "btn_open_dash":   "Open Dashboard",
        "btn_token_saver": "Token Saver",
        # Tools
        "tools_title":     "AI Tools",
        "tools_cli":       "Command-line tools — configured automatically",
        "btn_connect":     "Connect",
        "btn_remove":      "Remove",
        "btn_connect_all": "Connect all",
        "btn_refresh":     "Refresh",
        "tool_on":         "Connected — {url}",
        "tool_off":        "Not connected",
        "tools_loading":   "Loading…",
        "tools_hint":      "Restart the tool after connecting or removing it. The password asked for is your 9Router dashboard password; it is kept in memory only while the app is open.",
        "tools_need_server": "Start 9Router first (Dashboard tab).",
        "tools_busy":      "Working…",
        "tools_done":      "Done. Details in the Logs tab.",
        "tools_failed":    "Failed. Details in the Logs tab.",
        "tools_dash_title":"Through the 9Router dashboard",
        "kiro_prov_title": "Kiro AI — free provider",
        "kiro_prov_text":  "Use Kiro's models in all the tools above: Providers → Connect Kiro AI → sign in with your Kiro account.",
        "btn_open_providers": "Open Providers",
        "mitm_title":      "Kiro IDE, Cursor and GitHub Copilot",
        "mitm_text":       "These IDEs go through 9Router by interception (MITM). Open the MITM page, enable it and follow the steps — it may ask you to install a certificate.",
        "btn_open_mitm":   "Open MITM",
        # Password dialog
        "pw_dialog_title": "Dashboard password",
        "pw_dialog_text":  "Enter your 9Router dashboard password.\nIf you never created one, it is 123456.\nWarning: login locks after 5 wrong attempts.",
        "btn_ok":          "OK",
        "btn_cancel":      "Cancel",
        # Logs
        "logs_title":      "Logs",
        "btn_clear":       "Clear",
        "log_starting":    "Starting 9Router…",
        "log_stopping":    "Stopping 9Router…",
        "log_not_found":   "ERROR: '9router' command not found.",
        "log_ended":       "9Router process ended.",
        "log_old_env":     "[Config] Removed the ANTHROPIC_BASE_URL variable set by an older version. Connect Claude Code from the Tools tab.",
    },
}

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# ── System helpers ────────────────────────────────────────────────────────────

def get_user_env(name: str) -> str | None:
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_READ)
        val, _ = winreg.QueryValueEx(key, name)
        winreg.CloseKey(key)
        return val
    except FileNotFoundError:
        return None


def delete_user_env(name: str):
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, name)
        winreg.CloseKey(key)
        import ctypes
        ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001A, 0, "Environment", 0x0002, 5000, None)
    except FileNotFoundError:
        pass


def port_open(port: int = ROUTER_PORT) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.5):
            return True
    except OSError:
        return False


def pids_listening_on(port: int = ROUTER_PORT) -> set[int]:
    out = subprocess.run("netstat -ano -p TCP", shell=True, capture_output=True, text=True,
                         creationflags=NO_WINDOW).stdout
    pids = set()
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 5 and parts[1].endswith(f":{port}") and parts[3].upper() in ("LISTENING", "ESCUTANDO"):
            pids.add(int(parts[4]))
    return pids


def kill_tree(pid: int):
    subprocess.run(f"taskkill /PID {pid} /T /F", shell=True, capture_output=True, creationflags=NO_WINDOW)


def _db():
    # Read-only: the app never writes to 9router's database
    return sqlite3.connect(f"file:{ROUTER_DB}?mode=ro", uri=True, timeout=2)


def password_created() -> bool | None:
    """True if a dashboard password was created, False if still the default, None if unknown.
    Reads the DB instead of trying a login, because failed logins count toward 9router's lockout."""
    try:
        with _db() as c:
            row = c.execute("select data from settings where id=1").fetchone()
        return bool(row and json.loads(row[0]).get("password"))
    except Exception:
        return None


def usage_totals() -> tuple[int, int, float] | None:
    try:
        with _db() as c:
            return c.execute(
                "select count(*), coalesce(sum(coalesce(tokens, coalesce(promptTokens,0)+coalesce(completionTokens,0))),0),"
                " coalesce(sum(cost),0) from usageHistory"
            ).fetchone()
    except Exception:
        return None


def list_tools() -> list[dict]:
    out = subprocess.run("9router show --json", shell=True, capture_output=True, text=True,
                         stdin=subprocess.DEVNULL, creationflags=NO_WINDOW, encoding="utf-8").stdout
    start = out.find("[")
    return json.loads(out[start:]) if start >= 0 else []


# ── Password dialog ───────────────────────────────────────────────────────────

class PasswordDialog(ctk.CTkToplevel):
    def __init__(self, parent, t):
        super().__init__(parent)
        self.title(t("pw_dialog_title"))
        self.resizable(False, False)
        self.result: str | None = None
        self.transient(parent)

        ctk.CTkLabel(self, text=t("pw_dialog_text"), justify="left", wraplength=340).pack(padx=20, pady=(18, 10))
        self._entry = ctk.CTkEntry(self, show="•", width=320)
        self._entry.pack(padx=20)
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(pady=14)
        ctk.CTkButton(row, text=t("btn_ok"), width=100, command=self._ok).pack(side="left", padx=6)
        ctk.CTkButton(row, text=t("btn_cancel"), width=100, fg_color="gray30", command=self.destroy).pack(side="left", padx=6)

        self._entry.bind("<Return>", lambda _e: self._ok())
        self.bind("<Escape>", lambda _e: self.destroy())
        self.after(150, self._focus)

    def _focus(self):
        self.grab_set()
        self._entry.focus_force()

    def _ok(self):
        self.result = self._entry.get() or None
        self.destroy()

    def ask(self) -> str | None:
        self.wait_window()
        return self.result


# ── Main window ───────────────────────────────────────────────────────────────

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("9Router Manager")
        self.geometry("900x660")
        self.resizable(True, True)
        self.minsize(760, 560)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self._process: subprocess.Popen | None = None
        self._running = False
        self._lang = "pt"
        self._translatable: list[tuple] = []   # (widget, text_key)
        self._current_tab = "Dashboard"
        self._tools: list[dict] | None = None
        self._tools_busy = False
        self._password: str | None = None      # memory only, never written to disk
        self._pw_state: bool | None = None

        self._build_ui()
        self._migrate_old_env()
        self._refresh_status()
        self._refresh_password_status()
        self._refresh_usage()
        self._load_tools()
        self.after(1000, self._watch_port)
        self.after(10000, self._periodic)

    # ── Translation ───────────────────────────────────────────────────────────

    def t(self, key: str, **kw) -> str:
        text = TEXTS[self._lang].get(key, TEXTS["en"].get(key, key))
        return text.format(**kw) if kw else text

    def _reg(self, widget, key: str):
        self._translatable.append((widget, key))
        return widget

    def _set_lang(self, lang: str):
        self._lang = lang
        for widget, key in self._translatable:
            widget.configure(text=self.t(key))
        for tab_key, btn in self._nav_btns.items():
            btn.configure(text=self.t(f"nav_{tab_key.lower()}"))
        self._nav_btns[self._current_tab].configure(fg_color=("#1f538d", "#1f538d"))
        self._btn_pt.configure(fg_color="#1f538d" if lang == "pt" else "transparent")
        self._btn_en.configure(fg_color="#1f538d" if lang == "en" else "transparent")
        self._refresh_status()
        self._refresh_password_status()
        self._refresh_usage()
        self._render_tools()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        sidebar = ctk.CTkFrame(self, width=185, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        ctk.CTkLabel(sidebar, text="9Router", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(24, 4))
        self._reg(
            ctk.CTkLabel(sidebar, text=self.t("app_subtitle"), font=ctk.CTkFont(size=11), text_color="gray"),
            "app_subtitle",
        ).pack(pady=(0, 20))

        self._nav_btns: dict[str, ctk.CTkButton] = {}
        for tab_key in ("Dashboard", "Tools", "Logs"):
            btn = ctk.CTkButton(
                sidebar, text=self.t(f"nav_{tab_key.lower()}"),
                width=155, anchor="w",
                fg_color="transparent", hover_color=("#2b2b2b", "#2b2b2b"),
                command=lambda k=tab_key: self._show_tab(k),
            )
            btn.pack(padx=12, pady=4)
            self._nav_btns[tab_key] = btn

        lang_row = ctk.CTkFrame(sidebar, fg_color="transparent")
        lang_row.pack(side="bottom", pady=(0, 8))
        self._btn_pt = ctk.CTkButton(lang_row, text="PT", width=62, height=26,
                                     font=ctk.CTkFont(size=11, weight="bold"),
                                     fg_color="#1f538d", hover_color="#1a4575",
                                     command=lambda: self._set_lang("pt"))
        self._btn_pt.pack(side="left", padx=(0, 4))
        self._btn_en = ctk.CTkButton(lang_row, text="EN", width=62, height=26,
                                     font=ctk.CTkFont(size=11, weight="bold"),
                                     fg_color="transparent", hover_color="#1a4575",
                                     command=lambda: self._set_lang("en"))
        self._btn_en.pack(side="left")
        self._reg(
            ctk.CTkLabel(sidebar, text=self.t("version"), font=ctk.CTkFont(size=10), text_color="gray"),
            "version",
        ).pack(side="bottom", pady=(0, 4))

        self._content = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self._content.pack(side="left", fill="both", expand=True, padx=16, pady=16)

        self._tabs: dict[str, ctk.CTkFrame] = {}
        self._build_dashboard()
        self._build_tools()
        self._build_logs()
        self._show_tab("Dashboard")

    def _show_tab(self, name: str):
        self._current_tab = name
        for n, frame in self._tabs.items():
            frame.pack_forget()
            self._nav_btns[n].configure(fg_color="transparent")
        self._tabs[name].pack(fill="both", expand=True)
        self._nav_btns[name].configure(fg_color=("#1f538d", "#1f538d"))
        if name == "Dashboard":
            self._refresh_password_status()

    def _link_button(self, parent, key: str, url: str, width=150):
        return self._reg(
            ctk.CTkButton(parent, text=self.t(key), width=width, height=26, font=ctk.CTkFont(size=11),
                          command=lambda: webbrowser.open(url)),
            key,
        )

    # ── Dashboard tab ─────────────────────────────────────────────────────────

    def _build_dashboard(self):
        frame = ctk.CTkFrame(self._content, fg_color="transparent")
        self._tabs["Dashboard"] = frame

        self._reg(ctk.CTkLabel(frame, text=self.t("dash_title"), font=ctk.CTkFont(size=18, weight="bold")),
                  "dash_title").pack(anchor="w", pady=(0, 10))

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
        self._start_btn = self._reg(ctk.CTkButton(btn_row, text=self.t("btn_start"), width=150,
                                                  command=self._start_router), "btn_start")
        self._start_btn.pack(side="left", padx=(0, 8))
        self._stop_btn = self._reg(ctk.CTkButton(btn_row, text=self.t("btn_stop"), width=150,
                                                 fg_color="#c0392b", hover_color="#922b21",
                                                 command=self._stop_router, state="disabled"), "btn_stop")
        self._stop_btn.pack(side="left")

        # Default-password warning (shown only when needed)
        self._pw_banner = ctk.CTkFrame(frame, fg_color="#5a3a00")
        self._pw_banner_lbl = self._reg(
            ctk.CTkLabel(self._pw_banner, text=self.t("pw_warn"), wraplength=480, justify="left",
                         font=ctk.CTkFont(size=12)),
            "pw_warn",
        )
        self._pw_banner_lbl.pack(side="left", padx=14, pady=10)
        self._link_button(self._pw_banner, "btn_password", f"{DASH}/profile", width=170).pack(side="right", padx=12)

        # Usage card
        self._usage_card = ctk.CTkFrame(frame)
        self._usage_card.pack(fill="x", pady=(0, 8))
        hdr = ctk.CTkFrame(self._usage_card, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(10, 6))
        self._reg(ctk.CTkLabel(hdr, text=self.t("savings_title"), font=ctk.CTkFont(size=13, weight="bold")),
                  "savings_title").pack(side="left")
        self._link_button(hdr, "btn_open_dash", DASH, width=130).pack(side="right")
        self._link_button(hdr, "btn_token_saver", f"{DASH}/token-saver", width=140).pack(side="right", padx=6)

        stat_row = ctk.CTkFrame(self._usage_card, fg_color="transparent")
        stat_row.pack(fill="x", padx=16, pady=(0, 4))
        self._stat_tokens_lbl = ctk.CTkLabel(stat_row, text="0", font=ctk.CTkFont(size=22, weight="bold"), text_color="#2ecc71")
        self._stat_tokens_lbl.pack(side="left", padx=(0, 2))
        self._reg(ctk.CTkLabel(stat_row, text=self.t("stat_tokens"), font=ctk.CTkFont(size=10), text_color="gray"),
                  "stat_tokens").pack(side="left", padx=(0, 20))
        self._stat_req_lbl = ctk.CTkLabel(stat_row, text="0", font=ctk.CTkFont(size=22, weight="bold"))
        self._stat_req_lbl.pack(side="left", padx=(0, 2))
        self._reg(ctk.CTkLabel(stat_row, text=self.t("stat_requests"), font=ctk.CTkFont(size=10), text_color="gray"),
                  "stat_requests").pack(side="left", padx=(0, 20))
        self._stat_cost_lbl = ctk.CTkLabel(stat_row, text="$0.00", font=ctk.CTkFont(size=22, weight="bold"), text_color="#f39c12")
        self._stat_cost_lbl.pack(side="left", padx=(0, 2))
        self._reg(ctk.CTkLabel(stat_row, text=self.t("stat_cost"), font=ctk.CTkFont(size=10), text_color="gray"),
                  "stat_cost").pack(side="left")
        self._usage_note = ctk.CTkLabel(self._usage_card, text="", font=ctk.CTkFont(size=10), text_color="gray",
                                        wraplength=600, justify="left")
        self._usage_note.pack(anchor="w", padx=16, pady=(2, 8))

        # Info cards
        info_row = ctk.CTkFrame(frame, fg_color="transparent")
        info_row.pack(fill="x", pady=(0, 8))
        self._make_info_card(info_row, "card_port", str(ROUTER_PORT))
        self._tools_count_lbl = self._make_info_card(info_row, "card_tools", "—")
        self._pw_status_lbl = self._make_info_card(info_row, "card_password", self.t("pw_unknown"))

        self._reg(ctk.CTkLabel(frame, text=self.t("dash_hint"), font=ctk.CTkFont(size=11), text_color="gray",
                               wraplength=600, justify="left"), "dash_hint").pack(anchor="w", pady=2)

    def _make_info_card(self, parent, title_key: str, value: str) -> ctk.CTkLabel:
        card = ctk.CTkFrame(parent)
        card.pack(side="left", expand=True, fill="x", padx=(0, 8))
        self._reg(ctk.CTkLabel(card, text=self.t(title_key), font=ctk.CTkFont(size=10), text_color="gray"),
                  title_key).pack(anchor="w", padx=12, pady=(8, 0))
        val_lbl = ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=12, weight="bold"))
        val_lbl.pack(anchor="w", padx=12, pady=(0, 8))
        return val_lbl

    def _refresh_password_status(self):
        self._pw_state = password_created()
        if self._pw_state is None:
            self._pw_status_lbl.configure(text=self.t("pw_unknown"), text_color=("gray10", "gray90"))
            self._pw_banner.pack_forget()
        elif self._pw_state:
            self._pw_status_lbl.configure(text=self.t("pw_custom"), text_color="#2ecc71")
            self._pw_banner.pack_forget()
        else:
            self._pw_status_lbl.configure(text=self.t("pw_default"), text_color="#f39c12")
            self._pw_banner.pack(fill="x", pady=(0, 8), before=self._usage_card)

    def _refresh_usage(self):
        totals = usage_totals()
        reqs, tokens, cost = totals if totals else (0, 0, 0.0)
        self._stat_tokens_lbl.configure(text=f"{int(tokens):,}".replace(",", "."))
        self._stat_req_lbl.configure(text=str(reqs))
        self._stat_cost_lbl.configure(text=f"${cost:.4f}")
        self._usage_note.configure(text="" if reqs else self.t("stat_empty"))

    # ── Tools tab ─────────────────────────────────────────────────────────────

    def _build_tools(self):
        frame = ctk.CTkScrollableFrame(self._content, fg_color="transparent")
        self._tabs["Tools"] = frame

        hdr = ctk.CTkFrame(frame, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 6))
        self._reg(ctk.CTkLabel(hdr, text=self.t("tools_title"), font=ctk.CTkFont(size=18, weight="bold")),
                  "tools_title").pack(side="left")
        self._reg(ctk.CTkButton(hdr, text=self.t("btn_refresh"), width=100, command=self._load_tools),
                  "btn_refresh").pack(side="right")
        self._connect_all_btn = self._reg(
            ctk.CTkButton(hdr, text=self.t("btn_connect_all"), width=130, command=lambda: self._connect("all")),
            "btn_connect_all",
        )
        self._connect_all_btn.pack(side="right", padx=6)

        self._tools_status = ctk.CTkLabel(frame, text="", font=ctk.CTkFont(size=11), text_color="#f39c12")
        self._tools_status.pack(anchor="w")

        self._reg(ctk.CTkLabel(frame, text=self.t("tools_cli"), font=ctk.CTkFont(size=13, weight="bold")),
                  "tools_cli").pack(anchor="w", pady=(4, 4))
        self._tools_list = ctk.CTkFrame(frame)
        self._tools_list.pack(fill="x")
        self._reg(ctk.CTkLabel(frame, text=self.t("tools_hint"), font=ctk.CTkFont(size=10), text_color="gray",
                               wraplength=600, justify="left"), "tools_hint").pack(anchor="w", pady=(4, 12))

        self._reg(ctk.CTkLabel(frame, text=self.t("tools_dash_title"), font=ctk.CTkFont(size=13, weight="bold")),
                  "tools_dash_title").pack(anchor="w", pady=(4, 4))
        for title_key, text_key, btn_key, url in (
            ("kiro_prov_title", "kiro_prov_text", "btn_open_providers", f"{DASH}/providers"),
            ("mitm_title", "mitm_text", "btn_open_mitm", f"{DASH}/mitm"),
        ):
            card = ctk.CTkFrame(frame)
            card.pack(fill="x", pady=(0, 8))
            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=14, pady=(10, 2))
            self._reg(ctk.CTkLabel(top, text=self.t(title_key), font=ctk.CTkFont(size=12, weight="bold")),
                      title_key).pack(side="left")
            self._link_button(top, btn_key, url).pack(side="right")
            self._reg(ctk.CTkLabel(card, text=self.t(text_key), font=ctk.CTkFont(size=11), text_color="gray",
                                   wraplength=580, justify="left"), text_key).pack(anchor="w", padx=14, pady=(0, 10))

    def _load_tools(self):
        self._tools = None
        self._render_tools()

        def work():
            try:
                tools = list_tools()
            except Exception as e:
                self._log(f"[tools] {e}")
                tools = []
            self.after(0, self._set_tools, tools)

        threading.Thread(target=work, daemon=True).start()

    def _set_tools(self, tools: list[dict]):
        self._tools = tools
        self._render_tools()

    def _render_tools(self):
        for child in self._tools_list.winfo_children():
            child.destroy()
        if self._tools is None:
            ctk.CTkLabel(self._tools_list, text=self.t("tools_loading"), text_color="gray").pack(padx=14, pady=10, anchor="w")
            self._tools_count_lbl.configure(text="—")
            return
        state = "disabled" if self._tools_busy else "normal"
        for tool in self._tools:
            row = ctk.CTkFrame(self._tools_list, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=3)
            on = bool(tool.get("configured"))
            ctk.CTkLabel(row, text="●", text_color="#2ecc71" if on else "gray40", width=18).pack(side="left")
            ctk.CTkLabel(row, text=tool.get("name", tool.get("id", "?")), width=150, anchor="w",
                         font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
            status = self.t("tool_on", url=tool.get("baseUrl") or "") if on else self.t("tool_off")
            ctk.CTkLabel(row, text=status, anchor="w", text_color="gray", font=ctk.CTkFont(size=11)).pack(side="left", padx=6)
            ctk.CTkButton(row, text=self.t("btn_remove"), width=80, height=26, fg_color="gray30", state=state,
                          command=lambda i=tool["id"]: self._reset(i)).pack(side="right", padx=(4, 0))
            ctk.CTkButton(row, text=self.t("btn_connect"), width=90, height=26, state=state,
                          command=lambda i=tool["id"]: self._connect(i)).pack(side="right")
        self._connect_all_btn.configure(state=state)
        connected = sum(1 for t in self._tools if t.get("configured"))
        self._tools_count_lbl.configure(text=f"{connected} / {len(self._tools)}")

    def _connect(self, tool_ids: str):
        if not port_open():
            self._tools_status.configure(text=self.t("tools_need_server"))
            return
        if self._password is None:
            self._password = PasswordDialog(self, self.t).ask()
            if self._password is None:
                return
        env = os.environ.copy()
        env["NINE_ROUTER_PASSWORD"] = self._password   # env var keeps it off the command line
        self._run_tool_cmd(f"9router connect {ROUTER_LOCAL} --tools {tool_ids}", env, is_login=True)

    def _reset(self, tool_id: str):
        self._run_tool_cmd(f"9router connect --reset --tools {tool_id}", None, is_login=False)

    def _run_tool_cmd(self, cmd: str, env: dict | None, is_login: bool):
        self._tools_busy = True
        self._tools_status.configure(text=self.t("tools_busy"))
        self._render_tools()
        self._log(f"[tools] {cmd}")

        def work():
            proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=env,
                                  stdin=subprocess.DEVNULL, creationflags=NO_WINDOW, encoding="utf-8", errors="replace")
            output = (proc.stdout or "") + (proc.stderr or "")
            for line in output.splitlines():
                if line.strip():
                    self._log(f"[tools] {line.rstrip()}")
            self.after(0, self._tool_cmd_done, proc.returncode == 0, is_login and "Login failed" in output)

        threading.Thread(target=work, daemon=True).start()

    def _tool_cmd_done(self, ok: bool, bad_password: bool):
        if bad_password:
            self._password = None   # ask again next time
        self._tools_busy = False
        self._tools_status.configure(text=self.t("tools_done") if ok else self.t("tools_failed"))
        self._load_tools()

    # ── Logs tab ──────────────────────────────────────────────────────────────

    def _build_logs(self):
        frame = ctk.CTkFrame(self._content, fg_color="transparent")
        self._tabs["Logs"] = frame
        hdr = ctk.CTkFrame(frame, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 8))
        self._reg(ctk.CTkLabel(hdr, text=self.t("logs_title"), font=ctk.CTkFont(size=18, weight="bold")),
                  "logs_title").pack(side="left")
        self._reg(ctk.CTkButton(hdr, text=self.t("btn_clear"), width=80, command=self._clear_logs),
                  "btn_clear").pack(side="right")
        self._log_box = ctk.CTkTextbox(frame, font=ctk.CTkFont(family="Consolas", size=11), state="disabled")
        self._log_box.pack(fill="both", expand=True)

    def _log(self, text: str):
        if threading.current_thread() is not threading.main_thread():
            self.after(0, self._log, text)  # Tk widgets are only safe on the main thread
            return
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

    def _migrate_old_env(self):
        if get_user_env(ENV_KEY) == ROUTER_ENDPOINT:
            delete_user_env(ENV_KEY)
            self._log(self.t("log_old_env"))

    def _install_9router(self) -> bool:
        self._log("[install] npm install -g --allow-scripts=9router 9router")
        try:
            proc = subprocess.Popen("npm install -g --allow-scripts=9router 9router", shell=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
                                    creationflags=NO_WINDOW)
            for line in proc.stdout:
                self._log(f"[npm] {line.rstrip()}")
            proc.wait()
            if proc.returncode == 0:
                self._log("[install] OK")
                return True
            self._log(f"[install] npm exit {proc.returncode}")
            return False
        except Exception as e:
            self._log(f"[install] ERRO: {e} — Node.js 18+: https://nodejs.org/")
            return False

    def _start_router(self):
        if self._running or port_open():
            self._set_running(True)
            return
        if subprocess.run("9router --version", shell=True, capture_output=True,
                          creationflags=NO_WINDOW).returncode != 0:
            self._log(self.t("log_not_found"))
            self._show_tab("Logs")
            threading.Thread(target=self._install_and_retry, daemon=True).start()
            return
        self._log(self.t("log_starting"))
        self._process = subprocess.Popen(ROUTER_CMD, shell=True, stdin=subprocess.DEVNULL,
                                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                         text=True, bufsize=1, encoding="utf-8", errors="replace",
                                         creationflags=NO_WINDOW)
        threading.Thread(target=self._stream_logs, daemon=True).start()
        # _watch_port flips the status to Running once the server actually answers

    def _install_and_retry(self):
        if self._install_9router():
            self.after(500, self._start_router)

    def _set_running(self, running: bool):
        if running == self._running:
            return
        self._running = running
        self._refresh_status()

    def _watch_port(self):
        self._set_running(port_open())
        self.after(2000, self._watch_port)

    def _periodic(self):
        self._refresh_usage()
        self.after(10000, self._periodic)

    def _stop_router(self):
        self._log(self.t("log_stopping"))
        if self._process:
            kill_tree(self._process.pid)
            self._process = None
        # The server may have detached to the tray, so also kill whoever owns the port
        for pid in pids_listening_on():
            kill_tree(pid)
        self._set_running(port_open())

    def _stream_logs(self):
        proc = self._process
        try:
            for line in proc.stdout:
                self._log(line.rstrip())
        except Exception:
            pass
        self._log(self.t("log_ended"))

    def _refresh_status(self):
        if self._running:
            self._status_dot.configure(text_color="#2ecc71")
            self._status_label.configure(text=self.t("status_running"))
            self._start_btn.configure(state="disabled")
            self._stop_btn.configure(state="normal")
            self._tools_status.configure(text="")
        else:
            self._status_dot.configure(text_color="#e74c3c")
            self._status_label.configure(text=self.t("status_stopped"))
            self._start_btn.configure(state="normal")
            self._stop_btn.configure(state="disabled")

    def on_close(self):
        self._password = None
        self._stop_router()
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
