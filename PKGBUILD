# Maintainer: Jan Alexander Steffens (heftig) <heftig@archlinux.org>
# Maintainer: Fabian Bornschein <fabiscafe@archlinux.org>

pkgname=gtk4-live-css
pkgver=4.24.1
pkgrel=1.1
epoch=1
pkgdesc="GTK 4 with live user CSS reloading for Mainstream OS"
url="https://www.gtk.org/"
arch=(x86_64)
license=(LGPL-2.1-or-later)
depends=(
  adwaita-fonts
  adwaita-icon-theme
  at-spi2-core
  bash
  cairo
  dconf
  desktop-file-utils
  fontconfig
  fribidi
  gdk-pixbuf2
  glib2
  glibc
  graphene
  gst-plugins-bad-libs
  gst-plugins-base-libs
  gstreamer
  gtk-update-icon-cache
  harfbuzz
  iso-codes
  libcloudproviders
  libcolord
  libcups
  libegl
  libepoxy
  libgcc
  libgl
  libjpeg-turbo
  libpng
  librsvg
  libtiff
  libx11
  libxcursor
  libxdamage
  libxext
  libxfixes
  libxi
  libxinerama
  libxkbcommon
  libxrandr
  libxrender
  pango
  shared-mime-info
  tinysparql
  vulkan-icd-loader
  wayland
  xdg-desktop-portal-gtk
)
makedepends=(
  git
  glib2-devel
  gobject-introspection
  hicolor-icon-theme
  libsysprof-capture
  meson
  python-gobject
  sassc
  shaderc
  vulkan-headers
  wayland-protocols
)
source=(
  "git+https://gitlab.gnome.org/GNOME/gtk.git#tag=$pkgver"
  gtk-update-icon-cache.{hook,script}
  gtk4-querymodules.{hook,script}
  gtk4-user-css-live-reload.patch
)
b2sums=('824667f399ee085521f149f5ed2bffeb52a72034dc59f25fc88beeefb567a37e70f30ec911e39a9b5b29ca8961795555c46d50a3b1d4e8dd5d9dd0b2e021ef5b'
        '136bdb410c46daf769175e8e8837286576391797a4762b8cf388217e893dd6c5087c5c91c347cbdf7d3e9dcd2c978c2fb275b5af1f3425c9f7979fbc65a81324'
        '6bcd839ef82296d864587e0cc7acc0145bdea8e5235af304747cf3c0e564c2757cc67c0373dc044bec83dccfc57dc899546c2fccea96cff2bba22f09978a3814'
        'dd589bd1ad2b13f0e06f6899776a083f20a1aac24d4308d666ffd0d1cff38457b8257b8366f92e767b4233b3d86b6b54fa50339faf84c4801a824986366dce30'
        '4b90eb8d582509b09aab401313d4399cc139ad21b5dd7d45d79860d0764c7494c60714e0794e09823e51d1894ac032a994f27d79d1499abf24ee6f59bdb0c243'
        '0916bad3c2a61659d45b5fbe4beb0dfb62d0c3297c28defcd92ee3870c60ffa51f46470ca40ad8c032881a011a541ba9e3ca3e15f5714fd72b8a88725e13951f')

prepare() {
  cd gtk
  patch -Np1 -i ../gtk4-user-css-live-reload.patch
}

build() {
  local meson_options=(
    -D broadway-backend=true
    -D cloudproviders=enabled
    -D colord=enabled
    -D documentation=false
    -D screenshots=false
    -D man-pages=false
    -D build-demos=false
    -D build-testsuite=false
    -D build-examples=false
    -D build-tests=false
    -D sysprof=enabled
    -D tracker=enabled
  )

  CFLAGS+=" -DG_DISABLE_CAST_CHECKS"
  arch-meson gtk build "${meson_options[@]}"
  meson compile -C build
}

_pick() {
  local p="$1" f d; shift
  for f; do
    [ -e "$f" ] || continue
    d="$srcdir/$p/${f#$pkgdir/}"
    mkdir -p "$(dirname "$d")"
    mv "$f" "$d"
    rmdir -p --ignore-fail-on-non-empty "$(dirname "$f")"
  done
}

package() {
  optdepends=('papers: default print previewer')
  provides=("gtk4=${epoch:-0}:$pkgver-$pkgrel" libgtk-4.so)
  conflicts=(gtk4)
  replaces=(gtk4)

  meson install -C build --no-rebuild --destdir "$pkgdir"

  install -Dm644 /dev/stdin "$pkgdir/usr/share/gtk-4.0/settings.ini" <<END
[Settings]
gtk-icon-theme-name = Adwaita
gtk-theme-name = Adwaita
gtk-font-name = Adwaita Sans 11
END

  install -Dt "$pkgdir/usr/share/libalpm/hooks" -m644 gtk4-querymodules.hook
  install -D gtk4-querymodules.script "$pkgdir/usr/share/libalpm/scripts/gtk4-querymodules"

  cd "$pkgdir"

  _pick demo usr/bin/gtk4-{demo,demo-application,node-editor,print-editor,widget-factory}
  _pick demo usr/share/applications/org.gtk.{Demo4,PrintEditor4,WidgetFactory4,gtk4.NodeEditor}.desktop
  _pick demo usr/share/glib-2.0/schemas/org.gtk.Demo4.gschema.xml
  _pick demo usr/share/icons/hicolor/*/apps/org.gtk.{Demo4,PrintEditor4,WidgetFactory4,gtk4.NodeEditor}[-.]*
  _pick demo usr/share/man/man1/gtk4-{demo,demo-application,node-editor,widget-factory}.1
  _pick demo usr/share/metainfo/org.gtk.{Demo4,PrintEditor4,WidgetFactory4,gtk4.NodeEditor}.appdata.xml

  _pick docs usr/share/doc

  # Built by GTK 4, shared with GTK 3
  _pick guic usr/bin/gtk4-update-icon-cache
  _pick guic usr/share/man/man1/gtk4-update-icon-cache.1
}

# vim:set sw=2 sts=-1 et:
