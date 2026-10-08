# Verfahrensdokumentation PGH-Brandschutz

nach den GoBD (BMF-Schreiben vom 28.11.2019, geändert am 11.03.2024 und 14.07.2025)

| | |
|---|---|
| Unternehmen | PGH-Brandschutz, Inhaber Patrick Gerhäuser, Am Pfannenstiel 8, 85406 Zolling |
| Gültig ab | 08.10.2026 |
| Verantwortlich | Patrick Gerhäuser |
| Versionierung | Git-Repository `staubi0815/pgh-brandschutz-buero`, Datei `docs/verfahrensdokumentation.md`. Jede geänderte Fassung wird automatisch als PDF mit Datum und Git-Kennung unter `06_Steuer/<Jahr>/verfahrensdokumentation/` auf dem NAS archiviert (GoBD Rz. 154). |

Diese Dokumentation beschreibt, wie Belege, Aufzeichnungen und Rechnungen entstehen, verarbeitet, gespeichert,
wiedergefunden, gesichert und aufbewahrt werden – so, dass ein sachverständiger Dritter das Verfahren in
angemessener Zeit nachvollziehen kann (GoBD Rz. 151–155).

---

## 1. Allgemeine Beschreibung

### 1.1 Unternehmen
- Einzelunternehmen im Nebengewerbe, Gewerbebeginn 11.10.2026 (Anmeldung 06.10.2026).
- Tätigkeiten: Beratung, Verkauf, Montage und (nach Qualifikation) Wartung von Rauchwarnmeldern; Hausmeister-
  und Gartendienste. Kunden überwiegend Hausverwaltungen/WEG, daneben Privatpersonen.
- Gewinnermittlung durch Einnahmen-Überschuss-Rechnung (§ 4 Abs. 3 EStG); keine Buchführungspflicht.
- Umsatzsteuer: Kleinunternehmer nach § 19 UStG (keine Umsatzsteuer, keine USt-Erklärungspflicht).
- Keine Mitarbeiter, keine Registrierkasse; Grundsatz: **keine Barzahlungen** (Zahlung per Überweisung).
- Geschäftskonto: ING (in Eröffnung). Bis dahin privat bezahlte Betriebsausgaben werden als solche gekennzeichnet.

### 1.2 Organisation und Verantwortung
- Patrick Gerhäuser ist für alle Aufzeichnungen verantwortlich, gibt Rechnungen/Angebote frei und übermittelt
  Steuererklärungen selbst (ELSTER).
- Als Hilfsmittel wird der KI-Assistent **Claude** (Anthropic) eingesetzt. Er bereitet vor, sortiert Belege ein,
  erfasst nach Angaben von Patrick und führt die unten beschriebenen Werkzeuge aus. **Endgültige Rechnungen und
  Angebote entstehen erst nach ausdrücklicher Freigabe durch Patrick.** Claude verändert keine abgeschlossenen
  Aufzeichnungen; Korrekturen erfolgen ausschließlich über Storno-/Gegenbuchungen.
- Alle Arbeitsschritte laufen über die versionierten Werkzeuge in `tools/` (Abschnitt 3.4), nicht über manuelles
  Bearbeiten der Bücher.

### 1.3 Grundsätze
1. **Belegprinzip:** keine Aufzeichnung ohne Beleg; fehlt ein Fremdbeleg, wird ein Eigenbeleg mit Begründung erstellt (Rz. 61).
2. **Zeitnah:** unbare Vorgänge werden innerhalb von 10 Tagen erfasst (Rz. 47, 50).
3. **Unveränderbarkeit:** abgeschlossene Belege und Rechnungen werden nicht geändert; Bücher werden nur über
   Werkzeuge fortgeschrieben, jede Änderung mit Vorversion und Protokoll (Rz. 58–60, 107–111).
4. **Empfangsformat:** elektronische Belege bleiben im Format, in dem sie empfangen wurden (XML, PDF, Bild) (Rz. 131).
5. **Ordnung:** feste Ablagestruktur und Dateinamen (Rz. 117); Zuordnung zum Geschäftsjahr nach Zahlungsdatum (§ 11 EStG).

### 1.4 Ablauf im Überblick
```
Papierbeleg ──Foto──┐
Rechnung per Mail ──┴→ belege@pgh-brandschutz.de ──(alle 15 min)──→ 00_Eingang ──einsortieren──→ 01_Ausgaben/<Jahr> …
                                                                                     │
                                                                          journal.py ausgabe ──→ Journal <Jahr> (+ GWG-Verzeichnis)
Angebot/Rechnung: Entwurf ──Freigabe Patrick──→ dokument.py --final ──→ 02_Rechnungen/<Jahr> + Rechnungsausgangsbuch <Jahr>
Zahlungseingang (Kontoauszug) ──→ journal.py einnahme ──→ Journal <Jahr> + „bezahlt am“ im Rechnungsausgangsbuch
Fahrt mit Privat-PKW ──→ fahrten.py ──→ Fahrtenliste <Jahr>
Täglich: Sicherung (verschlüsselt, Hetzner) + Kontrolle (Mail bei Problemen)
```

---

## 2. Anwenderdokumentation (Abläufe)

### 2.1 Belegeingang
- **Elektronische Belege** (Rechnungen per Mail, auch E-Rechnungen XML/ZUGFeRD) werden an
  `belege@pgh-brandschutz.de` weitergeleitet bzw. dorthin adressiert. `tools/belege_abholen.py` holt alle 15 Minuten
  ab: erlaubte Anhänge (PDF, Bilder, XML) bzw. anhanglose Mails als `.eml` werden **unverändert** nach `00_Eingang`
  gelegt; die Mail wandert in den IMAP-Ordner „Abgeholt“ (nicht gelöscht). Andere Dateitypen (ZIP, EXE, Office)
  werden aus Sicherheitsgründen nicht übernommen und protokolliert. Jede Abholung steht im Eingangsprotokoll
  `06_Steuer/<Jahr>/protokolle/belegeingang_<Jahr>.log` (Rz. 117).
- **Papierbelege** werden fotografiert und ebenfalls an belege@ geschickt (Abschnitt 2.2).

### 2.2 Organisationsanweisung bildliche Erfassung von Papierbelegen (GoBD Rz. 130, 136–140)
| Regel | Festlegung |
|---|---|
| Wer erfasst | Patrick Gerhäuser (Smartphone-Kamera) |
| Wann | bei Erhalt, spätestens innerhalb von 7 Tagen |
| Was | alle Papierbelege mit steuerlicher Bedeutung (Kassenbons, Quittungen, Rechnungen, Verträge, Bescheide) |
| Wie | jeder Beleg einzeln, vollständig (alle Seiten, alle Ränder), gut lesbar, in Farbe; Thermopapier sofort |
| Qualitätskontrolle | beim Einsortieren wird jede Aufnahme auf Lesbarkeit und Vollständigkeit geprüft; ungenügende Aufnahmen werden neu erstellt, bis dahin bleibt das Papier erhalten |
| Fehler | Mängel werden Patrick gemeldet und im Journal (Beschreibung) bzw. Ablageprotokoll vermerkt |
| Weiterbearbeitung | danach nur noch mit der elektronischen Fassung; keine Vermerke mehr auf dem Papier (Rz. 139) |
| Papier | darf nach erfolgreicher Kontrolle vernichtet werden (Rz. 140). **Empfehlung:** Papier eines Jahres bis zur Abgabe der EÜR aufbewahren. Verträge im Original zusätzlich aufbewahren. |

### 2.3 Einsortieren und Benennung
- `tools/einsortieren.py <Datei> <Zielordner> --name <Name>` verschiebt aus `00_Eingang` in die Ablage, ohne den
  Inhalt zu verändern und ohne zu überschreiben; Protokoll `06_Steuer/<Jahr>/protokolle/ablage_<Jahr>.log`.
- Dateiname: `JJJJ-MM-TT_Firma_Betrag_Kurzbeschreibung.<ursprüngliche Endung>` (Belegdatum).
- Unklare Belege bleiben in `00_Eingang`, bis Patrick sie geklärt hat. Die tägliche Kontrolle meldet Belege, die
  länger als 7 Tage dort liegen.

### 2.4 Erfassung im Journal (Einnahmen-/Ausgaben-Aufzeichnung)
- `tools/journal.py` führt je Jahr `06_Steuer/<Jahr>/journal_<Jahr>.csv`, geordnet nach **Zahlungsdatum**.
- Ausgaben: Kategorie (`journal.py kategorien`), Zahlweg `bank`/`privat` (privat bezahlte Betriebsausgabe)/`bar`,
  Beleg aus der Ablage oder Eigenbeleg mit Begründung.
- **GWG:** Wirtschaftsgüter über 250 € bis 800 € netto → Kategorie `gwg`, automatisch im GWG-Verzeichnis
  `06_Steuer/<Jahr>/gwg_verzeichnis_<Jahr>.csv` (§ 6 Abs. 2 EStG). Über 800 € netto: Anlagevermögen mit Abschreibung
  (gesondert, ggf. Steuerberater).
- Einnahmen aus Rechnungen nur mit Rechnungsnummer; setzt „bezahlt am“ im Rechnungsausgangsbuch.
- **Korrektur nur per `journal.py storno <Nr> --grund …`** (Gegenbuchung) und neuem Eintrag – nie Ändern oder Löschen.
- Fahrten mit dem Privat-PKW stehen in der Fahrtenliste (2.7) und werden in der Auswertung addiert.

### 2.5 Angebote und Rechnungen
1. Angaben von Patrick → Eingabedatei (TOML, nur in `/tmp` und auf dem NAS, nie im Repository).
2. `tools/dokument.py rechnung|angebot <Datei>` erzeugt einen **Entwurf** mit Wasserzeichen in
   `02_Rechnungen/Entwuerfe` bzw. `07_Kunden/Entwuerfe`. Patrick prüft.
3. Nach Freigabe: `… --final`. Das Werkzeug
   - vergibt die nächste Nummer der Jahresreihe (`2026-001`, Angebote `A-2026-001`),
   - setzt das **Ausstellungsdatum auf heute** (kein Zurückdatieren; Datum nie vor dem letzten Eintrag),
   - prüft Pflichtangaben nach § 34a UStDV (u. a. Steuernummer) und die **Kleinunternehmergrenze**
     (Gründungsjahr 25.000 €, danach Vorjahr ≤ 25.000 € und laufendes Jahr ≤ 100.000 €, vereinnahmt; Warnung ab 80 %,
     Sperre bei Überschreiten),
   - erzeugt bei Rechnungen eine **E-Rechnung (ZUGFeRD/Factur-X, EN 16931)** und prüft sie mit dem Mustang-Validator;
     ungültig ⇒ nichts gespeichert, keine Nummer verbraucht,
   - legt PDF und Eingabedaten (mit Werkzeugstand) ab und trägt die Rechnung ins Jahresbuch ein,
   - verweigert die Erstellung, wenn die Werkzeuge nicht eingecheckte Änderungen haben (Programmidentität).
4. Rechnungen werden nie geändert oder gelöscht. Fehler ⇒ Stornorechnung mit Bezug auf die Originalnummer und neue
   Rechnung (Werkzeugunterstützung folgt; bis dahin nicht ohne Rücksprache erstellen).

### 2.6 Zahlungseingänge und Bank
- Kontoauszüge des Geschäftskontos werden monatlich als PDF heruntergeladen (Empfangsformat) und nach
  `03_Bank/<Jahr>/` gelegt.
- Monatlich: jede Kontobewegung mit dem Journal abgleichen; fehlende Einträge erfassen (`journal.py einnahme|ausgabe`),
  dann `journal.py pruefen`.

### 2.7 Fahrten
`tools/fahrten.py eintragen` – Datum, Ziel, Zweck/Kunde, gefahrene km (bzw. einfache Strecke); Kilometerpauschale aus
`vorlagen/firma.toml` (0,30 €/km). Liste `04_Fahrten/<Jahr>/fahrten_<Jahr>.csv`, zeitnah führen.

### 2.8 Korrespondenz
Geschäftsbriefe (auch E-Mails, Angebote, Auftragsbestätigungen) sind 6 Jahre aufzubewahren, als Buchungsbeleg 8 Jahre.
Seit 08.10.2026 archiviert `tools/mail_archivieren.py` (Cron LXC 191, täglich 00:15 UTC, also vor der Nachtsicherung) alle
Mails von info@ – empfangen und gesendet, alle Ordner außer Spam/Entwürfe, auch Papierkorb – unverändert als `.eml` nach
`09_Korrespondenz/<Jahr>/eingang|ausgang/` (Name `JJJJ-MM-TT_HHMM_<Partner>_<Betreff>_<Prüfsumme>.eml`). Das Postfach wird
nur gelesen; jede Mail wird über die SHA-256-Prüfsumme genau einmal abgelegt, nichts überschrieben. Protokoll
`06_Steuer/<Jahr>/protokolle/mailarchiv_<Jahr>.log`. Mails im Postfach trotzdem nicht vorschnell löschen.

### 2.9 Monats- und Jahresabschluss
- **Monatlich:** Kontoauszug ablegen, Abgleich, `journal.py pruefen`, offene Rechnungen nachverfolgen.
- **Jahreswechsel:** `tools/jahreswechsel.py` (neue Jahresordner, Prüfung des abgelaufenen Jahres, Hinweise zu § 11 EStG,
  Archiv der Verfahrensdokumentation und des Werkzeugstands, Prüfbericht in `06_Steuer/<Jahr>/`).
- **EÜR:** `journal.py auswertung --jahr <J>` als Grundlage für die Anlage EÜR; Abgabe durch Patrick.

---

## 3. Technische Systemdokumentation

### 3.1 Komponenten
| Komponente | Aufgabe |
|---|---|
| NAS QNAP TS-262 (Heimnetz, RAID 1) | Ablage aller Geschäftsunterlagen, Freigabe `PGH-Brandschutz` |
| LXC 191 (Proxmox, Heimnetz) | führt die Werkzeuge aus (Python 3.11), Cron für Belegabholung und Kontrolle |
| Hetzner Webhosting S | Domain, Website, Postfächer info@ und belege@ |
| Hetzner Storage Box BX11 | verschlüsselte Außer-Haus-Sicherung (rclone crypt) |
| GitHub (privat) | Werkzeuge, Vorlagen, Dokumentation – **keine Geschäftsdaten** |

### 3.2 Ablagestruktur und Formate (NAS `\\192.168.178.40\PGH-Brandschutz`)
| Ordner | Inhalt | Format |
|---|---|---|
| 00_Eingang | neu eingegangene Belege (Durchgang) | wie empfangen |
| 01_Ausgaben/<Jahr> | Eingangsrechnungen, Quittungen, Eigenbelege | PDF/JPG/XML/EML/TXT |
| 02_Rechnungen/<Jahr> | Ausgangsrechnungen (E-Rechnung PDF/A-3 mit XML), `_daten/` Eingabedaten | PDF, TOML |
| 02_Rechnungen | `rechnungsausgangsbuch_<Jahr>.csv`, `_historie/` | CSV |
| 03_Bank/<Jahr> | Kontoauszüge | PDF wie empfangen |
| 04_Fahrten/<Jahr> | Fahrtenliste | CSV |
| 05_Vertraege | Verträge, Versicherungen, BG, Gewerbeanmeldung | PDF |
| 06_Steuer/<Jahr> | Journal, GWG-Verzeichnis, Protokolle, Steuererklärungen, Bescheide, Verfahrensdokumentation | CSV, LOG, PDF |
| 07_Kunden/<Kunde> | Angebote, Montage-/Wartungsprotokolle, Korrespondenz; `angebotsbuch_<Jahr>.csv` | PDF, CSV |
| 08_Nachweise | Qualifikationen, Zertifikate | PDF |
| 09_Korrespondenz/<Jahr> | Mail-Archiv info@ (`eingang/`, `ausgang/`), automatisch | EML |

**Bücher (CSV):** UTF-8 mit BOM, Trennzeichen Semikolon, Dezimalkomma, feste Kopfzeile. Sie werden nur von den
Werkzeugen geschrieben; vor jeder Änderung wird die bisherige Fassung nach `<Ordner>/_historie/` kopiert und die
Änderung in `_historie/aenderungen.log` protokolliert (Zeit, Datei, Aktion, Werkzeugstand). Zum Ansehen dürfen sie in
Excel geöffnet, aber **nicht gespeichert** werden – das Werkzeug erkennt abweichende Spalten und bricht ab.

### 3.3 Werkzeuge (`tools/` im Repository)
| Werkzeug | Zweck |
|---|---|
| `gemeinsam.py` | Ablage, Bücher mit Historie, Werkzeugstand, Kleinunternehmergrenze |
| `belege_abholen.py` | belege@ → 00_Eingang, Eingangsprotokoll |
| `einsortieren.py` | 00_Eingang → Ablage, Ablageprotokoll |
| `journal.py` | Journal, GWG-Verzeichnis, Storno, Auswertung, Vollständigkeitsprüfung |
| `dokument.py`, `erechnung.py` | Angebote/Rechnungen, E-Rechnung + Validierung |
| `fahrten.py` | Fahrtenliste |
| `kontrolle.py` | tägliche Kontrolle mit Mail |
| `jahreswechsel.py` | Jahreswechsel-Routine |
| `vd_archiv.py` | PDF-Archiv dieser Verfahrensdokumentation |
| `ansage.py` | Anrufbeantworter-Ansage (nicht steuerrelevant) |

Abhängigkeiten auf LXC 191: Python 3.11; venv `~/.venvs/pgh` (factur-x 7.3, pikepdf, piper-tts, scipy, markdown);
Chromium 1243 (Playwright) für PDF; Java 17 + Mustang-CLI 2.26.0 für die E-Rechnungsprüfung. Die tägliche Kontrolle
prüft, dass alles vorhanden ist.

**Programmidentität (Rz. 154):** jede Rechnung, jeder Buch- und Journaleintrag trägt die Git-Kennung des
Werkzeugstands; endgültige Rechnungen nur aus eingechecktem Stand. Der vollständige Werkzeugstand wird jährlich als
`git bundle` unter `06_Steuer/<Jahr>/` archiviert, damit er auch ohne GitHub 10 Jahre verfügbar bleibt.

### 3.4 Zugriffsschutz
- Freigabe `PGH-Brandschutz`: nur Gruppe Administratoren (kein Gast, keine Familienkonten), Netzwerk-Papierkorb an.
- Zugangsdaten nur in `~/.config/pgh-brandschutz/` auf LXC 191 (Dateirechte 600), nie im Repository.
- Außer-Haus-Sicherung clientseitig verschlüsselt (Datei- und Ordnernamen); Schlüssel getrennt vom NAS aufbewahrt
  (Notfall-Anleitung im Google Drive „Notfall-Wiederherstellung Hetzner Fotos-Backup“).

### 3.5 Maßnahmen zur Unveränderbarkeit (Rz. 110)
- Werkzeuge überschreiben keine Belege/Rechnungen; Bücher nur mit Vorversion + Änderungsprotokoll.
- Nächtliche Sicherung mit Archiv: was auf dem NAS geändert oder gelöscht wird, bleibt bei Hetzner unter
  `archiv/<Zeitstempel>` erhalten und wird nicht gelöscht.
- Rechtekonzept (nur Administratoren), Git-Historie der Werkzeuge und dieser Dokumentation.
- Geplant: automatische Snapshots der Storage Box (nur über die Hetzner Console löschbar).

---

## 4. Betriebsdokumentation

### 4.1 Datensicherung
| Was | Wann | Wie |
|---|---|---|
| Freigabe PGH-Brandschutz | täglich 02:30 | rclone im Container `rclone-hetzner` (NAS) → `hetzner-crypt-pgh:aktuell`, Geändertes/Gelöschtes → `archiv/<Zeit>` |
| Fotos (privat) | mittwochs 01:00 | rclone sync → `hetzner-crypt:` |
| LXC 191 (Werkzeuge, Zugangsdaten) | täglich 02:00 | Proxmox vzdump → NAS |
| Repository | bei jeder Änderung | GitHub + jährliches Bundle auf dem NAS |

Technische Details: homelab-infra `infra/nas-qnap.md`, `infra/lxc-191-claude-code.md`.

### 4.2 Kontrolle
`tools/kontrolle.py` läuft täglich (07:15 Uhr Sommerzeit) und prüft Sicherungen, RAID, Speicher, Belegabholung, Mailarchiv,
`00_Eingang`, überfällige Rechnungen, Kleinunternehmergrenze und Werkzeuge. Bei Fehlern/Warnungen Mail an info@,
montags immer Wochenbericht (bleibt er aus, läuft die Kontrolle nicht). Log `~/.local/state/pgh-brandschutz/kontrolle.log`.

### 4.3 Wiederherstellung
- Rücksicherung: `rclone copy hetzner-crypt-pgh:aktuell <Ziel>` (bzw. `archiv/<Zeit>` für ältere Stände) mit der
  Konfiguration aus der Notfall-Anleitung.
- Test am 08.10.2026: alle Dateien bitgleich wiederhergestellt, `rclone cryptcheck` ohne Abweichung. Wiederholung
  mindestens jährlich beim Jahreswechsel.

### 4.4 Änderungen an Werkzeugen und Dokumentation
Jede Änderung wird vor dem Einsatz getestet (lokaler Testmodus `--lokal`) und mit Beschreibung in Git eingecheckt.
Die Verfahrensdokumentation wird bei Änderungen der Abläufe angepasst; geänderte Fassungen werden automatisch als
PDF archiviert.

---

## 5. Internes Kontrollsystem (Übersicht)
| Risiko | Kontrolle |
|---|---|
| Beleg geht verloren | belege@-Abholung mit Protokoll; tägliche Kontrolle (Postfach, 00_Eingang); `journal.py pruefen` (Belege ohne Eintrag) |
| Doppelte/falsche Rechnung | Doppelschutz (Prüfsumme der Eingabe), fortlaufende Nummer, Freigabe durch Patrick, E-Rechnungsvalidierung |
| Zurückdatieren | Ausstellungsdatum = heute, nie vor letztem Eintrag |
| Kleinunternehmergrenze überschritten | Prüfung bei jeder Rechnung und täglich (Warnung 80 %) |
| Zahlungen nicht erfasst | monatlicher Bankabgleich, überfällige Rechnungen in der Kontrolle |
| Unbemerkte Änderungen an Büchern | Historie + Änderungsprotokoll, Spaltenprüfung, nächtliches Archiv |
| Datenverlust | RAID 1, tägliche verschlüsselte Außer-Haus-Sicherung mit Archiv, jährlicher Wiederherstellungstest |
| Werkzeugfehler | Tests vor Einsatz, Programmidentität, Selbsttest in der Kontrolle |

---

## 6. Aufbewahrung und Löschung
Fristbeginn: 31.12. des Jahres der Entstehung bzw. der letzten Eintragung (§ 147 Abs. 4 AO); keine Löschung,
solange eine Festsetzungsfrist offen ist (§ 147 Abs. 3 AO).

| Unterlagen | Frist |
|---|---|
| Buchungsbelege (01_Ausgaben, 02_Rechnungen, 03_Bank, Eigenbelege) | 8 Jahre |
| Aufzeichnungen (Journal, Rechnungs-/Angebotsbuch, Fahrtenliste, GWG-Verzeichnis, Protokolle), EÜR, Verfahrensdokumentation, Werkzeug-Bundles | 10 Jahre (Verfahrensdokumentation so lange wie die beschriebenen Unterlagen) |
| Geschäftsbriefe (Angebote, Korrespondenz) | 6 Jahre |
| Montage-/Wartungsprotokolle (Haftung, § 199 Abs. 2 BGB bis 30 Jahre) | mindestens 30 Jahre empfohlen |
| Qualifikationsnachweise | dauerhaft |
| Steuerbescheide | dauerhaft empfohlen |

Löschung erst nach Fristablauf und Prüfung (frühestens 2033 für Geschäftsbriefe 2026, 2035 für Belege 2026);
personenbezogene Daten werden dann gelöscht (DSGVO, Speicherbegrenzung), auch im Hetzner-Archiv. Die Prüfung erfolgt
jährlich beim Jahreswechsel.

---

## 7. Mitgeltende Unterlagen
- `CLAUDE.md` (Arbeitsanleitung), `STATUS.md`, `docs/pruefbericht-2026-10-08.md` im Repository
- `LIESMICH.txt` in der Freigabe PGH-Brandschutz
- homelab-infra: `infra/nas-qnap.md`, `infra/lxc-191-claude-code.md`
- Notfall-Anleitung Wiederherstellung (Google Drive, getrennt vom NAS)

## 8. Änderungshistorie
Siehe `git log -- docs/verfahrensdokumentation.md`; archivierte Fassungen in `06_Steuer/<Jahr>/verfahrensdokumentation/`.
