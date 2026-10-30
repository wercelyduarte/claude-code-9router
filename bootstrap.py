#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bootstrapper do AI Router Manager.

Garante que todas as dependencias Python estejam instaladas antes de abrir o app.
Funciona em qualquer PC Windows com Python 3.10+ no PATH.

Fluxo:
  1. Tenta importar cada dependencia.
  2. Se faltar alguma, instala via pip do mesmo interpretador.
  3. So entao abre o app principal (app.py).
"""
import os
import re
import sys
import subprocess
import importlib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REQUIREMENTS = os.path.join(BASE_DIR, "requirements.txt")

DEPENDENCIAS_PY = [
    ("customtkinter", "customtkinter"),
    ("pystray", "pystray"),
    ("PIL", "Pillow"),
]


def _versao_minima(pkg_pip):
    if not os.path.exists(REQUIREMENTS):
        return ""
    try:
        with open(REQUIREMENTS, "r", encoding="utf-8") as f:
            for linha in f:
                linha = linha.strip()
                if not linha or linha.startswith("#"):
                    continue
                nome = re.split(r"[<>=!~\[]", linha, 1)[0].strip()
                if nome.lower() == pkg_pip.lower():
                    m = re.search(r"(>=|==|~=|>|<).*$", linha)
                    return m.group(0).strip() if m else ""
    except Exception:
        pass
    return ""


def _tem(modulo):
    try:
        importlib.import_module(modulo)
        return True
    except Exception:
        return False


def _instalar(pkg_pip):
    spec = _versao_minima(pkg_pip)
    alvo = f"{pkg_pip}{spec}" if spec else pkg_pip
    cmd = [sys.executable, "-m", "pip", "install",
           "--disable-pip-version-check", "--no-warn-script-location", alvo]
    print(f"[bootstrap] Instalando: {alvo}")
    try:
        subprocess.check_call(cmd)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[bootstrap] FALHA ao instalar {alvo} (exit {e.returncode}).")
        return False


def _pausar():
    try:
        input("Pressione Enter para sair...")
    except EOFError:
        pass  # stdin nao e terminal (pipe), ignora


def _cmd_existe(cmd: str) -> bool:
    # shell=True necessario no Windows para encontrar .cmd do npm/9router
    try:
        subprocess.check_call(f"{cmd} --version",
                              shell=True,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


def garantir_node():
    if not _cmd_existe("npm"):
        print("[bootstrap] Node.js/npm NAO encontrado.")
        print("[bootstrap] Instale Node.js 18+ em https://nodejs.org/ e tente novamente.")
        return False
    print("[bootstrap] npm: OK")
    return True


def garantir_9router():
    if _cmd_existe("9router"):
        print("[bootstrap] 9router: OK")
        return True
    print("[bootstrap] 9router NAO encontrado. Instalando via npm...")
    try:
        subprocess.check_call(
            "npm install -g --allow-scripts=9router 9router",
            shell=True,
        )
    except subprocess.CalledProcessError:
        print("[bootstrap] Falha ao instalar 9router via npm.")
        return False
    if _cmd_existe("9router"):
        print("[bootstrap] 9router instalado com sucesso!")
        return True
    print("[bootstrap] Instalado mas comando ainda nao encontrado. Reinicie o terminal.")
    return False


def garantir_deps_python():
    faltando = [m for m, _ in DEPENDENCIAS_PY if not _tem(m)]
    if not faltando:
        print("[bootstrap] Dependencias Python: OK")
        return True

    print("[bootstrap] Dependencias Python faltando:", ", ".join(faltando))
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "--version"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        try:
            import ensurepip
            ensurepip.bootstrap(upgrade=True, default_pip=True)
        except Exception as e:
            print(f"[bootstrap] Nao foi possivel habilitar o pip: {e}")
            return False

    ok = True
    for modulo, pkg in DEPENDENCIAS_PY:
        if _tem(modulo):
            continue
        if not _instalar(pkg):
            ok = False
            continue
        if not _tem(modulo):
            print(f"[bootstrap] {pkg} instalado mas import '{modulo}' ainda falha.")
            ok = False
    return ok


def main():
    print("=" * 60)
    print(" AI Router Manager - verificacao de ambiente")
    print("=" * 60)
    print(f"Python: {sys.executable} ({sys.version.split()[0]})")
    print(f"Local : {BASE_DIR}")
    print()

    if not garantir_node():
        _pausar()
        sys.exit(1)

    if not garantir_9router():
        _pausar()
        sys.exit(1)

    if not garantir_deps_python():
        print()
        print("[bootstrap] NAO foi possivel preparar o ambiente Python.")
        print("[bootstrap] Tente manualmente: pip install -r requirements.txt")
        _pausar()
        sys.exit(1)

    print()
    print("[bootstrap] Ambiente OK. Abrindo o app...")
    # pythonw has no console, so this black window can close and the app lives on in the tray
    pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    if os.path.exists(pythonw):
        subprocess.Popen([pythonw, os.path.join(BASE_DIR, "app.py")], cwd=BASE_DIR,
                         creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
        return
    import app as router_app
    router_app.App().mainloop()


if __name__ == "__main__":
    main()
