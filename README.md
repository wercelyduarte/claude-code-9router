# claude-code-9router

A Windows app (Portuguese / English) that runs [9Router](https://9router.com) and connects your AI coding tools to it: **Claude Code, Codex, OpenCode, Cline, Kilo Code, Factory Droid, Crush, Pi, Oh My Pi**, plus **Kiro, Cursor and GitHub Copilot** through the 9Router dashboard.

---

## What is 9Router?

9Router is an open-source gateway that runs on your own PC. Your AI tools send their requests to it, and it forwards them to the AI providers you configured (Anthropic, OpenAI, Gemini, Kiro, and 40+ others). It can switch to a cheaper or free provider when a quota runs out, and it has token-saving features.

```
Claude Code / Codex / Cline / ...      Kiro IDE / Cursor / Copilot
              │                                   │ (interception, MITM)
              ▼                                   ▼
        9Router on your PC — http://localhost:20128
              │
              ├── Kiro AI (free)
              ├── Anthropic, OpenAI, Gemini ...
              └── fallback providers
```

---

## Installation

You need **Python 3.10+** and **Node.js 18+**.

```bash
git clone https://github.com/wercelyduarte/claude-code-9router.git
cd claude-code-9router
```

Double-click **`rodar.bat`**. On first run it installs 9Router (npm) and the Python dependency (`customtkinter`), then opens the app.

To build a standalone `.exe`: `build.bat`. To build an `.msi` installer: `build.bat msi`.

---

## First use, step by step

### 1. Start 9Router
**Painel / Dashboard** tab → **Iniciar 9Router / Start 9Router**. The dot turns green ("Running").

### 2. Create your dashboard password
9Router protects its dashboard with a password. **If you never created one, the password is `123456`.** In that case the app shows an orange warning. Click **Criar / alterar senha** (Create / change password) and set your own on the page that opens.

> The app never stores your password. It only reads (read-only) whether one exists, so it can show the warning.
>
> **Warning:** 9Router locks the login after **5 wrong attempts**.

### 3. Add an AI provider
Click **Abrir Dashboard** (Open Dashboard) → **Providers**. The quickest free option is **Kiro AI**: click *Connect* and sign in with your Kiro account. You can add others with an API key or OAuth.

### 4. Connect your tools
**Ferramentas / Tools** tab:

| Group | What to do |
|---|---|
| **Command-line tools** (Claude Code, Codex, OpenCode, Cline, Kilo Code, Factory Droid, Crush, Pi, Oh My Pi) | Click **Conectar / Connect** on the tool, or **Conectar todas / Connect all**. The app asks for your dashboard password once and keeps it in memory until you close the app. 9Router then writes the tool's config file and keeps a backup of the original (`*.bak-9router`). |
| **Kiro AI as a free provider** | **Abrir Providers** → Connect Kiro AI. Every tool above can then use Kiro's models. |
| **Kiro IDE, Cursor, GitHub Copilot** | **Abrir MITM** → enable it and follow the steps. These IDEs are routed by interception, and the page may ask you to install a certificate. |

**Restart the tool** after connecting it.

### 5. Turn on the token savers (optional)
**Economia / Savers** tab:

| Saver | What it does | In the app |
|---|---|---|
| **[Headroom](https://github.com/headroomlabs-ai/headroom)** | Compresses tool outputs, logs and JSON before they reach the model (20–90% fewer tokens). 9Router's *Headroom* mode sends requests to it at `localhost:8787`, **so that mode does nothing unless Headroom is running.** | **Install** puts `headroom-ai[proxy]` in its own isolated environment (`%APPDATA%\9RouterManager\headroom-venv`). After that it starts and stops together with 9Router. Its anonymous usage upload is turned off. |
| **[Caveman](https://github.com/JuliusBrussee/caveman)** | Short answers with code kept intact, and shrinks logs, JSON and web pages. | **Install** opens a window running `npx @caveman-ai/cli@latest`, where you review and confirm what it changes. Also: *Show status*, *Turn off telemetry*, *Uninstall*. |

> **Order matters for Caveman:** connect your tools to 9Router (step 4) **before** installing it. Caveman leaves a tool alone when it already points to another address, so the route through 9Router stays. Caveman sends anonymous usage statistics (no content, with your IP) by default; use *Turn off telemetry* to stop it.

9Router also has built-in saving modes (Caveman, Headroom). See and change them with the **Token Saver** button.

### 6. Turning it off
- To stop using 9Router in a tool: **Ferramentas → Remover / Remove** on that tool, then restart the tool. Its original configuration is restored.
- **Remove the tool first, then stop 9Router.** If a tool is still connected while 9Router is stopped, its requests will fail.

---

## What the Dashboard shows

| Item | Meaning |
|---|---|
| **Running / Stopped** | Whether the 9Router server is answering on port 20128. Stopped means nothing goes through 9Router. |
| **To save tokens** (checklist) | The 5 steps that must all be done before 9Router saves anything: server running, own password, provider added, tool connected, usage going through. Each missing step has a button that takes you there. Below it: which saving modes are on, and a warning if Headroom mode is on but Headroom isn't running. |
| **Usage and Savings** | Requests, tokens and cost that went through 9Router, read from its local database (updated every 5 s). |

**If it isn't saving anything:** look at the checklist. The most common cause is that no tool is connected (step 4). In that case your tools still talk to the provider directly and 9Router never sees the traffic.

## Window, background and theme

- **Close (X) or "Rodar em segundo plano" (Run in background)** hides the window to the tray, next to the clock. 9Router and Headroom **keep running**. Click the tray icon to open the window again. To really exit, right-click the icon → **Quit**, which also stops 9Router and Headroom.
- `rodar.bat` closes its black console window once the app opens.
- **Tema: escuro / claro** (Theme: dark / light) switches the theme. **PT / EN** switches the language. Both are remembered in `%APPDATA%\9RouterManager\config.json`.
- The app icon is made by `gerar_icone.py` (run it again to recreate `icone.ico` / `icone.png`).

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `rodar.bat` opens a black window and closes | Run it from a terminal (`cmd`, then `rodar.bat`) to read the message. Check that Python and Node.js are installed. |
| Start turns back to Stopped | Open the **Logs** tab. Another program may be using port 20128. |
| "Login failed" when connecting | Wrong dashboard password. If you never created one, use `123456`. After 5 errors the login locks for a while. |
| A tool shows "Connected" but doesn't work | Restart the tool and check that a provider is added in the dashboard. |
| Numbers stay at 0 | Follow the checklist on the Dashboard. Usually no tool is connected yet, or the tool wasn't restarted after connecting. |
| The window disappeared | It's in the tray next to the clock (you may need to click ^ to see hidden icons). |

For command-line setup without the app, see [docs/manual-setup.md](docs/manual-setup.md).

---

## Project structure

```
claude-code-9router/
├── rodar.bat               # launcher: checks/installs everything and opens the app
├── bootstrap.py            # installs missing dependencies, then opens app.py
├── app.py                  # the app (CustomTkinter)
├── build.bat / setup.py    # build .exe / .msi (cx_Freeze)
├── gerar_icone.py          # draws icone.ico / icone.png
├── requirements.txt        # runtime dependency
├── requirements-build.txt  # build dependencies
└── docs/manual-setup.md    # manual setup with commands
```

## License

MIT
