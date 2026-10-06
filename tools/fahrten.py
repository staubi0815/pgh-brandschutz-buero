#!/usr/bin/env python3
"""Fahrtenliste für betriebliche Fahrten mit dem Privat-PKW (pauschal je gefahrenem km, Satz aus firma.toml).

  fahrten.py eintragen --datum 2026-10-14 --ziel "Hausverwaltung X, Freising" --zweck "Vorstellungstermin" \
                       (--km 68 | --einfach 34) [--start "Zolling (Betrieb)"] [--bemerkung "..."] [--lokal DIR]
  fahrten.py summe [--jahr 2026] [--lokal DIR]

--km = insgesamt gefahrene km; --einfach = einfache Strecke, wird für Hin- und Rückfahrt verdoppelt.
Datei: NAS PGH-Brandschutz/04_Fahrten/<Jahr>/fahrten_<Jahr>.csv (Semikolon, Dezimalkomma, öffnet direkt in Excel).
"""
import argparse
import csv
import io
import os
import sys
import tomllib
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dokument import VORLAGEN, Ablage, eur, fehler, zahl  # noqa: E402

KOPF = ["Datum", "Start", "Ziel", "Zweck / Kunde", "km", "Satz €/km", "Betrag €", "Bemerkung"]
START = "Am Pfannenstiel 8, Zolling (Betrieb)"


def komma(d):
    return f"{d}".replace(".", ",")


def lade_liste(ablage, jahr):
    rel = f"04_Fahrten/{jahr}/fahrten_{jahr}.csv"
    roh = ablage.lesen(rel)
    zeilen = list(csv.DictReader(io.StringIO(roh.decode("utf-8-sig")), delimiter=";")) if roh else []
    return rel, zeilen


def speichern(ablage, rel, zeilen):
    puffer = io.StringIO()
    w = csv.DictWriter(puffer, fieldnames=KOPF, delimiter=";")
    w.writeheader()
    w.writerows(sorted(zeilen, key=lambda z: z["Datum"]))
    ablage.schreiben(rel, ("﻿" + puffer.getvalue()).encode("utf-8"), ueberschreiben=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="befehl", required=True)
    e = sub.add_parser("eintragen")
    e.add_argument("--datum", required=True)
    e.add_argument("--ziel", required=True)
    e.add_argument("--zweck", required=True)
    km = e.add_mutually_exclusive_group(required=True)
    km.add_argument("--km", type=Decimal)
    km.add_argument("--einfach", type=Decimal)
    e.add_argument("--start", default=START)
    e.add_argument("--bemerkung", default="")
    e.add_argument("--lokal")
    s = sub.add_parser("summe")
    s.add_argument("--jahr", type=int, default=date.today().year)
    s.add_argument("--lokal")
    a = ap.parse_args()

    ablage = Ablage(a.lokal)
    if a.befehl == "eintragen":
        tag = date.fromisoformat(a.datum)
        satz = Decimal(tomllib.load(open(os.path.join(VORLAGEN, "firma.toml"), "rb"))["km_satz"])
        gesamt_km = a.km if a.km is not None else a.einfach * 2
        if gesamt_km <= 0:
            fehler("km muss größer 0 sein")
        betrag = (gesamt_km * satz).quantize(Decimal("0.01"), ROUND_HALF_UP)
        bem = a.bemerkung or ("Hin- und Rückfahrt" if a.einfach is not None else "")
        rel, zeilen = lade_liste(ablage, tag.year)
        zeilen.append({"Datum": tag.isoformat(), "Start": a.start, "Ziel": a.ziel, "Zweck / Kunde": a.zweck,
                       "km": zahl(gesamt_km), "Satz €/km": komma(satz), "Betrag €": komma(betrag), "Bemerkung": bem})
        speichern(ablage, rel, zeilen)
        print(f"Eingetragen: {tag:%d.%m.%Y} {a.ziel} – {zahl(gesamt_km)} km = {eur(betrag)}")
    else:
        rel, zeilen = lade_liste(ablage, a.jahr)
        km_summe = sum((Decimal(z["km"].replace(",", ".")) for z in zeilen), Decimal("0"))
        eur_summe = sum((Decimal(z["Betrag €"].replace(",", ".")) for z in zeilen), Decimal("0"))
        print(f"Fahrten {a.jahr}: {len(zeilen)} Fahrten, {zahl(km_summe)} km, {eur(eur_summe)} (Betriebsausgabe)")


if __name__ == "__main__":
    main()
