# PGH-Brandschutz – Büro-Repo

Arbeitsanleitung für Claude-Code-Sitzungen. Wenn eine Sitzung abbricht: **zuerst diese Datei
und `STATUS.md` lesen**, dann weiterarbeiten. Antworten immer auf Deutsch.

## Unternehmen (Stammdaten)

| | |
|---|---|
| Inhaber | Patrick Gerhäuser (Einzelunternehmen, nicht im Handelsregister) |
| Geschäftsbezeichnung | PGH-Brandschutz |
| Art | Nebenerwerb, 0 Beschäftigte, Gewerbe angemeldet (GEWAN Bayern, 06.10.2026) |
| Beginn | 11.10.2026 |
| Umsatzsteuer | Kleinunternehmer nach § 19 UStG (geplant, im Fragebogen zur steuerlichen Erfassung ankreuzen) |
| Gewinnermittlung | Einnahmen-Überschuss-Rechnung (EÜR) |
| Bank | ING Geschäftskonto (Eröffnung läuft) |
| Zielgruppe | vor allem Hausverwaltungen |

Angemeldete Tätigkeiten: Beratung, Montage und Wartung von batteriebetriebenen Rauchwarnmeldern
(Schwerpunkt) · Groß- und Einzelhandel mit Rauchwarnmeldern und Brandschutzzubehör · Prüfung und
Wartung von Brandschutztüren und Feststellanlagen (ohne Einbau und Instandsetzung) ·
Hausmeisterdienste (nicht handwerklich) · Gartenpflege.

Keine 230-V-Melder. Türen-/Feststellanlagen-Wartung erst nach Sachkunde/DIN-14677-Lehrgang.
Rauchmelder-Wartung nach DIN 14676 erst nach Fachkraft-Lehrgang.

## Grundsätze

1. **Claude bereitet vor, Patrick gibt frei.** Rechnungen, Mails an Kunden, ELSTER-Werte: nie
   ohne Freigabe verschicken/übermitteln. ELSTER übermittelt Patrick selbst.
2. **Regeln/Vorlagen/Code ins Repo – Daten aufs NAS.** Keine Belege, Kundenadressen,
   Kontoauszüge oder Zugangsdaten in dieses Repo (privat, liegt aber bei GitHub/USA).
3. **Zugangsdaten** nur in `~/.config/pgh-brandschutz/` auf LXC 191 (`chmod 600`), nie im Chat.
4. **Feuerwehr und Unternehmen strikt trennen** (keine Feuerwehrbilder/-bezüge auf Website o.ä.).
5. Steuer-/Rechtsfragen: recherchieren, Quellen nennen, als "keine Steuerberatung" kennzeichnen.

## Architektur (Zielbild)

| Baustein | Ort | Stand |
|---|---|---|
| Dieses Repo (Anleitung, Website-Quelltext, Vorlagen, Skripte) | GitHub `staubi0815/pgh-brandschutz-buero`, Klon `/home/claude/repos/pgh-brandschutz-buero` | angelegt 2026-10-06 |
| Domain + Webhosting + Mail | Hetzner Webhosting S, `pgh-brandschutz.de` | aktiv (2026-10-06) |
| Website | statisch, `website/` (siehe unten) | Entwurf fertig, **nicht online** |
| Mail | `info@` (Kunden), `belege@` (Belegeingang: `tools/belege_abholen.py` per Cron alle 15 min auf LXC 191 → NAS `00_Eingang`, Mail danach in IMAP-Ordner `Abgeholt`; Log `~/.local/state/pgh-brandschutz/belege.log`) | aktiv 2026-10-06 |
| Datenablage | NAS QNAP, Freigabe `PGH-Brandschutz` (`\\192.168.178.40\PGH-Brandschutz`, per SSH `/share/CACHEDEV1_DATA/PGH-Brandschutz`), nur Administratoren. Struktur + Benennung siehe `LIESMICH.txt` dort | angelegt 2026-10-06 |
| Außer-Haus-Sicherung | Container `rclone-hetzner` auf dem NAS: täglich 02:30 verschlüsselt nach `hetzner-crypt-pgh:aktuell`, Gelöschtes/Geändertes nach `archiv/<Zeitstempel>` – **Archiv nie löschen**. Details: homelab-infra `infra/nas-qnap.md` | aktiv 2026-10-06 |
| Rechnungen, Angebote, Fahrtenliste | `tools/dokument.py`, `tools/fahrten.py`, Vorlagen in `vorlagen/`; Ergebnisse + Bücher auf dem NAS | Werkzeuge fertig 2026-10-06; endgültige Rechnungen erst mit Steuernummer + IBAN |
| EÜR / Einnahmen-Ausgaben-Auswertung | auf NAS | offen |
| Paperless-ngx / Telegram-Bot | bewusst zurückgestellt | später |

## Arbeitsabläufe

Alle Werkzeuge laufen hier auf LXC 191 und schreiben per `ssh nas` in die Freigabe
`/share/CACHEDEV1_DATA/PGH-Brandschutz`. Kundendaten nie ins Repo – Eingabedateien nur in `/tmp` und auf dem NAS.

### Rechnung / Angebot schreiben
1. Angaben von Patrick sammeln: Kunde (Name, Anschrift, Kurzname), Objekt, Leistungsdatum, Positionen mit Menge/Preis/Art
   (`material`, `arbeit`, `fahrt` – Arbeit+Fahrt ergeben den § 35a-Anteil). Format: `vorlagen/beispiel_rechnung.toml`.
2. Eingabe als `/tmp/<kurz>.toml` schreiben, **Entwurf** erzeugen: `tools/dokument.py rechnung /tmp/<kurz>.toml`
   → `02_Rechnungen/Entwuerfe/` (Angebot: `07_Kunden/Entwuerfe/`). Kontrollbild: `pdftoppm -png -r 80 <pdf> /tmp/x`.
3. Patrick prüft den Entwurf (NAS). **Erst nach seiner Freigabe**: `… --final` → fortlaufende Nummer
   (`2026-001` bzw. `A-2026-001`), PDF nach `02_Rechnungen/<Jahr>/` bzw. `07_Kunden/<kurz>/`, Eingabe unter `_daten/`,
   Zeile in `02_Rechnungen/rechnungsausgangsbuch.csv` bzw. `07_Kunden/angebotsbuch.csv`. Entwurf danach löschen.
   Endgültige Rechnungen sind automatisch **E-Rechnungen** (ZUGFeRD/Factur-X, Profil EN 16931, `tools/erechnung.py`):
   XML im PDF, vor dem Speichern mit Mustang geprüft – ungültig ⇒ nichts gespeichert, keine Nummer verbraucht.
   Leistungsdatum dafür strikt `TT.MM.JJJJ` oder `TT.MM.JJJJ - TT.MM.JJJJ`. Optional im `[kunde]`-Block:
   `lieferantennummer` (meine Nummer beim Kunden, BT-29; sonst Steuernummer) und `email` (Rechnungsadresse).
   Voraussetzungen auf LXC 191: venv `~/.venvs/pgh` (factur-x, pikepdf – `dokument.py` wechselt selbst hinein),
   Java 17 + `~/tools/mustang/Mustang-CLI-2.26.0.jar`.
4. Rechnungen werden nie geändert oder gelöscht. Fehler → Stornorechnung (negative Beträge, Bezug auf Original-Nr.) + neue Rechnung.
5. Zahlungseingang: im Ausgangsbuch Spalte `Bezahlt_am` eintragen (Kontoauszug in `03_Bank/<Jahr>/`).

Rechtsgrundlage Pflichtangaben: § 34a UStDV (Kleinunternehmer, seit 2025) – Name/Anschrift beider Seiten, **Steuernummer**
(oder USt-IdNr/Kleinunternehmer-IdNr), Ausstellungsdatum, Menge/Art bzw. Umfang/Art, Entgelt + Hinweis auf § 19 UStG.
Kleinunternehmer dürfen immer als PDF („sonstige Rechnung“) schicken (§ 34a Satz 3 UStDV) – die E-Rechnung ist freiwillig
(Wunsch Patrick 07.10.2026), Pflicht erst bei Wegfall der Kleinunternehmerregelung (B2B ab 2028). `dokument.py --final`
bricht ab, solange `steuernummer`/`iban` in `vorlagen/firma.toml` leer sind.

### Fahrt eintragen
`tools/fahrten.py eintragen --datum JJJJ-MM-TT --ziel "…" --zweck "…" --einfach <km>` (Hin+Rück) oder `--km <gesamt>`.
Liste: `04_Fahrten/<Jahr>/fahrten_<Jahr>.csv` (0,30 €/km aus `firma.toml`). Summe: `tools/fahrten.py summe --jahr <J>`.

### Belege einsortieren
Neue Dateien in `00_Eingang` (von `belege@` oder Patrick) ansehen, umbenennen nach
`JJJJ-MM-TT_Firma_Betrag_Beschreibung.<ext>` und verschieben: Ausgaben → `01_Ausgaben/<Jahr>/`, Kontoauszüge →
`03_Bank/<Jahr>/`, Verträge/Versicherung → `05_Vertraege/`, Steuer → `06_Steuer/<Jahr>/`, Zertifikate → `08_Nachweise/`.
Unklare Belege in `00_Eingang` lassen und Patrick fragen. Nichts löschen.

## Website (`website/`)

- Statisches HTML, **kein JavaScript, keine Cookies, keine externen Schriften/Inhalte** → kein Cookie-Banner nötig.
- Inhalte: `website/src/pages/*.html` (Metadaten im Kopfkommentar), Rahmen `src/layout.html`,
  CSS/Logo/robots.txt in `static/`, strukturierte Daten `src/index.jsonld`.
- Bauen: `python3 website/build.py --check` → `website/dist/` (nicht im Git) + Liste offener `[OFFEN: …]`-Stellen.
- Vorschau für Patrick: `website/vorschau.sh` → http://192.168.178.40:8092/ (NAS-Container `pgh-vorschau`, nur Heimnetz).
  Screenshots per Playwright (`~/tools/screenshot-tool/node_modules/playwright`). Vor jeder Fertigmeldung Screenshot prüfen.
- Hetzner: FTP-Hauptbenutzer `ebgkry` auf `www793.your-server.de`, Webroot `public_html/` (enthält bis zum ersten
  Upload Hetzners Platzhalter `index.htm`, wird von `deploy.sh` entfernt). Logs: IPs gekürzt, 7 Tage (Standard) –
  Datenschutzerklärung beruht darauf, Einstellung nicht ändern ohne Text anzupassen.
- Hochladen: `website/deploy.sh` (SFTP mit Schlüssel `~/.ssh/id_hetzner_webhosting_pgh`, Server/User in
  `~/.config/pgh-brandschutz/hetzner.env`). Bricht ab, solange `[OFFEN: …]`-Stellen existieren.
  **Nur nach ausdrücklicher Freigabe durch Patrick.**
- Inhaltliche Regeln: keine Feuerwehr-Bezüge; „Fachkraft für Rauchwarnmelder“/„nach DIN 14676“ erst nach
  bestandenem Lehrgang; Brandschutztüren/Feststellanlagen erst nach Sachkunde (DIN 14677); keine
  erfundenen Referenzen/Bewertungen/Erfahrungsjahre; Rechtsaussagen mit „keine Rechtsberatung“.
- NAP überall identisch: „PGH-Brandschutz · Am Pfannenstiel 8 · 85406 Zolling (OT Oberappersdorf) · 08168 9998332“.

Details/Entscheidungen: `STATUS.md`.
