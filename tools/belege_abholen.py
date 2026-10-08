#!/usr/bin/env python3
"""Holt Belege aus dem Postfach belege@pgh-brandschutz.de und legt sie auf dem NAS ab.

Ablauf je Mail im Posteingang:
  - Anhänge mit erlaubter Endung (PDF, Bilder, XML für E-Rechnungen) werden nach
    PGH-Brandschutz/00_Eingang kopiert.
  - Hat eine Mail keinen solchen Anhang (z. B. Online-Quittung als HTML-Mail), wird die
    komplette Mail als .eml abgelegt, damit nichts verloren geht.
  - Anschließend wird die Mail in den IMAP-Ordner "Abgeholt" verschoben (nicht gelöscht).
  - Jede Abholung steht im Eingangsprotokoll 06_Steuer/<Jahr>/protokolle/belegeingang_<Jahr>.log (GoBD Rz. 117).

Andere Dateitypen (exe, zip, Office mit Makros …) werden bewusst nicht übernommen, nur protokolliert.
Zugangsdaten: ~/.config/pgh-brandschutz/belege.env (IMAP_HOST, IMAP_USER, IMAP_PASS), nie im Repo.
Läuft per cron auf LXC 191 (siehe CLAUDE.md), kann auch von Hand gestartet werden.
Option --dry-run: nur anzeigen, nichts speichern oder verschieben.
"""
import email
import email.policy
import imaplib
import os
import re
import subprocess
import sys
from datetime import datetime
from email.utils import parseaddr, parsedate_to_datetime
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gemeinsam import Ablage, protokoll_pfad, werkzeug_version  # noqa: E402

ENV = os.path.expanduser("~/.config/pgh-brandschutz/belege.env")
NAS_HOST = "nas"  # SSH-Alias aus ~/.ssh/config
NAS_DIR = "/share/CACHEDEV1_DATA/PGH-Brandschutz/00_Eingang"
DONE_FOLDER = "INBOX.Abgeholt"
TZ = ZoneInfo("Europe/Berlin")
ERLAUBT = {".pdf", ".jpg", ".jpeg", ".png", ".heic", ".heif", ".tif", ".tiff", ".webp", ".xml"}


def log(msg):
    print(f"{datetime.now(TZ):%Y-%m-%d %H:%M:%S} {msg}", flush=True)


def lade_env():
    werte = {}
    with open(ENV) as f:
        for zeile in f:
            if "=" in zeile:
                k, _, v = zeile.strip().partition("=")
                werte[k] = v
    return werte


def sauber(text, maxlen=60):
    text = text.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    text = text.replace("Ä", "Ae").replace("Ö", "Oe").replace("Ü", "Ue")
    text = re.sub(r"[^A-Za-z0-9._,-]+", "_", text).strip("._")
    return text[:maxlen] or "ohne_name"


def nas_ablegen(name, daten, dry_run):
    """Speichert Bytes auf dem NAS, hängt bei Namensgleichheit _2, _3 … an. Gibt Zielnamen zurück."""
    stamm, endung = os.path.splitext(name)
    skript = (
        'cd "$1" || exit 2; n="$2"; e="$3"; z="$n$e"; i=2; '
        'while [ -e "$z" ]; do z="${n}_$i$e"; i=$((i+1)); done; '
        'cat > "$z" && chmod 660 "$z" && echo "$z"'
    )
    if dry_run:
        return name + " (dry-run)"
    erg = subprocess.run(
        ["ssh", NAS_HOST, "sh", "-c", f"'{skript}'", "_", NAS_DIR, stamm, endung],
        input=daten, capture_output=True, timeout=120,
    )
    if erg.returncode != 0:
        raise RuntimeError(f"NAS-Ablage fehlgeschlagen: {erg.stderr.decode(errors='replace').strip()}")
    return erg.stdout.decode().strip()


def protokollieren(absender, betreff, msg_id, abgelegt, uebersprungen):
    """Eingangsprotokoll je Jahr auf dem NAS (GoBD Rz. 117). Fehler hier stoppen die Abholung nicht."""
    zeile = (f"{datetime.now(TZ):%Y-%m-%d %H:%M:%S} | von {absender} | „{betreff}“ | {msg_id} | "
             f"abgelegt: {', '.join(abgelegt)}" + (f" | nicht übernommen: {', '.join(uebersprungen)}" if uebersprungen else "")
             + f" | Werkzeug {werkzeug_version()}\n")
    try:
        Ablage().anhaengen(protokoll_pfad(datetime.now(TZ).year, "belegeingang"), zeile)
    except SystemExit as exc:
        log(f"FEHLER Eingangsprotokoll: {exc}")


def verarbeite(msg_bytes, dry_run):
    msg = email.message_from_bytes(msg_bytes, policy=email.policy.default)
    absender = parseaddr(msg.get("From", ""))[1] or "unbekannt"
    try:
        zeit = parsedate_to_datetime(msg.get("Date")).astimezone(TZ)
    except Exception:
        zeit = datetime.now(TZ)
    praefix = f"{zeit:%Y-%m-%d_%H%M}_{sauber(absender.split('@')[0], 20)}"
    betreff = msg.get("Subject", "")
    abgelegt, uebersprungen = [], []
    for teil in msg.walk():
        if teil.is_multipart():
            continue
        dateiname = teil.get_filename()
        if not dateiname:
            continue
        endung = os.path.splitext(dateiname)[1].lower()
        if endung not in ERLAUBT:
            uebersprungen.append(dateiname)
            continue
        daten = teil.get_payload(decode=True) or b""
        if not daten:
            continue
        stamm = sauber(os.path.splitext(dateiname)[0])
        abgelegt.append(nas_ablegen(f"{praefix}_{stamm}{endung}", daten, dry_run))
    if not abgelegt and not uebersprungen:
        abgelegt.append(nas_ablegen(f"{praefix}_{sauber(betreff or 'Mail')}.eml", msg_bytes, dry_run))
    if not abgelegt:
        abgelegt.append("NICHTS abgelegt – nur nicht erlaubte Anhänge, Mail liegt in IMAP-Ordner Abgeholt")
    if not dry_run:
        protokollieren(absender, betreff, msg.get("Message-ID", "ohne Message-ID"), abgelegt, uebersprungen)
    return absender, betreff, abgelegt, uebersprungen


def main():
    dry_run = "--dry-run" in sys.argv
    env = lade_env()
    imap = imaplib.IMAP4_SSL(env["IMAP_HOST"], 993)
    imap.login(env["IMAP_USER"], env["IMAP_PASS"])
    if not dry_run:
        imap.create(DONE_FOLDER)  # Fehler, falls vorhanden – egal
        imap.subscribe(DONE_FOLDER)
    imap.select("INBOX", readonly=dry_run)
    _, daten = imap.uid("search", None, "ALL")
    uids = daten[0].split()
    if not uids:
        imap.logout()
        return 0
    fehler = 0
    for uid in uids:
        _, teile = imap.uid("fetch", uid, "(BODY.PEEK[])")
        msg_bytes = teile[0][1]
        try:
            absender, betreff, abgelegt, uebersprungen = verarbeite(msg_bytes, dry_run)
        except Exception as exc:  # Mail bleibt im Posteingang und wird beim nächsten Lauf erneut versucht
            fehler += 1
            log(f"FEHLER uid={uid.decode()}: {exc}")
            continue
        log(f"Mail von {absender} „{betreff}“ → {', '.join(abgelegt)}")
        if uebersprungen:
            log(f"  nicht übernommen (Dateityp): {', '.join(uebersprungen)}")
        if not dry_run:
            kopie, _ = imap.uid("copy", uid, DONE_FOLDER)
            if kopie == "OK":
                imap.uid("store", uid, "+FLAGS", r"(\Deleted)")
            else:
                log(f"  Hinweis: Verschieben nach {DONE_FOLDER} fehlgeschlagen, Mail bleibt im Posteingang")
    if not dry_run:
        imap.expunge()
    imap.logout()
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
