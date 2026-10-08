# Prüfbericht Büro-Struktur PGH-Brandschutz – 08.10.2026

Auftrag (Patrick, 08.10.2026): gesamte Struktur Schritt für Schritt prüfen – langfristige Tragfähigkeit,
Jahreswechsel, Dokumentation, Aufbewahrungsfristen, Nachvollziehbarkeit; selbstständig nach Problemen suchen.
Erstellt von Claude. **Keine Steuer- oder Rechtsberatung** – Einordnung nach Gesetzestext und BMF-Schreiben,
Quellen am Ende. Zweifelsfälle sind als solche markiert.

Vorgehen in 7 Teilen: (1) Rechtsrahmen, (2) Bestandsaufnahme, (3) Soll/Ist, (4) Technik-Prüfung,
(5) Jahreswechsel-Simulation, (6) Datenschutz, (7) Maßnahmenplan.

---

## 1. Rechtsrahmen (geprüft an Primärquellen)

| Thema | Regel | Quelle |
|---|---|---|
| Aufbewahrungsfristen | Bücher/Aufzeichnungen/**Organisationsunterlagen (inkl. Verfahrensdokumentation)** 10 Jahre, **Buchungsbelege 8 Jahre** (seit 2025), Geschäftsbriefe/sonstige Unterlagen 6 Jahre | § 147 Abs. 3 AO |
| Fristbeginn | Ende des Kalenderjahres der **letzten Eintragung** bzw. Entstehung | § 147 Abs. 4 AO |
| Ablaufhemmung | Frist läuft nicht ab, solange die Festsetzungsfrist der betroffenen Steuer läuft | § 147 Abs. 3 AO |
| GoBD gelten auch für EÜR | EÜR-Rechner müssen nach § 147 aufbewahren; bei Kleinstunternehmen wird die Unternehmensgröße berücksichtigt | GoBD Rz. 115, 15 |
| Zeitgerechte Erfassung | unbare Vorgänge **innerhalb 10 Tagen** in Grundaufzeichnungen; bare täglich | GoBD Rz. 47, 50 |
| Unveränderbarkeit | Änderungen müssen erkennbar bleiben/protokolliert sein; **reine Dateiablage genügt nicht ohne Zusatzmaßnahmen** (Versionierung, Sicherungen, Rechte …) | GoBD Rz. 58–59, 107–111 |
| Protokoll Belegeingang | Eingang, Archivierung, Konvertierung elektronischer Unterlagen protokollieren | GoBD Rz. 117 |
| Fotografieren von Belegen | mit Smartphone zulässig; **Organisationsanweisung** nötig (wer, wann, was, Qualitätskontrolle, Fehler); danach Papier vernichtbar | GoBD Rz. 130, 136–140 |
| Empfangsformat | eingehende elektronische Belege im **Empfangsformat** aufbewahren (XML, PDF) | GoBD Rz. 131 (Fassung 14.07.2025) |
| E-Rechnung | XML-Teil ist maßgeblich; PDF-Teil nur bei Zusatzinfos; **keine Umwandlung XML → Bild** | GoBD Rz. 119, 125, 131 (2025) |
| Eigene Rechnungen | Kopie nicht nötig, wenn jederzeit inhaltsgleich reproduzierbar – bei geänderten Stammdaten/Vorlagen gerade NICHT gegeben (Beispiel 4) → PDF fest ablegen | GoBD Rz. 59, 76 |
| Verfahrensdokumentation | Pflicht; allgemeine Beschreibung, Anwender-, System-, Betriebsdoku; **Programmidentität**; Änderungen versioniert; Aufbewahrung so lange wie die Unterlagen | GoBD Rz. 151–155 |
| Kleinunternehmer | Vorjahr ≤ 25.000 €, lfd. Jahr ≤ 100.000 €; **Gründungsjahr ≤ 25.000 €**; Berechnung nach **vereinnahmten** Entgelten; Umsatz, mit dem die Grenze überschritten wird, ist bereits steuerpflichtig; keine USt-Erklärungspflicht | § 19 UStG; Abschn. 19.1 UStAE (BMF 18.03.2025) |
| Rechnungspflichtangaben KU | u. a. **Steuernummer**, § 19-Hinweis; PDF immer zulässig | § 34a UStDV |
| GWG | ≤ 800 € netto sofort abziehbar; > 250 € netto: **Verzeichnis** (sofern nicht aus Aufzeichnungen ersichtlich) | § 6 Abs. 2 EStG |
| Jahreszuordnung EÜR | Zufluss/Abfluss; regelmäßig wiederkehrende Zahlungen ±10 Tage um den Jahreswechsel gehören ins wirtschaftliche Jahr | § 11 EStG |
| Haftung (außersteuerlich) | Ansprüche aus Verletzung von Leben/Körper/Gesundheit verjähren spätestens **30 Jahre** nach der Pflichtverletzung → Montage-/Wartungsprotokolle sehr lange aufbewahren | § 199 Abs. 2 BGB |

---

## 2. Bestandsaufnahme (Stand 08.10.2026, nur lesend geprüft)

| Baustein | Ist-Zustand | Prüfergebnis |
|---|---|---|
| NAS QNAP TS-262 | RAID 1 (2 Platten, `[UU]`), Volume 7,2 TB, 35 % belegt | ✅ gesund; SMART per SSH nicht auslesbar; keine NAS-Snapshots |
| Freigabe `PGH-Brandschutz` | 00–08 + LIESMICH; nur Administratoren | ✅; enthält noch 2 Beispiel-Entwürfe (Musterkunde) |
| Sicherung Belege | täglich 02:30, `aktuell` + `archiv/<Zeit>` (nichts gelöscht) | ✅ 3 Läufe ohne Fehler; **Wiederherstellung getestet: 3/3 bitgleich; cryptcheck 0 Abweichungen** |
| Sicherung Bilder | mittwochs 01:00, `rclone sync` | ✅ läuft; ⚠️ lokales Löschen wird mitgelöscht (keine Versionen) |
| Storage Box | BX11, 1 TiB, 524 GiB belegt, Host-Key geprüft | ✅; ⚠️ keine Snapshots aktiv |
| LXC 191 (Werkzeuge) | Cron Belege alle 15 min; venv, Mustang, Piper, Chromium; Zugangsdaten chmod 600 | ✅; nächtliches vzdump aufs NAS (keep-last 3) |
| Repo GitHub | Code, Vorlagen, Doku; keine Kundendaten | ✅ |
| Mail info@/belege@ | Hetzner; belege@ → NAS automatisiert | ⚠️ info@ ohne Archiv/Sicherung |
| Werkzeuge | Rechnung/Angebot (E-Rechnung, Mustang-geprüft), Fahrten, Belege, Ansage | ✅ getestet; Befunde s. unten |

**Stärken:** Trennung Code (Repo) / Daten (NAS); Belege verschlüsselt außer Haus mit Archiv; E-Rechnungen
werden vor dem Speichern validiert; fortlaufende Nummern mit Doppelschutz; PDFs + Eingabedaten fest abgelegt
(genau das, was GoBD Rz. 59/76 verlangt); Doku in Git versioniert.

---

## 3. Befunde (Soll/Ist) – nach Priorität

Priorität: **A** = vor dem ersten Geschäftsvorfall/zeitnah, **B** = in den nächsten Wochen, **C** = vor dem ersten Jahreswechsel / bei Gelegenheit.

### A – zeitnah

| Nr. | Befund | Warum wichtig | Maßnahme |
|---|---|---|---|
| A1 | **Es fehlt die Einnahmen-/Ausgaben-Aufzeichnung (Journal).** Wir haben Ablage + Rechnungsausgangsbuch, aber keine Grundaufzeichnung mit Zahlungsdatum, Betrag, Kategorie, Belegverweis | Kern der EÜR; GoBD Rz. 47/50 (10-Tage-Frist); ohne Zahlungsdatum keine korrekte Jahreszuordnung (§ 11) und keine Kleinunternehmer-Grenze (vereinnahmt) | `journal_<Jahr>.csv` auf dem NAS + `tools/journal.py` (Eintragen beim Einsortieren, Abgleich mit Kontoauszug, Auswertung nach EÜR-Zeilen) |
| A2 | **Ausgaben vor dem Start sind nicht erfasst** (Bohrhammer, Leiter, Domain/Hosting, Gewerbeanmeldung, Lehrgang DIN 14676, Fahrten) – `01_Ausgaben` ist leer | vorweggenommene Betriebsausgaben 2026; Belege gehen sonst verloren | Belege sammeln/fotografieren → belege@; als Einlage (privat bezahlt) im Journal |
| A3 | **GWG-Verzeichnis fehlt** (Bohrhammer > 250 € netto) | § 6 Abs. 2 EStG | `anlagen_gwg.csv` (Datum, Bezeichnung, Betrag, Beleg) |
| A4 | **Keine Alarmierung bei Fehlern** – Sicherungen und Belege-Abholung schreiben nur Logs. Genau so ist die Fotosicherung wochenlang unbemerkt ausgefallen | Ausfall wird sonst erst im Ernstfall bemerkt | täglicher Kontrolllauf (LXC 191): letzte Sicherung < 26 h, Exit-Code 0, Abholer ohne Fehler → sonst Mail an info@ |
| A5 | **Zurückdatieren von Rechnungen wird nicht verhindert** (Simulation: Rechnung vom 15.11. bekam Nr. nach einer vom 20.12.) | Nummern- und Datumsfolge widersprüchlich → Prüfungsrisiko | `dokument.py --final`: Datum muss ≥ letztem Datum der Jahresreihe und ≤ heute sein (Ausnahme nur mit Begründung, die protokolliert wird) |
| A6 | **Umsatzgrenzen werden nicht überwacht** (Gründungsjahr 25.000 €, danach 25.000/100.000 €, vereinnahmt) | überschreitender Umsatz wäre sofort steuerpflichtig → Rechnungen falsch | Auswertung aus Journal; Warnung in `dokument.py` ab 80 % |

### B – in den nächsten Wochen

| Nr. | Befund | Maßnahme |
|---|---|---|
| B1 | **Verfahrensdokumentation fehlt als zusammenhängendes Dokument** (Inhalte verteilt auf CLAUDE.md, LIESMICH, Infra-Doku) – inkl. Organisationsanweisung Fotografieren (Rz. 136) | `docs/verfahrensdokumentation.md` (versioniert in Git) + jährlich als PDF in `06_Steuer/<Jahr>` |
| B2 | **Programmidentität** (Rz. 154) nicht nachweisbar: welche Werkzeug-Version hat eine Rechnung erzeugt? | Git-Commit-Kennung in Ausgangsbuch und `_daten`; jährlich `git bundle` des Repos auf das NAS (10 Jahre) |
| B3 | **Ausgangsbuch wird bei jeder Änderung überschrieben**, Änderungen (z. B. „bezahlt am“) nicht protokolliert (Rz. 59/111) | Änderungen nur per Werkzeug; vorher Kopie in `_historie/` + Änderungsprotokoll |
| B4 | **Ein Ausgangsbuch für alle Jahre** → Frist beginnt erst mit der letzten Eintragung (§ 147 Abs. 4), Datei wird nie „fristfrei“ | `rechnungsausgangsbuch_<Jahr>.csv`, `angebotsbuch_<Jahr>.csv` |
| B5 | **info@ wird nicht archiviert** (Angebote, Aufträge, Absprachen = Geschäftsbriefe, 6 Jahre; Rechnungen per Mail 8 Jahre); auch „Gesendet“ | IMAP-Archivierung info@ (empfangen + gesendet) nach `09_Korrespondenz/<Jahr>` als .eml, täglich |
| B6 | **Storage-Box-Snapshots nicht aktiv** – heute könnte jemand mit Zugriff aufs NAS (z. B. Schadsoftware) mit den dort gespeicherten Zugangsdaten auch die Hetzner-Daten löschen | automatische Snapshots in der Hetzner Console (BX11: 10 Plätze, z. B. wöchentlich) – nur dort löschbar |
| B7 | **Protokoll des Belegeingangs** liegt nur auf LXC 191 (Rz. 117) | Protokoll zusätzlich je Jahr auf das NAS schreiben |
| B8 | **Datenschutz:** kein Verzeichnis der Verarbeitungstätigkeiten (Art. 30), kein Löschkonzept, Datenschutzhinweis nur für die Website | VVT + Löschkonzept (kurz) + Abschnitt „Kunden/Interessenten“ in der Datenschutzerklärung |
| B9 | **Claude (Anthropic):** für Privatabos (Free/Pro/Max) gibt es keinen AV-Vertrag nach Art. 28 DSGVO; nur Team/Enterprise/API haben ihn. Kundendaten, die im Chat genannt werden, landen bei Anthropic und in den Sitzungsprotokollen auf LXC 191 (+ vzdump) | Abo prüfen; Kundendaten möglichst nicht im Chat (Kundenstamm auf dem NAS, Werkzeuge lesen direkt) oder Team/API mit AV |
| B10 | **Zugangsdaten im Chatverlauf** (Storage Box = Verschlüsselungspasswort, FTP) – auch in Sitzungsprotokollen und vzdump-Sicherungen | Storage-Box-Passwort + FTP-Passwort ändern (Verschlüsselung bleibt, kein Neu-Upload) |

### C – vor dem ersten Jahreswechsel / bei Gelegenheit

| Nr. | Befund | Maßnahme |
|---|---|---|
| C1 | **Keine Jahreswechsel-Routine** (neue Jahresordner, 00_Eingang leer?, offene Rechnungen, Fahrtsumme, 10-Tage-Regel, VD-Archiv, Restore-Test) | `tools/jahreswechsel.py` + Checkliste in der VD |
| C2 | **Storno/Gutschrift** nicht im Werkzeug (Fehler in Rechnung → Stornorechnung nötig) | `dokument.py storno <Nr>` (E-Rechnung Typ 381 mit Bezug) |
| C3 | **Fotosicherung löscht mit** (Familienfotos) | durch Snapshots (B6) abgedeckt oder Archiv wie bei Belegen |
| C4 | **CSV-Bücher in Excel** öffnen/speichern kann Kodierung/Format zerstören | Bücher nur lesend öffnen (LIESMICH); bei Bedarf Excel-Ansicht erzeugen |
| C5 | **Aufbewahrungsübersicht/Löschplanung** fehlt; „Archiv nie löschen“ kollidiert langfristig mit DSGVO-Speicherbegrenzung | Tabelle (s. Abschnitt 5) in VD; erste Prüfung frühestens 2035 |
| C6 | Abhängigkeit von festen Pfaden (Chromium-Version im Playwright-Cache, Mustang-Version) | Selbsttest `tools/selbsttest.py` (prüft alle Abhängigkeiten) vor jeder Rechnung |
| C7 | STATUS.md wächst (Status + Entscheidungen gemischt) | `docs/entscheidungen.md` (Protokoll) abtrennen |
| C8 | 2 Beispiel-Entwürfe (Musterkunde) liegen in der echten Ablage | löschen |
| C9 | Kontoauszüge ING: monatlich als PDF abholen (Bank hält sie nur begrenzt vor), Empfangsformat behalten | Routine in VD, sobald Konto aktiv |
| C10 | Bargeld | Grundsatz „keine Barzahlung“ (auch Voraussetzung § 35a für Kunden); falls doch: Einzelaufzeichnung |

---

## 4. Jahreswechsel – Simulation (Testkopie, Testwerte)

- ✅ Neue Nummernreihe `2027-001`, Jahresordner werden automatisch angelegt, Fahrten je Jahr getrennt.
- ❌ Rückdatierte Rechnung wird ohne Warnung in die Vorjahresreihe einsortiert (→ A5).
- ⚠️ Ausgangsbuch über Jahre hinweg eine Datei (→ B4).
- Hinweis § 11 EStG: regelmäßig wiederkehrende Zahlungen (z. B. Hosting) innerhalb 10 Tagen um den 31.12. dem wirtschaftlichen Jahr zuordnen → in Journal/Jahreswechsel-Check.

---

## 5. Aufbewahrung je Ordner (Vorschlag für die Verfahrensdokumentation)

Frist beginnt am 31.12. des Jahres der Entstehung bzw. letzten Eintragung; vor Löschung Ablaufhemmung prüfen.

| Ablage | Art | Frist | Beispiel 2026 → frühestens löschbar |
|---|---|---|---|
| 01_Ausgaben, 03_Bank | Buchungsbelege | 8 J. | 01.01.2035 |
| 02_Rechnungen (PDF/E-Rechnung) | Buchungsbelege (§ 14b UStG) | 8 J. | 01.01.2035 |
| Ausgangsbuch, Journal, Fahrtenliste, GWG-Verzeichnis | Aufzeichnungen | 10 J. | 01.01.2037 |
| 06_Steuer (EÜR, Erklärungen) | Aufzeichnungen/Jahresunterlagen | 10 J. (Bescheide besser dauerhaft) | 01.01.2037 |
| 07_Kunden (Angebote, Korrespondenz), 09_Korrespondenz | Geschäftsbriefe | 6 J. | 01.01.2033 |
| 07_Kunden Montage-/Wartungsprotokolle | Haftungsnachweis (außersteuerlich) | **≥ 30 J. empfohlen** (§ 199 Abs. 2 BGB) | – |
| 05_Vertraege | sonstige Unterlagen | 6 J. nach Vertragsende | – |
| 08_Nachweise (Qualifikation) | Haftungsnachweis | dauerhaft | – |
| Verfahrensdokumentation + Repo-Bundle | Organisationsunterlagen | so lange wie die beschriebenen Unterlagen | – |

---

## 6. Datenschutz – Datenflüsse

| Ort | Daten | Grundlage/Absicherung | Befund |
|---|---|---|---|
| NAS | alle Geschäftsdaten | eigenes Gerät, nur Administratoren | ✅ |
| Hetzner Storage Box | Belege/Fotos **clientseitig verschlüsselt** | Hetzner kann nicht lesen | AV-Vertrag deckt bisher konsoleH (Webhosting/Mail) – prüfen, ob er auch die Storage Box (Hetzner Console) umfasst |
| Hetzner Mail/Webhosting | Kundenmails, AB-Nachrichten | AV-Vertrag abgeschlossen | ✅ (Archiv fehlt → B5) |
| GitHub | nur Code/Vorlagen | – | ✅ keine Kundendaten |
| Claude/Anthropic + LXC 191 | alles, was im Chat steht (auch Zugangsdaten) | Privatabo: kein AV-Vertrag | ⚠️ B9/B10 |
| Google Drive | Zugangsdaten-Dateien | privat | ok als „getrennte Aufbewahrung“; besser Passwortmanager |
| FritzBox | AB-Nachrichten | lokal | nach Bearbeitung löschen |

---

## 7. Maßnahmenplan (Vorschlag)

1. **Phase 1 (sofort, ohne Kosten):** A5 Rückdatierungsschutz, B2 Programmidentität, B3/B4 Bücher je Jahr + Historie, C8 Beispiel-Entwürfe entfernen – Code im Repo, getestet.
2. **Phase 2 (diese/nächste Woche):** A1 Journal + A3 GWG-Verzeichnis + A6 Umsatzgrenze; A2 Belege der Anlaufkosten (Patrick liefert); A4 Alarmierung.
3. **Phase 3:** B1 Verfahrensdokumentation (inkl. Fotografier-Anweisung, Aufbewahrungstabelle, Jahreswechsel-Checkliste), B7 Eingangsprotokoll, C1 Jahreswechsel-Werkzeug, C6 Selbsttest.
4. **Phase 4 (braucht Patrick):** B6 Snapshots (Hetzner Console), B10 Passwörter, B5 info@-Archiv (neues info@-Passwort per Datei), B8/B9 Datenschutz-Entscheidungen, C2 Storno.

---

## Quellen
- § 147 AO: https://www.gesetze-im-internet.de/ao_1977/__147.html
- § 19 UStG: https://www.gesetze-im-internet.de/ustg_1980/__19.html
- § 34a UStDV: https://www.gesetze-im-internet.de/ustdv_1980/__34a.html
- GoBD (BMF 28.11.2019), Spiegel IHK München: https://www.ihk-muenchen.de/ihk/documents/Recht-Steuern/Steuerrecht/2019-11-28-GoBD.pdf
- GoBD 2. Änderung (BMF 14.07.2025): https://www.bundesfinanzministerium.de/Content/DE/Downloads/BMF_Schreiben/Weitere_Steuerthemen/Abgabenordnung/2025-07-14-GoBD-2-aenderung.pdf
- Kleinunternehmer-Anwendungsschreiben (BMF 18.03.2025), Zusammenfassung: https://www.haufe.de/steuern/finanzverwaltung/bmf-anwendungsschreiben-zur-neuen-kleinunternehmerbesteuerung_164_644410.html
- GWG: https://www.meinbuero.de/ratgeber/buchhaltung/gwg-grenze-sonderregelung-fuer-kleinunternehmer/
- Hetzner Storage Box Snapshots: https://docs.hetzner.com/storage/storage-box/snapshots/
- Claude-Pläne und DPA: https://compound.law/en-DE/tools/claude-dpa/
