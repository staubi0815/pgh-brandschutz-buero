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
import csv
import hashlib
import io
import os
import re
import subprocess
import sys
import tempfile
import tomllib
from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from html import escape
from string import Template
from zoneinfo import ZoneInfo

# E-Rechnung braucht factur-x/pikepdf aus der venv ~/.venvs/pgh – bei Aufruf mit System-Python dorthin wechseln
VENV = os.path.expanduser("~/.venvs/pgh")
try:
    import facturx  # noqa: F401
except ImportError:
    if os.path.exists(os.path.join(VENV, "bin", "python")) and sys.prefix != VENV:
        os.execv(os.path.join(VENV, "bin", "python"), [os.path.join(VENV, "bin", "python")] + sys.argv)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VORLAGEN = os.path.join(REPO, "vorlagen")
LOGO = os.path.join(REPO, "website", "static", "img", "logo.svg")
CHROME = os.path.expanduser("~/.cache/ms-playwright/chromium-1243/chrome-linux64/chrome")
NAS_HOST = "nas"
NAS_BASIS = "/share/CACHEDEV1_DATA/PGH-Brandschutz"
TZ = ZoneInfo("Europe/Berlin")

ARTEN = {"material": "Material", "arbeit": "Arbeitsleistung", "fahrt": "Fahrtkosten"}
KLEINUNTERNEHMER = ("Steuerfreie Leistung als Kleinunternehmer nach § 19 UStG – "
                    "Umsatzsteuer wird daher nicht berechnet.")

KONFIG = {
    "rechnung": {
        "titel": "Rechnung", "praefix": "", "buch": "02_Rechnungen/rechnungsausgangsbuch.csv",
        "entwurf_dir": "02_Rechnungen/Entwuerfe",
        "kopf": ["Nummer", "Datum", "Kunde", "Betreff", "Betrag", "davon_35a", "Datei", "Quelle_SHA256", "Bezahlt_am"],
    },
    "angebot": {
        "titel": "Angebot", "praefix": "A-", "buch": "07_Kunden/angebotsbuch.csv",
        "entwurf_dir": "07_Kunden/Entwuerfe",
        "kopf": ["Nummer", "Datum", "Kunde", "Betreff", "Betrag", "gueltig_bis", "Datei", "Quelle_SHA256", "Status"],
    },
}


# ---------- Hilfsfunktionen ----------
def fehler(text):
    sys.exit(f"FEHLER: {text}")


def eur(betrag):
    s = f"{betrag:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{s} €"


def zahl(d):
    d = Decimal(d)
    if d == d.to_integral_value():
        return str(int(d))
    return f"{d.normalize()}".replace(".", ",")


def dmy(d):
    return d.strftime("%d.%m.%Y")


def sauber(text):
    text = text.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    text = text.replace("Ä", "Ae").replace("Ö", "Oe").replace("Ü", "Ue")
    return re.sub(r"[^A-Za-z0-9_-]+", "_", text).strip("_")[:40] or "Kunde"


def offen(text):
    return f'<span class="offen">[OFFEN: {escape(text)}]</span>'


# ---------- Ablage: NAS oder lokal ----------
class Ablage:
    def __init__(self, lokal=None):
        self.lokal = lokal

    def _ssh(self, skript, *args, eingabe=None):
        erg = subprocess.run(["ssh", NAS_HOST, "sh", "-c", f"'{skript}'", "_", *args],
                             input=eingabe, capture_output=True, timeout=120)
        if erg.returncode != 0:
            fehler(f"NAS: {erg.stderr.decode(errors='replace').strip()}")
        return erg.stdout

    def pfad(self, rel):
        return os.path.join(self.lokal, rel) if self.lokal else f"{NAS_BASIS}/{rel}"

    def lesen(self, rel):
        if self.lokal:
            p = self.pfad(rel)
            return open(p, "rb").read() if os.path.exists(p) else None
        out = self._ssh('[ -f "$1" ] && cat "$1" || echo __FEHLT__', self.pfad(rel))
        return None if out.strip() == b"__FEHLT__" else out

    def schreiben(self, rel, daten, ueberschreiben=False):
        if self.lokal:
            p = self.pfad(rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            if os.path.exists(p) and not ueberschreiben:
                fehler(f"Datei existiert bereits: {p}")
            open(p, "wb").write(daten)
            return p
        flag = "1" if ueberschreiben else "0"
        self._ssh('mkdir -p "$(dirname "$1")" && { [ "$2" = 1 ] || [ ! -e "$1" ] || { echo "existiert: $1" >&2; exit 3; }; } '
                  '&& cat > "$1" && chmod 660 "$1"', self.pfad(rel), flag, eingabe=daten)
        return self.pfad(rel)


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


def naechste_nummer(buch_csv, praefix, jahr):
    hoechste = 0
    if buch_csv:
        for zeile in csv.DictReader(io.StringIO(buch_csv.decode("utf-8-sig")), delimiter=";"):
            m = re.fullmatch(rf"{re.escape(praefix)}{jahr}-(\d+)", zeile.get("Nummer", ""))
            if m:
                hoechste = max(hoechste, int(m.group(1)))
    return f"{praefix}{jahr}-{hoechste + 1:03d}"


def schon_erzeugt(buch_csv, sha):
    if not buch_csv:
        return None
    for zeile in csv.DictReader(io.StringIO(buch_csv.decode("utf-8-sig")), delimiter=";"):
        if zeile.get("Quelle_SHA256") == sha:
            return zeile.get("Nummer")
    return None


# ---------- HTML/PDF ----------
def baue_html(art, d, firma, nummer, entwurf):
    k = KONFIG[art]
    doc = d.get("dokument", {})
    kunde = d["kunde"]
    datum = date.fromisoformat(doc["datum"]) if doc.get("datum") else datetime.now(TZ).date()
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
    ap.add_argument("--lokal")
    a = ap.parse_args()

    firma = tomllib.load(open(os.path.join(VORLAGEN, "firma.toml"), "rb"))
    d, roh = lade(a.daten)
    pruefe_eingabe(d)
    k = KONFIG[a.art]
    ablage = Ablage(a.lokal)
    kurz = sauber(d["kunde"]["kurz"])
    sha = hashlib.sha256(roh).hexdigest()

    if not a.final:
        html, meta = baue_html(a.art, d, firma, "ENTWURF", entwurf=True)
        stempel = datetime.now(TZ).strftime("%Y-%m-%d_%H%M")
        ziel = ablage.schreiben(f"{k['entwurf_dir']}/ENTWURF_{k['titel']}_{kurz}_{stempel}.pdf", pdf_aus_html(html))
        print(f"Entwurf: {ziel}  ({eur(meta['gesamt'])})")
        if a.art == "rechnung":
            import erechnung
            try:
                erechnung.leistungszeit(d.get("dokument", {}).get("leistungsdatum", ""))
            except ValueError as exc:
                print(f"HINWEIS für die endgültige Rechnung: {exc}")
        return

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

    buch = ablage.lesen(k["buch"])
    vorher = schon_erzeugt(buch, sha)
    if vorher:
        fehler(f"Diese Eingabedaten wurden bereits als {vorher} erzeugt.")
    datum = date.fromisoformat(d["dokument"]["datum"]) if d.get("dokument", {}).get("datum") else datetime.now(TZ).date()
    nummer = naechste_nummer(buch, k["praefix"], datum.year)
    html, meta = baue_html(a.art, d, firma, nummer, entwurf=False)
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

    if a.art == "rechnung":
        ordner = f"02_Rechnungen/{datum.year}"
    else:
        ordner = f"07_Kunden/{kurz}"
    pdf_rel = f"{ordner}/{nummer}_{kurz}.pdf"
    ablage.schreiben(pdf_rel, pdf)
    ablage.schreiben(f"{ordner}/_daten/{nummer}_{kurz}.toml", f"# {k['titel']} {nummer}\n".encode() + roh)

    zeile = {"Nummer": nummer, "Datum": datum.isoformat(), "Kunde": d["kunde"]["name"],
             "Betreff": d.get("dokument", {}).get("betreff", ""), "Betrag": f"{meta['gesamt']:.2f}".replace(".", ","),
             "Datei": pdf_rel, "Quelle_SHA256": sha}
    if a.art == "rechnung":
        zeile.update({"davon_35a": f"{meta['anteil_35a']:.2f}".replace(".", ","), "Bezahlt_am": ""})
    else:
        zeile.update({"gueltig_bis": meta["gueltig"].isoformat(), "Status": "offen"})
    puffer = io.StringIO()
    w = csv.DictWriter(puffer, fieldnames=k["kopf"], delimiter=";")
    if not buch:
        w.writeheader()
    w.writerow(zeile)
    neu = (buch.decode("utf-8-sig") if buch else "") + puffer.getvalue()
    ablage.schreiben(k["buch"], ("﻿" + neu).encode("utf-8"), ueberschreiben=True)
    print(f"{k['titel']} {nummer}: {ablage.pfad(pdf_rel)}  ({eur(meta['gesamt'])})")


if __name__ == "__main__":
    main()
