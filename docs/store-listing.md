# Microsoft Store listing

Texts pasted into Partner Center → Listagens da Store. Keep both languages in sync when the app changes.

## Português (Brasil) — pt-br

**Nome:** AI Router Manager

**Descrição**

Use Claude Code, Codex, Cursor e outras ferramentas de programação com IA através do 9Router, sem abrir terminal.

O AI Router Manager instala e executa o 9Router (um gateway local de IA) e conecta suas ferramentas a ele com um clique. Ele mostra quanto das suas cotas você já usou e quantos tokens economizou, sempre visíveis no topo da janela e atualizados a cada minuto.

• Instala o 9Router e avisa quando há uma versão nova, com botão para atualizar
• Inicia o 9Router automaticamente quando já existe uma conexão configurada
• Conecta Claude Code e outras ferramentas ao 9Router ou de volta à conexão direta
• Mostra o consumo de cada conta (sessão, semanal, créditos) e quando a cota renova
• Economia de tokens com Headroom e Caveman, com uma barra por ferramenta
• Fica na bandeja do sistema; tema claro e escuro; português e inglês

Gratuito e de código aberto. Não coleta dados: tudo roda no seu computador.

Requer Node.js para instalar o 9Router.

**Recursos do produto** (um por linha)

- Instala, inicia e atualiza o 9Router com um clique
- Conecta Claude Code e outras ferramentas de IA ao 9Router
- Consumo das cotas de cada conta, atualizado a cada minuto
- Tokens economizados por ferramenta (Headroom e Caveman)
- Início automático quando já há conexão configurada
- Fica na bandeja do sistema
- Tema claro e escuro, português e inglês

**Termos de pesquisa** (até 7)

9router · claude code · token saver · ai gateway · ai router · llm proxy · economizar tokens

**Notas de direitos autorais:** © 2026 WD Software

## English (United States) — en-us

**Name:** AI Router Manager

**Description**

Use Claude Code, Codex, Cursor and other AI coding tools through 9Router, without touching the terminal.

AI Router Manager installs and runs 9Router (a local AI gateway) and connects your tools to it in one click. It shows how much of your quotas you have used and how many tokens you have saved, always visible at the top of the window and refreshed every minute.

• Installs 9Router and tells you when a new version is out, with an update button
• Starts 9Router automatically when a connection is already set up
• Points Claude Code and other tools at 9Router, or back to their direct connection
• Usage per account (session, weekly, credits) and when each quota resets
• Token savings from Headroom and Caveman, with a bar per tool
• Lives in the system tray; light and dark theme; English and Portuguese

Free and open source. No data collection: everything runs on your computer.

Requires Node.js to install 9Router.

**Product features** (one per line)

- Install, start and update 9Router in one click
- Connect Claude Code and other AI tools to 9Router
- Quota usage per account, refreshed every minute
- Tokens saved per tool (Headroom and Caveman)
- Auto-start when a connection is already set up
- Runs from the system tray
- Light and dark theme, English and Portuguese

**Search terms** (up to 7)

9router · claude code · token saver · ai gateway · ai router · llm proxy · save tokens

**Copyright:** © 2026 WD Software

## Restricted capability justifications (Opções de envio, 500 characters each)

**runFullTrust**

> AI Router Manager is a Win32 desktop app (Python, Desktop Bridge). It needs full trust to start and stop local processes: the 9Router gateway (Node.js) on localhost:20128, npm to install and update 9Router, and optional token-saving tools (Headroom, Caveman). It also edits AI coding tool settings in the user's profile (e.g. ~/.claude/settings.json) so they use the local gateway. None of this works inside the AppContainer sandbox.

**unvirtualizedResources**

> The app installs developer CLI tools with "npm install -g" (9Router, Caveman) into %APPDATA%\npm. Those commands must work from the user's own terminal and from Claude Code hooks, outside the package. With AppData write virtualization they would land in the package's private storage, invisible to other programs, so the manifest disables FileSystemWriteVirtualization. The app only writes to the current user's AppData and profile folders.
