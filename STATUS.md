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
- FritzBox 7590 (FRITZ!OS 8.25), von Claude mit Patricks Freigabe eingerichtet (06.10.2026; Login danach gelöscht, Patrick ändert das Kennwort):
  - Integrierter AB „PGH-Brandschutz“ (**601), nur für 9998332, Annahme nach 20 s, Aufnahme max. 180 s, aktiv.
  - Ansage per Text-zu-Sprache (männlich): „Guten Tag, Sie sind verbunden mit PGH-Brandschutz, Patrick Gerhäuser. Leider bin ich gerade nicht erreichbar. Bitte hinterlassen Sie nach dem Signalton Ihren Namen, Ihre Telefonnummer und Ihr Anliegen. Ich rufe Sie schnellstmöglich zurück.“ Später ggf. durch eigene Aufnahme ersetzen (Datei hochladen).
  - Privater AB (**600, „alle“ Nummern) ist deaktiviert – nicht anfassen; falls er je aktiviert wird, 9998332 dort abwählen.
  - Bei 9998332 klingeln Mobilteil 1 + 3 und FRITZ!App Fon (HUAWEI BLN-L21) mit („alle“). Ausgehend nutzen alle Telefone 9994199 (privat).
  - Push Service: Absender ist Patricks privates Gmail → AB-Mail für PGH-Brandschutz bewusst **nicht** aktiviert (Gmail legt versandte Mails in „Gesendet“ ab = Kundendaten im Privatkonto).
  - Rest: externes Gerät „PGH-Brandschutz“ an FON 1 (**1) – Fehlversuch, an FON 1 hängt nichts (keine Anrufe darüber seit 05/2025). Löschen durch Patrick (Telefoniegeräte → Mülleimer).

## Offen (nächste Schritte)
1. Nach Lehrgang DIN 14676 (KW 42): Wartungs-Texte + Qualifikation freischalten (3 `[OFFEN]`-Stellen), Vorschau, Freigabe Patrick → `website/deploy.sh`.
2. FritzBox: Testanruf auf 9998332 (Patrick), FON-1-Gerät löschen, FritzBox-Kennwort + info@-Kennwort ändern. Danach optional AB-Nachrichten per Mail an info@ (Absender auf info@ via `mail.your-server.de` 465/SSL umstellen – betrifft auch private Push-Mails) und ggf. Geschäftstelefon mit ausgehender 9998332.
3. Postfach `belege@` erst zusammen mit der Belegablage anlegen (Passwort-Übergabe ohne Chat, z. B. Datei auf NAS).
4. NAS-Freigabe `PGH-Brandschutz` + Aufnahme in Hetzner-Sicherung (rclone-Container sieht bisher nur `Multimedia/Bilder`).
5. Fragebogen zur steuerlichen Erfassung (ELSTER) – Frist 1 Monat ab 11.10.2026.
6. Berufsgenossenschaft-Meldung, Betriebshaftpflicht, ggf. Nebentätigkeitsgenehmigung.
7. Nach Go-Live: Google-Unternehmensprofil (Servicegebiet, Adresse ausgeblendet), Bing Places, Search Console/Bing Webmaster, Das Örtliche/Gelbe Seiten.
