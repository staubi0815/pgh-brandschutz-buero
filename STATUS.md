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

## Offen (nächste Schritte)
1. Patrick: FTP-Benutzernamen nennen (SFTP-Key in konsoleH eintragen) → `~/.config/pgh-brandschutz/hetzner.env`.
2. Website: 7 `[OFFEN]`-Stellen klären (Lehrgangstermin DIN 14676, Türen-Text, W-IdNr, Log-Speicherdauer, AV-Vertrag Hetzner); danach Freigabe durch Patrick → `website/deploy.sh`.
3. FritzBox: Anleitung für Geschäftsnummer (AB, Ansage, ausgehende Nummer) an Patrick gegeben – Umsetzung durch Patrick.
4. Postfächer `info@`, `belege@` anlegen (IMAP-Passwort belege@ → `~/.config/pgh-brandschutz/`).
5. NAS-Freigabe `PGH-Brandschutz` + Aufnahme in Hetzner-Sicherung (rclone-Container sieht bisher nur `Multimedia/Bilder`; NAS-Änderung nur nach Rückfrage).
6. Fragebogen zur steuerlichen Erfassung (ELSTER) – Frist 1 Monat ab 11.10.2026.
7. Berufsgenossenschaft-Meldung, Betriebshaftpflicht, ggf. Nebentätigkeitsgenehmigung.
8. Später: Google-Unternehmensprofil (Servicegebiet, Adresse ausgeblendet), Bing Places, Search Console/Bing Webmaster, Das Örtliche/Gelbe Seiten.
