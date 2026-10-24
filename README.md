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

### 5. Turning it off
- To stop using 9Router in a tool: **Ferramentas → Remover / Remove** on that tool, then restart the tool. Its original configuration is restored.
- **Remove the tool first, then stop 9Router.** If a tool is still connected while 9Router is stopped, its requests will fail.

---

## What the Dashboard shows

| Item | Meaning |
|---|---|
| **Running / Stopped** | Whether the 9Router server is answering on port 20128. Stopped means nothing goes through 9Router. |
| **Usage and Savings** | Requests, tokens and cost that went through 9Router, read from its local database (updated every 10 s). **Token Saver** opens 9Router's page with the savings details. |
| **Connected tools** | How many of the 9 command-line tools point to 9Router. |
| **Dashboard password** | *Created ✓*, or *Default (123456)* if you still need to create one. |

The **PT / EN** buttons at the bottom of the sidebar switch the language.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `rodar.bat` opens a black window and closes | Run it from a terminal (`cmd`, then `rodar.bat`) to read the message. Check that Python and Node.js are installed. |
| Start turns back to Stopped | Open the **Logs** tab. Another program may be using port 20128. |
| "Login failed" when connecting | Wrong dashboard password. If you never created one, use `123456`. After 5 errors the login locks for a while. |
| A tool shows "Connected" but doesn't work | Restart the tool and check that a provider is added in the dashboard. |
| Numbers stay at 0 | No tool has sent requests through 9Router yet. |

For command-line setup without the app, see [docs/manual-setup.md](docs/manual-setup.md).

---

## Project structure

```
claude-code-9router/
├── rodar.bat               # launcher: checks/installs everything and opens the app
├── bootstrap.py            # installs missing dependencies, then opens app.py
├── app.py                  # the app (CustomTkinter)
├── build.bat / setup.py    # build .exe / .msi (cx_Freeze)
├── requirements.txt        # runtime dependency
├── requirements-build.txt  # build dependencies
└── docs/manual-setup.md    # manual setup with commands
```

## License

MIT
