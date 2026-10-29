#!/usr/bin/env python3
"""Refresh the standalone recipe from a pinned or stable Arch packaging tag."""

import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import urllib.request


ROOT = Path(__file__).resolve().parent
PACKAGING = "https://gitlab.archlinux.org/archlinux/packaging/packages/gtk4.git"
SIDECARS = ("gtk-update-icon-cache.hook", "gtk-update-icon-cache.script",
            "gtk4-querymodules.hook", "gtk4-querymodules.script")


def prepare(version):
    if version == "latest":
        with urllib.request.urlopen("https://archlinux.org/packages/extra/x86_64/gtk4/json/", timeout=60) as response:
            package = json.load(response)
        version = f"{package['epoch']}:{package['pkgver']}-{package['pkgrel']}"
    elif version == "pinned":
        version = (ROOT / "upstream-version").read_text().strip()
    if not re.fullmatch(r"[0-9]+:[A-Za-z0-9_.+]+-[0-9]+(?:\.[0-9]+)?", version):
        raise ValueError(f"invalid Arch package version: {version}")
    tag = version.replace(":", "-", 1)
    arch = ROOT / "arch"
    if not arch.exists():
        subprocess.run(["git", "clone", "--no-checkout", PACKAGING, str(arch)], check=True)
    subprocess.run(["git", "-C", str(arch), "fetch", "origin", "tag", tag], check=True)
    subprocess.run(["git", "-C", str(arch), "checkout", "--detach", "--force", tag], check=True)
    recipe = subprocess.check_output([sys.executable, str(ROOT / "derive-pkgbuild.py"), str(arch / "PKGBUILD")])
    # Keep hook files with the recipe: both makepkg and the signed Mainstream
    # builder can then use this checkout directly without fetching Arch again.
    for name in SIDECARS:
        if not (arch / name).is_file():
            raise ValueError(f"Arch packaging is missing {name}")
    for name in SIDECARS:
        shutil.copyfile(arch / name, ROOT / name)
    (ROOT / "PKGBUILD").write_bytes(recipe)
    (ROOT / "upstream-version").write_text(version + "\n")
    print(f"Prepared gtk4-live-css from Arch {version}")


if __name__ == "__main__":
    if len(sys.argv) > 2:
        sys.exit("usage: prepare-upstream.py [pinned|latest|epoch:pkgver-pkgrel]")
    prepare(sys.argv[1] if len(sys.argv) == 2 else "pinned")
