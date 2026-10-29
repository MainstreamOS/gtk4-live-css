#!/usr/bin/env bash
# Build gtk4-live-css locally, the same way the workflow does.
#
#   ./build.sh            Arch's gtk4 at the version the committed PKGBUILD names
#   ./build.sh latest     Arch's current stable gtk4 (then review the regenerated recipe)
#
# Needs gtk4's makedepends installed. makepkg tells you which ones are missing.
set -euo pipefail
cd "$(dirname "$0")"

python3 prepare-upstream.py "${1:-pinned}"
makepkg -Cf --noconfirm
makepkg --packagelist
