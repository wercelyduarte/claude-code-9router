# claude-code-9router

A local gateway manager that routes **Claude Code** (and other AI coding tools) through [9Router](https://9router.com) — giving you access to 60+ AI providers, a three-tier fallback system, and token-saving features, all from a single GUI.

---

## What is 9Router?

9Router is an open-source local proxy that sits between your coding tools and AI providers. It exposes one OpenAI-compatible endpoint at `http://localhost:20128/v1` and handles:

- Routing across 60+ providers (Anthropic, OpenAI, Gemini, Groq, and more)
- Automatic fallback (subscription → cheap → free) when quotas run out
- Token savings via RTK and Caveman Mode
- Cloud Sync + Cloudflare Tunnel for remote access

---

## Prerequisites

| Requirement | Version |
|---|---|
| Node.js | ≥ 18 |
| npm | ≥ 8 |
| Python | ≥ 3.10 |

---

## Installation

### Step 1 — Install 9Router

```bash
npm install -g --allow-scripts=9router 9router
```

### Step 2 — Clone this repo

```bash
git clone https://github.com/wercelyduarte/claude-code-9router.git
cd claude-code-9router
```

### Step 3 — Install Python dependencies

```bash
pip install -r requirements.txt
```

---

## Running the GUI

```bash
python app.py
```

The app has three sections:

### Dashboard
- **Status indicator** — shows whether 9Router is running (green) or stopped (red)
- **Start / Stop buttons** — launches or terminates the local 9Router process

### Configure
- **Routing toggle** — sets or removes the `ANTHROPIC_BASE_URL` Windows environment variable so Claude Code sends requests through 9Router
- **settings.json viewer** — shows the current Claude Code configuration

### Logs
- **Live output** — streams everything 9Router prints to stdout in real time
- **Clear button** — wipes the log panel

---

## Enable / Disable Routing (Quick Reference)

### Enable (via GUI)
1. Start the app: `python app.py`
2. Dashboard → click **Start 9Router**
3. Configure tab → toggle **Route Claude Code through 9Router** ON
4. Restart Claude Code

### Disable (via GUI)
1. Configure tab → toggle OFF
2. Dashboard → click **Stop 9Router**
3. Restart Claude Code

### Enable / Disable manually
See [docs/manual-setup.md](docs/manual-setup.md) for PowerShell and shell commands.

---

## How it works

```
Claude Code
    │
    │  ANTHROPIC_BASE_URL=http://localhost:20128
    ▼
9Router (local proxy on :20128)
    │
    ├── Provider 1 (Anthropic)
    ├── Provider 2 (OpenAI)
    └── Provider N (fallback…)
```

When `ANTHROPIC_BASE_URL` is set, Claude Code sends its API requests to the local 9Router instance instead of `api.anthropic.com`. 9Router translates and routes the request to whichever provider is configured.

---

## Adding Providers

1. Start 9Router (via GUI or `9router` in terminal)
2. Open `http://localhost:20128` in your browser
3. Go to **Providers → Add Provider**
4. Enter your API key and save
5. Configure fallback order under **Routing**

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `'9router' not found` | Run `npm install -g --allow-scripts=9router 9router` |
| Routing not working after toggle | Restart Claude Code to pick up the new env var |
| Port 20128 in use | Kill the process using that port or change it in 9Router settings |
| GUI won't open | Run `pip install customtkinter` |

---

## Project Structure

```
claude-code-9router/
├── app.py              # Main GUI (CustomTkinter)
├── requirements.txt    # Python dependencies
├── docs/
│   └── manual-setup.md # Full manual instructions
└── README.md
```

---

## License

MIT
