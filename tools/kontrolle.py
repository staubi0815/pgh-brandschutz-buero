#!/usr/bin/env python3
"""Tägliche Kontrolle von Sicherung, Ablage und Werkzeugen – mit Mail an info@ bei Problemen.

  kontrolle.py               prüfen; Mail bei FEHLER/WARNUNG, montags immer (Wochenbericht)
  kontrolle.py --keine-mail  nur anzeigen
  kontrolle.py --immer-mail  Mail auch ohne Befund (Test)

Läuft per Cron auf LXC 191. Hintergrund: Die Fotosicherung ist 2026 wochenlang unbemerkt ausgefallen –
Ausfälle sollen künftig spätestens am nächsten Morgen auffallen. Log: ~/.local/state/pgh-brandschutz/kontrolle.log
"""
import argparse
import imaplib
import json
import os
import re
import shutil
import smtplib
import ssl
import subprocess
import sys
from datetime import datetime, timedelta
from email.message import EmailMessage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gemeinsam import (RECHNUNG_KOPF, TZ, Ablage, Buch, eur, firma, heute, jetzt, ku_status,  # noqa: E402
                       rechnungsbuch_pfad, werkzeug_version)

ENV = os.path.expanduser("~/.config/pgh-brandschutz/belege.env")
BELEGE_LOG = os.path.expanduser("~/.local/state/pgh-brandschutz/belege.log")
VENV_PY = os.path.expanduser("~/.venvs/pgh/bin/python")
CHROME = os.path.expanduser("~/.cache/ms-playwright/chromium-1243/chrome-linux64/chrome")
MUSTANG = os.path.expanduser("~/tools/mustang/Mustang-CLI-2.26.0.jar")
EMPFAENGER = "info@pgh-brandschutz.de"

NAS_SKRIPT = r"""
C=/share/CACHEDEV1_DATA/Container/rclone-config
export PATH=$PATH:/share/CACHEDEV1_DATA/.qpkg/container-station/bin
echo "pgh_ende=$(grep 'Ende Sync PGH' $C/sync-pgh.log | tail -1)"
echo "bilder_ende=$(grep 'Ende Sync Bilder' $C/sync.log | tail -1)"
echo "container=$(docker inspect -f '{{.State.Status}}' rclone-hetzner 2>&1)"
echo "raid=$(grep -A1 '^md1 ' /proc/mdstat | grep -o '\[[U_]*\]' | tail -1)"
echo "volume=$(df -P /share/CACHEDEV1_DATA | awk 'NR==2{print $5}')"
echo "eingang_alt=$(find /share/CACHEDEV1_DATA/PGH-Brandschutz/00_Eingang -type f -mtime +7 ! -path '*/@Recycle/*' ! -path '*/_*' | wc -l)"
echo "about=$(docker exec rclone-hetzner rclone about hetzner: --json 2>&1 | tr -d '\n')"
"""


class Befund:
    def __init__(self):
        self.punkte = []

    def add(self, stufe, text):
        self.punkte.append((stufe, text))

    def anzahl(self, stufe):
        return sum(1 for s, _ in self.punkte if s == stufe)


def sync_alter(zeile):
    """'=== 2026-10-08 02:30:03 Ende Sync …, Exit-Code 0' → (Alter in Stunden, Exit-Code)."""
    m = re.search(r"=== (\d{4}-\d\d-\d\d \d\d:\d\d:\d\d) .*Exit-Code (\d+)", zeile or "")
    if not m:
        return None, None
    t = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S").replace(tzinfo=TZ)
    return (jetzt() - t).total_seconds() / 3600, int(m.group(2))


def pruefe_nas(b):
    try:
        out = subprocess.run(["ssh", "nas", "sh", "-s"], input=NAS_SKRIPT, capture_output=True, text=True,
                             timeout=120).stdout
    except subprocess.TimeoutExpired:
        b.add("FEHLER", "NAS antwortet nicht (SSH-Zeitüberschreitung)")
        return
    w = dict(z.split("=", 1) for z in out.splitlines() if "=" in z)
    if not w:
        b.add("FEHLER", "NAS nicht erreichbar (keine Antwort per SSH)")
        return
    for name, schluessel, max_h in (("Belege-Sicherung (täglich)", "pgh_ende", 26),
                                    ("Fotosicherung (mittwochs)", "bilder_ende", 8 * 24 + 2)):
        alter, rc = sync_alter(w.get(schluessel))
        if alter is None:
            b.add("FEHLER", f"{name}: kein abgeschlossener Lauf im Log gefunden")
        elif rc != 0:
            b.add("FEHLER", f"{name}: letzter Lauf mit Exit-Code {rc} (vor {alter:.0f} h)")
        elif alter > max_h:
            b.add("FEHLER", f"{name}: letzter erfolgreicher Lauf vor {alter:.0f} h (erwartet < {max_h} h)")
        else:
            b.add("OK", f"{name}: zuletzt vor {alter:.0f} h, fehlerfrei")
    if w.get("container") != "running":
        b.add("FEHLER", f"Container rclone-hetzner: {w.get('container')}")
    raid = w.get("raid", "")
    b.add("OK" if raid == "[UU]" else "FEHLER", f"RAID NAS: {raid or 'unbekannt'}")
    vol = int(w.get("volume", "0%").rstrip("%") or 0)
    b.add("OK" if vol < 85 else "WARNUNG", f"NAS-Volume belegt: {vol} %")
    try:
        about = json.loads(w.get("about", "{}"))
        frei = about["free"] / about["total"]
        b.add("OK" if frei > 0.10 else "WARNUNG", f"Storage Box frei: {frei:.0%} von {about['total'] / 2**40:.1f} TiB")
    except (ValueError, KeyError, ZeroDivisionError):
        b.add("WARNUNG", f"Storage Box: Belegung nicht abfragbar ({w.get('about', '')[:80]})")
    alt = int(w.get("eingang_alt", "0") or 0)
    if alt:
        b.add("WARNUNG", f"{alt} Beleg(e) liegen länger als 7 Tage in 00_Eingang – einsortieren und erfassen (10-Tage-Regel)")


def pruefe_belege_abholung(b):
    gestern = (heute() - timedelta(days=1)).isoformat()
    fehlerzeilen = []
    if os.path.exists(BELEGE_LOG):
        for z in open(BELEGE_LOG, encoding="utf-8", errors="replace"):
            if ("FEHLER" in z or "Traceback" in z) and z[:10] >= gestern:
                fehlerzeilen.append(z.strip())
    if fehlerzeilen:
        b.add("FEHLER", f"Belege-Abholung: {len(fehlerzeilen)} Fehler seit gestern, z. B. {fehlerzeilen[-1][:120]}")
    try:
        e = dict(z.strip().split("=", 1) for z in open(ENV) if "=" in z)
        m = imaplib.IMAP4_SSL(e["IMAP_HOST"], 993, timeout=30)
        m.login(e["IMAP_USER"], e["IMAP_PASS"])
        m.select("INBOX", readonly=True)
        seit = (heute() - timedelta(days=1)).strftime("%d-%b-%Y")
        _, d = m.search(None, "BEFORE", seit)
        haengen = len(d[0].split())
        m.logout()
        b.add("OK" if not haengen else "FEHLER",
              "Belege-Postfach: leer" if not haengen else f"Belege-Postfach: {haengen} Mail(s) älter als 1 Tag nicht abgeholt")
    except Exception as exc:  # noqa: BLE001
        b.add("FEHLER", f"Belege-Postfach nicht prüfbar: {exc}")


def pruefe_buchhaltung(b):
    ablage = Ablage()
    jahr = heute().year
    for j in (jahr - 1, jahr):
        for r in Buch(ablage, rechnungsbuch_pfad(j), RECHNUNG_KOPF).zeilen:
            if not r["Bezahlt_am"] and r["Faellig"] < heute().isoformat():
                b.add("WARNUNG", f"Rechnung {r['Nummer']} überfällig seit {r['Faellig']} ({r['Betrag']} €, {r['Kunde']})")
    ku = ku_status(ablage, jahr)
    if not ku["vorjahr_ok"]:
        b.add("WARNUNG", f"Vorjahresumsatz {eur(ku['vorjahr'])} > 25.000 € – Kleinunternehmerregelung {jahr} prüfen!")
    stufe = "WARNUNG" if ku["quote"] >= ku["warnung_ab"] else "OK"
    b.add(stufe, f"Kleinunternehmer {jahr}: {eur(ku['vereinnahmt'])} vereinnahmt + {eur(ku['offen'])} offen = "
                 f"{ku['quote']:.0%} von {eur(ku['grenze'])}")
    f = firma()
    fehlend = [n for n in ("steuernummer", "iban") if not f.get(n)]
    if fehlend:
        b.add("INFO", f"Endgültige Rechnungen noch gesperrt – fehlt in firma.toml: {', '.join(fehlend)}")


def pruefe_werkzeuge(b):
    probleme = []
    if not os.path.exists(CHROME):
        probleme.append("Chromium (PDF) fehlt")
    if not os.path.exists(MUSTANG):
        probleme.append("Mustang-Validator fehlt")
    if not shutil.which("java"):
        probleme.append("Java fehlt")
    r = subprocess.run([VENV_PY, "-c", "import facturx, pikepdf, piper, scipy, markdown"], capture_output=True)
    if r.returncode != 0:
        probleme.append("venv ~/.venvs/pgh unvollständig")
    v = werkzeug_version()
    if v.endswith("+geändert") or v == "unbekannt":
        probleme.append(f"Werkzeugstand nicht eingecheckt ({v}) – endgültige Rechnungen gesperrt")
    gesamt, _, frei = shutil.disk_usage(os.path.expanduser("~"))
    if frei / gesamt < 0.10:
        probleme.append(f"LXC 191 Platte fast voll ({frei / 2**30:.1f} GiB frei)")
    b.add("FEHLER" if probleme else "OK", "Werkzeuge: " + ("; ".join(probleme) if probleme else f"vollständig (Stand {v})"))


def pruefe_archiv_und_termine(b):
    """Neue Fassung der Verfahrensdokumentation archivieren; Erinnerungen an die Jahreswechsel-Routine."""
    r = subprocess.run([VENV_PY, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vd_archiv.py"), "vd"],
                       capture_output=True, text=True, timeout=300)
    text = (r.stdout + r.stderr).strip()
    if r.returncode != 0:
        b.add("WARNUNG", f"Archiv Verfahrensdokumentation fehlgeschlagen: {text[-150:]}")
    elif "archiviert:" in text:
        b.add("INFO", "Neue Fassung der Verfahrensdokumentation archiviert")
    else:
        b.add("OK", "Verfahrensdokumentation: aktuelle Fassung archiviert")
    ablage, t = Ablage(), heute()
    if t.month == 12 and t.day >= 20 and not ablage.existiert(f"01_Ausgaben/{t.year + 1}"):
        b.add("WARNUNG", f"Jahreswechsel vorbereiten: tools/jahreswechsel.py vorbereiten --jahr {t.year + 1}")
    if t.month == 1 and t.day >= 20:
        berichte = [r for r, _ in ablage.dateien(f"06_Steuer/{t.year - 1}") if "jahreswechsel_pruefung" in r]
        if not berichte:
            b.add("WARNUNG", f"Jahresabschluss {t.year - 1} fehlt: tools/jahreswechsel.py abschluss --jahr {t.year - 1}")


def mail(b, betreff):
    e = dict(z.strip().split("=", 1) for z in open(ENV) if "=" in z)
    zeilen = [f"Kontrolle PGH-Brandschutz vom {jetzt():%d.%m.%Y %H:%M}", ""]
    for stufe in ("FEHLER", "WARNUNG", "INFO", "OK"):
        punkte = [t for s, t in b.punkte if s == stufe]
        if punkte:
            zeilen += [f"{stufe}:"] + [f"  - {t}" for t in punkte] + [""]
    zeilen += ["Diese Mail kommt automatisch (tools/kontrolle.py auf LXC 191): bei Fehlern/Warnungen sofort,",
               "sonst montags als Wochenbericht. Bleibt sie montags aus, läuft die Kontrolle selbst nicht."]
    m = EmailMessage()
    m["From"] = f"PGH-Brandschutz Kontrolle <{e['IMAP_USER']}>"
    m["To"] = EMPFAENGER
    m["Subject"] = betreff
    m.set_content("\n".join(zeilen))
    with smtplib.SMTP_SSL("mail.your-server.de", 465, context=ssl.create_default_context(), timeout=60) as s:
        s.login(e["IMAP_USER"], e["IMAP_PASS"])
        s.send_message(m)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--keine-mail", action="store_true")
    ap.add_argument("--immer-mail", action="store_true")
    a = ap.parse_args()
    b = Befund()
    for pruefung in (pruefe_nas, pruefe_belege_abholung, pruefe_buchhaltung, pruefe_werkzeuge, pruefe_archiv_und_termine):
        try:
            pruefung(b)
        except SystemExit as exc:      # fehler() aus gemeinsam.py
            b.add("FEHLER", f"{pruefung.__name__}: {exc}")
        except Exception as exc:  # noqa: BLE001
            b.add("FEHLER", f"{pruefung.__name__}: {type(exc).__name__}: {exc}")
    f, w = b.anzahl("FEHLER"), b.anzahl("WARNUNG")
    status = "OK" if not (f or w) else ", ".join(x for x in (f"{f} Fehler" if f else "", f"{w} Warnung(en)" if w else "") if x)
    print(f"{jetzt():%Y-%m-%d %H:%M} Kontrolle: {status}")
    for s, t in b.punkte:
        print(f"  [{s}] {t}")
    montag = heute().weekday() == 0
    if not a.keine_mail and (f or w or montag or a.immer_mail):
        betreff = f"[PGH Kontrolle] {status}" if (f or w) else "[PGH Kontrolle] Wochenbericht – alles in Ordnung"
        mail(b, betreff)
        print(f"  Mail an {EMPFAENGER}: {betreff}")
    return 1 if f else 0


if __name__ == "__main__":
    sys.exit(main())
