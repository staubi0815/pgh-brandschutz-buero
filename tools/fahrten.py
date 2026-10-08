#!/usr/bin/env python3
"""Fahrtenliste für betriebliche Fahrten mit dem Privat-PKW (pauschal je gefahrenem km, Satz aus firma.toml).

  fahrten.py eintragen --datum 2026-10-14 --ziel "Hausverwaltung X, Freising" --zweck "Vorstellungstermin" \
                       (--km 68 | --einfach 34) [--start "Zolling (Betrieb)"] [--bemerkung "..."] [--lokal DIR]
  fahrten.py summe [--jahr 2026] [--lokal DIR]

--km = insgesamt gefahrene km; --einfach = einfache Strecke, wird für Hin- und Rückfahrt verdoppelt.
Datei: NAS PGH-Brandschutz/04_Fahrten/<Jahr>/fahrten_<Jahr>.csv (Semikolon, Dezimalkomma; nur lesend in Excel öffnen).
Jede Änderung wird mit Vorversion in 04_Fahrten/<Jahr>/_historie/ protokolliert.
"""
import argparse
import os
import sys
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gemeinsam import (Ablage, Buch, betrag_text, dez, dmy, eur, fahrten_pfad, fehler, firma,  # noqa: E402
                       heute, jetzt, zahl)

KOPF = ["Datum", "Start", "Ziel", "Zweck / Kunde", "km", "Satz €/km", "Betrag €", "Bemerkung", "Erfasst_am"]
START = "Am Pfannenstiel 8, Zolling (Betrieb)"


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
    s.add_argument("--jahr", type=int, default=heute().year)
    s.add_argument("--lokal")
    a = ap.parse_args()

    ablage = Ablage(a.lokal)
    if a.befehl == "eintragen":
        tag = date.fromisoformat(a.datum)
        if tag > heute():
            fehler("Fahrten in der Zukunft können nicht eingetragen werden.")
        satz = Decimal(firma()["km_satz"])
        gesamt_km = a.km if a.km is not None else a.einfach * 2
        if gesamt_km <= 0:
            fehler("km muss größer 0 sein")
        betrag = (gesamt_km * satz).quantize(Decimal("0.01"), ROUND_HALF_UP)
        bem = a.bemerkung or ("Hin- und Rückfahrt" if a.einfach is not None else "")
        buch = Buch(ablage, fahrten_pfad(tag.year), KOPF)
        buch.zeilen.append({"Datum": tag.isoformat(), "Start": a.start, "Ziel": a.ziel, "Zweck / Kunde": a.zweck,
                            "km": zahl(gesamt_km), "Satz €/km": betrag_text(satz),
                            "Betrag €": betrag_text(betrag), "Bemerkung": bem, "Erfasst_am": f"{jetzt():%Y-%m-%d %H:%M}"})
        buch.zeilen.sort(key=lambda z: z["Datum"])
        buch.speichern(f"Fahrt {dmy(tag)} {a.ziel} ({zahl(gesamt_km)} km) eingetragen")
        print(f"Eingetragen: {dmy(tag)} {a.ziel} – {zahl(gesamt_km)} km = {eur(betrag)}")
        if (heute() - tag).days > 10:
            print("HINWEIS: Fahrt liegt mehr als 10 Tage zurück – künftig zeitnah eintragen (GoBD Rz. 47).")
    else:
        zeilen = Buch(ablage, fahrten_pfad(a.jahr), KOPF).zeilen
        km_summe = sum((dez(z["km"]) for z in zeilen), Decimal("0"))
        eur_summe = sum((dez(z["Betrag €"]) for z in zeilen), Decimal("0"))
        print(f"Fahrten {a.jahr}: {len(zeilen)} Fahrten, {zahl(km_summe)} km, {eur(eur_summe)} (Betriebsausgabe)")


if __name__ == "__main__":
    main()
