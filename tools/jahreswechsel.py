#!/usr/bin/env python3
"""Jahreswechsel-Routine PGH-Brandschutz.

  jahreswechsel.py vorbereiten --jahr 2027   Ordner des neuen Jahres anlegen
  jahreswechsel.py pruefen     --jahr 2026   Prüfung des (abgelaufenen) Jahres, nur Anzeige
  jahreswechsel.py abschluss   --jahr 2026   Prüfung + Archiv (Verfahrensdokumentation, Werkzeugstand) +
                                             Wiederherstellungstest + Bericht nach 06_Steuer/<Jahr>/
  [--lokal DIR]  Testmodus (ohne Archiv und Wiederherstellungstest)

Empfohlen: „vorbereiten“ Ende Dezember, „abschluss“ in der zweiten Januarhälfte (nach den letzten Kontoauszügen).
Gelöscht wird nie automatisch – Fristabläufe werden nur gemeldet.
"""
import argparse
import os
import subprocess
import sys
from datetime import date
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gemeinsam import (JOURNAL_KOPF, Ablage, Buch, eur, firma, jetzt, journal_pfad,  # noqa: E402
                       vereinnahmt, werkzeug_version)

HIER = os.path.dirname(os.path.abspath(__file__))
WIEDERKEHREND = {"telekom", "versicherung", "gebuehren"}   # typische regelmäßig wiederkehrende Ausgaben (§ 11 EStG)
NEUE_ORDNER = ["01_Ausgaben/{j}", "02_Rechnungen/{j}", "03_Bank/{j}", "04_Fahrten/{j}", "06_Steuer/{j}/protokolle"]


def werkzeug(name, *args, lokal=None):
    cmd = [sys.executable, os.path.join(HIER, name), *args] + (["--lokal", lokal] if lokal else [])
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    return (r.stdout + r.stderr).strip()


def vorbereiten(ablage, jahr):
    for muster in NEUE_ORDNER:
        ablage.ordner(muster.format(j=jahr))
        print(f"Ordner bereit: {muster.format(j=jahr)}")


def pruefen(ablage, jahr, lokal):
    teile, warnungen = [], []

    eingang = [r for r, _ in ablage.dateien("00_Eingang") if "/_" not in r]
    if eingang:
        warnungen.append(f"00_Eingang ist nicht leer ({len(eingang)} Datei(en)) – erst einsortieren und erfassen")

    pruef = werkzeug("journal.py", "pruefen", "--jahr", str(jahr), lokal=lokal)
    teile.append("== Vollständigkeit (journal.py pruefen)\n" + pruef)
    if "keine Auffälligkeiten" not in pruef:
        warnungen.append("journal.py pruefen meldet offene Punkte (siehe unten)")

    teile.append("== Auswertung (Grundlage Anlage EÜR)\n" + werkzeug("journal.py", "auswertung", "--jahr", str(jahr), lokal=lokal))
    teile.append("== Fahrten\n" + werkzeug("fahrten.py", "summe", "--jahr", str(jahr), lokal=lokal))

    # Kontoauszüge: je aktivem Monat mindestens eine Datei erwartet
    start = date.fromisoformat(firma()["gruendung"])
    monate = 12 if jahr > start.year else 13 - start.month
    auszuege = len(ablage.dateien(f"03_Bank/{jahr}"))
    if auszuege < monate:
        warnungen.append(f"03_Bank/{jahr}: {auszuege} Datei(en), erwartet mindestens {monate} Monatsauszüge")

    # § 11 EStG: regelmäßig wiederkehrende Zahlungen 22.12.–10.01. prüfen
    kandidaten = []
    for j, von, bis in ((jahr, f"{jahr}-12-22", f"{jahr}-12-31"), (jahr + 1, f"{jahr + 1}-01-01", f"{jahr + 1}-01-10")):
        for z in Buch(ablage, journal_pfad(j), JOURNAL_KOPF).zeilen:
            if von <= z["Zahlungsdatum"] <= bis and z["Kategorie"] in WIEDERKEHREND:
                kandidaten.append(f"{z['Nr']} {z['Zahlungsdatum']} {z['Betrag']} € {z['Gegenpartei']} – {z['Beschreibung']}")
    teile.append("== § 11 EStG – regelmäßig wiederkehrende Zahlungen um den Jahreswechsel (von Hand prüfen, "
                 "welchem Jahr sie wirtschaftlich gehören)\n" + ("\n".join(kandidaten) if kandidaten else "keine"))

    # Kleinunternehmer im Folgejahr
    ist = vereinnahmt(ablage, jahr)
    grenze = Decimal(str(firma()["ku_grenze_vorjahr"]))
    if ist > grenze:
        warnungen.append(f"Umsatz {jahr} {eur(ist)} > {eur(grenze)}: ab {jahr + 1} KEIN Kleinunternehmer mehr – "
                         "Rechnungen mit USt, E-Rechnungspflicht ab 2028, Steuerberater einschalten")
    teile.append(f"== Kleinunternehmer {jahr + 1}\nUmsatz {jahr} (vereinnahmt): {eur(ist)} – Grenze Vorjahr {eur(grenze)} → "
                 + ("Regelung bleibt möglich" if ist <= grenze else "Regelung entfällt"))

    # Aufbewahrung: nur melden, nie automatisch löschen
    faellig = []
    for jahre, art in ((6, "Geschäftsbriefe (07_Kunden-Korrespondenz)"), (8, "Buchungsbelege (01, 02, 03)"),
                       (10, "Aufzeichnungen/Bücher (Journal, Bücher, Fahrten, 06_Steuer)")):
        alt = jahr - jahre
        if alt >= start.year:
            faellig.append(f"{art} des Jahres {alt}: Frist abgelaufen am 31.12.{jahr} – Löschprüfung "
                           "(Ablaufhemmung § 147 Abs. 3 AO: offene Festsetzungen? Montageprotokolle NICHT löschen)")
    teile.append("== Aufbewahrungsfristen\n" + ("\n".join(faellig) if faellig else "keine Unterlagen mit abgelaufener Frist"))
    return teile, warnungen


def abschluss(ablage, jahr, lokal):
    teile, warnungen = pruefen(ablage, jahr, lokal)
    if not lokal:
        teile.append("== Archiv Verfahrensdokumentation\n" + werkzeug("vd_archiv.py", "vd"))
        teile.append("== Archiv Werkzeugstand\n" + werkzeug("vd_archiv.py", "bundle"))
        r = subprocess.run(["ssh", "nas", "export PATH=$PATH:/share/CACHEDEV1_DATA/.qpkg/container-station/bin; "
                            "docker exec rclone-hetzner rclone cryptcheck /pgh hetzner-crypt-pgh:aktuell "
                            "--exclude '@Recycle/**' 2>&1 | grep -E 'differences|matching|ERROR' | tail -3"],
                           capture_output=True, text=True, timeout=1800)
        test = r.stdout.strip()
        teile.append("== Wiederherstellungstest (cryptcheck NAS ↔ Hetzner)\n" + test)
        if "0 differences" not in test:
            warnungen.append("Wiederherstellungstest zeigt Abweichungen – Sicherung prüfen!")
    kopf = [f"Jahreswechsel-Prüfung {jahr} – erstellt {jetzt():%d.%m.%Y %H:%M}, Werkzeug {werkzeug_version()}", "",
            "ERGEBNIS: " + ("keine Warnungen" if not warnungen else f"{len(warnungen)} Warnung(en)")]
    kopf += [f"  ⚠ {w}" for w in warnungen] + [""]
    bericht = "\n".join(kopf) + "\n\n".join(teile) + "\n"
    rel = f"06_Steuer/{jahr}/jahreswechsel_pruefung_{jahr}_{jetzt():%Y-%m-%d_%H%M}.txt"
    ablage.schreiben(rel, bericht.encode("utf-8"))
    print(bericht)
    print(f"Bericht gespeichert: {ablage.pfad(rel)}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("schritt", choices=["vorbereiten", "pruefen", "abschluss"])
    ap.add_argument("--jahr", type=int, required=True)
    ap.add_argument("--lokal")
    a = ap.parse_args()
    ablage = Ablage(a.lokal)
    if a.schritt == "vorbereiten":
        vorbereiten(ablage, a.jahr)
    elif a.schritt == "pruefen":
        teile, warnungen = pruefen(ablage, a.jahr, a.lokal)
        print("ERGEBNIS: " + ("keine Warnungen" if not warnungen else f"{len(warnungen)} Warnung(en)"))
        for w in warnungen:
            print(f"  ⚠ {w}")
        print("\n" + "\n\n".join(teile))
    else:
        abschluss(ablage, a.jahr, a.lokal)
    return 0


if __name__ == "__main__":
    sys.exit(main())
