#!/usr/bin/env python3
"""Rechnungen und Angebote für PGH-Brandschutz als PDF erzeugen.

  dokument.py rechnung <daten.toml> [--final] [--lokal DIR]
  dokument.py angebot  <daten.toml> [--final] [--lokal DIR]

Ohne --final: Entwurf mit Wasserzeichen „ENTWURF“, verbraucht keine Nummer.
  Ablage: NAS 02_Rechnungen/Entwuerfe bzw. 07_Kunden/Entwuerfe.
Mit --final: nächste freie Nummer aus dem Ausgangsbuch (Rechnung 2026-001, Angebot A-2026-001),
  PDF + Eingabedaten auf dem NAS, Zeile im Ausgangsbuch. Bricht ab, wenn Pflichtangaben fehlen
  (§ 34a UStDV: u. a. Steuernummer) oder dieselben Eingabedaten schon einmal final erzeugt wurden.
--lokal DIR: alles in ein lokales Verzeichnis statt aufs NAS (zum Testen).

Endgültige Rechnungen sind zugleich E-Rechnungen (ZUGFeRD/Factur-X, Profil EN 16931, siehe erechnung.py):
das XML wird ins PDF eingebettet und vor dem Speichern mit Mustang geprüft – bei Fehlern wird nichts
gespeichert und keine Nummer verbraucht. Läuft automatisch in der venv ~/.venvs/pgh.

Eingabeformat: siehe vorlagen/beispiel_rechnung.toml. Kundendaten gehören NICHT ins Repo –
Eingabedateien liegen nur auf dem NAS (bzw. in /tmp beim Erstellen).
"""
import argparse
import hashlib
import os
import re
import subprocess
import sys
import tempfile
import tomllib
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from html import escape
from string import Template

# E-Rechnung braucht factur-x/pikepdf aus der venv ~/.venvs/pgh – bei Aufruf mit System-Python dorthin wechseln
VENV = os.path.expanduser("~/.venvs/pgh")
try:
    import facturx  # noqa: F401
except ImportError:
    if os.path.exists(os.path.join(VENV, "bin", "python")) and sys.prefix != VENV:
        os.execv(os.path.join(VENV, "bin", "python"), [os.path.join(VENV, "bin", "python")] + sys.argv)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gemeinsam import (ANGEBOT_KOPF, RECHNUNG_KOPF, REPO, VORLAGEN, Ablage, Buch,  # noqa: E402
                       angebotsbuch_pfad, betrag_text, dmy, eur, fehler, firma as lade_firma, heute,
                       jetzt, ku_status, rechnungsbuch_pfad, sauber, werkzeug_version, zahl)

LOGO = os.path.join(REPO, "website", "static", "img", "logo.svg")
CHROME = os.path.expanduser("~/.cache/ms-playwright/chromium-1243/chrome-linux64/chrome")

ARTEN = {"material": "Material", "arbeit": "Arbeitsleistung", "fahrt": "Fahrtkosten"}
KLEINUNTERNEHMER = ("Steuerfreie Leistung als Kleinunternehmer nach § 19 UStG – "
                    "Umsatzsteuer wird daher nicht berechnet.")

KONFIG = {
    "rechnung": {"titel": "Rechnung", "praefix": "", "buch": rechnungsbuch_pfad, "kopf": RECHNUNG_KOPF,
                 "entwurf_dir": "02_Rechnungen/Entwuerfe"},
    "angebot": {"titel": "Angebot", "praefix": "A-", "buch": angebotsbuch_pfad, "kopf": ANGEBOT_KOPF,
                "entwurf_dir": "07_Kunden/Entwuerfe"},
}


def offen(text):
    return f'<span class="offen">[OFFEN: {escape(text)}]</span>'


# ---------- Daten ----------
def lade(datei):
    with open(datei, "rb") as f:
        roh = f.read()
    return tomllib.loads(roh.decode()), roh


def pruefe_eingabe(d):
    k = d.get("kunde", {})
    for feld in ("name", "strasse", "plz_ort", "kurz"):
        if not str(k.get(feld, "")).strip():
            fehler(f"[kunde].{feld} fehlt")
    if not d.get("position"):
        fehler("keine [[position]] angegeben")
    for i, p in enumerate(d["position"], 1):
        for feld in ("menge", "text", "preis"):
            if feld not in p:
                fehler(f"Position {i}: {feld} fehlt")
        if p.get("art", "material") not in ARTEN:
            fehler(f"Position {i}: art muss {', '.join(ARTEN)} sein")


def berechne(d):
    zeilen, gesamt, anteil_35a = [], Decimal("0"), Decimal("0")
    for p in d["position"]:
        menge, preis = Decimal(str(p["menge"])), Decimal(str(p["preis"]))
        betrag = (menge * preis).quantize(Decimal("0.01"), ROUND_HALF_UP)
        art = p.get("art", "material")
        gesamt += betrag
        if art in ("arbeit", "fahrt"):
            anteil_35a += betrag
        zeilen.append({**p, "menge_d": menge, "preis_d": preis, "betrag": betrag, "art": art})
    return zeilen, gesamt, anteil_35a


def naechste_nummer(buch, praefix, jahr):
    hoechste = 0
    for zeile in buch.zeilen:
        m = re.fullmatch(rf"{re.escape(praefix)}{jahr}-(\d+)", zeile["Nummer"])
        if m:
            hoechste = max(hoechste, int(m.group(1)))
    return f"{praefix}{jahr}-{hoechste + 1:03d}"


def schon_erzeugt(buecher, sha):
    for b in buecher:
        z = b.finde("Quelle_SHA256", sha)
        if z:
            return z["Nummer"]
    return None


# ---------- HTML/PDF ----------
def baue_html(art, d, firma, nummer, entwurf):
    k = KONFIG[art]
    doc = d.get("dokument", {})
    kunde = d["kunde"]
    datum = date.fromisoformat(doc["datum"]) if doc.get("datum") else heute()
    zeilen, gesamt, anteil_35a = berechne(d)

    f = {f"f_{key}": escape(str(val)) for key, val in firma.items()}
    f["f_steuernummer"] = escape(firma["steuernummer"]) if firma.get("steuernummer") else offen("Steuernummer")
    f["f_iban"] = escape(firma["iban"]) if firma.get("iban") else offen("IBAN Geschäftskonto")

    empf = [kunde["name"], kunde.get("zusatz", ""), kunde["strasse"], kunde["plz_ort"]]
    empfaenger = "<br>".join(escape(x) for x in empf if x)

    info = [(f"{k['titel']}snummer" if art == "rechnung" else "Angebotsnummer",
             offen("Nummer bei Freigabe") if entwurf else escape(nummer)),
            (f"{k['titel']}sdatum" if art == "rechnung" else "Datum", dmy(datum))]
    if art == "rechnung":
        leistung = doc.get("leistungsdatum", "")
        info.append(("Leistungsdatum", escape(leistung) if leistung else offen("Leistungsdatum")))
        faellig = datum + timedelta(days=int(firma["zahlungsziel_tage"]))
    else:
        gueltig = datum + timedelta(days=int(doc.get("gueltig_tage", firma["angebot_gueltig_tage"])))
        info.append(("Gültig bis", dmy(gueltig)))
    if kunde.get("kundennummer"):
        info.append(("Kundennummer", escape(str(kunde["kundennummer"]))))
    if doc.get("ihr_zeichen"):
        info.append(("Ihr Zeichen", escape(doc["ihr_zeichen"])))
    infozeilen = "".join(f"<tr><td>{a}</td><td>{b}</td></tr>" for a, b in info)

    pos_html = []
    for i, z in enumerate(zeilen, 1):
        # Kurze Vorsilben mit Bindestrich (Q-Label, E-Mail) nicht am Zeilenende trennen
        text = re.sub(r"\b(\w{1,2})-(\w)", "\\1\u2011\\2", escape(z["text"])).replace("\n", "<br>")
        pos_html.append(
            f'<tr><td class="nr">{i}</td><td>{text}<span class="art">{ARTEN[z["art"]]}</span></td>'
            f'<td class="menge r">{zahl(z["menge_d"])} {escape(z.get("einheit", ""))}</td>'
            f'<td class="ep r">{eur(z["preis_d"])}</td><td class="gp r">{eur(z["betrag"])}</td></tr>')

    summen = f'<tr class="gesamt"><td>Gesamtbetrag</td><td>{eur(gesamt)}</td></tr>'

    hinweis_35a = ""
    if d.get("dokument", {}).get("ausweis_35a", True) and anteil_35a > 0:
        if art == "rechnung":
            hinweis_35a = (f"<p>Im Gesamtbetrag sind Arbeits- und Fahrtkosten von <strong>{eur(anteil_35a)}</strong> "
                           "enthalten (begünstigter Anteil für Handwerkerleistungen nach § 35a EStG; "
                           "Voraussetzung ist die Zahlung per Überweisung).</p>")
        else:
            hinweis_35a = (f"<p>Davon Arbeits- und Fahrtkosten: {eur(anteil_35a)} "
                           "(in der Rechnung gesondert ausgewiesen, § 35a EStG).</p>")

    if art == "rechnung":
        zweck = escape(nummer) if not entwurf else "die Rechnungsnummer"
        zahlung = (f"<p>Bitte überweisen Sie den Gesamtbetrag ohne Abzug bis zum <strong>{dmy(faellig)}</strong> "
                   f"auf das unten genannte Konto. Verwendungszweck: {zweck}.</p>")
        if not entwurf:
            zahlung += ("<p style=\"font-size:8pt;color:#52606d\">Diese PDF-Rechnung enthält die Rechnungsdaten zusätzlich "
                        "maschinenlesbar (E-Rechnung ZUGFeRD/Factur-X, Profil EN 16931).</p>")
        ueberschrift = f"Rechnung {'' if entwurf else escape(nummer)}".strip()
    else:
        zahlung = "<p>Ich freue mich auf Ihren Auftrag. Bei Fragen erreichen Sie mich unter der unten genannten Telefonnummer.</p>"
        ueberschrift = f"Angebot {'' if entwurf else escape(nummer)}".strip()

    betreff = doc.get("betreff", "")
    if betreff:
        ueberschrift += f" – {escape(betreff)}"
    objekt = f'<p class="objekt">Objekt / Leistungsort: {escape(doc["objekt"])}</p>' if doc.get("objekt") else ""
    standard_einl = ("für die durchgeführten Arbeiten erlaube ich mir, wie folgt abzurechnen:" if art == "rechnung"
                     else "vielen Dank für Ihre Anfrage. Gerne biete ich Ihnen folgende Leistungen an:")
    anrede = escape(doc.get("anrede", "Sehr geehrte Damen und Herren,"))
    einleitung = f"<p>{anrede}<br>{escape(doc.get('einleitung', standard_einl))}</p>"
    schluss = f"<p>{escape(doc['schluss'])}</p>" if doc.get("schluss") else ""
    schluss += f"<p>Mit freundlichen Grüßen<br>{escape(firma['inhaber'])}</p>"

    werte = {
        **f,
        "titel": f"{k['titel']} {nummer}", "css": open(os.path.join(VORLAGEN, "dokument.css")).read(),
        "logo": open(LOGO).read(), "wasserzeichen": '<div class="wasserzeichen">ENTWURF</div>' if entwurf else "",
        "empfaenger": empfaenger, "infozeilen": infozeilen, "ueberschrift": ueberschrift, "objekt": objekt,
        "einleitung": einleitung, "positionen": "".join(pos_html), "summenzeilen": summen,
        "kleinunternehmer": KLEINUNTERNEHMER, "hinweis_35a": hinweis_35a, "zahlung": zahlung, "schluss": schluss,
    }
    html = Template(open(os.path.join(VORLAGEN, "dokument.html")).read()).substitute(werte)
    meta = {"datum": datum, "gesamt": gesamt, "anteil_35a": anteil_35a, "zeilen": zeilen,
            "gueltig": gueltig if art == "angebot" else None,
            "faellig": faellig if art == "rechnung" else None}
    return html, meta


def pdf_aus_html(html):
    with tempfile.TemporaryDirectory() as tmp:
        h, p = os.path.join(tmp, "d.html"), os.path.join(tmp, "d.pdf")
        open(h, "w", encoding="utf-8").write(html)
        subprocess.run([CHROME, "--headless=new", "--no-pdf-header-footer", "--disable-gpu",
                        f"--print-to-pdf={p}", f"file://{h}"], capture_output=True, timeout=120, check=True)
        return open(p, "rb").read()


# ---------- Ablauf ----------
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("art", choices=KONFIG)
    ap.add_argument("daten")
    ap.add_argument("--final", action="store_true")
    ap.add_argument("--lokal", help="Testmodus: Ablage in lokalem Verzeichnis, Datum darf abweichen")
    a = ap.parse_args()

    firma = lade_firma()
    d, roh = lade(a.daten)
    pruefe_eingabe(d)
    k = KONFIG[a.art]
    ablage = Ablage(a.lokal)
    kurz = sauber(d["kunde"]["kurz"])
    sha = hashlib.sha256(roh).hexdigest()

    if not a.final:
        html, meta = baue_html(a.art, d, firma, "ENTWURF", entwurf=True)
        ziel = ablage.schreiben(f"{k['entwurf_dir']}/ENTWURF_{k['titel']}_{kurz}_{jetzt():%Y-%m-%d_%H%M}.pdf",
                                pdf_aus_html(html))
        print(f"Entwurf: {ziel}  ({eur(meta['gesamt'])})")
        if a.art == "rechnung":
            import erechnung
            try:
                erechnung.leistungszeit(d.get("dokument", {}).get("leistungsdatum", ""))
            except ValueError as exc:
                print(f"HINWEIS für die endgültige Rechnung: {exc}")
        return

    # --- Prüfungen vor der endgültigen Erstellung (nichts wird gespeichert, solange eine fehlschlägt) ---
    version = werkzeug_version(sauber_pflicht=not a.lokal)
    fehlend = [n for n in ("steuernummer", "iban") if not firma.get(n)]
    if a.art == "rechnung" and not d.get("dokument", {}).get("leistungsdatum"):
        fehlend.append("[dokument].leistungsdatum")
    if fehlend:
        fehler(f"Für ein endgültiges Dokument fehlt: {', '.join(fehlend)} (vorlagen/firma.toml bzw. Eingabe)")
    if a.art == "rechnung":
        import erechnung
        try:
            erechnung.leistungszeit(d["dokument"]["leistungsdatum"])
        except ValueError as exc:
            fehler(str(exc))

    # Ausstellungsdatum = heute (kein Zurückdatieren); abweichend nur im Testmodus --lokal
    vorgabe = d.get("dokument", {}).get("datum")
    if vorgabe and not a.lokal and date.fromisoformat(vorgabe) != heute():
        fehler(f"Ausstellungsdatum muss heute sein ({dmy(heute())}), nicht {vorgabe} – Feld „datum“ weglassen.")
    datum = date.fromisoformat(vorgabe) if vorgabe else heute()

    buch = Buch(ablage, k["buch"](datum.year), k["kopf"])
    vorjahr = Buch(ablage, k["buch"](datum.year - 1), k["kopf"])
    vorher = schon_erzeugt([buch, vorjahr], sha)
    if vorher:
        fehler(f"Diese Eingabedaten wurden bereits als {vorher} erzeugt.")
    if buch.zeilen and max(z["Datum"] for z in buch.zeilen) > datum.isoformat():
        fehler(f"Datum {dmy(datum)} liegt vor dem letzten Eintrag im Buch {datum.year} – Reihenfolge wäre widersprüchlich.")

    nummer = naechste_nummer(buch, k["praefix"], datum.year)
    html, meta = baue_html(a.art, d, firma, nummer, entwurf=False)
    if meta["datum"] != datum:
        fehler("interner Datumsfehler")

    if a.art == "rechnung":
        ku = ku_status(ablage, datum.year, zusaetzlich=meta["gesamt"])
        if not ku["vorjahr_ok"]:
            fehler(f"Vorjahresumsatz {eur(ku['vorjahr'])} > 25.000 € – Kleinunternehmerregelung gilt {datum.year} nicht mehr. "
                   "Rechnung mit Umsatzsteuer nötig (Steuerberater).")
        if ku["erwartet"] > ku["grenze"]:
            fehler(f"Mit dieser Rechnung würden die Umsätze {datum.year} ({eur(ku['erwartet'])} inkl. offener Rechnungen) "
                   f"die Kleinunternehmergrenze von {eur(ku['grenze'])} überschreiten – der überschreitende Umsatz ist "
                   "umsatzsteuerpflichtig. Nicht als Kleinunternehmer-Rechnung erstellen (Steuerberater).")
        if ku["quote"] >= ku["warnung_ab"]:
            print(f"WARNUNG Kleinunternehmergrenze: {ku['quote']:.0%} von {eur(ku['grenze'])} erreicht "
                  f"({eur(ku['erwartet'])} inkl. offener Rechnungen und dieser).")

    pdf = pdf_aus_html(html)
    if a.art == "rechnung":
        try:
            xml = erechnung.cii_xml(d, firma, nummer, meta["datum"], meta["faellig"], meta["zeilen"], meta["gesamt"])
        except ValueError as exc:
            fehler(str(exc))
        pdf = erechnung.einbetten(pdf, xml, nummer, firma, d["kunde"]["name"])
        gueltig, bericht = erechnung.pruefen(pdf)
        if not gueltig:
            fehler(f"E-Rechnung nicht gültig – nichts gespeichert, keine Nummer verbraucht. Mustang: {bericht}")
        print("E-Rechnung (ZUGFeRD EN 16931) mit Mustang geprüft: gültig")

    # --- Speichern: PDF, Eingabedaten (mit Werkzeugstand), Buchzeile mit Historie ---
    ordner = f"02_Rechnungen/{datum.year}" if a.art == "rechnung" else f"07_Kunden/{kurz}"
    pdf_rel = f"{ordner}/{nummer}_{kurz}.pdf"
    ablage.schreiben(pdf_rel, pdf)
    kopf = f"# {k['titel']} {nummer} | erzeugt {jetzt():%Y-%m-%d %H:%M} | Werkzeug {version}\n"
    ablage.schreiben(f"{ordner}/_daten/{nummer}_{kurz}.toml", kopf.encode() + roh)

    zeile = {"Nummer": nummer, "Datum": datum.isoformat(), "Kunde": d["kunde"]["name"],
             "Betreff": d.get("dokument", {}).get("betreff", ""), "Betrag": betrag_text(meta["gesamt"]),
             "Datei": pdf_rel, "Quelle_SHA256": sha, "Werkzeug": version}
    if a.art == "rechnung":
        zeile.update({"davon_35a": betrag_text(meta["anteil_35a"]), "Faellig": meta["faellig"].isoformat(),
                      "Bezahlt_am": "", "Journal": ""})
    else:
        zeile.update({"gueltig_bis": meta["gueltig"].isoformat(), "Status": "offen"})
    buch.zeilen.append(zeile)
    buch.speichern(f"{k['titel']} {nummer} angelegt ({eur(meta['gesamt'])})")
    print(f"{k['titel']} {nummer}: {ablage.pfad(pdf_rel)}  ({eur(meta['gesamt'])})")


if __name__ == "__main__":
    main()
