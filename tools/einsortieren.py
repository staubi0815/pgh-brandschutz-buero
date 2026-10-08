#!/usr/bin/env python3
"""Belege aus 00_Eingang in die Ablage verschieben – mit Protokoll (GoBD Rz. 117).

  einsortieren.py liste                                   zeigt 00_Eingang
  einsortieren.py <datei in 00_Eingang> <zielordner> [--name JJJJ-MM-TT_Firma_Betrag_Text]

Zielordner: 01_Ausgaben/<Jahr>, 03_Bank/<Jahr>, 05_Vertraege, 06_Steuer/<Jahr>, 07_Kunden/<Kurzname>, 08_Nachweise.
Der Inhalt bleibt unverändert (Empfangsformat, GoBD Rz. 131); nur der Dateiname ändert sich, die Endung bleibt.
Es wird nie überschrieben. Jede Verschiebung steht in 06_Steuer/<Jahr>/protokolle/ablage_<Jahr>.log.
"""
import argparse
import os
import re
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gemeinsam import Ablage, fehler, heute, jetzt, protokoll_pfad, sauber, werkzeug_version  # noqa: E402

ZIELE = [r"01_Ausgaben/\d{4}", r"03_Bank/\d{4}", r"05_Vertraege", r"06_Steuer/\d{4}", r"07_Kunden/[A-Za-z0-9_-]+",
         r"08_Nachweise"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("quelle", help="Datei in 00_Eingang oder „liste“")
    ap.add_argument("ziel", nargs="?")
    ap.add_argument("--name", help="neuer Dateiname ohne Endung")
    ap.add_argument("--lokal")
    a = ap.parse_args()
    ablage = Ablage(a.lokal)

    if a.quelle == "liste":
        dateien = [(r, ts) for r, ts in ablage.dateien("00_Eingang") if "/_" not in r]
        for rel, ts in sorted(dateien, key=lambda x: x[1]):
            print(f"{datetime.fromtimestamp(ts):%Y-%m-%d %H:%M}  {rel}")
        print(f"{len(dateien)} Datei(en) in 00_Eingang")
        return

    quelle = a.quelle if a.quelle.startswith("00_Eingang/") else f"00_Eingang/{a.quelle}"
    if not a.ziel or not any(re.fullmatch(m, a.ziel.rstrip("/")) for m in ZIELE):
        fehler(f"Zielordner ungültig. Erlaubt: {', '.join(ZIELE)}")
    endung = os.path.splitext(quelle)[1].lower()
    name = (sauber(a.name, 120) if a.name else os.path.splitext(os.path.basename(quelle))[0]) + endung
    ziel = f"{a.ziel.rstrip('/')}/{name}"
    ablage.verschieben(quelle, ziel)
    ablage.anhaengen(protokoll_pfad(heute().year, "ablage"),
                     f"{jetzt():%Y-%m-%d %H:%M:%S} | {quelle} → {ziel} | Werkzeug {werkzeug_version()}\n")
    print(f"einsortiert: {ziel}")


if __name__ == "__main__":
    main()
