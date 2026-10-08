# Recherche Ferninspektion Sontex Ei6500 SA2 (Stand 08.10.2026)

Frage Patrick: Kann ich die Auslesung der Melder (Datenbank, Registrierung per QR-Code) selbst daheim auf Proxmox betreiben?

## Gerät (Datenblatt V1.2 05/26, Installationsanleitung 05/2026)
- Ei6500 SA2-**O**: wM-Bus EN 13757-4, OMS-kompatibel, T1/C1, 868,95 MHz, AES-128 Mode 5/7, **unidirektional**,
  sendet alle 2 min 12 h/Tag (OMS-Betrieb: alle 4 min 24 h/Tag). Installationsmodus: alle 30 s bis zweites 0:00 Uhr.
- Ei6500 SA2-**L**: LoRaWAN 1.0.2 Klasse A, AppKey, 1× täglich, bidirektional, öffentliche oder private Netze.
- Typ C nach DIN 14676-1 Verfahren C, Zulassung KRIWAN 1772-FIRWM-181135. Kein Funk → Inspektion vor Ort.
- „Zur Entschlüsselung ist ein individueller AES-Schlüssel erforderlich (Bereitstellung über Onlineportal).“

## Hersteller-Weg (Sontex)
- **Sonexa KeyXchange** = Schlüsselportal. Push (Händler weist Schlüssel zu) oder Pull (Endanwender scannt
  QR-Code am Gerät). Web + REST-API. Zugangsbedingungen/Kosten nicht veröffentlicht.
- **Tools Supercom** (Windows/Android) + **Supercom 637** (wM-Bus-Modem, Bluetooth) = Walk-by.
- **Superlink C** Gateway (NB-IoT/LTE-M, Batterie oder 230 V) → nur **Sonexa Superlink Service** (Cloud, EU,
  2 Jahre Speicherung, Export per sFTP/API). Gateway kostenlos, 3 Monate Test, Preise nicht veröffentlicht.

## Vergleich Ei Electronics (Original Ei6500-OMS)
- Walk-by: Funkmodem Michael RAC MBWBlue 700 € einmalig + Software „Rauchwarnmelder-Manager“ ab 40 €/Monat.
- AES-Schlüsseldatei verschlüsselt, Entschlüsselung über aes.eielectronics.de.

## Selbst betreiben (Proxmox)
- **wmbusmeters** (GPL, Linux) hat Treiber `ei6500` (Hersteller-Kennung EIE, Typ 0x1A): Alarmzähler/-datum,
  Demontage, Testknopf, Staub, Batterie, Hindernisabstand, Kopfstatus. Empfänger z. B. RTL-SDR oder iM871A.
- Offen: sendet der Sontex-SA2-O als EIE oder SON? Treiber ist teils nachgebaut → alle Fehlerzustände selbst testen.
- Funk reicht nur ums Gebäude: Proxmox daheim = Datenbank/Auswertung; Empfang beim Kunden per Walk-by-Gerät
  oder Empfänger im Kundengebäude.
- SA2-L: ChirpStack selbst möglich, aber LoRaWAN-Gateway/Netzabdeckung nötig, Payload-Beschreibung nicht öffentlich.

## Offene Fragen an Sontex (vor Kauf)
1. KeyXchange-Konto für Kleinbetrieb möglich, Kosten? Schlüssel exportierbar (CSV/XML)?
2. Beschreibung der Funktelegramme/Datenpunkte SA2-O (und SA2-L-Payload)?
3. Bezugsquelle und Preis in Kleinmengen in Deutschland.

Quellen: sontex.com/de/produkt/ei6500-sa2/ (Datenblatt, Installations-/Bedienungsanleitung),
sontex.com/de/software/sonexa-keyxchange-service-de/, …/sonexa-superlink-service-de/, …/tools-supercom-de/,
Superlink C User Manual, eielectronics.de/loesungen/ferninspektion, rauchwarnmelder-manager.de,
github.com/wmbusmeters/wmbusmeters (drivers/src/ei6500.xmq).
