# -*- coding: utf-8 -*-
r"""
Empacota o build do cx_Freeze como .msix para a Microsoft Store.

  python setup.py build_exe   (ou bdist_msi)  -> build\AIRouterManager\
  python build_msix.py                        -> dist\AIRouterManager-X.Y.Z.msix

O pacote sai sem assinatura: a Store assina ao publicar. Os valores de identidade vem de
Partner Center > AI Router Manager > Identidade do produto.
"""
import glob
import shutil
import subprocess
import sys
from pathlib import Path
from xml.sax.saxutils import escape
from PIL import Image

IDENTITY_NAME   = "WDSoftware.AIRouterManager"
PUBLISHER       = "CN=9D10F0A4-908D-48F7-8443-E79125171516"
PUBLISHER_NAME  = "WD Software"
DISPLAY_NAME    = "AI Router Manager"
DESCRIPTION     = "Run 9Router and connect AI coding tools to it"

ROOT    = Path(__file__).parent
BUILD   = ROOT / "build" / "AIRouterManager"
STAGE   = ROOT / "build" / "msix"
LOGOS   = {"Square44x44Logo.png": 44, "Square150x150Logo.png": 150, "StoreLogo.png": 50}

# The app installs npm packages globally (9Router, Caveman) whose paths end up in the user's
# terminal and in ~/.claude hooks. With the default AppData write virtualization those files
# would land in a private copy that no program outside the package sees.
MANIFEST = """<?xml version="1.0" encoding="utf-8"?>
<Package xmlns="http://schemas.microsoft.com/appx/manifest/foundation/windows10"
         xmlns:uap="http://schemas.microsoft.com/appx/manifest/uap/windows10"
         xmlns:desktop6="http://schemas.microsoft.com/appx/manifest/desktop/windows10/6"
         xmlns:rescap="http://schemas.microsoft.com/appx/manifest/foundation/windows10/restrictedcapabilities"
         IgnorableNamespaces="uap desktop6 rescap">
  <Identity Name="{name}" Publisher="{publisher}" Version="{version}" ProcessorArchitecture="x64" />
  <Properties>
    <DisplayName>{display}</DisplayName>
    <PublisherDisplayName>{publisher_name}</PublisherDisplayName>
    <Logo>Assets\\StoreLogo.png</Logo>
    <desktop6:FileSystemWriteVirtualization>disabled</desktop6:FileSystemWriteVirtualization>
  </Properties>
  <Dependencies>
    <TargetDeviceFamily Name="Windows.Desktop" MinVersion="10.0.19041.0" MaxVersionTested="10.0.26100.0" />
  </Dependencies>
  <Resources>
    <Resource Language="pt-BR" />
    <Resource Language="en-US" />
  </Resources>
  <Applications>
    <Application Id="AIRouterManager" Executable="AIRouterManager.exe" EntryPoint="Windows.FullTrustApplication">
      <uap:VisualElements DisplayName="{display}" Description="{description}" BackgroundColor="transparent"
                          Square150x150Logo="Assets\\Square150x150Logo.png" Square44x44Logo="Assets\\Square44x44Logo.png" />
    </Application>
  </Applications>
  <Capabilities>
    <rescap:Capability Name="runFullTrust" />
    <rescap:Capability Name="unvirtualizedResources" />
  </Capabilities>
</Package>
"""


def makeappx() -> str:
    found = sorted(glob.glob(r"C:\Program Files (x86)\Windows Kits\10\bin\10.*\x64\makeappx.exe"))
    if not found:
        sys.exit("makeappx.exe nao encontrado (instale o Windows SDK)")
    return found[-1]


def main():
    if not (BUILD / "AIRouterManager.exe").exists():
        sys.exit(f"{BUILD} nao existe: rode antes  python setup.py build_exe")
    version = (BUILD / "VERSION").read_text(encoding="utf-8").strip()
    msix_version = ".".join((version.split(".") + ["0"] * 4)[:3]) + ".0"   # Store wants X.Y.Z.0

    shutil.rmtree(STAGE, ignore_errors=True)
    shutil.copytree(BUILD, STAGE)
    (STAGE / "Assets").mkdir()
    icon = Image.open(ROOT / "icone.png").convert("RGBA")
    for filename, size in LOGOS.items():
        icon.resize((size, size), Image.LANCZOS).save(STAGE / "Assets" / filename)
    (STAGE / "AppxManifest.xml").write_text(MANIFEST.format(
        name=IDENTITY_NAME, publisher=escape(PUBLISHER), version=msix_version, display=DISPLAY_NAME,
        publisher_name=PUBLISHER_NAME, description=DESCRIPTION), encoding="utf-8")

    out = ROOT / "dist" / f"AIRouterManager-{version}.msix"
    out.parent.mkdir(exist_ok=True)
    subprocess.run([makeappx(), "pack", "/o", "/d", str(STAGE), "/p", str(out)], check=True)
    print(out)


if __name__ == "__main__":
    main()
