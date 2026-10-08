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
6. **Kunden- und Mieterdaten bleiben lokal** (Entscheidung Patrick 08.10.2026): NAS bzw. eigener Server.
   Claude holt sie nicht in den Chat – Werkzeuge verarbeiten sie direkt und geben nur Zählwerte/Nummern aus;
   Mailinhalte von info@ nur lesen, wenn Patrick darum bittet. Grund: Claude-Privatabo ohne AV-Vertrag
   (Prüfbericht B9).

## Architektur (Zielbild)

| Baustein | Ort | Stand |
|---|---|---|
| Dieses Repo (Anleitung, Website-Quelltext, Vorlagen, Skripte) | GitHub `staubi0815/pgh-brandschutz-buero`, Klon `/home/claude/repos/pgh-brandschutz-buero` | angelegt 2026-10-06 |
| Domain + Webhosting + Mail | Hetzner Webhosting S, `pgh-brandschutz.de` | aktiv (2026-10-06) |
| Website | statisch, `website/` (siehe unten) | Entwurf fertig, **nicht online** |
| Mail | `info@` (Kunden), `belege@` (Belegeingang: `tools/belege_abholen.py` per Cron alle 15 min auf LXC 191 → NAS `00_Eingang`, Mail danach in IMAP-Ordner `Abgeholt`; Log `~/.local/state/pgh-brandschutz/belege.log`) | aktiv 2026-10-06 |
| Datenablage | NAS QNAP, Freigabe `PGH-Brandschutz` (`\\192.168.178.40\PGH-Brandschutz`, per SSH `/share/CACHEDEV1_DATA/PGH-Brandschutz`), nur Administratoren. Struktur + Benennung siehe `LIESMICH.txt` dort | angelegt 2026-10-06 |
| Außer-Haus-Sicherung | Container `rclone-hetzner` auf dem NAS: täglich 02:30 verschlüsselt nach `hetzner-crypt-pgh:aktuell`, Gelöschtes/Geändertes nach `archiv/<Zeitstempel>` – **Archiv nie löschen**. Details: homelab-infra `infra/nas-qnap.md` | aktiv 2026-10-06 |
| Rechnungen, Angebote, Fahrtenliste | `tools/dokument.py`, `tools/fahrten.py`, Vorlagen in `vorlagen/`; Ergebnisse + Bücher je Jahr auf dem NAS | fertig; endgültige Rechnungen erst mit Steuernummer + IBAN |
| Journal (EÜR), GWG-Verzeichnis, Einsortieren | `tools/journal.py`, `tools/einsortieren.py` → `06_Steuer/<Jahr>/` | fertig 2026-10-08 |
| Kontrolle, Jahreswechsel, Verfahrensdoku | `tools/kontrolle.py` (Cron täglich), `tools/jahreswechsel.py`, `docs/verfahrensdokumentation.md` + `tools/vd_archiv.py` | fertig 2026-10-08 |
| Paperless-ngx / Telegram-Bot | bewusst zurückgestellt | später |

## Arbeitsabläufe

**Maßgeblich ist `docs/verfahrensdokumentation.md`** (GoBD) – Abläufe dort ändern, wenn sie sich ändern (wird
automatisch als PDF auf dem NAS archiviert). Alle Werkzeuge laufen auf LXC 191 und schreiben per `ssh nas` in
`/share/CACHEDEV1_DATA/PGH-Brandschutz`; Testmodus jeweils `--lokal <Verzeichnis>`. Kundendaten nie ins Repo.
**Bücher (CSV) nie von Hand ändern** – nur über die Werkzeuge (Vorversion + Protokoll in `_historie/`).
Endgültige Rechnungen nur aus eingechecktem Werkzeugstand → Änderungen an `tools/`/`vorlagen/` sofort testen + committen.

### Belege einsortieren und erfassen (zeitnah, spätestens 10 Tage)
1. `tools/einsortieren.py liste` – Dateien ansehen (Lesbarkeit/Vollständigkeit prüfen, sonst Patrick um neues Foto bitten).
2. `tools/einsortieren.py <Datei> 01_Ausgaben/<Jahr> --name JJJJ-MM-TT_Firma_Betrag_Text` (Kontoauszüge → `03_Bank/<Jahr>`,
   Verträge → `05_Vertraege`, Steuer → `06_Steuer/<Jahr>`, Nachweise → `08_Nachweise`). Inhalt/Endung bleiben unverändert.
3. `tools/journal.py ausgabe --datum <Zahlungsdatum> --betrag … --an … --text … --kategorie … --zahlweg bank|privat|bar
   --beleg <Pfad>` (Kategorien: `journal.py kategorien`; GWG 250–800 € netto → `gwg`, landet im GWG-Verzeichnis;
   ohne Fremdbeleg `--eigenbeleg "Grund"`). Unklares in `00_Eingang` lassen und Patrick fragen.

### Zahlungseingang
`tools/journal.py einnahme --datum <Zahlungsdatum> --betrag … --rechnung <Nr> [--teilzahlung]` → setzt „bezahlt am“.
Fehler korrigieren: `journal.py storno <Nr> --grund …` (+ neuer Eintrag). Monatlich: Kontoauszug ablegen, mit Journal
abgleichen, `journal.py pruefen`. Auswertung: `journal.py auswertung --jahr <J>`.

### Rechnung / Angebot schreiben
1. Angaben von Patrick: Kunde (Name, Anschrift, Kurzname), Objekt, Leistungsdatum, Positionen mit Menge/Preis/Art
   (`material`, `arbeit`, `fahrt` – Arbeit+Fahrt = § 35a-Anteil). Format: `vorlagen/beispiel_rechnung.toml`; Feld `datum` weglassen.
2. Eingabe als `/tmp/<kurz>.toml`, **Entwurf**: `tools/dokument.py rechnung /tmp/<kurz>.toml` → `02_Rechnungen/Entwuerfe/`
   (Angebot: `07_Kunden/Entwuerfe/`). Kontrollbild: `pdftoppm -png -r 80 <pdf> /tmp/x`.
3. **Erst nach Freigabe durch Patrick**: `… --final` → Ausstellungsdatum heute, nächste Nummer (`2026-001`/`A-2026-001`),
   E-Rechnung (ZUGFeRD EN 16931, Mustang-geprüft), Prüfung Kleinunternehmergrenze, PDF + `_daten/` (mit Werkzeugstand),
   Zeile in `02_Rechnungen/rechnungsausgangsbuch_<Jahr>.csv` bzw. `07_Kunden/angebotsbuch_<Jahr>.csv`. Entwurf danach löschen.
   Leistungsdatum strikt `TT.MM.JJJJ` oder `TT.MM.JJJJ - TT.MM.JJJJ`. Optional `[kunde]`: `lieferantennummer`, `email`.
4. Rechnungen nie ändern/löschen. Fehler → Stornorechnung (Werkzeug noch offen – bis dahin nicht ohne Rücksprache).

Rechtsgrundlage Pflichtangaben: § 34a UStDV (Kleinunternehmer, seit 2025) – u. a. **Steuernummer**, § 19-Hinweis;
PDF immer zulässig, E-Rechnung freiwillig (Wunsch Patrick). `--final` bricht ab, solange `steuernummer`/`iban` in
`vorlagen/firma.toml` leer sind. Voraussetzungen: venv `~/.venvs/pgh`, Java 17, `~/tools/mustang/Mustang-CLI-2.26.0.jar`.

### Fahrt eintragen
`tools/fahrten.py eintragen --datum JJJJ-MM-TT --ziel "…" --zweck "…" --einfach <km>` (Hin+Rück) oder `--km <gesamt>`.

### Kontrolle und Jahreswechsel
- `tools/kontrolle.py` läuft täglich 05:15 UTC per Cron (Mail an info@ bei Problemen, montags Wochenbericht).
  Von Hand: `tools/kontrolle.py --keine-mail`.
- Ende Dezember `tools/jahreswechsel.py vorbereiten --jahr <neu>`, zweite Januarhälfte
  `tools/jahreswechsel.py abschluss --jahr <alt>` (Bericht in `06_Steuer/<alt>/`). Die Kontrolle erinnert daran.

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
