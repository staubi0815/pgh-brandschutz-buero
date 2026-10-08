#!/usr/bin/env python3
"""Archiviert alle Mails von info@pgh-brandschutz.de (empfangen und gesendet) als .eml auf dem NAS.

Geschäftsbriefe (Angebote, Aufträge, Absprachen) sind 6 Jahre, Rechnungen per Mail 8 Jahre aufzubewahren.
Ablage: PGH-Brandschutz/09_Korrespondenz/<Jahr>/<eingang|ausgang>/JJJJ-MM-TT_HHMM_<Partner>_<Betreff>_<Prüfsumme>.eml

  - Das Postfach wird nur gelesen (BODY.PEEK, readonly) – nichts wird verschoben, markiert oder gelöscht.
  - Alle Ordner außer Spam und Entwürfen, auch der Papierkorb (falls eine Mail vor dem Lauf gelöscht wurde).
  - Jede Mail genau einmal: Die ersten 12 Zeichen der SHA-256-Prüfsumme stehen im Dateinamen; was auf dem NAS
    schon liegt, wird übersprungen (auch wenn dieselbe Mail in zwei Ordnern liegt). Auf dem NAS wird nichts
    überschrieben.
  - Protokoll je Jahr: 06_Steuer/<Jahr>/protokolle/mailarchiv_<Jahr>.log (nur Anzahl, Ordner, Prüfsummen).
  - Ausgabe/Log nur mit Zählwerten, ohne Absender oder Betreff (Kundendaten bleiben auf dem NAS).

Zugangsdaten: ~/.config/pgh-brandschutz/info.env (HOST, USER, PASS), nie im Repo.
Läuft per cron auf LXC 191 täglich vor der Nachtsicherung (siehe CLAUDE.md).
Option --dry-run: nur zählen, nichts speichern. Option --lokal <Ordner>: Test ohne NAS.
"""
import email
import email.policy
import hashlib
import imaplib
import os
import re
import sys
from datetime import datetime
from email.utils import getaddresses, parseaddr, parsedate_to_datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gemeinsam import TZ, Ablage, protokoll_pfad, werkzeug_version  # noqa: E402

ENV = os.path.expanduser("~/.config/pgh-brandschutz/info.env")
ZIEL = "09_Korrespondenz"
AUSLASSEN = re.compile(r"(spam|junk|draft|entw[uü]rf)", re.I)
PRUEFSUMME = re.compile(r"_([0-9a-f]{12})\.eml$")


def log(msg):
    print(f"{datetime.now(TZ):%Y-%m-%d %H:%M:%S} {msg}", flush=True)


def lade_env():
    with open(ENV, encoding="utf-8") as f:
        return dict(z.strip().split("=", 1) for z in f if "=" in z and not z.startswith("#"))


def sauber(text, maxlen):
    text = text.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    text = text.replace("Ä", "Ae").replace("Ö", "Oe").replace("Ü", "Ue")
    text = re.sub(r"[^A-Za-z0-9._,-]+", "_", text).strip("._")
    return text[:maxlen].rstrip("._") or "ohne"


def ordnerliste(imap):
    namen = []
    for zeile in imap.list()[1]:
        z = zeile.decode(errors="replace")
        if "\\Noselect" in z:
            continue
        m = re.search(r'"([^"]+)"$', z)
        name = m.group(1) if m else z.split()[-1]
        if not AUSLASSEN.search(name) and "\\Junk" not in z and "\\Drafts" not in z:
            namen.append(name)
    return namen


def dateiname(roh, eigene_adresse, imap_datum):
    msg = email.message_from_bytes(roh, policy=email.policy.default)
    try:
        zeit = parsedate_to_datetime(str(msg.get("Date"))).astimezone(TZ)
    except Exception:
        zeit = imap_datum
    absender = parseaddr(str(msg.get("From", "")))[1].lower()
    if absender == eigene_adresse:
        richtung = "ausgang"
        empf = getaddresses([str(msg.get(k, "")) for k in ("To", "Cc")])
        partner = empf[0][1] if empf else "unbekannt"
    else:
        richtung, partner = "eingang", absender or "unbekannt"
    try:
        betreff = str(msg.get("Subject", "")) or "ohne_Betreff"
    except Exception:
        betreff = "ohne_Betreff"
    summe = hashlib.sha256(roh).hexdigest()[:12]
    name = f"{zeit:%Y-%m-%d_%H%M}_{sauber(partner, 40)}_{sauber(betreff, 50)}_{summe}.eml"
    return zeit.year, f"{ZIEL}/{zeit.year}/{richtung}/{name}", summe, richtung


def imap_zeit(antwort_kopf):
    m = re.search(rb'INTERNALDATE "([^"]+)"', antwort_kopf)
    if m:
        try:
            return datetime.strptime(m.group(1).decode(), "%d-%b-%Y %H:%M:%S %z").astimezone(TZ)
        except ValueError:
            pass
    return datetime.now(TZ)


def main():
    dry_run = "--dry-run" in sys.argv
    env = lade_env()
    # --lokal <Ordner>: Test gegen ein lokales Verzeichnis statt des NAS
    ablage = Ablage(sys.argv[sys.argv.index("--lokal") + 1]) if "--lokal" in sys.argv else Ablage()
    vorhanden = {m.group(1) for f, _ in ablage.dateien(ZIEL) if (m := PRUEFSUMME.search(f))}
    imap = imaplib.IMAP4_SSL(env.get("HOST", "mail.your-server.de"), 993)
    imap.login(env["USER"], env["PASS"])
    zaehler = {"neu": 0, "schon_da": 0, "eingang": 0, "ausgang": 0, "fehler": 0}
    je_jahr = {}
    for ordner in ordnerliste(imap):
        typ, _ = imap.select(f'"{ordner}"', readonly=True)
        if typ != "OK":
            log(f"FEHLER Ordner nicht lesbar: {ordner}")
            zaehler["fehler"] += 1
            continue
        _, daten = imap.uid("search", None, "ALL")
        for uid in daten[0].split():
            try:
                _, teile = imap.uid("fetch", uid, "(INTERNALDATE BODY.PEEK[])")
                kopf, roh = teile[0][0], teile[0][1]
                jahr, rel, summe, richtung = dateiname(roh, env["USER"].lower(), imap_zeit(kopf))
                if summe in vorhanden:
                    zaehler["schon_da"] += 1
                    continue
                if not dry_run:
                    ablage.schreiben(rel, roh)
                vorhanden.add(summe)
                zaehler["neu"] += 1
                zaehler[richtung] += 1
                je_jahr.setdefault(jahr, []).append(f"{ordner}:{uid.decode()}:{summe}")
            except Exception as exc:  # beim nächsten Lauf erneut versucht
                zaehler["fehler"] += 1
                log(f"FEHLER {ordner} uid={uid.decode()}: {type(exc).__name__}")
    imap.logout()
    if not dry_run:
        for jahr, eintraege in je_jahr.items():
            ablage.anhaengen(protokoll_pfad(jahr, "mailarchiv"),
                             f"{datetime.now(TZ):%Y-%m-%d %H:%M:%S} | {len(eintraege)} Mail(s) archiviert | "
                             f"{' '.join(eintraege)} | Werkzeug {werkzeug_version()}\n")
    log(("DRY-RUN " if dry_run else "") + f"Ende Mailarchiv: {zaehler['neu']} neu ({zaehler['eingang']} Eingang, "
        f"{zaehler['ausgang']} Ausgang), {zaehler['schon_da']} schon archiviert, {zaehler['fehler']} Fehler, "
        f"Exit-Code {1 if zaehler['fehler'] else 0}")
    return 1 if zaehler["fehler"] else 0


if __name__ == "__main__":
    sys.exit(main())
