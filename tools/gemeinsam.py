"""Gemeinsame Bausteine der PGH-Werkzeuge (nur Python-Standardbibliothek).

- Ablage:        Dateien auf dem NAS (per `ssh nas`) oder lokal (--lokal, für Tests)
- Buch:          CSV-Bücher (Semikolon, UTF-8 mit BOM). Jede Änderung legt die vorherige Fassung unter
                 `_historie/` ab und protokolliert sie in `_historie/aenderungen.log` (GoBD Rz. 59, 111)
- werkzeug_version(): Git-Kennung der Werkzeuge (Programmidentität, GoBD Rz. 154)
- ku_status():   Kleinunternehmer-Grenzen nach § 19 UStG / Abschn. 19.1 UStAE (vereinnahmte Entgelte)
"""
import csv
import io
import os
import re
import subprocess
import sys
import tomllib
from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VORLAGEN = os.path.join(REPO, "vorlagen")
NAS_HOST = "nas"
NAS_BASIS = "/share/CACHEDEV1_DATA/PGH-Brandschutz"
TZ = ZoneInfo("Europe/Berlin")


# ---------- Formatierung ----------
def fehler(text):
    sys.exit(f"FEHLER: {text}")


def jetzt():
    return datetime.now(TZ)


def heute():
    return jetzt().date()


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


def betrag_text(d):
    """Decimal → '427,80' (Format in den Büchern)."""
    return f"{Decimal(d):.2f}".replace(".", ",")


def dez(text):
    """'427,80' / '1.234,56' / '427.80' → Decimal."""
    s = str(text).strip().replace("€", "").replace(" ", "")
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    return Decimal(s or "0")


def sauber(text, maxlen=40):
    text = text.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    text = text.replace("Ä", "Ae").replace("Ö", "Oe").replace("Ü", "Ue")
    return re.sub(r"[^A-Za-z0-9_,.-]+", "_", text).strip("_.")[:maxlen] or "ohne_name"


def firma():
    with open(os.path.join(VORLAGEN, "firma.toml"), "rb") as f:
        return tomllib.load(f)


# ---------- Programmidentität ----------
def werkzeug_version(sauber_pflicht=False):
    """Kurz-Hash des Repos; „+geändert“, wenn tools/ oder vorlagen/ nicht eingecheckte Änderungen haben."""
    try:
        h = subprocess.run(["git", "-C", REPO, "rev-parse", "--short=10", "HEAD"],
                           capture_output=True, text=True, check=True).stdout.strip()
        dirty = subprocess.run(["git", "-C", REPO, "status", "--porcelain", "--", "tools", "vorlagen"],
                               capture_output=True, text=True).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        h, dirty = "unbekannt", ""
    if sauber_pflicht and (dirty or h == "unbekannt"):
        fehler("Werkzeugstand nicht eindeutig (nicht eingecheckte Änderungen in tools/ oder vorlagen/) – "
               "erst committen (Programmidentität, GoBD Rz. 154).")
    return h + ("+geändert" if dirty else "")


# ---------- Ablage: NAS oder lokal ----------
class Ablage:
    def __init__(self, lokal=None):
        self.lokal = lokal

    def _ssh(self, skript, *args, eingabe=None, pruefen=True):
        erg = subprocess.run(["ssh", NAS_HOST, "sh", "-c", f"'{skript}'", "_", *args],
                             input=eingabe, capture_output=True, timeout=180)
        if pruefen and erg.returncode != 0:
            fehler(f"NAS: {erg.stderr.decode(errors='replace').strip()}")
        return erg.stdout

    def pfad(self, rel):
        return os.path.join(self.lokal, rel) if self.lokal else f"{NAS_BASIS}/{rel}"

    def existiert(self, rel):
        if self.lokal:
            return os.path.exists(self.pfad(rel))
        return self._ssh('[ -e "$1" ] && echo ja || echo nein', self.pfad(rel)).strip() == b"ja"

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

    def anhaengen(self, rel, text):
        daten = text.encode("utf-8")
        if self.lokal:
            p = self.pfad(rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, "ab").write(daten)
            return
        self._ssh('mkdir -p "$(dirname "$1")" && cat >> "$1" && chmod 660 "$1"', self.pfad(rel), eingabe=daten)

    def verschieben(self, alt, neu):
        """Verschiebt ohne zu überschreiben (Ziel darf nicht existieren)."""
        if self.lokal:
            q, z = self.pfad(alt), self.pfad(neu)
            if os.path.exists(z):
                fehler(f"Ziel existiert bereits: {z}")
            os.makedirs(os.path.dirname(z), exist_ok=True)
            os.rename(q, z)
            return
        self._ssh('[ -f "$1" ] || { echo "Quelle fehlt: $1" >&2; exit 2; }; [ ! -e "$2" ] || { echo "Ziel existiert: $2" >&2; exit 3; }; '
                  'mkdir -p "$(dirname "$2")" && mv "$1" "$2"', self.pfad(alt), self.pfad(neu))

    def dateien(self, rel_dir, tiefe=None):
        """Liste relativer Dateipfade unterhalb rel_dir mit Änderungszeit (Unix-Sekunden)."""
        if self.lokal:
            basis = self.pfad(rel_dir)
            out = []
            for wurzel, dirs, files in os.walk(basis):
                dirs[:] = [x for x in dirs if not x.startswith(("@", ".", "_historie"))]
                for f in files:
                    p = os.path.join(wurzel, f)
                    out.append((os.path.relpath(p, self.pfad("")), int(os.path.getmtime(p))))
            return out
        t = f"-maxdepth {int(tiefe)}" if tiefe else ""
        roh = self._ssh(f'[ -d "$1" ] || exit 0; cd "$2" && find "$3" {t} -type f ! -path "*/@Recycle/*" ! -path "*/.@__*" '
                        '! -path "*/_historie/*" | while read f; do echo "$(date -r "$f" +%s) $f"; done',
                        self.pfad(rel_dir), NAS_BASIS, rel_dir)
        out = []
        for zeile in roh.decode(errors="replace").splitlines():
            ts, _, f = zeile.partition(" ")
            if f:
                out.append((f[2:] if f.startswith("./") else f, int(ts)))
        return out


# ---------- Bücher mit Änderungshistorie ----------
class Buch:
    def __init__(self, ablage, rel, kopf):
        self.ablage, self.rel, self.kopf = ablage, rel, kopf
        self._roh = ablage.lesen(rel)
        self.zeilen = []
        if self._roh:
            leser = csv.DictReader(io.StringIO(self._roh.decode("utf-8-sig")), delimiter=";")
            if leser.fieldnames != kopf:
                fehler(f"{rel}: Spalten passen nicht zum Werkzeug ({leser.fieldnames} ≠ {kopf}) – "
                       "wurde die Datei außerhalb der Werkzeuge (z. B. in Excel) gespeichert?")
            self.zeilen = list(leser)

    def finde(self, feld, wert):
        return next((z for z in self.zeilen if z.get(feld) == wert), None)

    def speichern(self, aktion):
        puffer = io.StringIO()
        w = csv.DictWriter(puffer, fieldnames=self.kopf, delimiter=";", extrasaction="raise")
        w.writeheader()
        w.writerows(self.zeilen)
        neu = ("﻿" + puffer.getvalue()).encode("utf-8")
        ordner, name = os.path.split(self.rel)
        stempel = jetzt()
        if self._roh:  # vorherige Fassung sichern, bevor sie überschrieben wird
            self.ablage.schreiben(f"{ordner}/_historie/{os.path.splitext(name)[0]}_{stempel:%Y%m%d-%H%M%S-%f}.csv", self._roh)
        self.ablage.schreiben(self.rel, neu, ueberschreiben=True)
        self.ablage.anhaengen(f"{ordner}/_historie/aenderungen.log",
                              f"{stempel:%Y-%m-%d %H:%M:%S} | {name} | {aktion} | Werkzeug {werkzeug_version()}\n")
        self._roh = neu


# ---------- Pfade der Bücher ----------
def rechnungsbuch_pfad(jahr):
    return f"02_Rechnungen/rechnungsausgangsbuch_{jahr}.csv"


def angebotsbuch_pfad(jahr):
    return f"07_Kunden/angebotsbuch_{jahr}.csv"


def journal_pfad(jahr):
    return f"06_Steuer/{jahr}/journal_{jahr}.csv"


def gwg_pfad(jahr):
    return f"06_Steuer/{jahr}/gwg_verzeichnis_{jahr}.csv"


def fahrten_pfad(jahr):
    return f"04_Fahrten/{jahr}/fahrten_{jahr}.csv"


def protokoll_pfad(jahr, art):
    return f"06_Steuer/{jahr}/protokolle/{art}_{jahr}.log"


RECHNUNG_KOPF = ["Nummer", "Datum", "Kunde", "Betreff", "Betrag", "davon_35a", "Faellig", "Datei",
                 "Quelle_SHA256", "Werkzeug", "Bezahlt_am", "Journal"]
ANGEBOT_KOPF = ["Nummer", "Datum", "Kunde", "Betreff", "Betrag", "gueltig_bis", "Datei", "Quelle_SHA256",
                "Werkzeug", "Status"]
JOURNAL_KOPF = ["Nr", "Zahlungsdatum", "Art", "Betrag", "Gegenpartei", "Beschreibung", "Kategorie", "Zahlweg",
                "Beleg", "Rechnung", "Storno_von", "Erfasst_am", "Werkzeug"]


# ---------- Kleinunternehmer (§ 19 UStG, Abschn. 19.1 UStAE i. d. F. BMF 18.03.2025) ----------
def vereinnahmt(ablage, jahr):
    """Summe der vereinnahmten Entgelte (Journal, Kategorie „umsatz“, inkl. Stornos)."""
    j = Buch(ablage, journal_pfad(jahr), JOURNAL_KOPF)
    return sum((dez(z["Betrag"]) for z in j.zeilen if z["Art"] == "Einnahme" and z["Kategorie"] == "umsatz"),
               Decimal("0"))


def offene_rechnungen(ablage, jahr):
    b = Buch(ablage, rechnungsbuch_pfad(jahr), RECHNUNG_KOPF)
    return [z for z in b.zeilen if not z["Bezahlt_am"]]


def ku_status(ablage, jahr, zusaetzlich=Decimal("0")):
    """Gründungsjahr: Grenze 25.000 € im laufenden Jahr; sonst Vorjahr ≤ 25.000 € und laufendes Jahr ≤ 100.000 €.
    Vorsichtig gerechnet: vereinnahmt + noch offene Rechnungen + zusaetzlich (z. B. neue Rechnung)."""
    f = firma()
    gruendung = date.fromisoformat(f["gruendung"]).year
    grenze = Decimal(str(f["ku_grenze_gruendungsjahr"] if jahr == gruendung else f["ku_grenze_laufend"]))
    ist = vereinnahmt(ablage, jahr)
    offen = sum((dez(z["Betrag"]) for z in offene_rechnungen(ablage, jahr)), Decimal("0"))
    vorjahr = None if jahr <= gruendung else vereinnahmt(ablage, jahr - 1)
    vorjahr_ok = vorjahr is None or vorjahr <= Decimal(str(f["ku_grenze_vorjahr"]))
    erwartet = ist + offen + zusaetzlich
    return {"jahr": jahr, "grenze": grenze, "vereinnahmt": ist, "offen": offen, "erwartet": erwartet,
            "quote": erwartet / grenze, "vorjahr": vorjahr, "vorjahr_ok": vorjahr_ok,
            "warnung_ab": Decimal(str(f["ku_warnung_ab"]))}
