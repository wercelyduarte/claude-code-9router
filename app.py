"""
9Router Manager — GUI para gerenciar o 9router e conectar ferramentas de IA
Requires: pip install customtkinter pystray Pillow
"""

import customtkinter as ctk
import subprocess
import threading
import os
import sys
import json
import sqlite3
import winreg
import time
import webbrowser
import socket
import urllib.request
import urllib.error
import urllib.parse
import hashlib
from datetime import datetime, timezone
from pathlib import Path

try:
    import pystray
    from PIL import Image
    TRAY_IMPORT_ERROR = None
except ImportError as e:  # without them the X button simply quits
    pystray = None
    TRAY_IMPORT_ERROR = e

# ─────────────────────────────────────────
ROUTER_PORT     = 20128
ROUTER_ENDPOINT = f"http://localhost:{ROUTER_PORT}"
ROUTER_LOCAL    = f"http://127.0.0.1:{ROUTER_PORT}"
ROUTER_V1       = f"{ROUTER_ENDPOINT}/v1"
DASH            = f"{ROUTER_ENDPOINT}/dashboard"
ROUTER_DB       = Path(os.environ.get("APPDATA", "")) / "9router" / "db" / "data.sqlite"
ENV_KEY         = "ANTHROPIC_BASE_URL"   # set by older versions of this app; migrated away on start
# --log skips the interactive menu (which exits without a keyboard); 127.0.0.1 keeps it off the LAN
ROUTER_CMD      = f"9router --host 127.0.0.1 --port {ROUTER_PORT} --no-browser --log --skip-update"
NO_WINDOW       = subprocess.CREATE_NO_WINDOW
BASE_DIR        = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
ICON_ICO        = BASE_DIR / "icone.ico"
ICON_PNG        = BASE_DIR / "icone.png"
CONFIG_FILE     = Path(os.environ.get("APPDATA", "")) / "9RouterManager" / "config.json"
HEADROOM_PORT   = 8787   # where 9Router's Headroom mode sends requests (its headroomUrl default)
HEADROOM_VENV   = Path(os.environ.get("APPDATA", "")) / "9RouterManager" / "headroom-venv"
HEADROOM_EXE    = HEADROOM_VENV / "Scripts" / "headroom.exe"
HEADROOM_CMD    = f'"{HEADROOM_EXE}" proxy --host 127.0.0.1 --port {HEADROOM_PORT}'
CAVEMAN_PORT    = 8788
CAVEMAN_REPORT  = Path.home() / ".caveman" / "reports" / "caveman-stats.html"
CAVEMAN_INSTALL = "npx -y @caveman-ai/cli@latest"
CAVEMAN_UNINSTALL = "npx -y github:JuliusBrussee/caveman -- --uninstall && npm uninstall -g @caveman-ai/cli"
SELECTED        = ("#1f538d", "#1f538d")
HOVER           = ("gray80", "gray25")
# ─────────────────────────────────────────

TEXTS: dict[str, dict[str, str]] = {
    "pt": {
        "app_subtitle":    "Gateway de IA",
        "nav_dashboard":   "Painel",
        "nav_tools":       "Ferramentas",
        "nav_savers":      "Economia",
        "nav_accounts":    "Consumo",
        "nav_logs":        "Logs",
        # Accounts tab
        "accounts_title":  "Consumo de tokens & limites",
        "accounts_updated":"Atualizado às {time} · atualiza a cada 1 min",
        "accounts_empty":  "Nenhuma conta encontrada.",
        "accounts_hint":   "Inicie o 9Router no Painel e clique em Atualizar.",
        "accounts_offline":"O 9Router não está rodando.",
        "accounts_error":  "Não foi possível ler as cotas desta conta agora.",
        "accounts_no_quota":"Este provedor não informa cotas.",
        "accounts_unlimited":"Ilimitado",
        "accounts_left":   "restante",
        "accounts_reset":  "renova em",
        "accounts_loading":"Carregando cotas…",
        "accounts_open_dash": "Abrir Dashboard",
        "accounts_session":"sessão",
        "accounts_weekly": "semanal",
        "accounts_credit": "crédito",
        # Savers
        "savers_title":    "Economia de tokens",
        "savers_intro":    "Extras que reduzem os tokens enviados e recebidos. O 9Router já tem os modos Caveman e Headroom; o Headroom precisa do programa abaixo rodando para funcionar.",
        "hr_title":        "Headroom — comprime o que o agente lê",
        "hr_text":         "Comprime saídas de ferramentas, logs e JSON antes de chegarem ao modelo (20% a 90% menos tokens). Roda no seu PC, na porta 8787, onde o modo Headroom do 9Router envia as requisições. Inicia junto com o 9Router.",
        "hr_missing":      "Não instalado",
        "hr_stopped":      "Instalado — parado",
        "hr_running":      "Rodando na porta 8787 ✓",
        "hr_installing":   "Instalando (pode levar alguns minutos)…",
        "btn_install":     "Instalar",
        "btn_start_short": "Iniciar",
        "btn_stop_short":  "Parar",
        "cv_title":        "Caveman — respostas curtas e mais",
        "cv_text":         "Faz o agente responder curto (código intacto) e encolhe logs, JSON e páginas web. A instalação abre uma janela onde você revisa e confirma o que muda.",
        "cv_order":        "Importante: conecte suas ferramentas ao 9Router (aba Ferramentas) ANTES de instalar. O Caveman não altera uma ferramenta que já aponta para outro endereço, então a rota pelo 9Router continua.",
        "cv_telemetry":    "O Caveman envia estatísticas de uso anônimas (sem conteúdo, com seu IP). Use 'Desligar telemetria' para parar.",
        "cv_missing":      "Não instalado",
        "cv_installed":    "Instalado ✓ ({v})",
        "btn_cv_status":   "Ver status",
        "btn_cv_telemetry":"Desligar telemetria",
        "btn_uninstall":   "Desinstalar",
        "saver_hr_down":   "Headroom (ligado no 9Router, mas não está rodando — veja a aba Economia)",
        "tool_other":      "Aponta para outro proxy — {url}",
        "tool_other_cv":   "Usa o Caveman, não o 9Router — {url}",
        "route_caveman":   "O Claude Code está passando pelo Caveman, não pelo 9Router. Por isso o 9Router não conta esse uso — a economia dele aparece no card do Caveman abaixo.",
        "cv_card_title":   "Economia do Caveman (últimos 30 dias)",
        "cv_saved":        "Tokens economizados",
        "cv_requests":     "Requisições",
        "cv_pct":          "da entrada",
        "cv_usd":          "Equivalente (USD)",
        "btn_cv_report":   "Abrir relatório",
        "cv_note":         "Estimativa do próprio Caveman. Com assinatura (Pro/Max) o valor em USD é só uma referência — não reduz sua fatura.",
        "version":         "v0.5.x",
        "btn_background":  "Rodar em segundo plano",
        "theme_dark":      "Tema: escuro",
        "theme_light":     "Tema: claro",
        # Dashboard
        "dash_title":      "Painel",
        "status_running":  "Executando",
        "status_stopped":  "Parado",
        "btn_start":       "Iniciar 9Router",
        "btn_stop":        "Parar 9Router",
        # Checklist
        "check_title":     "Para economizar tokens",
        "check_all_ok":    "Tudo pronto — o 9Router está sendo usado.",
        "check_missing":   "Falta {n} passo(s). Siga a lista abaixo.",
        "step_server":     "1. 9Router em execução",
        "step_password":   "2. Senha própria criada (não a padrão 123456)",
        "step_provider":   "3. Provedor de IA adicionado ({n})",
        "step_tool":       "4. Ferramenta conectada ao 9Router ({n})",
        "step_traffic":    "5. Uso passando pelo 9Router",
        "step_traffic_hint": "Reinicie a ferramenta conectada e use-a normalmente.",
        "act_start":       "Iniciar",
        "act_password":    "Criar senha",
        "act_provider":    "Abrir Providers",
        "act_tool":        "Conectar ferramenta",
        "saver_on":        "Modos de economia ativos no 9Router: {modes}",
        "saver_off":       "Nenhum modo de economia ativo. Ative em Economia de Tokens.",
        # Usage
        "savings_title":   "Uso pelo 9Router",
        "stat_tokens":     "Tokens",
        "stat_requests":   "Requisições",
        "stat_cost":       "Custo (USD)",
        "stat_empty":      "Nenhum uso registrado ainda.",
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
        "tools_failed":    "Falhou:",
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
        # Tray
        "tray_open":       "Abrir 9Router Manager",
        "tray_quit":       "Sair (para o 9Router)",
        "tray_notice":     "O 9Router Manager continua rodando aqui. Clique no ícone para abrir.",
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
        "nav_savers":      "Savers",
        "nav_accounts":    "Usage",
        "nav_logs":        "Logs",
        # Accounts tab
        "accounts_title":  "Token usage & limits",
        "accounts_updated":"Updated at {time} · refreshes every 1 min",
        "accounts_empty":  "No accounts found.",
        "accounts_hint":   "Start 9Router on the Dashboard and click Refresh.",
        "accounts_offline":"9Router is not running.",
        "accounts_error":  "Could not read this account's quotas right now.",
        "accounts_no_quota":"This provider does not report quotas.",
        "accounts_unlimited":"Unlimited",
        "accounts_left":   "left",
        "accounts_reset":  "resets in",
        "accounts_loading":"Loading quotas…",
        "accounts_open_dash": "Open Dashboard",
        "accounts_session":"session",
        "accounts_weekly": "weekly",
        "accounts_credit": "credit",
        # Savers
        "savers_title":    "Token savers",
        "savers_intro":    "Extras that cut the tokens sent and received. 9Router already has Caveman and Headroom modes; Headroom needs the program below running to work.",
        "hr_title":        "Headroom — compresses what the agent reads",
        "hr_text":         "Compresses tool outputs, logs and JSON before they reach the model (20% to 90% fewer tokens). Runs on your PC on port 8787, where 9Router's Headroom mode sends requests. Starts together with 9Router.",
        "hr_missing":      "Not installed",
        "hr_stopped":      "Installed — stopped",
        "hr_running":      "Running on port 8787 ✓",
        "hr_installing":   "Installing (may take a few minutes)…",
        "btn_install":     "Install",
        "btn_start_short": "Start",
        "btn_stop_short":  "Stop",
        "cv_title":        "Caveman — short answers and more",
        "cv_text":         "Makes the agent answer briefly (code untouched) and shrinks logs, JSON and web pages. The install opens a window where you review and confirm what changes.",
        "cv_order":        "Important: connect your tools to 9Router (Tools tab) BEFORE installing. Caveman leaves a tool alone when it already points to another address, so the 9Router route stays.",
        "cv_telemetry":    "Caveman sends anonymous usage statistics (no content, with your IP). Use 'Turn off telemetry' to stop it.",
        "cv_missing":      "Not installed",
        "cv_installed":    "Installed ✓ ({v})",
        "btn_cv_status":   "Show status",
        "btn_cv_telemetry":"Turn off telemetry",
        "btn_uninstall":   "Uninstall",
        "saver_hr_down":   "Headroom (on in 9Router, but not running — see the Savers tab)",
        "tool_other":      "Points to another proxy — {url}",
        "tool_other_cv":   "Uses Caveman, not 9Router — {url}",
        "route_caveman":   "Claude Code goes through Caveman, not 9Router, so 9Router doesn't count that usage — its savings show in the Caveman card below.",
        "cv_card_title":   "Caveman savings (last 30 days)",
        "cv_saved":        "Tokens saved",
        "cv_requests":     "Requests",
        "cv_pct":          "of input",
        "cv_usd":          "Equivalent (USD)",
        "btn_cv_report":   "Open report",
        "cv_note":         "Caveman's own estimate. On a subscription (Pro/Max) the USD value is only a reference — it doesn't lower your bill.",
        "version":         "v0.5.x",
        "btn_background":  "Run in background",
        "theme_dark":      "Theme: dark",
        "theme_light":     "Theme: light",
        # Dashboard
        "dash_title":      "Dashboard",
        "status_running":  "Running",
        "status_stopped":  "Stopped",
        "btn_start":       "Start 9Router",
        "btn_stop":        "Stop 9Router",
        # Checklist
        "check_title":     "To save tokens",
        "check_all_ok":    "All set — 9Router is being used.",
        "check_missing":   "{n} step(s) missing. Follow the list below.",
        "step_server":     "1. 9Router running",
        "step_password":   "2. Own password created (not the default 123456)",
        "step_provider":   "3. AI provider added ({n})",
        "step_tool":       "4. Tool connected to 9Router ({n})",
        "step_traffic":    "5. Usage going through 9Router",
        "step_traffic_hint": "Restart the connected tool and use it as usual.",
        "act_start":       "Start",
        "act_password":    "Create password",
        "act_provider":    "Open Providers",
        "act_tool":        "Connect a tool",
        "saver_on":        "Saving modes active in 9Router: {modes}",
        "saver_off":       "No saving mode active. Turn one on in Token Saver.",
        # Usage
        "savings_title":   "Usage through 9Router",
        "stat_tokens":     "Tokens",
        "stat_requests":   "Requests",
        "stat_cost":       "Cost (USD)",
        "stat_empty":      "No usage recorded yet.",
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
        "tools_failed":    "Failed:",
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
        # Tray
        "tray_open":       "Open 9Router Manager",
        "tray_quit":       "Quit (stops 9Router)",
        "tray_notice":     "9Router Manager keeps running here. Click the icon to open it.",
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


# ── Error log (the .exe and pythonw have no console, so errors would vanish) ──

ERROR_LOG = CONFIG_FILE.parent / "app.log"


def log_error(exc_info=None):
    import traceback
    try:
        ERROR_LOG.parent.mkdir(parents=True, exist_ok=True)
        with ERROR_LOG.open("a", encoding="utf-8") as f:
            f.write(f"--- {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("".join(traceback.format_exception(*(exc_info or sys.exc_info()))))
    except OSError:
        pass


sys.excepthook = lambda *exc: log_error(exc)
threading.excepthook = lambda a: log_error((a.exc_type, a.exc_value, a.exc_traceback))
if TRAY_IMPORT_ERROR:
    log_error((type(TRAY_IMPORT_ERROR), TRAY_IMPORT_ERROR, TRAY_IMPORT_ERROR.__traceback__))


# ── Preferences ───────────────────────────────────────────────────────────────

def load_config() -> dict:
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_config(cfg: dict):
    try:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(cfg), encoding="utf-8")
    except OSError:
        pass


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
    # netstat prints in the console code page (accents in pt-BR); the frozen .exe defaults to UTF-8
    out = subprocess.run("netstat -ano -p TCP", shell=True, capture_output=True, text=True,
                         encoding="oem", errors="replace", creationflags=NO_WINDOW).stdout or ""
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


def router_snapshot() -> dict:
    """Password/provider/usage/saver state from 9router's DB. Reading the DB instead of trying a
    login matters: failed logins count toward 9router's lockout."""
    snap = {"password": None, "providers": 0, "requests": 0, "tokens": 0, "cost": 0.0, "savers": []}
    try:
        with _db() as c:
            row = c.execute("select data from settings where id=1").fetchone()
            settings = json.loads(row[0]) if row else {}
            snap["password"] = bool(settings.get("password"))
            snap["providers"] = c.execute(
                "select count(*) from providerConnections where isActive=1").fetchone()[0]
            snap["requests"], snap["tokens"], snap["cost"] = c.execute(
                "select count(*), coalesce(sum(coalesce(tokens, coalesce(promptTokens,0)+coalesce(completionTokens,0))),0),"
                " coalesce(sum(cost),0) from usageHistory").fetchone()
        if settings.get("cavemanEnabled"):
            level = settings.get("cavemanLevel")
            snap["savers"].append(f"Caveman ({level})" if level else "Caveman")
        if settings.get("headroomEnabled"):
            snap["savers"].append("Headroom")
    except Exception:
        pass
    return snap


def list_tools() -> list[dict]:
    out = subprocess.run("9router show --json", shell=True, capture_output=True, text=True,
                         stdin=subprocess.DEVNULL, creationflags=NO_WINDOW, encoding="utf-8").stdout
    start = out.find("[")
    return json.loads(out[start:]) if start >= 0 else []


def tool_route(tool: dict) -> str:
    """'router' if the tool really points at 9Router, 'other' if at another proxy, else 'off'.
    9router's own 'configured' flag is true for ANY custom base URL (e.g. Caveman's)."""
    url = tool.get("baseUrl") or ""
    if not url:
        return "off"
    return "router" if f":{ROUTER_PORT}" in url else "other"


def caveman_stats() -> dict | None:
    r = subprocess.run("caveman stats --json", shell=True, capture_output=True, text=True, stdin=subprocess.DEVNULL,
                       creationflags=NO_WINDOW, encoding="utf-8", errors="replace")
    start = r.stdout.find("{")
    if r.returncode != 0 or start < 0:
        return None
    try:
        return json.loads(r.stdout[start:]).get("totals")
    except ValueError:
        return None


def _cli_token() -> str:
    """The same local token 9router's own CLI sends (x-9r-cli-token): built from files only this
    Windows user can read, so no dashboard password is needed and no failed logins are counted."""
    data = ROUTER_DB.parent.parent
    try:
        raw = (data / "machine-id").read_text(encoding="utf-8").strip()
        secret = (data / "auth" / "cli-secret").read_text(encoding="utf-8").strip()
    except OSError:
        return ""
    return hashlib.sha256((raw + "9r-cli-auth" + secret).encode()).hexdigest()[:16] if raw else ""


def _router_get(path: str, token: str, timeout: float = 15):
    req = urllib.request.Request(ROUTER_ENDPOINT + path, headers={"x-9r-cli-token": token})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def list_accounts() -> list[dict] | None:
    """Live quotas per connected account, as 9router's dashboard shows them. None = 9router
    unreachable. Only display fields are copied: connections also carry OAuth secrets."""
    token = _cli_token()
    try:
        conns = _router_get("/api/providers", token, timeout=5).get("connections", [])
    except (urllib.error.URLError, OSError, ValueError, AttributeError):
        return None
    accounts = []
    for c in conns:
        if not c.get("isActive", True):
            continue
        acc = {"provider": c.get("provider", "?"), "name": c.get("email") or c.get("name") or "",
               "plan": "", "quotas": [], "error": False}
        try:
            usage = _router_get(f"/api/usage/{urllib.parse.quote(str(c.get('id', '')))}", token)
            acc["plan"] = usage.get("plan") or ""
            for qname, q in (usage.get("quotas") or {}).items():
                if isinstance(q, dict):
                    acc["quotas"].append({"name": qname, **{k: q.get(k) for k in
                                          ("used", "total", "remaining", "resetAt", "unlimited")}})
        except (urllib.error.URLError, OSError, ValueError, AttributeError):
            acc["error"] = True
        accounts.append(acc)
    return accounts


def _time_until(iso: str | None) -> str:
    """'2026-10-27T01:00:00.497Z' -> '3h 12m' (empty if missing or already past)."""
    try:
        secs = int((datetime.fromisoformat(iso.replace("Z", "+00:00")) - datetime.now(timezone.utc)).total_seconds())
    except (AttributeError, ValueError):
        return ""
    if secs <= 0:
        return ""
    d, h, m = secs // 86400, secs % 86400 // 3600, secs % 3600 // 60
    return " ".join(([f"{d}d"] if d else []) + ([f"{h}h"] if h else []) + ([f"{m}m"] if not d else []))


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
        ctk.CTkButton(row, text=t("btn_cancel"), width=100, fg_color="gray50", command=self.destroy).pack(side="left", padx=6)

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
        self._cfg = load_config()
        ctk.set_appearance_mode(self._cfg.get("theme", "dark"))
        ctk.set_default_color_theme("blue")
        super().__init__()
        self.title("9Router Manager")
        self.geometry("920x700")
        self.resizable(True, True)
        self.minsize(780, 560)
        if ICON_ICO.exists():
            self.iconbitmap(str(ICON_ICO))
        self.protocol("WM_DELETE_WINDOW", self.hide_to_tray)

        self._process: subprocess.Popen | None = None
        self._running = False
        self._lang = self._cfg.get("lang", "pt")
        self._translatable: list[tuple] = []   # (widget, text_key)
        self._current_tab = "Dashboard"
        self._tools: list[dict] | None = None
        self._tools_busy = False
        self._password: str | None = None      # memory only, never written to disk
        self._snap = router_snapshot()
        self._tray = None
        self._tray_notified = False
        self._hr_proc: subprocess.Popen | None = None
        self._hr_installing = False
        self._cv_version: str | None = None
        self._cv_stats: dict | None = None
        self._ticks = 0
        self._accounts_loading = False
        self._accounts_data: list[dict] | None = None   # last result, re-rendered on language change
        self._accounts_time = ""

        self._build_ui()
        self._apply_lang_buttons()
        self._migrate_old_env()
        self._refresh_status()
        self._refresh_snapshot_views()
        self._refresh_savers()
        # Worker threads call self.after(), which fails until mainloop runs, so start them from inside it
        self.after(0, self._load_tools)
        self.after(0, self._check_caveman)
        self.after(0, self._start_tray)
        self.after(1000, self._watch_port)
        self.after(5000, self._periodic)

    def report_callback_exception(self, *exc):
        log_error(exc)

    # ── Translation / theme ───────────────────────────────────────────────────

    def t(self, key: str, **kw) -> str:
        text = TEXTS[self._lang].get(key, TEXTS["en"].get(key, key))
        return text.format(**kw) if kw else text

    def _reg(self, widget, key: str):
        self._translatable.append((widget, key))
        return widget

    def _set_lang(self, lang: str):
        self._lang = lang
        self._cfg["lang"] = lang
        save_config(self._cfg)
        for widget, key in self._translatable:
            widget.configure(text=self.t(key))
        for tab_key, btn in self._nav_btns.items():
            btn.configure(text=self.t(f"nav_{tab_key.lower()}"))
        self._apply_lang_buttons()
        self._refresh_status()
        self._refresh_snapshot_views()
        self._render_tools()
        self._refresh_savers()
        if self._accounts_data is not None:
            self._render_accounts(self._accounts_data)
        if self._tray:
            self._tray.update_menu()

    def _apply_lang_buttons(self):
        self._btn_pt.configure(fg_color=SELECTED if self._lang == "pt" else "transparent")
        self._btn_en.configure(fg_color=SELECTED if self._lang == "en" else "transparent")
        dark = ctk.get_appearance_mode().lower() == "dark"
        self._theme_btn.configure(text=self.t("theme_dark") if dark else self.t("theme_light"))

    def _toggle_theme(self):
        new = "light" if ctk.get_appearance_mode().lower() == "dark" else "dark"
        ctk.set_appearance_mode(new)
        self._cfg["theme"] = new
        save_config(self._cfg)
        self._apply_lang_buttons()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        sidebar = ctk.CTkFrame(self, width=190, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        ctk.CTkLabel(sidebar, text="9Router", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(24, 4))
        self._reg(ctk.CTkLabel(sidebar, text=self.t("app_subtitle"), font=ctk.CTkFont(size=11), text_color="gray"),
                  "app_subtitle").pack(pady=(0, 20))

        self._nav_btns: dict[str, ctk.CTkButton] = {}
        for tab_key in ("Dashboard", "Tools", "Savers", "Accounts", "Logs"):
            btn = ctk.CTkButton(sidebar, text=self.t(f"nav_{tab_key.lower()}"), width=160, anchor="w",
                                fg_color="transparent", hover_color=HOVER, text_color=("gray10", "gray90"),
                                command=lambda k=tab_key: self._show_tab(k))
            btn.pack(padx=12, pady=4)
            self._nav_btns[tab_key] = btn

        lang_row = ctk.CTkFrame(sidebar, fg_color="transparent")
        lang_row.pack(side="bottom", pady=(0, 12))
        self._btn_pt = ctk.CTkButton(lang_row, text="PT", width=64, height=26, font=ctk.CTkFont(size=11, weight="bold"),
                                     hover_color=HOVER, text_color=("gray10", "gray90"),
                                     command=lambda: self._set_lang("pt"))
        self._btn_pt.pack(side="left", padx=(0, 4))
        self._btn_en = ctk.CTkButton(lang_row, text="EN", width=64, height=26, font=ctk.CTkFont(size=11, weight="bold"),
                                     hover_color=HOVER, text_color=("gray10", "gray90"),
                                     command=lambda: self._set_lang("en"))
        self._btn_en.pack(side="left")

        self._theme_btn = ctk.CTkButton(sidebar, text="", width=160, height=26, font=ctk.CTkFont(size=11),
                                        fg_color="transparent", border_width=1, hover_color=HOVER,
                                        text_color=("gray10", "gray90"), command=self._toggle_theme)
        self._theme_btn.pack(side="bottom", pady=(0, 6))
        if pystray:
            self._reg(ctk.CTkButton(sidebar, text=self.t("btn_background"), width=160, height=26,
                                    font=ctk.CTkFont(size=11), fg_color="gray40", hover_color="gray30",
                                    command=self.hide_to_tray), "btn_background").pack(side="bottom", pady=(0, 6))
        self._reg(ctk.CTkLabel(sidebar, text=self.t("version"), font=ctk.CTkFont(size=10), text_color="gray"),
                  "version").pack(side="bottom", pady=(0, 6))

        self._content = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self._content.pack(side="left", fill="both", expand=True, padx=16, pady=16)

        self._tabs: dict[str, ctk.CTkFrame] = {}
        self._build_dashboard()
        self._build_tools()
        self._build_savers()
        self._build_accounts()
        self._build_logs()
        self._show_tab("Dashboard")

    def _show_tab(self, name: str):
        self._current_tab = name
        for n, frame in self._tabs.items():
            frame.pack_forget()
            self._nav_btns[n].configure(fg_color="transparent")
        self._tabs[name].pack(fill="both", expand=True)
        self._nav_btns[name].configure(fg_color=SELECTED)
        if name == "Accounts":
            self.after(100, self._load_accounts)

    def _link_button(self, parent, key: str, url: str, width=150):
        return self._reg(ctk.CTkButton(parent, text=self.t(key), width=width, height=26, font=ctk.CTkFont(size=11),
                                       command=lambda: webbrowser.open(url)), key)

    # ── Dashboard tab ─────────────────────────────────────────────────────────

    def _build_dashboard(self):
        frame = ctk.CTkScrollableFrame(self._content, fg_color="transparent")
        self._tabs["Dashboard"] = frame

        self._reg(ctk.CTkLabel(frame, text=self.t("dash_title"), font=ctk.CTkFont(size=18, weight="bold")),
                  "dash_title").pack(anchor="w", pady=(0, 10))

        # Status card
        status_card = ctk.CTkFrame(frame)
        status_card.pack(fill="x", pady=(0, 8))
        row = ctk.CTkFrame(status_card, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=12)
        self._status_dot = ctk.CTkLabel(row, text="●", font=ctk.CTkFont(size=22), text_color="#e74c3c", width=30)
        self._status_dot.pack(side="left")
        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", padx=8)
        self._status_label = ctk.CTkLabel(info, text=self.t("status_stopped"), font=ctk.CTkFont(size=14, weight="bold"))
        self._status_label.pack(anchor="w")
        ctk.CTkLabel(info, text=f"Endpoint: {ROUTER_V1}", font=ctk.CTkFont(size=11), text_color="gray").pack(anchor="w")
        self._stop_btn = self._reg(ctk.CTkButton(row, text=self.t("btn_stop"), width=140,
                                                 fg_color="#c0392b", hover_color="#922b21",
                                                 command=self._stop_router, state="disabled"), "btn_stop")
        self._stop_btn.pack(side="right")
        self._start_btn = self._reg(ctk.CTkButton(row, text=self.t("btn_start"), width=140,
                                                  command=self._start_router), "btn_start")
        self._start_btn.pack(side="right", padx=8)

        # Checklist card
        check = ctk.CTkFrame(frame)
        check.pack(fill="x", pady=(0, 8))
        self._reg(ctk.CTkLabel(check, text=self.t("check_title"), font=ctk.CTkFont(size=13, weight="bold")),
                  "check_title").pack(anchor="w", padx=16, pady=(10, 0))
        self._check_summary = ctk.CTkLabel(check, text="", font=ctk.CTkFont(size=12, weight="bold"))
        self._check_summary.pack(anchor="w", padx=16, pady=(0, 6))

        self._steps: dict[str, tuple] = {}
        for key, act_key, action in (
            ("server", "act_start", self._start_router),
            ("password", "act_password", lambda: webbrowser.open(f"{DASH}/profile")),
            ("provider", "act_provider", lambda: webbrowser.open(f"{DASH}/providers")),
            ("tool", "act_tool", lambda: self._show_tab("Tools")),
            ("traffic", None, None),
        ):
            r = ctk.CTkFrame(check, fg_color="transparent")
            r.pack(fill="x", padx=16, pady=2)
            mark = ctk.CTkLabel(r, text="○", width=22, font=ctk.CTkFont(size=15, weight="bold"))
            mark.pack(side="left")
            lbl = ctk.CTkLabel(r, text="", anchor="w", font=ctk.CTkFont(size=12))
            lbl.pack(side="left", padx=4)
            btn = None
            if act_key:
                btn = self._reg(ctk.CTkButton(r, text=self.t(act_key), width=150, height=24,
                                              font=ctk.CTkFont(size=11), command=action), act_key)
            self._steps[key] = (mark, lbl, btn)
        self._traffic_hint = self._reg(ctk.CTkLabel(check, text=self.t("step_traffic_hint"), font=ctk.CTkFont(size=10),
                                                    text_color="gray"), "step_traffic_hint")
        self._route_note = self._reg(ctk.CTkLabel(check, text=self.t("route_caveman"), font=ctk.CTkFont(size=11, weight="bold"),
                                                  text_color="#3498db", wraplength=600, justify="left"), "route_caveman")
        self._saver_lbl = ctk.CTkLabel(check, text="", font=ctk.CTkFont(size=11), text_color="gray",
                                       wraplength=600, justify="left")
        self._saver_lbl.pack(anchor="w", padx=16, pady=(6, 10))

        # Usage card
        usage = ctk.CTkFrame(frame)
        usage.pack(fill="x", pady=(0, 8))
        hdr = ctk.CTkFrame(usage, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(10, 6))
        self._reg(ctk.CTkLabel(hdr, text=self.t("savings_title"), font=ctk.CTkFont(size=13, weight="bold")),
                  "savings_title").pack(side="left")
        self._link_button(hdr, "btn_open_dash", DASH, width=130).pack(side="right")
        self._link_button(hdr, "btn_token_saver", f"{DASH}/token-saver", width=140).pack(side="right", padx=6)

        stat_row = ctk.CTkFrame(usage, fg_color="transparent")
        stat_row.pack(fill="x", padx=16, pady=(0, 4))
        self._stat_tokens_lbl = ctk.CTkLabel(stat_row, text="0", font=ctk.CTkFont(size=22, weight="bold"), text_color="#27ae60")
        self._stat_tokens_lbl.pack(side="left", padx=(0, 2))
        self._reg(ctk.CTkLabel(stat_row, text=self.t("stat_tokens"), font=ctk.CTkFont(size=10), text_color="gray"),
                  "stat_tokens").pack(side="left", padx=(0, 20))
        self._stat_req_lbl = ctk.CTkLabel(stat_row, text="0", font=ctk.CTkFont(size=22, weight="bold"))
        self._stat_req_lbl.pack(side="left", padx=(0, 2))
        self._reg(ctk.CTkLabel(stat_row, text=self.t("stat_requests"), font=ctk.CTkFont(size=10), text_color="gray"),
                  "stat_requests").pack(side="left", padx=(0, 20))
        self._stat_cost_lbl = ctk.CTkLabel(stat_row, text="$0.00", font=ctk.CTkFont(size=22, weight="bold"), text_color="#e67e22")
        self._stat_cost_lbl.pack(side="left", padx=(0, 2))
        self._reg(ctk.CTkLabel(stat_row, text=self.t("stat_cost"), font=ctk.CTkFont(size=10), text_color="gray"),
                  "stat_cost").pack(side="left")
        self._usage_note = ctk.CTkLabel(usage, text="", font=ctk.CTkFont(size=10), text_color="gray")
        self._usage_note.pack(anchor="w", padx=16, pady=(2, 8))

        # Caveman card (shown only when Caveman is installed)
        self._cv_card = ctk.CTkFrame(frame)
        hdr = ctk.CTkFrame(self._cv_card, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(10, 6))
        self._reg(ctk.CTkLabel(hdr, text=self.t("cv_card_title"), font=ctk.CTkFont(size=13, weight="bold")),
                  "cv_card_title").pack(side="left")
        self._reg(ctk.CTkButton(hdr, text=self.t("btn_cv_report"), width=130, height=26, font=ctk.CTkFont(size=11),
                                command=lambda: CAVEMAN_REPORT.exists() and os.startfile(CAVEMAN_REPORT)),
                  "btn_cv_report").pack(side="right")
        row = ctk.CTkFrame(self._cv_card, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(0, 4))
        self._cv_vals = {}
        for key, color in (("cv_saved", "#27ae60"), ("cv_pct", None), ("cv_requests", None), ("cv_usd", "#e67e22")):
            v = ctk.CTkLabel(row, text="—", font=ctk.CTkFont(size=22, weight="bold"),
                             **({"text_color": color} if color else {}))
            v.pack(side="left", padx=(0, 2))
            self._reg(ctk.CTkLabel(row, text=self.t(key), font=ctk.CTkFont(size=10), text_color="gray"),
                      key).pack(side="left", padx=(0, 18))
            self._cv_vals[key] = v
        self._reg(ctk.CTkLabel(self._cv_card, text=self.t("cv_note"), font=ctk.CTkFont(size=10), text_color="gray",
                               wraplength=600, justify="left"), "cv_note").pack(anchor="w", padx=16, pady=(2, 8))

    def _refresh_snapshot_views(self):
        s = self._snap
        tools = self._tools or []
        connected = sum(1 for t in tools if tool_route(t) == "router")
        claude_elsewhere = any(t.get("id") == "claude" and tool_route(t) == "other" for t in tools)
        if claude_elsewhere:
            self._route_note.pack(anchor="w", padx=16, pady=(6, 0), before=self._saver_lbl)
        else:
            self._route_note.pack_forget()
        self._refresh_caveman_card()
        done = {
            "server": self._running,
            "password": bool(s["password"]),
            "provider": s["providers"] > 0,
            "tool": connected > 0,
            "traffic": s["requests"] > 0,
        }
        texts = {
            "server": self.t("step_server"),
            "password": self.t("step_password"),
            "provider": self.t("step_provider", n=s["providers"]),
            "tool": self.t("step_tool", n=connected),
            "traffic": self.t("step_traffic"),
        }
        for key, (mark, lbl, btn) in self._steps.items():
            ok = done[key]
            mark.configure(text="✓" if ok else "○", text_color="#27ae60" if ok else "#e67e22")
            lbl.configure(text=texts[key], text_color=("gray10", "gray90") if ok else "#e67e22")
            if btn:
                if ok:
                    btn.pack_forget()
                else:
                    btn.pack(side="right")
        # hint only matters when everything before step 5 is done
        if all(done[k] for k in ("server", "provider", "tool")) and not done["traffic"]:
            self._traffic_hint.pack(anchor="w", padx=42, before=self._saver_lbl)
        else:
            self._traffic_hint.pack_forget()

        missing = sum(1 for v in done.values() if not v)
        self._check_summary.configure(
            text=self.t("check_all_ok") if not missing else self.t("check_missing", n=missing),
            text_color="#27ae60" if not missing else "#e67e22",
        )
        savers = [self.t("saver_hr_down") if m == "Headroom" and not port_open(HEADROOM_PORT) else m
                  for m in s["savers"]]
        self._saver_lbl.configure(text=self.t("saver_on", modes=", ".join(savers)) if savers
                                  else self.t("saver_off"))

        self._stat_tokens_lbl.configure(text=f"{int(s['tokens']):,}".replace(",", "."))
        self._stat_req_lbl.configure(text=str(s["requests"]))
        self._stat_cost_lbl.configure(text=f"${s['cost']:.4f}")
        self._usage_note.configure(text="" if s["requests"] else self.t("stat_empty"))

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
            "btn_connect_all")
        self._connect_all_btn.pack(side="right", padx=6)

        self._tools_status = ctk.CTkLabel(frame, text="", font=ctk.CTkFont(size=11), text_color="#e67e22")
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
        self._refresh_snapshot_views()

    def _render_tools(self):
        for child in self._tools_list.winfo_children():
            child.destroy()
        if self._tools is None:
            ctk.CTkLabel(self._tools_list, text=self.t("tools_loading"), text_color="gray").pack(padx=14, pady=10, anchor="w")
            return
        state = "disabled" if self._tools_busy else "normal"
        for tool in self._tools:
            row = ctk.CTkFrame(self._tools_list, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=3)
            route = tool_route(tool)
            url = tool.get("baseUrl") or ""
            dot = {"router": "#27ae60", "other": "#3498db"}.get(route, "gray50")
            ctk.CTkLabel(row, text="●", text_color=dot, width=18).pack(side="left")
            ctk.CTkLabel(row, text=tool.get("name", tool.get("id", "?")), width=150, anchor="w",
                         font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
            if route == "router":
                status = self.t("tool_on", url=url)
            elif route == "other":
                status = self.t("tool_other_cv" if f":{CAVEMAN_PORT}" in url else "tool_other", url=url)
            else:
                status = self.t("tool_off")
            ctk.CTkLabel(row, text=status, anchor="w", text_color="gray", font=ctk.CTkFont(size=11)).pack(side="left", padx=6)
            remove_state = "disabled" if self._tools_busy or route == "off" else "normal"
            connect_state = "disabled" if self._tools_busy or route == "router" else "normal"
            ctk.CTkButton(row, text=self.t("btn_remove"), width=80, height=26, fg_color="gray50", state=remove_state,
                          command=lambda i=tool["id"]: self._reset(i)).pack(side="right", padx=(4, 0))
            ctk.CTkButton(row, text=self.t("btn_connect"), width=90, height=26, state=connect_state,
                          command=lambda i=tool["id"]: self._connect(i)).pack(side="right")
        self._connect_all_btn.configure(state=state)

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
            lines = [line.strip() for line in output.splitlines() if line.strip()]
            for line in lines:
                self._log(f"[tools] {line}")
            # 9router marks its errors with ❌, e.g. "Login failed (401): Invalid password. 2 attempt(s) left"
            reason = next((line.lstrip("❌ ").strip() for line in lines if line.startswith("❌")),
                          lines[-1] if lines else "")
            self.after(0, self._tool_cmd_done, proc.returncode == 0, is_login and "Login failed" in output, reason)

        threading.Thread(target=work, daemon=True).start()

    def _tool_cmd_done(self, ok: bool, bad_password: bool, reason: str):
        if bad_password:
            self._password = None   # ask again next time
        self._tools_busy = False
        if ok:
            text = self.t("tools_done")
        else:
            text = f"{self.t('tools_failed')} {reason}".strip()
        self._tools_status.configure(text=text, wraplength=600, justify="left")
        self._load_tools()

    # ── Savers tab (Headroom + Caveman) ───────────────────────────────────────

    def _build_savers(self):
        frame = ctk.CTkScrollableFrame(self._content, fg_color="transparent")
        self._tabs["Savers"] = frame

        hdr = ctk.CTkFrame(frame, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 4))
        self._reg(ctk.CTkLabel(hdr, text=self.t("savers_title"), font=ctk.CTkFont(size=18, weight="bold")),
                  "savers_title").pack(side="left")
        self._link_button(hdr, "btn_token_saver", f"{DASH}/token-saver", width=150).pack(side="right")
        self._reg(ctk.CTkLabel(frame, text=self.t("savers_intro"), font=ctk.CTkFont(size=11), text_color="gray",
                               wraplength=620, justify="left"), "savers_intro").pack(anchor="w", pady=(0, 10))

        def card(title_key, text_key):
            c = ctk.CTkFrame(frame)
            c.pack(fill="x", pady=(0, 10))
            self._reg(ctk.CTkLabel(c, text=self.t(title_key), font=ctk.CTkFont(size=13, weight="bold")),
                      title_key).pack(anchor="w", padx=14, pady=(10, 2))
            self._reg(ctk.CTkLabel(c, text=self.t(text_key), font=ctk.CTkFont(size=11), text_color="gray",
                                   wraplength=600, justify="left"), text_key).pack(anchor="w", padx=14)
            status = ctk.CTkLabel(c, text="", font=ctk.CTkFont(size=12, weight="bold"))
            status.pack(anchor="w", padx=14, pady=(6, 4))
            row = ctk.CTkFrame(c, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=(0, 10))
            return c, status, row

        def button(row, key, cmd, **kw):
            b = self._reg(ctk.CTkButton(row, text=self.t(key), width=130, height=28, command=cmd, **kw), key)
            b.pack(side="left", padx=(0, 6))
            return b

        _, self._hr_status, row = card("hr_title", "hr_text")
        self._hr_install_btn = button(row, "btn_install", self._install_headroom)
        self._hr_start_btn = button(row, "btn_start_short", self._start_headroom)
        self._hr_stop_btn = button(row, "btn_stop_short", self._stop_headroom, fg_color="#c0392b", hover_color="#922b21")

        cv_card, self._cv_status, row = card("cv_title", "cv_text")
        self._reg(ctk.CTkLabel(cv_card, text=self.t("cv_order"), font=ctk.CTkFont(size=11, weight="bold"),
                               text_color="#e67e22", wraplength=600, justify="left"),
                  "cv_order").pack(anchor="w", padx=14, pady=(0, 4), before=row)
        self._reg(ctk.CTkLabel(cv_card, text=self.t("cv_telemetry"), font=ctk.CTkFont(size=10), text_color="gray",
                               wraplength=600, justify="left"), "cv_telemetry").pack(anchor="w", padx=14, pady=(0, 6), before=row)
        self._cv_install_btn = button(row, "btn_install", lambda: self._open_terminal("Caveman", CAVEMAN_INSTALL))
        button(row, "btn_cv_status", lambda: self._open_terminal("Caveman", "caveman status"))
        button(row, "btn_cv_telemetry", lambda: self._open_terminal("Caveman", "caveman telemetry off"))
        button(row, "btn_uninstall", lambda: self._open_terminal("Caveman", CAVEMAN_UNINSTALL), fg_color="gray50")

    def _refresh_savers(self):
        if self._hr_installing:
            text, color = self.t("hr_installing"), "#e67e22"
        elif port_open(HEADROOM_PORT):
            text, color = self.t("hr_running"), "#27ae60"
        elif HEADROOM_EXE.exists():
            text, color = self.t("hr_stopped"), "#e67e22"
        else:
            text, color = self.t("hr_missing"), "gray50"
        self._hr_status.configure(text=text, text_color=color)
        installed = HEADROOM_EXE.exists()
        running = port_open(HEADROOM_PORT)
        self._hr_install_btn.configure(state="disabled" if installed or self._hr_installing else "normal")
        self._hr_start_btn.configure(state="normal" if installed and not running else "disabled")
        self._hr_stop_btn.configure(state="normal" if running else "disabled")

        if self._cv_version:
            self._cv_status.configure(text=self.t("cv_installed", v=self._cv_version), text_color="#27ae60")
        else:
            self._cv_status.configure(text=self.t("cv_missing"), text_color="gray50")

    def _check_caveman(self):
        def work():
            r = subprocess.run("caveman --version", shell=True, capture_output=True, text=True,
                               stdin=subprocess.DEVNULL, creationflags=NO_WINDOW, encoding="utf-8", errors="replace")
            version = (r.stdout.strip().splitlines() or [""])[-1] if r.returncode == 0 else None
            stats = caveman_stats() if version else None
            self.after(0, self._set_caveman_version, version, stats)

        threading.Thread(target=work, daemon=True).start()

    def _set_caveman_version(self, version: str | None, stats: dict | None):
        self._cv_version = version
        self._cv_stats = stats
        self._refresh_savers()
        self._refresh_caveman_card()

    def _refresh_caveman_card(self):
        st = self._cv_stats
        if not st:
            self._cv_card.pack_forget()
            return
        self._cv_card.pack(fill="x", pady=(0, 8))
        saved, before = st.get("saved_tokens") or 0, st.get("before_tokens") or 0
        usd = st.get("api_equivalent_savings_usd") or 0
        self._cv_vals["cv_saved"].configure(text=f"{int(saved):,}".replace(",", "."))
        self._cv_vals["cv_pct"].configure(text=f"{saved / before:.1%}" if before else "—")
        self._cv_vals["cv_requests"].configure(text=str(st.get("requests") or 0))
        self._cv_vals["cv_usd"].configure(text=f"${usd:.4f}")

    def _open_terminal(self, title: str, command: str):
        # Interactive installers need a real console the user can read and answer
        self._log(f"[{title}] {command}")
        subprocess.Popen(f'start "{title}" cmd /k "{command}"', shell=True, creationflags=NO_WINDOW)

    def _install_headroom(self):
        self._hr_installing = True
        self._refresh_savers()
        self._show_tab("Logs")

        def work():
            base_python = "py -3" if getattr(sys, "frozen", False) else f'"{Path(sys.executable).with_name("python.exe")}"'
            vpy = f'"{HEADROOM_VENV / "Scripts" / "python.exe"}"'
            ok = True
            for cmd in (f'{base_python} -m venv "{HEADROOM_VENV}"',
                        f"{vpy} -m pip install --disable-pip-version-check --upgrade pip",
                        f'{vpy} -m pip install --disable-pip-version-check "headroom-ai[proxy]"'):
                self._log(f"[headroom] {cmd}")
                proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                        bufsize=1, encoding="utf-8", errors="replace", creationflags=NO_WINDOW)
                for line in proc.stdout:
                    if line.strip() and not line.startswith("  "):
                        self._log(f"[headroom] {line.rstrip()}")
                if proc.wait() != 0:
                    ok = False
                    break
            self._log("[headroom] OK" if ok else "[headroom] FAILED")
            self.after(0, self._headroom_install_done, ok)

        threading.Thread(target=work, daemon=True).start()

    def _headroom_install_done(self, ok: bool):
        self._hr_installing = False
        if ok and self._running:
            self._start_headroom()
        self._refresh_savers()

    def _start_headroom(self):
        if not HEADROOM_EXE.exists() or port_open(HEADROOM_PORT):
            return
        self._log(f"[headroom] {HEADROOM_CMD}")
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env.setdefault("HEADROOM_BEACON", "off")   # Headroom uploads session summaries unless opted out
        self._hr_proc = subprocess.Popen(HEADROOM_CMD, shell=True, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                         stderr=subprocess.STDOUT, text=True, bufsize=1, encoding="utf-8",
                                         errors="replace", env=env, creationflags=NO_WINDOW)
        proc = self._hr_proc

        def stream():
            for line in proc.stdout:
                if line.strip():
                    self._log(f"[headroom] {line.rstrip()}")

        threading.Thread(target=stream, daemon=True).start()
        self.after(3000, self._refresh_savers)

    def _stop_headroom(self):
        if self._hr_proc:
            kill_tree(self._hr_proc.pid)
            self._hr_proc = None
        for pid in pids_listening_on(HEADROOM_PORT):
            kill_tree(pid)
        self._refresh_savers()

    # ── Accounts / Quotas tab ────────────────────────────────────────────────

    def _build_accounts(self):
        frame = ctk.CTkScrollableFrame(self._content, fg_color="transparent")
        self._tabs["Accounts"] = frame

        hdr = ctk.CTkFrame(frame, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 10))
        self._reg(ctk.CTkLabel(hdr, text=self.t("accounts_title"),
                               font=ctk.CTkFont(size=18, weight="bold")), "accounts_title").pack(side="left")
        btn_row = ctk.CTkFrame(hdr, fg_color="transparent")
        btn_row.pack(side="right")
        self._reg(ctk.CTkButton(btn_row, text=self.t("btn_refresh"), width=80, height=26,
                                font=ctk.CTkFont(size=11), command=self._load_accounts),
                  "btn_refresh").pack(side="left", padx=4)
        self._link_button(btn_row, "accounts_open_dash", DASH, width=140).pack(side="left")

        self._accounts_body = ctk.CTkFrame(frame, fg_color="transparent")
        self._accounts_body.pack(fill="both", expand=True)

    def _load_accounts(self, quiet: bool = False):
        if self._accounts_loading:
            return
        self._accounts_loading = True
        if not (quiet and self._accounts_data):
            self._render_accounts(None)  # loading state; auto-refresh keeps the old cards until new data arrives

        def work():
            data = list_accounts()
            self.after(0, self._finish_accounts, data)

        threading.Thread(target=work, daemon=True).start()

    def _finish_accounts(self, data: list[dict] | None):
        self._accounts_loading = False
        self._accounts_data = data
        self._accounts_time = datetime.now().strftime("%H:%M")
        self._render_accounts(data, offline=data is None)

    def _render_accounts(self, accounts: list[dict] | None, offline: bool = False):
        for w in self._accounts_body.winfo_children():
            w.destroy()

        if accounts is None and not offline:
            ctk.CTkLabel(self._accounts_body, text=self.t("accounts_loading"),
                         text_color="gray").pack(anchor="w", pady=20)
            return

        if not accounts:
            ctk.CTkLabel(self._accounts_body, text=self.t("accounts_offline" if offline else "accounts_empty"),
                         text_color="gray", font=ctk.CTkFont(size=13)).pack(anchor="w", pady=(20, 6))
            ctk.CTkLabel(self._accounts_body, text=self.t("accounts_hint"),
                         text_color="gray", font=ctk.CTkFont(size=11)).pack(anchor="w")
            return

        ctk.CTkLabel(self._accounts_body, text=self.t("accounts_updated", time=self._accounts_time),
                     text_color="gray", font=ctk.CTkFont(size=11)).pack(anchor="w", pady=(0, 6))
        for account in accounts:
            self._render_account_card(account)

    def _render_account_card(self, account: dict):
        card = ctk.CTkFrame(self._accounts_body)
        card.pack(fill="x", pady=(0, 10))

        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=14, pady=(10, 6))
        ctk.CTkLabel(hdr, text="●", text_color="#e74c3c" if account["error"] else "#2ecc71",
                     font=ctk.CTkFont(size=16)).pack(side="left")
        ctk.CTkLabel(hdr, text=f"{account['provider'].capitalize()}  {account['name']}".strip(),
                     font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", padx=8)
        if account["plan"]:
            ctk.CTkLabel(hdr, text=account["plan"], font=ctk.CTkFont(size=11),
                         text_color="gray").pack(side="right")

        if account["error"]:
            message = self.t("accounts_error")
        elif not account["quotas"]:
            message = self.t("accounts_no_quota")
        else:
            message = None
        if message:
            ctk.CTkLabel(card, text=message, font=ctk.CTkFont(size=11),
                         text_color="gray").pack(anchor="w", padx=14, pady=(0, 10))
            return
        for q in account["quotas"]:
            self._render_quota_row(card, q)
        ctk.CTkFrame(card, height=6, fg_color="transparent").pack()

    def _quota_label(self, name: str) -> str:
        # 9router names quotas like "session (5h)", "weekly (7d)" or "credit"
        for key in ("session", "weekly", "credit"):
            if name.lower().startswith(key):
                return self.t(f"accounts_{key}") + name[len(key):]
        return name

    def _render_quota_row(self, parent, quota: dict):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=3)
        ctk.CTkLabel(row, text=self._quota_label(quota["name"]), width=130, anchor="w",
                     font=ctk.CTkFont(size=11)).pack(side="left")

        if quota.get("unlimited"):
            ctk.CTkLabel(row, text=self.t("accounts_unlimited"), font=ctk.CTkFont(size=11),
                         text_color="gray").pack(side="left", padx=8)
            return

        total = quota.get("total") or 0
        remaining = quota.get("remaining")
        if remaining is None:
            remaining = total - (quota.get("used") or 0)
        ratio = max(0.0, min(1.0, remaining / total)) if total else 0.0
        color = "#2ecc71" if ratio > 0.5 else ("#f39c12" if ratio > 0.2 else "#e74c3c")

        bar = ctk.CTkProgressBar(row, width=180, height=12, corner_radius=4, progress_color=color)
        bar.set(ratio)
        bar.pack(side="left", padx=(8, 6))

        stats = f"{self.t('accounts_left')}: {remaining}/{total}   {round(ratio * 100)}%"
        left = _time_until(quota.get("resetAt"))
        if left:
            stats += f"   {self.t('accounts_reset')} {left}"
        ctk.CTkLabel(row, text=stats, font=ctk.CTkFont(size=11), text_color="gray").pack(side="left")

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

    # ── Tray / background ─────────────────────────────────────────────────────

    def _start_tray(self):
        if not pystray:
            return
        image = Image.open(ICON_PNG) if ICON_PNG.exists() else Image.new("RGB", (64, 64), (217, 119, 87))
        menu = pystray.Menu(
            pystray.MenuItem(lambda _i: self.t("tray_open"), lambda: self.after(0, self.show_window), default=True),
            pystray.MenuItem(lambda _i: self.t("tray_quit"), lambda: self.after(0, self.quit_app)),
        )
        self._tray = pystray.Icon("9router-manager", image, "9Router Manager", menu)
        threading.Thread(target=self._tray.run, daemon=True).start()

    def hide_to_tray(self):
        if not self._tray:
            self.quit_app()
            return
        self.withdraw()
        if not self._tray_notified:
            self._tray_notified = True
            try:
                self._tray.notify(self.t("tray_notice"), "9Router Manager")
            except Exception:
                pass

    def show_window(self):
        self.deiconify()
        self.lift()
        self.focus_force()

    def quit_app(self):
        self._password = None
        try:
            self._stop_router()
            self._stop_headroom()
            if self._tray:
                self._tray.stop()
        except Exception:
            log_error()
        finally:
            self.destroy()   # always close, even if stopping a server failed

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
        if running:
            self._start_headroom()   # no-op if not installed or already up
        self._refresh_status()
        self._refresh_snapshot_views()

    def _watch_port(self):
        self._set_running(port_open())
        self.after(2000, self._watch_port)

    def _periodic(self):
        def work():
            snap = router_snapshot()
            self.after(0, self._apply_snapshot, snap)

        threading.Thread(target=work, daemon=True).start()
        self._ticks += 1
        if self._ticks % 12 == 0:   # every minute: caveman stats and tool routes spawn node, so less often
            self._check_caveman()
            self._load_tools_quiet()
            if self._current_tab == "Accounts" and self.state() != "withdrawn":
                self._load_accounts(quiet=True)
        self.after(5000, self._periodic)

    def _load_tools_quiet(self):
        def work():
            try:
                tools = list_tools()
            except Exception:
                return
            self.after(0, self._set_tools, tools)

        if not self._tools_busy:
            threading.Thread(target=work, daemon=True).start()

    def _apply_snapshot(self, snap: dict):
        self._snap = snap
        self._refresh_snapshot_views()
        self._refresh_savers()

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
            self._status_dot.configure(text_color="#27ae60")
            self._status_label.configure(text=self.t("status_running"))
            self._start_btn.configure(state="disabled")
            self._stop_btn.configure(state="normal")
            self._tools_status.configure(text="")
        else:
            self._status_dot.configure(text_color="#e74c3c")
            self._status_label.configure(text=self.t("status_stopped"))
            self._start_btn.configure(state="normal")
            self._stop_btn.configure(state="disabled")


if __name__ == "__main__":
    App().mainloop()
