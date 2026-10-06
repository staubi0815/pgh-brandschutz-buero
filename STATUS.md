# Status & Entscheidungen

## 2026-10-06
- Gewerbe angemeldet, Beginn 11.10.2026. ING-Geschäftskonto in Eröffnung.
- Entscheidung Kleinunternehmer (§ 19 UStG): Kunden (WEG/Vermieter Wohnraum) können Vorsteuer
  nicht abziehen → Kleinunternehmer günstiger; Verzicht bindet 5 Jahre.
- Domain `pgh-brandschutz.de` per DENIC-WHOIS frei (Stand 06.10.2026).
- Hosting-Wahl: Hetzner Webhosting S (1,90 €/Monat brutto, Domain ab 5,83 €/Jahr).
- Impressum: Privatadresse ok; Telefon: bisher ungenutzte private Festnetznummer (Idee).
- Belege kommen per Mail (`belege@`), nicht per Telegram.
- Repo angelegt, Deploy-Key `~/.ssh/id_deploy_pgh-brandschutz-buero`, Alias `github.com-pgh-brandschutz-buero`.

- Hetzner Webhosting S + Domain laut Patrick bestellt (06.10.2026 abends; DNS noch nicht aktiv).
- SFTP per Schlüssel: `~/.ssh/id_hetzner_webhosting_pgh` (RSA 4096, Public Key im RFC4716-Format in konsoleH beim FTP-Hauptbenutzer).
- Website-Strategie-Dokument von Patrick (Google Drive, "compass_artifact_wf-722e1c26…") geprüft: übernehmen = statisches HTML, robots.txt KI-Crawler erlauben, Google-Unternehmensprofil (Servicegebiet, Adresse ausgeblendet), Bing Places, Search Console/Bing Webmaster, wenige Verzeichnisse (Das Örtliche, Gelbe Seiten, ggf. wlw), FAQ-Inhalte. Weglassen = llms.txt-Aufwand, KI-Monitoring-Abos, Markenanmeldung, Wikidata, Analytics zum Start.

- Hetzner-Server: `www793.your-server.de` (FTP-Benutzername noch offen). Telefon geschäftlich: 08168 9998332 (bisher ungenutzte Festnetznummer). Einsatzgebiet: Landkreis Freising + ca. 30 km.
- Website-Entwurf gebaut (8 Seiten + 404, robots.txt, Sitemap, JSON-LD). Patrick: **noch nicht online stellen**.
- SFTP per Schlüssel getestet (nur lesend, `ls`) – funktioniert. FTP-User `ebgkry`. Passwort hatte Patrick im Chat genannt → nicht gespeichert, Empfehlung: in konsoleH ändern.
- Entscheidungen Patrick: Brandschutztüren/Feststellanlagen auf der Website **ganz ausblenden**; keine W-IdNr vorhanden (Abschnitt entfernt); Lehrgang DIN 14676 voraussichtlich KW 42/2026.
- Interne Vorschau auf dem NAS: http://192.168.178.40:8092/ (Container `pgh-vorschau`, Update per `website/vorschau.sh`).
- E-Mail `info@pgh-brandschutz.de` eingerichtet (Patrick, Thunderbird für Android per IMAP; Gmail-POP-Abruf wieder entfernt). Test in beide Richtungen ok.
- Mail-DNS geprüft (06.10.2026): MX `www793.your-server.de`, SPF `v=spf1 a mx ~all`, DKIM aktiv (Selektor `default2610`, Testmail dkim=pass/spf=pass), DMARC `v=DMARC1;p=quarantine;sp=quarantine;pct=100;adkim=r;aspf=r;`. Vor Versand über Fremddienste (z. B. Rechnungssoftware im eigenen Namen) DMARC/SPF anpassen.
- Gesendet-Ordner: Hetzner legt Sent/Drafts/Trash erst an (Webmail einmal öffnen bzw. dort anlegen), dann in Thunderbird zuordnen – Patrick erledigt das.
- AV-Vertrag (Art. 28 DSGVO) mit Hetzner von Patrick abgeschlossen (06.10.2026); PDF später in die Belegablage.
- FritzBox 7590 (FRITZ!OS 8.25), von Claude mit Patricks Freigabe eingerichtet (06.10.2026; Login danach jeweils gelöscht, Patrick ändert das Kennwort):
  - Integrierter AB „PGH-Brandschutz“ (**601), nur für 9998332, **nimmt sofort ab** (Wunsch Patrick: immer AB, er ruft zurück), Aufnahme max. 180 s, aktiv.
  - Ansage per Text-zu-Sprache (männlich): „Guten Tag, Sie sind verbunden mit PGH-Brandschutz, Patrick Gerhäuser. Leider bin ich gerade nicht erreichbar. Bitte hinterlassen Sie nach dem Signalton Ihren Namen, Ihre Telefonnummer und Ihr Anliegen. Ich rufe Sie schnellstmöglich zurück.“ Später ggf. eigene Aufnahme (Datei hochladen).
  - Push Service (auf Wunsch Patrick „alles auf die neue Mail“): Absender `info@pgh-brandschutz.de` über `mail.your-server.de:587` (TLS), Standard-Empfänger info@. Aktiv: AB PGH-Brandschutz (Sprachnachricht als Audio-Anhang), Faxfunktion (privat, bestand schon), „Kennwort vergessen“. Testmail kam an (06.10.2026 22:07).
  - **Wenn das info@-Kennwort geändert wird: auch in der FritzBox ändern** (System → Push Service → Absender; FritzBox verlangt 2FA – Authenticator-Code von Patrick).
  - Externes FON-1-Gerät (Fehlversuch) gelöscht. Privater AB (**600, „alle“) ist deaktiviert – nicht anfassen; falls je aktiviert, 9998332 dort abwählen.
  - Mobilteil 1 + 3 und FRITZ!App Fon (HUAWEI BLN-L21) reagieren weiter auf „alle“ Nummern (Änderung durch Claude vom Auto-Mode blockiert – Familientelefone). Durch Sofort-Annahme klingeln sie praktisch nicht; falls doch: bei den Geräten 9998332 abwählen (Patrick).
  - Ausgehend nutzen alle Telefone 9994199 (privat).
- NAS-Freigabe `PGH-Brandschutz` angelegt (06.10.2026, nur Administratoren; Ordner 00_Eingang … 08_Nachweise, `LIESMICH.txt`). Nächtliche verschlüsselte Sicherung zu Hetzner mit Archiv (nichts wird gelöscht), getestet.
- Dabei gefunden und behoben: Hetzner-Fotosicherung lief seit Wochen nicht (Config lag auf QNAP-RAM-Disk, nach Neustart 02.10. weg; Fotos vom 22.08. fehlten). Neu aufgesetzt, nachgeholt. Empfehlung an Patrick: Storage-Box-Passwort ändern (ist identisch mit Crypt-Passwort und stand im Chat).
- Postfach `belege@pgh-brandschutz.de` angelegt (Patrick), Abholung per Cron alle 15 min → NAS `00_Eingang` (erlaubt: PDF, Bilder, XML; anhanglose Mails als .eml; zip/exe/Office werden nicht übernommen). Getestet 06.10.2026.
- Vorlagen + Werkzeuge (06.10.2026): `tools/dokument.py` (Rechnung/Angebot, Entwurf/final, Ausgangsbücher), `tools/fahrten.py` (Fahrtenliste 0,30 €/km), Layout DIN 5008. Getestet lokal + NAS. Endgültige Rechnungen erst, wenn Steuernummer (Pflicht nach § 34a UStDV) und IBAN in `vorlagen/firma.toml` stehen.

## Offen (nächste Schritte)
1. Nach Lehrgang DIN 14676 (KW 42): Wartungs-Texte + Qualifikation freischalten (3 `[OFFEN]`-Stellen), Vorschau, Freigabe Patrick → `website/deploy.sh`.
2. Passwörter: info@ + FritzBox-Login von Patrick geändert (07.10.2026, altes info@-PW abgelehnt = geprüft). Noch offen: neues info@-PW im FritzBox-Push-Absender (System → Push Service → Absender, Testmail), Testanruf 9998332 → AB-Mail mit Audio; FTP-Passwort (konsoleH) und Storage-Box-Passwort (= Crypt-PW, stand im Chat) ändern.
3. Fragebogen zur steuerlichen Erfassung (ELSTER) – Frist 1 Monat ab 11.10.2026.
4. Berufsgenossenschaft-Meldung, Betriebshaftpflicht, ggf. Nebentätigkeitsgenehmigung.
5. Nach Go-Live: Google-Unternehmensprofil (Servicegebiet, Adresse ausgeblendet), Bing Places, Search Console/Bing Webmaster, Das Örtliche/Gelbe Seiten.
6. Steuernummer (nach Fragebogen) und IBAN (ING-Geschäftskonto) in `vorlagen/firma.toml` eintragen → dann sind endgültige Rechnungen möglich.
