# GTK4 live CSS for Mainstream OS

Arch's GTK4 with a small patch that reloads the user's stylesheet while apps
remain open. Mainstream's existing Matugen templates write
`$XDG_CONFIG_HOME/gtk-4.0/gtk.css`; an open native GTK4 or libadwaita app then
picks up wallpaper colors, accents, and light/dark styling without a restart.
There is no polling daemon, global `LD_PRELOAD`, or per-app injection.

The original live-CSS concept and implementation are by
[saneaspect](https://github.com/saneaspect), from
[gtk4-live-css](https://github.com/saneaspect/gtk4-live-css).
This fork adapts that work for Mainstream OS.
GTK remains licensed under LGPL-2.1-or-later. Arch's packaging, build options,
dependencies, and library ABI are retained.

## Shipping through Mainstream

The package is `gtk4-live-css`, providing the versioned `gtk4` package and
`libgtk-4.so`, and conflicting with/replacing stock `gtk4`. Mainstream's
`mainstream-fonts-themes` meta-package depends on it. Install it through the
existing **signed** `[mainstream]` repository; do not add the upstream
`[saneaspect]` repository or relax signature checks.

Once it is published, a normal full update migrates stock GTK4:

```sh
sudo pacman -Syu
```

Restart GTK4 apps **once** after that first installation so they load the
patched library. Later theme changes apply to those running apps. Applications
using bundled GTK libraries or Flatpak runtimes do not use this host library;
they need a corresponding runtime patch. GTK3, Qt, Electron, and application
stylesheets loaded outside the standard user CSS provider are not changed.
Changes inside imported CSS files are not independently watched; Mainstream
writes its generated palette directly to `gtk.css`.

## Maintaining the fork

Use the `mainstream` branch in `MainstreamOS/gtk4-live-css` as the shipping source
and default branch. `MainstreamOS/packages` consumes the standalone recipe as
`gtk4-live-css::mainstream-git` and applies its signing, rebuild `pkgrel`, immutable
file, and cached-database retention safeguards. Publish this fork and its package
**before** deploying the dots-hyprland dependency change.

The daily workflow checks the version actually in Arch's stable `[extra]`,
rather than the highest Git tag (which can belong to testing). It derives the
recipe and hook files, builds the package, tests live GTK and libadwaita windows,
and only then commits an updated recipe. An incompatible upstream change fails
before that commit. The workflow's unsigned build artifact is for testing only;
it does not replace the signed Mainstream package publication workflow. The
central package repository checks every six hours and requests a signed rebuild
when the fork has tested a newer stable GTK. It waits for an active build instead
of queuing duplicates. The normal weekly build also picks up the tested recipe.

`upstream-version` tracks Arch's exact epoch/version/release, separately from
Mainstream's patch subrelease (`1` → `1.1`) and later rebuild subreleases.
`prepare-upstream.py` fails if the expected
Arch packaging structure changes. Source checksums, including the patch and
Arch's hook files, are checked by makepkg as usual.

## Build and test locally

Install Arch's GTK4 build dependencies, then run as a non-root user:

```sh
./build.sh          # pinned version from upstream-version
./build.sh latest   # regenerate from Arch stable, then build
python3 tests/live-css.py --library-dir src/build/gtk
python3 tests/live-css.py --library-dir src/build/gtk --adwaita
```

The tests need Python GObject and a display (or `xvfb-run`). They use temporary
configuration directories and the built library without changing the installed
GTK or the user's theme. They cover direct writes, atomic replacement, repeated
updates, deletion/recreation, symlink targets and retargeting, and apps that
started before the stylesheet or its directory existed.

Inspect regenerated recipe changes before committing them. To return to stock
GTK, remove the `gtk4-live-css` dependency from the meta-package first, then use
a normal pacman transaction to install `extra/gtk4` and accept the conflict
replacement; never remove the toolkit with dependency checks disabled.
