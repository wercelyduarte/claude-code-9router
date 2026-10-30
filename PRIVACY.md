# Política de privacidade / Privacy policy

*Última atualização / Last updated: 2026-10-30*

## Português

Este app roda inteiramente no seu computador. **Ele não coleta, não armazena em servidores e não vende nenhum dado seu.** Não há conta, anúncios nem rastreamento.

**O que o app acessa, e por quê**

| Acesso | Para quê |
|---|---|
| 9Router no seu PC (`localhost:20128`) e o banco de dados local dele, só para leitura | Mostrar status, uso, cotas das contas e economia de tokens |
| Headroom no seu PC (`localhost:8787`) | Mostrar os tokens economizados pelo Headroom |
| `registry.npmjs.org` | Verificar se há uma versão nova do 9Router. Só consulta o número da versão; nenhum dado seu é enviado |
| Arquivos de configuração das ferramentas de IA (Claude Code, Codex etc.) | Conectar ou desconectar a ferramenta do 9Router, quando você pede. O 9Router guarda uma cópia do original |
| `%APPDATA%\9RouterManager\config.json` | Guardar idioma e tema escolhidos |

A senha do painel do 9Router fica só na memória enquanto o app está aberto e nunca é gravada em disco.

**Programas de terceiros.** O 9Router, o Headroom e o Caveman são projetos independentes, com políticas próprias. O Caveman envia estatísticas de uso anônimas por padrão; o app oferece um botão para desligar isso e desliga o envio de estatísticas do Headroom ao instalá-lo. Os provedores de IA que você conectar ao 9Router (Anthropic, OpenAI, Kiro e outros) recebem suas requisições conforme as políticas deles.

**Contato:** abra uma issue em https://github.com/wercelyduarte/claude-code-9router/issues

## English

This app runs entirely on your computer. **It does not collect, upload or sell any of your data.** There is no account, no ads and no tracking.

**What the app accesses, and why**

| Access | Purpose |
|---|---|
| 9Router on your PC (`localhost:20128`) and its local database, read-only | Show status, usage, account quotas and token savings |
| Headroom on your PC (`localhost:8787`) | Show the tokens Headroom saved |
| `registry.npmjs.org` | Check for a newer 9Router version. It only reads the version number; none of your data is sent |
| AI tools' config files (Claude Code, Codex, etc.) | Connect or disconnect a tool from 9Router when you ask. 9Router keeps a copy of the original |
| `%APPDATA%\9RouterManager\config.json` | Remember your language and theme |

The 9Router dashboard password is kept in memory only while the app is open and is never written to disk.

**Third-party programs.** 9Router, Headroom and Caveman are independent projects with their own policies. Caveman sends anonymous usage statistics by default; the app offers a button to turn that off and turns off Headroom's statistics upload when it installs it. The AI providers you connect to 9Router (Anthropic, OpenAI, Kiro and others) receive your requests under their own policies.

**Contact:** open an issue at https://github.com/wercelyduarte/claude-code-9router/issues
