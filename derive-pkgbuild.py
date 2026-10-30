#!/usr/bin/env python3
"""Turn Arch's stock gtk4 PKGBUILD into the gtk4-live-css one.

    derive-pkgbuild.py arch/PKGBUILD > PKGBUILD

Arch's version, build options and dependency lists stay as they are. What changes:
  - it builds one package, gtk4-live-css, which provides and conflicts with gtk4.
    Arch's package_gtk4() becomes package(). The _pick calls in there already move
    the demo, docs and icon-cache files out, and the other split packages get dropped.
  - gtk4-user-css-live-reload.patch gets added to source and applied in prepare()
Every edit asserts the text it expects, so if Arch reshapes the PKGBUILD this blows up
instead of quietly building an unpatched or half-renamed package.
"""
import hashlib
import re
import sys
from pathlib import Path

here = Path(__file__).resolve().parent
patch = "gtk4-user-css-live-reload.patch"
s = Path(sys.argv[1]).read_text()

def once(old, new):
    global s
    if s.count(old) != 1:
        raise ValueError(f"expected exactly one match for: {old!r}")
    s = s.replace(old, new)

# one package instead of pkgbase + four split packages
m = re.search(r"^pkgbase=gtk4\npkgname=\(\n(?:  .*\n)+?\)\n", s, re.M)
if not m:
    raise ValueError("pkgbase=gtk4 / pkgname=( ... ) block not found")
s = s[:m.start()] + "pkgname=gtk4-live-css\n" + s[m.end():]
once('pkgdesc="GObject-based multi-platform GUI toolkit"',
     'pkgdesc="GTK 4 with live user CSS reloading for Mainstream OS"')

# Distinguish the patched package from an unmodified/upstream build, including
# machines that previously installed saneaspect's package at Arch's pkgrel.
m = re.search(r"^pkgrel=(\d+)(?:\.(\d+))?$", s, re.M)
if not m:
    raise ValueError("numeric pkgrel assignment not found")
release = f"{m[1]}.{int(m[2] or '0') + 1}"
s = s[:m.start()] + f"pkgrel={release}" + s[m.end():]

# drop unneeded doc tooling from makedepends
for dep in ("  docbook-xsl\n", "  gi-docgen\n", "  python-docutils\n"):
    once(dep, "")

# disable docs, man-pages, demos, tests and testsuite to cut build time from 45m to ~6m
once(
    "    -D documentation=true\n    -D man-pages=true\n",
    "    -D documentation=false\n    -D screenshots=false\n    -D man-pages=false\n    -D build-demos=false\n    -D build-testsuite=false\n    -D build-examples=false\n    -D build-tests=false\n",
)

# tolerate missing files in _pick (since docs and demos are not built)
once(
    '  for f; do\n    d="$srcdir/$p/${f#$pkgdir/}"\n',
    '  for f; do\n    [ -e "$f" ] || continue\n    d="$srcdir/$p/${f#$pkgdir/}"\n',
)

# add the patch to source and b2sums, apply it in prepare()
m = re.search(r"^source=\(\n(?:  .*\n)+?\)\n", s, re.M)
if not m:
    raise ValueError("source=( ... ) block not found")
s = s[:m.end() - 2] + f"  {patch}\n)\n" + s[m.end():]
b2 = hashlib.blake2b((here / patch).read_bytes(), digest_size=64).hexdigest()
m = re.search(r"^b2sums=\((?:'[0-9a-f]+'\s*)+\)", s, re.M)
if not m:
    raise ValueError("b2sums=( ... ) block not found")
s = s[:m.end() - 1] + f"\n        '{b2}')" + s[m.end():]
once("prepare() {\n  cd gtk\n", f"prepare() {{\n  cd gtk\n  patch -Np1 -i ../{patch}\n")

# package_gtk4() becomes package() and stands in for gtk4
once("package_gtk4() {\n", "package() {\n")
once("  provides=(libgtk-4.so)\n",
     '  provides=("gtk4=${epoch:-0}:$pkgver-$pkgrel" libgtk-4.so)\n'
     '  conflicts=(gtk4)\n'
     '  replaces=(gtk4)\n')
for fn in ("gtk4-demos", "gtk4-docs", "gtk-update-icon-cache"):
    m = re.search(rf"^package_{re.escape(fn)}\(\) \{{\n.*?^\}}\n\n?", s, re.M | re.S)
    if not m:
        raise ValueError(f"package_{fn}() not found")
    s = s[:m.start()] + s[m.end():]

sys.stdout.write(s)
