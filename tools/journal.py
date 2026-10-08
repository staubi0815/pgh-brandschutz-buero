#!/usr/bin/env python3
"""Journal (Einnahmen-/Ausgaben-Aufzeichnung) für die EÜR – je Jahr nach ZAHLUNGSDATUM (§ 11 EStG).

  journal.py ausgabe  --datum JJJJ-MM-TT --betrag 49,90 --an "Bauhaus" --text "Leiter" --kategorie werkzeug_klein
                      --zahlweg bank|privat|bar (--beleg 01_Ausgaben/2026/… | --eigenbeleg "Grund")
  journal.py einnahme --datum JJJJ-MM-TT --betrag 427,80 --rechnung 2026-001 [--zahlweg bank]
  journal.py einnahme --datum … --betrag … --kategorie sonstige_einnahme --von "…" --text "…" (--beleg … | --eigenbeleg …)
  journal.py storno   J2026-007 --grund "falscher Betrag"
  journal.py auswertung [--jahr 2026]       Summen je Kategorie, Fahrten, Überschuss, Kleinunternehmer-Grenze
  journal.py pruefen    [--jahr 2026]       Vollständigkeit: Belege vorhanden? Belege ohne Eintrag? offene Rechnungen?
  journal.py abgleich   [--jahr 2026]       „bezahlt am“ im Rechnungsbuch aus dem Journal neu setzen
  journal.py kategorien

Grundsätze (Verfahrensdokumentation):
- Jeder Eintrag braucht einen Beleg in der Ablage (nicht in 00_Eingang) oder einen Eigenbeleg mit Begründung.
- Einträge werden nie geändert oder gelöscht; Korrektur nur per Storno (Gegenbuchung) + neuem Eintrag.
- Erfassung zeitnah, unbare Vorgänge innerhalb von 10 Tagen (GoBD Rz. 47).
- „privat“ = aus privaten Mitteln bezahlte Betriebsausgabe (Einlage) – zählt als Ausgabe.
- GWG (250,01–800 € netto) werden zusätzlich im GWG-Verzeichnis geführt (§ 6 Abs. 2 EStG).
- Fahrten mit dem Privat-PKW stehen in der Fahrtenliste (fahrten.py) und werden in der Auswertung addiert.
"""
import argparse
import os
import sys
from datetime import date
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gemeinsam import (JOURNAL_KOPF, RECHNUNG_KOPF, Ablage, Buch, betrag_text, dez, dmy, eur,  # noqa: E402
                       fahrten_pfad, fehler, gwg_pfad, heute, jetzt, journal_pfad, ku_status,
                       rechnungsbuch_pfad, sauber, werkzeug_version)

EINNAHMEN = {
    "umsatz": "Betriebseinnahmen als Kleinunternehmer (§ 19 UStG)",
    "sonstige_einnahme": "Sonstige Betriebseinnahmen (z. B. Erstattungen)",
}
AUSGABEN = {
    "material": "Waren und Material (z. B. Rauchwarnmelder)",
    "werkzeug_klein": "Werkzeug, Kleingeräte bis 250 € netto",
    "gwg": "GWG 250–800 € netto (Sofortabzug, GWG-Verzeichnis)",
    "telekom": "Telefon, Internet, Hosting, Domain",
    "fortbildung": "Fortbildung, Lehrgänge, Fachliteratur",
    "versicherung": "Betriebliche Versicherungen, Berufsgenossenschaft",
    "gebuehren": "Gebühren und Beiträge (Gewerbeamt, IHK, Bank)",
    "werbung": "Werbung, Visitenkarten, Website",
    "buero": "Bürobedarf, Porto, Software",
    "reise": "Reisekosten ohne Privat-PKW (Bahn, Parken, Übernachtung)",
    "sonstige": "Sonstige Betriebsausgaben",
}
GWG_KOPF = ["Lfd", "Anschaffung", "Bezeichnung", "Lieferant", "Betrag_brutto", "Netto_bei_19", "Beleg", "Journal"]
FAHRTEN_KOPF = ["Datum", "Start", "Ziel", "Zweck / Kunde", "km", "Satz €/km", "Betrag €", "Bemerkung", "Erfasst_am"]
NETTO = Decimal("1.19")


def naechste_nr(journal, jahr):
    n = max((int(z["Nr"].split("-")[1]) for z in journal.zeilen), default=0)
    return f"J{jahr}-{n + 1:03d}"


def zahlungsdatum(text):
    try:
        tag = date.fromisoformat(text)
    except ValueError:
        fehler(f"Datum „{text}“ bitte als JJJJ-MM-TT")
    if tag > heute():
        fehler("Zahlungen in der Zukunft können nicht erfasst werden.")
    return tag


def beleg_festlegen(ablage, a, tag, gegenpartei, betrag, art):
    if bool(a.beleg) == bool(a.eigenbeleg):
        fehler("Genau eins angeben: --beleg <Pfad in der Ablage> oder --eigenbeleg \"Grund\"")
    if a.beleg:
        if a.beleg.startswith("00_Eingang"):
            fehler("Beleg liegt noch in 00_Eingang – erst einsortieren (tools/einsortieren.py), dann erfassen.")
        if not ablage.existiert(a.beleg):
            fehler(f"Beleg nicht gefunden: {a.beleg}")
        return a.beleg
    # Eigenbeleg (GoBD Rz. 61): wenn kein Fremdbeleg vorhanden ist
    ordner = "01_Ausgaben" if art == "Ausgabe" else "02_Rechnungen"
    rel = f"{ordner}/{tag.year}/EIGENBELEG_{tag.isoformat()}_{sauber(gegenpartei, 30)}_{betrag_text(betrag)}.txt"
    text = (f"EIGENBELEG PGH-Brandschutz\n\nZahlungsdatum: {dmy(tag)}\nBetrag: {eur(betrag)}\nArt: {art}\n"
            f"Gegenpartei: {gegenpartei}\nZweck: {a.text}\nGrund für Eigenbeleg: {a.eigenbeleg}\n\n"
            f"Erstellt: {jetzt():%d.%m.%Y %H:%M} (tools/journal.py, Werkzeug {werkzeug_version()})\n"
            "Bestätigt durch: Patrick Gerhäuser\n")
    ablage.schreiben(rel, text.encode("utf-8"))
    print(f"Eigenbeleg angelegt: {rel}")
    return rel


def spaet_hinweis(tag):
    if (heute() - tag).days > 10:
        print("HINWEIS: Zahlung liegt mehr als 10 Tage zurück – künftig zeitnah erfassen (GoBD Rz. 47).")


def cmd_ausgabe(ablage, a):
    tag, betrag = zahlungsdatum(a.datum), dez(a.betrag)
    if betrag <= 0:
        fehler("Betrag muss positiv sein (Korrekturen per storno).")
    if a.kategorie not in AUSGABEN:
        fehler(f"Kategorie unbekannt. Möglich: {', '.join(AUSGABEN)}")
    netto = (betrag / NETTO).quantize(Decimal("0.01"))
    if a.kategorie == "werkzeug_klein" and netto > 250:
        fehler(f"{eur(betrag)} sind ca. {eur(netto)} netto (> 250 €) → Kategorie „gwg“ verwenden (GWG-Verzeichnis).")
    if a.kategorie == "gwg":
        if netto <= 250:
            fehler(f"ca. {eur(netto)} netto ≤ 250 € → Kategorie „werkzeug_klein“ (kein GWG-Verzeichnis nötig).")
        if netto > 800:
            fehler(f"ca. {eur(netto)} netto > 800 € → kein GWG, sondern Anlagevermögen mit Abschreibung "
                   "über die Nutzungsdauer (Steuerberater/Anlagenverzeichnis).")
    if a.zahlweg == "bar":
        print("HINWEIS: Barzahlung – Beleg ist zwingend; Grundsatz ist unbare Zahlung.")
    journal = Buch(ablage, journal_pfad(tag.year), JOURNAL_KOPF)
    beleg = beleg_festlegen(ablage, a, tag, a.an, betrag, "Ausgabe")
    nr = naechste_nr(journal, tag.year)
    journal.zeilen.append({"Nr": nr, "Zahlungsdatum": tag.isoformat(), "Art": "Ausgabe", "Betrag": betrag_text(betrag),
                           "Gegenpartei": a.an, "Beschreibung": a.text, "Kategorie": a.kategorie, "Zahlweg": a.zahlweg,
                           "Beleg": beleg, "Rechnung": "", "Storno_von": "",
                           "Erfasst_am": f"{jetzt():%Y-%m-%d %H:%M}", "Werkzeug": werkzeug_version()})
    journal.speichern(f"{nr} Ausgabe {eur(betrag)} {a.an} ({a.kategorie})")
    if a.kategorie == "gwg":
        gwg = Buch(ablage, gwg_pfad(tag.year), GWG_KOPF)
        gwg.zeilen.append({"Lfd": str(len(gwg.zeilen) + 1), "Anschaffung": tag.isoformat(), "Bezeichnung": a.text,
                           "Lieferant": a.an, "Betrag_brutto": betrag_text(betrag), "Netto_bei_19": betrag_text(netto),
                           "Beleg": beleg, "Journal": nr})
        gwg.speichern(f"GWG {a.text} ({nr})")
        print(f"GWG-Verzeichnis {tag.year}: {a.text} eingetragen")
    print(f"{nr}: Ausgabe {eur(betrag)} an {a.an} – {AUSGABEN[a.kategorie]}")
    spaet_hinweis(tag)


def rechnung_bezahlt_stand(ablage, nummer):
    """Summe aller Journal-Zahlungen (inkl. Storno) zu einer Rechnung über das Rechnungsjahr und das Folgejahr."""
    jahr = int(nummer.split("-")[-2])
    summe, letzte = Decimal("0"), None
    for j in (jahr, jahr + 1):
        for z in Buch(ablage, journal_pfad(j), JOURNAL_KOPF).zeilen:
            if z["Rechnung"] == nummer:
                summe += dez(z["Betrag"])
                letzte = z
    return summe, letzte


def rechnungsbuch_aktualisieren(ablage, nummer, aktion):
    jahr = int(nummer.split("-")[-2])
    rb = Buch(ablage, rechnungsbuch_pfad(jahr), RECHNUNG_KOPF)
    r = rb.finde("Nummer", nummer)
    summe, letzte = rechnung_bezahlt_stand(ablage, nummer)
    voll = summe >= dez(r["Betrag"])
    neu_bezahlt = letzte["Zahlungsdatum"] if (voll and letzte) else ""
    if r["Bezahlt_am"] != neu_bezahlt:
        r["Bezahlt_am"] = neu_bezahlt
        r["Journal"] = letzte["Nr"] if letzte else ""
        rb.speichern(f"Rechnung {nummer}: {aktion} → bezahlt_am „{neu_bezahlt}“")
    return summe, dez(r["Betrag"])


def cmd_einnahme(ablage, a):
    tag, betrag = zahlungsdatum(a.datum), dez(a.betrag)
    if betrag <= 0:
        fehler("Betrag muss positiv sein (Korrekturen per storno).")
    journal = Buch(ablage, journal_pfad(tag.year), JOURNAL_KOPF)
    nr = naechste_nr(journal, tag.year)
    if a.rechnung:
        jahr = int(a.rechnung.split("-")[-2])
        r = Buch(ablage, rechnungsbuch_pfad(jahr), RECHNUNG_KOPF).finde("Nummer", a.rechnung)
        if not r:
            fehler(f"Rechnung {a.rechnung} nicht im Rechnungsausgangsbuch {jahr}")
        if r["Bezahlt_am"]:
            fehler(f"Rechnung {a.rechnung} ist bereits als bezahlt am {r['Bezahlt_am']} erfasst.")
        if tag.isoformat() < r["Datum"]:
            fehler("Zahlungsdatum liegt vor dem Rechnungsdatum.")
        bisher, _ = rechnung_bezahlt_stand(ablage, a.rechnung)
        offen = dez(r["Betrag"]) - bisher
        if betrag > offen:
            fehler(f"Betrag {eur(betrag)} ist höher als der offene Betrag {eur(offen)} der Rechnung {a.rechnung}.")
        if betrag < offen and not a.teilzahlung:
            fehler(f"Offen sind {eur(offen)} – bei Teilzahlung --teilzahlung angeben.")
        kategorie, gegen, text, beleg = "umsatz", r["Kunde"], f"Zahlung Rechnung {a.rechnung}", r["Datei"]
    else:
        if a.kategorie not in EINNAHMEN or a.kategorie == "umsatz":
            fehler("Umsätze nur mit --rechnung erfassen; sonst --kategorie sonstige_einnahme.")
        if not (a.von and a.text):
            fehler("--von und --text angeben.")
        kategorie, gegen, text = a.kategorie, a.von, a.text
        beleg = beleg_festlegen(ablage, a, tag, a.von, betrag, "Einnahme")
    journal.zeilen.append({"Nr": nr, "Zahlungsdatum": tag.isoformat(), "Art": "Einnahme", "Betrag": betrag_text(betrag),
                           "Gegenpartei": gegen, "Beschreibung": text, "Kategorie": kategorie, "Zahlweg": a.zahlweg,
                           "Beleg": beleg, "Rechnung": a.rechnung or "", "Storno_von": "",
                           "Erfasst_am": f"{jetzt():%Y-%m-%d %H:%M}", "Werkzeug": werkzeug_version()})
    journal.speichern(f"{nr} Einnahme {eur(betrag)} {gegen}" + (f" zu {a.rechnung}" if a.rechnung else ""))
    print(f"{nr}: Einnahme {eur(betrag)} von {gegen}")
    if a.rechnung:
        summe, soll = rechnungsbuch_aktualisieren(ablage, a.rechnung, f"Zahlung {nr}")
        print(f"Rechnung {a.rechnung}: {eur(summe)} von {eur(soll)} bezahlt" + (" – vollständig" if summe >= soll else ""))
        ku = ku_status(ablage, tag.year)
        if ku["quote"] >= ku["warnung_ab"]:
            print(f"WARNUNG Kleinunternehmergrenze {tag.year}: {ku['quote']:.0%} von {eur(ku['grenze'])}")
    spaet_hinweis(tag)


def cmd_storno(ablage, a):
    jahr = int(a.nr[1:5])
    journal = Buch(ablage, journal_pfad(jahr), JOURNAL_KOPF)
    alt = journal.finde("Nr", a.nr)
    if not alt:
        fehler(f"{a.nr} nicht im Journal {jahr}")
    if alt["Storno_von"] or any(z["Storno_von"] == a.nr for z in journal.zeilen):
        fehler(f"{a.nr} ist selbst ein Storno oder wurde bereits storniert.")
    nr = naechste_nr(journal, jahr)
    neu = dict(alt)
    neu.update({"Nr": nr, "Betrag": betrag_text(-dez(alt["Betrag"])), "Storno_von": a.nr,
                "Beschreibung": f"STORNO {a.nr}: {a.grund}", "Erfasst_am": f"{jetzt():%Y-%m-%d %H:%M}",
                "Werkzeug": werkzeug_version()})
    journal.zeilen.append(neu)
    journal.speichern(f"{nr} Storno von {a.nr}: {a.grund}")
    print(f"{nr}: Storno von {a.nr} ({eur(-dez(alt['Betrag']))}) – Grund: {a.grund}")
    if alt["Rechnung"]:
        summe, soll = rechnungsbuch_aktualisieren(ablage, alt["Rechnung"], f"Storno {nr}")
        print(f"Rechnung {alt['Rechnung']}: jetzt {eur(summe)} von {eur(soll)} bezahlt")
    if alt["Kategorie"] == "gwg":
        print("HINWEIS: GWG-Verzeichnis-Eintrag bleibt stehen; Storno ist im Journal vermerkt.")


def cmd_auswertung(ablage, a):
    journal = Buch(ablage, journal_pfad(a.jahr), JOURNAL_KOPF)
    summen = {}
    for z in journal.zeilen:
        summen[(z["Art"], z["Kategorie"])] = summen.get((z["Art"], z["Kategorie"]), Decimal("0")) + dez(z["Betrag"])
    fahrten = sum((dez(z["Betrag €"]) for z in Buch(ablage, fahrten_pfad(a.jahr), FAHRTEN_KOPF).zeilen), Decimal("0"))
    ein = sum((v for (art, _), v in summen.items() if art == "Einnahme"), Decimal("0"))
    aus = sum((v for (art, _), v in summen.items() if art == "Ausgabe"), Decimal("0")) + fahrten
    print(f"Auswertung {a.jahr} (Zahlungsdatum; {len(journal.zeilen)} Journaleinträge)\n")
    print("Einnahmen")
    for k, text in EINNAHMEN.items():
        if ("Einnahme", k) in summen:
            print(f"  {text:<62} {eur(summen[('Einnahme', k)]):>14}")
    print(f"  {'Summe Einnahmen':<62} {eur(ein):>14}\nAusgaben")
    for k, text in AUSGABEN.items():
        if ("Ausgabe", k) in summen:
            print(f"  {text:<62} {eur(summen[('Ausgabe', k)]):>14}")
    if fahrten:
        print(f"  {'Fahrten Privat-PKW (Fahrtenliste, Kilometerpauschale)':<62} {eur(fahrten):>14}")
    print(f"  {'Summe Ausgaben':<62} {eur(aus):>14}\n")
    print(f"  {'Überschuss (Gewinn/Verlust)':<62} {eur(ein - aus):>14}\n")
    ku = ku_status(ablage, a.jahr)
    print(f"Kleinunternehmer {a.jahr}: vereinnahmt {eur(ku['vereinnahmt'])}, offene Rechnungen {eur(ku['offen'])} "
          f"→ {ku['quote']:.0%} von {eur(ku['grenze'])}" + ("" if ku["vorjahr_ok"] else "  ⚠ VORJAHR > 25.000 €!"))
    print("\nHinweis: Übersicht für die Anlage EÜR – keine Steuerberatung; Zuordnung der Zeilen beim Ausfüllen prüfen.")


def cmd_pruefen(ablage, a):
    probleme = []
    journal = Buch(ablage, journal_pfad(a.jahr), JOURNAL_KOPF)
    referenziert = {z["Beleg"] for z in journal.zeilen}
    for z in journal.zeilen:
        if not ablage.existiert(z["Beleg"]):
            probleme.append(f"{z['Nr']}: Beleg fehlt in der Ablage ({z['Beleg']})")
    storniert = {z["Storno_von"] for z in journal.zeilen if z["Storno_von"]}
    gezaehlt = {}
    for z in journal.zeilen:
        if z["Art"] == "Ausgabe" and not z["Storno_von"] and z["Nr"] not in storniert:
            gezaehlt.setdefault(z["Beleg"], []).append(z["Nr"])
    for beleg, nummern in gezaehlt.items():
        if len(nummern) > 1:
            probleme.append(f"Beleg mehrfach als Ausgabe erfasst ({', '.join(nummern)}): {beleg} – doppelt gezählt?")
    nrn = sorted(int(z["Nr"].split("-")[1]) for z in journal.zeilen)
    if nrn and nrn != list(range(1, len(nrn) + 1)):
        probleme.append("Journalnummern nicht lückenlos")
    for rel, _ in ablage.dateien(f"01_Ausgaben/{a.jahr}"):
        if rel not in referenziert:
            probleme.append(f"Beleg ohne Journaleintrag: {rel}")
    for rel, ts in ablage.dateien("00_Eingang"):
        alter = (jetzt().timestamp() - ts) / 86400
        if alter > 7 and "/_" not in rel:
            probleme.append(f"Seit {alter:.0f} Tagen in 00_Eingang: {rel}")
    for r in Buch(ablage, rechnungsbuch_pfad(a.jahr), RECHNUNG_KOPF).zeilen:
        if not r["Bezahlt_am"]:
            status = "ÜBERFÄLLIG" if r["Faellig"] < heute().isoformat() else "offen"
            probleme.append(f"Rechnung {r['Nummer']} {status} (fällig {r['Faellig']}, {r['Betrag']} €, {r['Kunde']})")
    for r in Buch(ablage, rechnungsbuch_pfad(a.jahr), RECHNUNG_KOPF).zeilen:
        summe, _ = rechnung_bezahlt_stand(ablage, r["Nummer"])
        if (summe >= dez(r["Betrag"])) != bool(r["Bezahlt_am"]):
            probleme.append(f"Rechnung {r['Nummer']}: „bezahlt am“ passt nicht zum Journal ({eur(summe)}) → journal.py abgleich")
    gwg_journal = {z["Nr"] for z in journal.zeilen if z["Kategorie"] == "gwg" and not z["Storno_von"]}
    gwg_verz = {z["Journal"] for z in Buch(ablage, gwg_pfad(a.jahr), GWG_KOPF).zeilen}
    for nr in gwg_journal - gwg_verz:
        probleme.append(f"{nr}: GWG fehlt im GWG-Verzeichnis")
    print(f"Prüfung {a.jahr}: " + ("keine Auffälligkeiten" if not probleme else f"{len(probleme)} Punkte"))
    for p in probleme:
        print(f"  - {p}")
    return 1 if probleme else 0


def cmd_abgleich(ablage, a):
    """Setzt „bezahlt am“ aller Rechnungen eines Jahres neu aus dem Journal (z. B. nach abgebrochenem Lauf)."""
    for r in Buch(ablage, rechnungsbuch_pfad(a.jahr), RECHNUNG_KOPF).zeilen:
        summe, soll = rechnungsbuch_aktualisieren(ablage, r["Nummer"], "Abgleich mit Journal")
        print(f"{r['Nummer']}: {eur(summe)} von {eur(soll)} bezahlt")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="befehl", required=True)
    for name in ("ausgabe", "einnahme"):
        p = sub.add_parser(name)
        p.add_argument("--datum", required=True, help="Zahlungsdatum JJJJ-MM-TT")
        p.add_argument("--betrag", required=True)
        p.add_argument("--zahlweg", choices=["bank", "privat", "bar"], default="bank")
        p.add_argument("--text", default="")
        p.add_argument("--beleg")
        p.add_argument("--eigenbeleg")
        p.add_argument("--lokal")
        if name == "ausgabe":
            p.add_argument("--an", required=True)
            p.add_argument("--kategorie", required=True)
        else:
            p.add_argument("--rechnung")
            p.add_argument("--teilzahlung", action="store_true")
            p.add_argument("--kategorie", default="umsatz")
            p.add_argument("--von")
    s = sub.add_parser("storno")
    s.add_argument("nr")
    s.add_argument("--grund", required=True)
    s.add_argument("--lokal")
    for name in ("auswertung", "pruefen", "abgleich"):
        p = sub.add_parser(name)
        p.add_argument("--jahr", type=int, default=heute().year)
        p.add_argument("--lokal")
    sub.add_parser("kategorien")
    a = ap.parse_args()

    if a.befehl == "kategorien":
        for titel, d in (("Einnahmen", EINNAHMEN), ("Ausgaben", AUSGABEN)):
            print(titel)
            for k, v in d.items():
                print(f"  {k:<18} {v}")
        return 0
    ablage = Ablage(a.lokal)
    return {"ausgabe": cmd_ausgabe, "einnahme": cmd_einnahme, "storno": cmd_storno,
            "auswertung": cmd_auswertung, "pruefen": cmd_pruefen, "abgleich": cmd_abgleich}[a.befehl](ablage, a) or 0


if __name__ == "__main__":
    sys.exit(main())
