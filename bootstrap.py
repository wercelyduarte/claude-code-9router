#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bootstrapper do 9Router Manager.

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

# (modulo_importado, nome_pip)
DEPENDENCIAS = [
    ("customtkinter", "customtkinter"),
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


def garantir_deps():
    faltando = [m for m, _ in DEPENDENCIAS if not _tem(m)]
    if not faltando:
        print("[bootstrap] Todas as dependencias estao presentes.")
        return True

    print("[bootstrap] Dependencias faltando:", ", ".join(faltando))
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "--version"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print("[bootstrap] pip nao encontrado. Tentando ensurepip...")
        try:
            import ensurepip
            ensurepip.bootstrap(upgrade=True, default_pip=True)
        except Exception as e:
            print(f"[bootstrap] Nao foi possivel habilitar o pip: {e}")
            return False

    ok = True
    for modulo, pkg in DEPENDENCIAS:
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
    print(" 9Router Manager - verificacao de ambiente")
    print("=" * 60)
    print(f"Python: {sys.executable} ({sys.version.split()[0]})")
    print(f"Local : {BASE_DIR}")

    if not garantir_deps():
        print()
        print("[bootstrap] NAO foi possivel preparar o ambiente.")
        print("[bootstrap] Tente: pip install -r requirements.txt")
        input("Pressione Enter para sair...")
        sys.exit(1)

    print()
    print("[bootstrap] Ambiente OK. Abrindo o app...")
    import app as router_app
    router_app.App().mainloop()


if __name__ == "__main__":
    main()
