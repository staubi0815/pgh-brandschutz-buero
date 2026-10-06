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
| Domain + Webhosting + Mail | Hetzner Webhosting S, `pgh-brandschutz.de` | Bestellung offen |
| Website | statisch, `website/` (siehe unten) | Entwurf fertig, **nicht online** |
| Mail | `info@` (Kunden), `belege@` (Belegeingang, Claude holt per IMAP ab) | offen |
| Datenablage | NAS QNAP, eigene Freigabe `PGH-Brandschutz` | offen |
| Außer-Haus-Sicherung | Hetzner (aktuell nur `Multimedia/Bilder`) – Büro-Freigabe ergänzen | offen |
| Fahrtenliste, Einnahmen/Ausgaben | auf NAS | offen |
| Paperless-ngx / Telegram-Bot | bewusst zurückgestellt | später |

## Website (`website/`)

- Statisches HTML, **kein JavaScript, keine Cookies, keine externen Schriften/Inhalte** → kein Cookie-Banner nötig.
- Inhalte: `website/src/pages/*.html` (Metadaten im Kopfkommentar), Rahmen `src/layout.html`,
  CSS/Logo/robots.txt in `static/`, strukturierte Daten `src/index.jsonld`.
- Bauen: `python3 website/build.py --check` → `website/dist/` (nicht im Git) + Liste offener `[OFFEN: …]`-Stellen.
- Vorschau: `python3 -m http.server 8765 --bind 127.0.0.1` in `dist/`, Screenshots per Playwright
  (`~/tools/screenshot-tool/node_modules/playwright`). Vor jeder Fertigmeldung Screenshot prüfen.
- Hochladen: `website/deploy.sh` (SFTP mit Schlüssel `~/.ssh/id_hetzner_webhosting_pgh`, Server/User in
  `~/.config/pgh-brandschutz/hetzner.env`). Bricht ab, solange `[OFFEN: …]`-Stellen existieren.
  **Nur nach ausdrücklicher Freigabe durch Patrick.**
- Inhaltliche Regeln: keine Feuerwehr-Bezüge; „Fachkraft für Rauchwarnmelder“/„nach DIN 14676“ erst nach
  bestandenem Lehrgang; Brandschutztüren/Feststellanlagen erst nach Sachkunde (DIN 14677); keine
  erfundenen Referenzen/Bewertungen/Erfahrungsjahre; Rechtsaussagen mit „keine Rechtsberatung“.
- NAP überall identisch: „PGH-Brandschutz · Am Pfannenstiel 8 · 85406 Zolling (OT Oberappersdorf) · 08168 9998332“.

Details/Entscheidungen: `STATUS.md`.
