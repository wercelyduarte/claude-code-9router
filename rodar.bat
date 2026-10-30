@echo off
REM ============================================================
REM  AI Router Manager - launcher (qualquer PC Windows)
REM  1. Verifica Python no PATH (py launcher ou python)
REM  2. Verifica se Node.js / npm estao instalados
REM  3. Verifica se 9router esta instalado (npm install -g)
REM  4. Roda bootstrap.py que instala deps Python faltantes
REM  5. Abre o app
REM ============================================================
cd /d "%~dp0"
setlocal

set "PY_CMD="

REM -- Python --
where py >nul 2>nul
if not errorlevel 1 (
  py -3 --version >nul 2>nul
  if not errorlevel 1 set "PY_CMD=py -3"
)
if not defined PY_CMD (
  where python >nul 2>nul
  if not errorlevel 1 set "PY_CMD=python"
)
if not defined PY_CMD (
  echo.
  echo [rodar] Python NAO encontrado.
  echo [rodar] Instale Python 3.10+ em https://www.python.org/downloads/
  echo [rodar] MARQUE a opcao "Add python.exe to PATH" na instalacao.
  echo.
  pause
  exit /b 1
)

REM -- Node.js / npm --
where npm >nul 2>nul
if errorlevel 1 (
  echo.
  echo [rodar] Node.js / npm NAO encontrado.
  echo [rodar] Instale Node.js 18+ em https://nodejs.org/
  echo.
  pause
  exit /b 1
)

REM -- 9router --
REM 'call' e obrigatorio: 9router.cmd e npm.cmd encerram o batch chamador sem ele
call 9router --version >nul 2>nul
if errorlevel 1 (
  echo.
  echo [rodar] 9router NAO esta instalado. Instalando agora via npm...
  echo.
  call npm install -g --allow-scripts=9router 9router
  if errorlevel 1 (
    echo.
    echo [rodar] Falha ao instalar 9router. Verifique a conexao e tente novamente.
    pause
    exit /b 1
  )
  REM Confirma que o executavel foi criado
  call 9router --version >nul 2>nul
  if errorlevel 1 (
    echo.
    echo [rodar] Instalacao concluida mas comando ainda nao encontrado.
    echo [rodar] Feche e reabra o terminal e tente novamente.
    pause
    exit /b 1
  )
  echo.
  echo [rodar] 9router instalado com sucesso!
)

REM -- Roda bootstrap + app --
echo [rodar] Usando: %PY_CMD%
%PY_CMD% bootstrap.py
if errorlevel 1 (
  echo.
  echo [rodar] Falha no bootstrap. Veja as mensagens acima.
  pause
  exit /b 1
)
REM Mantem a janela aberta se o app fechar com erro inesperado
if not "%ERRORLEVEL%"=="0" pause

endlocal
