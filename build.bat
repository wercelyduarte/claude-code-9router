@echo off
REM Uso:  build.bat        -> gera build\AIRouterManager\AIRouterManager.exe
REM       build.bat msi    -> gera tambem o instalador .msi em dist\
REM Release no GitHub: crie e envie uma tag vX.Y.Z (git tag v1.0.3, depois git push origin v1.0.3)
REM e o workflow .github\workflows\release.yml gera o .msi e publica a release.
setlocal
cd /d "%~dp0"

if not exist .venv-build (
    echo Criando ambiente virtual de build...
    python -m venv .venv-build || goto :erro
)
call .venv-build\Scripts\activate.bat

python -m pip install --upgrade pip --quiet
pip install -r requirements-build.txt || goto :erro

if exist build rmdir /s /q build

if /i "%~1"=="msi" (
    python setup.py bdist_msi || goto :erro
) else (
    python setup.py build || goto :erro
)

echo.
echo Build concluido.
echo   Executavel: build\AIRouterManager\AIRouterManager.exe
if /i "%~1"=="msi" echo   Instalador: pasta dist\
pause
exit /b 0

:erro
echo.
echo *** O build falhou. Veja as mensagens acima. ***
pause
exit /b 1
