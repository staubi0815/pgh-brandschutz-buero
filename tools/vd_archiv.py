#!/home/claude/.venvs/pgh/bin/python
"""Archiviert die Verfahrensdokumentation und den Werkzeugstand auf dem NAS (GoBD Rz. 154).

  vd_archiv.py vd       eingecheckte Fassung von docs/verfahrensdokumentation.md als PDF nach
                        06_Steuer/<Jahr>/verfahrensdokumentation/VD_<Datum>_<Git>.pdf – nur wenn diese Fassung fehlt
  vd_archiv.py bundle   gesamtes Repository als git bundle nach 06_Steuer/<Jahr>/werkzeuge/ (Programmidentität
                        auch ohne GitHub über die Aufbewahrungsfrist)
  [--lokal DIR]         Testmodus

Archiviert wird immer der eingecheckte Stand (git show), nie eine ungespeicherte Arbeitskopie.
"""
import argparse
import os
import subprocess
import sys
import tempfile

import markdown

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gemeinsam import REPO, Ablage, fehler, heute, jetzt  # noqa: E402

CHROME = os.path.expanduser("~/.cache/ms-playwright/chromium-1243/chrome-linux64/chrome")
VD = "docs/verfahrensdokumentation.md"
CSS = """@page { size: A4; margin: 18mm 16mm 18mm 20mm; }
body { font-family: "Liberation Sans", Arial, sans-serif; font-size: 9.5pt; line-height: 1.4; color: #1b2a3a; }
h1 { font-size: 16pt; } h2 { font-size: 13pt; border-bottom: 1px solid #c9d1d9; margin-top: 7mm; } h3 { font-size: 11pt; }
table { border-collapse: collapse; width: 100%; margin: 2mm 0; page-break-inside: auto; }
th, td { border: 0.4pt solid #c9d1d9; padding: 1.2mm 1.6mm; vertical-align: top; text-align: left; }
th { background: #f0f3f6; } tr { page-break-inside: avoid; }
code, pre { font-family: "Liberation Mono", monospace; font-size: 8.5pt; } pre { background: #f7f8fa; padding: 2mm; white-space: pre-wrap; }
.stand { border: 1pt solid #b71c1c; padding: 2mm 3mm; margin-bottom: 4mm; font-size: 9pt; }"""


def git(*args):
    return subprocess.run(["git", "-C", REPO, *args], capture_output=True, text=True, check=True).stdout.strip()


def archiv_vd(ablage):
    h = git("log", "-1", "--format=%h", "--abbrev=10", "--", VD)
    if not h:
        fehler(f"{VD} ist noch nicht eingecheckt")
    datum = git("log", "-1", "--format=%cs", "--", VD)
    ordner = f"06_Steuer/{datum[:4]}/verfahrensdokumentation"
    vorhanden = [r for r, _ in ablage.dateien(ordner)]
    if any(h in r for r in vorhanden):
        print(f"Verfahrensdokumentation Fassung {datum} ({h}) ist bereits archiviert.")
        return
    text = git("show", f"{h}:{VD}")
    html = markdown.markdown(text, extensions=["tables", "fenced_code"])
    kopf = (f'<div class="stand"><strong>Archivfassung</strong> der Verfahrensdokumentation – Fassung vom {datum}, '
            f'Git-Kennung {h} (Repository staubi0815/pgh-brandschutz-buero, {VD}). Archiviert am '
            f'{jetzt():%d.%m.%Y %H:%M}.</div>')
    with tempfile.TemporaryDirectory() as tmp:
        hp, pp = os.path.join(tmp, "vd.html"), os.path.join(tmp, "vd.pdf")
        open(hp, "w", encoding="utf-8").write(f"<!DOCTYPE html><html lang='de'><head><meta charset='utf-8'>"
                                              f"<style>{CSS}</style></head><body>{kopf}{html}</body></html>")
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", f"--print-to-pdf={pp}", f"file://{hp}"],
                       capture_output=True, timeout=120, check=True)
        ziel = ablage.schreiben(f"{ordner}/VD_{datum}_{h}.pdf", open(pp, "rb").read())
    print(f"Verfahrensdokumentation archiviert: {ziel}")


def archiv_bundle(ablage):
    h = git("rev-parse", "--short=10", "HEAD")
    jahr = heute().year
    rel = f"06_Steuer/{jahr}/werkzeuge/pgh-brandschutz-buero_{heute().isoformat()}_{h}.bundle"
    if any(h in r for r, _ in ablage.dateien(f"06_Steuer/{jahr}/werkzeuge")):
        print(f"Werkzeugstand {h} ist bereits archiviert.")
        return
    with tempfile.TemporaryDirectory() as tmp:
        b = os.path.join(tmp, "repo.bundle")
        git("bundle", "create", b, "--all")
        git("bundle", "verify", b)
        ziel = ablage.schreiben(rel, open(b, "rb").read())
    print(f"Werkzeugstand archiviert: {ziel}  (wiederherstellen: git clone <bundle> pgh-brandschutz-buero)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("was", choices=["vd", "bundle"])
    ap.add_argument("--lokal")
    a = ap.parse_args()
    ablage = Ablage(a.lokal)
    archiv_vd(ablage) if a.was == "vd" else archiv_bundle(ablage)


if __name__ == "__main__":
    main()
