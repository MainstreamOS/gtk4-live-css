#!/usr/bin/env python3
"""Exercise the real GTK user stylesheet in an open window, using a private config.

Run under a display (or xvfb-run), with --library-dir pointing to build/gtk.
No user configuration or installed libraries are modified.
"""

import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time


def child(scenario, adwaita, template):
    with tempfile.TemporaryDirectory(prefix="mainstream-live-css-") as folder:
        os.environ["XDG_CONFIG_HOME"] = folder
        os.environ["GSETTINGS_BACKEND"] = "memory"
        config = Path(folder) / "gtk-4.0"
        css = config / "gtk.css"
        base = Path(template).read_text() if template else ""

        def stylesheet(color):
            return base + f"\n@define-color mainstream_live_probe {color};\nlabel.live-probe {{ color: @mainstream_live_probe; }}\n"

        if scenario != "missing-directory":
            config.mkdir()
        if scenario == "normal":
            css.write_text(stylesheet("#123456"))
        elif scenario == "dangling-link":
            destination = Path(folder) / "theme"
            destination.mkdir()
            css.symlink_to("../theme/gtk.css")

        import gi
        gi.require_version("Gtk", "4.0")
        from gi.repository import GLib, Gtk
        Gtk.init()
        if adwaita:
            gi.require_version("Adw", "1")
            from gi.repository import Adw
            Adw.init()
            window = Adw.Window(title="Mainstream live CSS test", default_width=400, default_height=160)
        else:
            window = Gtk.Window(title="Mainstream live CSS test", default_width=400, default_height=160)
        label = Gtk.Label(label="This open window changes color without restarting")
        label.add_css_class("live-probe")
        if adwaita:
            window.set_content(label)
        else:
            window.set_child(label)
        window.present()
        context = GLib.MainContext.default()

        def wait_for(expected, operation):
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                while context.pending():
                    context.iteration(False)
                found, color = label.get_style_context().lookup_color("mainstream_live_probe")
                actual = "#{:02x}{:02x}{:02x}".format(*(round(channel * 255) for channel in (color.red, color.green, color.blue))) if found else None
                rendered = label.get_color()
                rendered_hex = "#{:02x}{:02x}{:02x}".format(*(round(channel * 255) for channel in (rendered.red, rendered.green, rendered.blue)))
                if actual == expected and (expected is None or rendered_hex == expected):
                    print(f"PASS {scenario}: {operation}", flush=True)
                    return
                time.sleep(0.01)
            raise AssertionError(f"{operation}: expected {expected}, observed {actual}")

        try:
            if scenario != "normal":
                wait_for(None, "starts without user CSS")
                config.mkdir(exist_ok=True)
                css.write_text(stylesheet("#123456"))
                wait_for("#123456", "first stylesheet created after startup")
                css.write_text(stylesheet("#234567"))
                wait_for("#234567", "later changes still observed")
                return
            wait_for("#123456", "initial stylesheet")
            css.write_text(stylesheet("#345678"))
            wait_for("#345678", "Matugen-style in-place write")
            temporary = config / "next.css"
            temporary.write_text(stylesheet("#56789a"))
            temporary.replace(css)
            wait_for("#56789a", "atomic file replacement")
            for color in ("#112233", "#223344", "#334455"):
                css.write_text(stylesheet(color))
            wait_for("#334455", "rapid consecutive writes")
            css.unlink()
            wait_for(None, "deleted stylesheet clears overrides")
            css.write_text(stylesheet("#6789ab"))
            wait_for("#6789ab", "stylesheet recreated")
            target_dir = Path(folder) / "theme files"
            target_dir.mkdir()
            target = target_dir / "palette.css"
            target.write_text(stylesheet("#789abc"))
            css.unlink()
            css.symlink_to(target)
            wait_for("#789abc", "symlinked theme")
            target.write_text(stylesheet("#89abcd"))
            wait_for("#89abcd", "write behind symlink")
            replacement = target_dir / "replacement.css"
            replacement.write_text(stylesheet("#9abcde"))
            replacement.replace(target)
            wait_for("#9abcde", "atomic replacement behind symlink")
            another = target_dir / "another.css"
            another.write_text(stylesheet("#abcdef"))
            temporary.symlink_to(another)
            temporary.replace(css)
            wait_for("#abcdef", "symlink retargeted")
            another.unlink()
            wait_for(None, "symlink target deleted")
            another.write_text(stylesheet("#bcdef0"))
            wait_for("#bcdef0", "symlink target recreated")
            missing = target_dir / "not-yet-created.css"
            temporary.symlink_to(os.path.relpath(missing, config))
            temporary.replace(css)
            wait_for(None, "retargeted to a missing relative destination")
            missing.write_text(stylesheet("#cdef01"))
            wait_for("#cdef01", "new relative destination created")
            # Mainstream supplies both palettes in one CSS file. Reloading
            # must preserve the provider's binding to the system color scheme.
            def palettes(light, dark):
                return (base + f"\n@media (prefers-color-scheme: light) {{ @define-color mainstream_live_probe {light}; }}\n"
                        + f"@media (prefers-color-scheme: dark) {{ @define-color mainstream_live_probe {dark}; }}\n"
                        + "label.live-probe { color: @mainstream_live_probe; }\n")
            css.write_text(palettes("#123abc", "#abc123"))
            settings = Gtk.Settings.get_default()
            settings.set_property("gtk-interface-color-scheme", Gtk.InterfaceColorScheme.LIGHT)
            wait_for("#123abc", "light palette selected")
            settings.set_property("gtk-interface-color-scheme", Gtk.InterfaceColorScheme.DARK)
            wait_for("#abc123", "dark palette selected without restarting")
            css.write_text(palettes("#234bcd", "#bcd234"))
            wait_for("#bcd234", "palette reloaded while dark")
            settings.set_property("gtk-interface-color-scheme", Gtk.InterfaceColorScheme.LIGHT)
            wait_for("#234bcd", "light palette binding survives reload")
        finally:
            window.destroy()
            while context.pending():
                context.iteration(False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library-dir", type=Path)
    parser.add_argument("--template", type=Path)
    parser.add_argument("--adwaita", action="store_true")
    parser.add_argument("--child", choices=("normal", "missing-file", "missing-directory", "dangling-link"))
    args = parser.parse_args()
    if args.child:
        child(args.child, args.adwaita, args.template)
        return
    if not args.library_dir or not (args.library_dir / "libgtk-4.so.1").exists():
        parser.error("--library-dir must contain the patched libgtk-4.so.1")
    env = dict(os.environ)
    env["LD_LIBRARY_PATH"] = str(args.library_dir.resolve()) + os.pathsep + env.get("LD_LIBRARY_PATH", "")
    for scenario in ("normal", "missing-file", "missing-directory", "dangling-link"):
        command = [sys.executable, __file__, "--child", scenario]
        if args.adwaita:
            command.append("--adwaita")
        if args.template:
            command.extend(["--template", str(args.template.resolve())])
        subprocess.run(command, env=env, check=True, timeout=45)


if __name__ == "__main__":
    main()
