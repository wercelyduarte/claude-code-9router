# -*- coding: utf-8 -*-
"""
Build do 9Router Manager com cx_Freeze.

  python setup.py build        -> pasta em build\9RouterManager\ (9RouterManager.exe)
  python setup.py bdist_msi    -> instalador .msi em dist\
"""
import os
import sys
import customtkinter
from cx_Freeze import setup, Executable

APP_NAME    = "9RouterManager"
VERSION     = os.environ.get("VERSAO", "1.0.0")
DESCRIPTION = "GUI para gerenciar o 9Router com Claude Code"

base = "gui" if sys.platform == "win32" else None

# Inclui o diretorio de assets do customtkinter (temas, imagens)
ctk_dir = os.path.dirname(customtkinter.__file__)

build_exe_options = {
    "build_exe": f"build/{APP_NAME}",
    "packages": [
        "customtkinter",
        "tkinter",
        "winreg",
        "ctypes",
        "sqlite3",
        "pystray",
        "PIL",
    ],
    "excludes": [
        "matplotlib", "pandas", "scipy", "numpy",
        "IPython", "pytest", "PyQt5", "PyQt6", "cv2",
    ],
    "include_files": [
        (ctk_dir, "customtkinter"),  # temas e imagens do customtkinter
        ("icone.ico", "icone.ico"),
        ("icone.png", "icone.png"),  # icone da bandeja
    ],
    "include_msvcr": True,
    "optimize": 1,
}

bdist_msi_options = {
    "upgrade_code":       "{3A7F2D91-6C4B-4E8A-B1D5-9E02F4C7A830}",
    "initial_target_dir": rf"[ProgramFiles64Folder]\{APP_NAME}",
    "add_to_path":        False,
}

executables = [
    Executable(
        "app.py",
        base=base,
        target_name=f"{APP_NAME}.exe",
        icon="icone.ico",
        shortcut_name="9Router Manager",
        shortcut_dir="DesktopFolder",
    )
]

setup(
    name=APP_NAME,
    version=VERSION,
    description=DESCRIPTION,
    options={"build_exe": build_exe_options, "bdist_msi": bdist_msi_options},
    executables=executables,
)
