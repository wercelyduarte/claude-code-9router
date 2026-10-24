# Manual setup (without the app)

Everything the app does, as commands. They work in `cmd` or PowerShell on Windows.

## 1. Install 9Router

Requires Node.js 18+.

```bash
npm install -g --allow-scripts=9router 9router
9router --version
```

## 2. Start the server

```bash
9router --host 127.0.0.1 --no-browser --log
```

- `--log` skips the interactive menu and shows the server log.
- `--host 127.0.0.1` makes 9Router reachable only from your own PC. Without it, other computers on your network can reach it too.
- The dashboard is at `http://localhost:20128/dashboard`.

## 3. Create your password

If you never created one, the dashboard password is **`123456`**. Change it at `http://localhost:20128/dashboard/profile`.

Login locks after 5 wrong attempts.

## 4. Add a provider

Dashboard → **Providers**. For a free option, connect **Kiro AI** and sign in with your Kiro account.

## 5. Connect command-line tools

```bash
9router connect http://127.0.0.1:20128 --tools claude          # one tool
9router connect http://127.0.0.1:20128 --tools claude,codex    # several
9router connect http://127.0.0.1:20128 --tools all             # all of them
```

Supported ids: `claude, codex, opencode, droid, crush, kilo, cline, pi, omp`.

The command asks for your dashboard password. It writes each tool's config file and keeps a backup (`*.bak-9router`). Restart the tool afterwards.

Check what each tool is set to:

```bash
9router show
```

## 6. Kiro IDE, Cursor, GitHub Copilot

These IDEs are routed by interception. Open `http://localhost:20128/dashboard/mitm`, enable it and follow the steps (it may ask you to install a certificate).

## 7. Turning it off

```bash
9router connect --reset --tools claude    # or: --tools all
```

This restores the tool's original configuration. Then stop the server with `Ctrl+C` in its window (or close it from the tray icon).

Remove the tools first, then stop the server. A tool that still points to 9Router fails while the server is off.
