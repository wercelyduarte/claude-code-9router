# Manual Setup — Without the GUI

This guide covers everything the GUI does, step by step, so you can do it manually or script it.

---

## 1. Install 9Router

Requires Node.js ≥ 18 and npm.

```bash
npm install -g --allow-scripts=9router 9router
```

Verify:

```bash
9router --version
```

---

## 2. Start the server

```bash
9router
```

The dashboard opens at `http://localhost:20128`.  
The OpenAI-compatible API endpoint is `http://localhost:20128/v1`.

---

## 3. Enable routing for Claude Code

Claude Code reads the `ANTHROPIC_BASE_URL` environment variable to override the default Anthropic endpoint.

### Windows — permanent (user-level)

```powershell
[System.Environment]::SetEnvironmentVariable("ANTHROPIC_BASE_URL", "http://localhost:20128", "User")
```

### Windows — current session only

```powershell
$env:ANTHROPIC_BASE_URL = "http://localhost:20128"
```

### macOS / Linux — permanent

Add to `~/.zshrc` or `~/.bashrc`:

```bash
export ANTHROPIC_BASE_URL=http://localhost:20128
```

Then reload: `source ~/.zshrc`

---

## 4. Restart Claude Code

After setting the environment variable, restart Claude Code so it picks up the new value.

---

## 5. Disable routing

### Windows

```powershell
[System.Environment]::SetEnvironmentVariable("ANTHROPIC_BASE_URL", $null, "User")
```

### macOS / Linux

Remove or comment out the `export` line from your shell profile, then reload it.

---

## 6. Add AI providers in the 9Router dashboard

1. Open `http://localhost:20128` in your browser.
2. Go to **Providers** → **Add Provider**.
3. Enter your API key for each provider (OpenAI, Anthropic, etc.).
4. Configure fallback order under **Routing**.

---

## Notes

- 9Router exposes an OpenAI-compatible endpoint. Claude Code routing via `ANTHROPIC_BASE_URL` depends on 9Router's proxy translation layer.
- The local server must be running **before** you start Claude Code for routing to work.
- To verify routing is active: check the 9Router dashboard's request log after sending a message in Claude Code.
