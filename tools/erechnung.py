"""E-Rechnung (ZUGFeRD 2 / Factur-X, Profil EN 16931) für Kleinunternehmer erzeugen und prüfen.

Wird von dokument.py für endgültige Rechnungen benutzt:
  - cii_xml(...)      baut das CII-XML (UN/CEFACT Cross Industry Invoice) nach EN 16931
  - einbetten(...)    bettet das XML als factur-x.xml in das PDF ein (PDF/A-3, factur-x-Bibliothek)
  - pruefen(...)      prüft das fertige PDF mit dem Mustang-Validator (PDF/A + XML-Schema + EN-16931-Regeln)

Kleinunternehmer (§ 19 UStG): Umsatzsteuerkategorie „E“ (befreit), Satz 0 %, Befreiungsgrund als Text;
Steuernummer als Steuerregistrierung des Verkäufers (BT-32, schemeID „FC“) – Pflicht nach BR-E-02.
Benötigt die venv ~/.venvs/pgh (factur-x, pikepdf) und Java + ~/tools/mustang/Mustang-CLI-*.jar.
"""
import glob
import os
import re
import subprocess
import tempfile
from datetime import date
from xml.sax.saxutils import escape

MUSTANG = sorted(glob.glob(os.path.expanduser("~/tools/mustang/Mustang-CLI-*.jar")))
BEFREIUNG = "Steuerfrei als Kleinunternehmer nach § 19 UStG"

# Einheiten nach UN/ECE Recommendation 20
EINHEITEN = {"stk": "H87", "stk.": "H87", "stück": "H87", "st.": "H87",
             "pausch.": "LS", "pauschal": "LS", "psch.": "LS", "pauschale": "LS",
             "std.": "HUR", "std": "HUR", "h": "HUR", "stunde": "HUR", "stunden": "HUR",
             "km": "KMT", "m": "MTR", "m²": "MTK", "qm": "MTK", "set": "SET"}


def _d(dt):
    return f'<udt:DateTimeString format="102">{dt:%Y%m%d}</udt:DateTimeString>'


def _betrag(x):
    return f"{x:.2f}"


def _plz_ort(text):
    m = re.match(r"\s*(\d{4,5})\s+(.+)", text)
    if not m:
        raise ValueError(f"PLZ/Ort nicht erkennbar: {text!r} (erwartet z. B. „85354 Freising“)")
    return m.group(1), m.group(2).strip()


def leistungszeit(text):
    """'15.10.2026' → (datum, None); '14.10.2026 - 16.10.2026' (auch '–' oder 'bis') → (start, ende).
    Alles andere (z. B. '14.–16.10.2026') wird abgelehnt, damit kein Zeitraum still zum Einzeltag wird."""
    datum = r"(\d{1,2})\.(\d{1,2})\.(\d{4})"
    text = (text or "").strip()
    m = re.fullmatch(datum, text)
    if m:
        t, mo, j = map(int, m.groups())
        return date(j, mo, t), None
    m = re.fullmatch(rf"{datum}\s*(?:-|–|bis)\s*{datum}", text)
    if m:
        t1, m1, j1, t2, m2, j2 = map(int, m.groups())
        start, ende = date(j1, m1, t1), date(j2, m2, t2)
        if ende < start:
            raise ValueError(f"Leistungszeitraum endet vor dem Beginn: {text}")
        return start, ende
    raise ValueError(f"Leistungsdatum „{text}“ nicht eindeutig – bitte als „TT.MM.JJJJ“ oder „TT.MM.JJJJ - TT.MM.JJJJ“ angeben")


def _adresse(strasse, plz_ort):
    plz, ort = _plz_ort(plz_ort)
    return (f"<ram:PostalTradeAddress><ram:PostcodeCode>{escape(plz)}</ram:PostcodeCode>"
            f"<ram:LineOne>{escape(strasse)}</ram:LineOne><ram:CityName>{escape(ort)}</ram:CityName>"
            f"<ram:CountryID>DE</ram:CountryID></ram:PostalTradeAddress>")


def cii_xml(d, firma, nummer, datum, faellig, zeilen, gesamt):
    doc, kunde = d.get("dokument", {}), d["kunde"]
    start, ende = leistungszeit(doc.get("leistungsdatum", ""))

    pos = []
    for i, z in enumerate(zeilen, 1):
        einheit = EINHEITEN.get(str(z.get("einheit", "")).strip().lower(), "C62")
        menge = f"{z['menge_d']:.4f}".rstrip("0").rstrip(".")
        pos.append(
            "<ram:IncludedSupplyChainTradeLineItem>"
            f"<ram:AssociatedDocumentLineDocument><ram:LineID>{i}</ram:LineID></ram:AssociatedDocumentLineDocument>"
            f"<ram:SpecifiedTradeProduct><ram:Name>{escape(z['text'])}</ram:Name></ram:SpecifiedTradeProduct>"
            "<ram:SpecifiedLineTradeAgreement><ram:NetPriceProductTradePrice>"
            f"<ram:ChargeAmount>{z['preis_d']:.2f}</ram:ChargeAmount></ram:NetPriceProductTradePrice></ram:SpecifiedLineTradeAgreement>"
            f'<ram:SpecifiedLineTradeDelivery><ram:BilledQuantity unitCode="{einheit}">{menge}</ram:BilledQuantity></ram:SpecifiedLineTradeDelivery>'
            "<ram:SpecifiedLineTradeSettlement><ram:ApplicableTradeTax><ram:TypeCode>VAT</ram:TypeCode>"
            "<ram:CategoryCode>E</ram:CategoryCode><ram:RateApplicablePercent>0</ram:RateApplicablePercent></ram:ApplicableTradeTax>"
            f"<ram:SpecifiedTradeSettlementLineMonetarySummation><ram:LineTotalAmount>{_betrag(z['betrag'])}</ram:LineTotalAmount>"
            "</ram:SpecifiedTradeSettlementLineMonetarySummation></ram:SpecifiedLineTradeSettlement>"
            "</ram:IncludedSupplyChainTradeLineItem>")

    kontakt_v = (f"<ram:DefinedTradeContact><ram:PersonName>{escape(firma['inhaber'])}</ram:PersonName>"
                 f"<ram:TelephoneUniversalCommunication><ram:CompleteNumber>{escape(firma['telefon'])}</ram:CompleteNumber></ram:TelephoneUniversalCommunication>"
                 f"<ram:EmailURIUniversalCommunication><ram:URIID>{escape(firma['email'])}</ram:URIID></ram:EmailURIUniversalCommunication>"
                 "</ram:DefinedTradeContact>")
    # BT-29 Verkäuferkennung (BR-CO-26): Lieferantennummer beim Kunden, sonst Steuernummer
    kennung = str(kunde.get("lieferantennummer") or firma["steuernummer"])
    verkaeufer = (f"<ram:SellerTradeParty><ram:ID>{escape(kennung)}</ram:ID><ram:Name>{escape(firma['name'])}</ram:Name>{kontakt_v}"
                  f"{_adresse(firma['strasse'], firma['plz_ort'])}"
                  f'<ram:URIUniversalCommunication><ram:URIID schemeID="EM">{escape(firma["email"])}</ram:URIID></ram:URIUniversalCommunication>'
                  f'<ram:SpecifiedTaxRegistration><ram:ID schemeID="FC">{escape(firma["steuernummer"])}</ram:ID></ram:SpecifiedTaxRegistration>'
                  "</ram:SellerTradeParty>")

    kontakt_k = ""
    zusatz = re.sub(r"^\s*z\.\s*Hd\.?\s*", "", kunde.get("zusatz", "")).strip()
    if zusatz:
        kontakt_k = f"<ram:DefinedTradeContact><ram:PersonName>{escape(zusatz)}</ram:PersonName></ram:DefinedTradeContact>"
    mail_k = ""
    if kunde.get("email"):
        mail_k = f'<ram:URIUniversalCommunication><ram:URIID schemeID="EM">{escape(kunde["email"])}</ram:URIID></ram:URIUniversalCommunication>'
    kaeufer = (f"<ram:BuyerTradeParty><ram:Name>{escape(kunde['name'])}</ram:Name>{kontakt_k}"
               f"{_adresse(kunde['strasse'], kunde['plz_ort'])}{mail_k}</ram:BuyerTradeParty>")

    referenz = f"<ram:BuyerReference>{escape(doc['ihr_zeichen'])}</ram:BuyerReference>" if doc.get("ihr_zeichen") else ""
    lieferung = ("<ram:ApplicableHeaderTradeDelivery>"
                 + ("" if ende else f"<ram:ActualDeliverySupplyChainEvent><ram:OccurrenceDateTime>{_d(start)}</ram:OccurrenceDateTime></ram:ActualDeliverySupplyChainEvent>")
                 + "</ram:ApplicableHeaderTradeDelivery>")
    zeitraum = (f"<ram:BillingSpecifiedPeriod><ram:StartDateTime>{_d(start)}</ram:StartDateTime>"
                f"<ram:EndDateTime>{_d(ende)}</ram:EndDateTime></ram:BillingSpecifiedPeriod>") if ende else ""
    iban = re.sub(r"\s+", "", firma["iban"])
    bic = (f"<ram:PayeeSpecifiedCreditorFinancialInstitution><ram:BICID>{escape(firma['bic'])}</ram:BICID>"
           "</ram:PayeeSpecifiedCreditorFinancialInstitution>") if firma.get("bic") else ""
    summe = _betrag(gesamt)

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100" xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100" xmlns:qdt="urn:un:unece:uncefact:data:standard:QualifiedDataType:100" xmlns:udt="urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100">
<rsm:ExchangedDocumentContext><ram:GuidelineSpecifiedDocumentContextParameter><ram:ID>urn:cen.eu:en16931:2017</ram:ID></ram:GuidelineSpecifiedDocumentContextParameter></rsm:ExchangedDocumentContext>
<rsm:ExchangedDocument><ram:ID>{escape(nummer)}</ram:ID><ram:TypeCode>380</ram:TypeCode><ram:IssueDateTime>{_d(datum)}</ram:IssueDateTime>
<ram:IncludedNote><ram:Content>{escape(BEFREIUNG)}. Umsatzsteuer wird nicht berechnet.</ram:Content></ram:IncludedNote></rsm:ExchangedDocument>
<rsm:SupplyChainTradeTransaction>
{''.join(pos)}
<ram:ApplicableHeaderTradeAgreement>{referenz}{verkaeufer}{kaeufer}</ram:ApplicableHeaderTradeAgreement>
{lieferung}
<ram:ApplicableHeaderTradeSettlement><ram:PaymentReference>{escape(nummer)}</ram:PaymentReference><ram:InvoiceCurrencyCode>EUR</ram:InvoiceCurrencyCode>
<ram:SpecifiedTradeSettlementPaymentMeans><ram:TypeCode>58</ram:TypeCode><ram:Information>SEPA-Überweisung</ram:Information>
<ram:PayeePartyCreditorFinancialAccount><ram:IBANID>{escape(iban)}</ram:IBANID><ram:AccountName>{escape(firma['name'])}</ram:AccountName></ram:PayeePartyCreditorFinancialAccount>{bic}</ram:SpecifiedTradeSettlementPaymentMeans>
<ram:ApplicableTradeTax><ram:CalculatedAmount>0.00</ram:CalculatedAmount><ram:TypeCode>VAT</ram:TypeCode><ram:ExemptionReason>{escape(BEFREIUNG)}</ram:ExemptionReason><ram:BasisAmount>{summe}</ram:BasisAmount><ram:CategoryCode>E</ram:CategoryCode><ram:RateApplicablePercent>0</ram:RateApplicablePercent></ram:ApplicableTradeTax>
{zeitraum}
<ram:SpecifiedTradePaymentTerms><ram:Description>Zahlbar ohne Abzug bis {faellig:%d.%m.%Y}</ram:Description><ram:DueDateDateTime>{_d(faellig)}</ram:DueDateDateTime></ram:SpecifiedTradePaymentTerms>
<ram:SpecifiedTradeSettlementHeaderMonetarySummation><ram:LineTotalAmount>{summe}</ram:LineTotalAmount><ram:TaxBasisTotalAmount>{summe}</ram:TaxBasisTotalAmount><ram:TaxTotalAmount currencyID="EUR">0.00</ram:TaxTotalAmount><ram:GrandTotalAmount>{summe}</ram:GrandTotalAmount><ram:DuePayableAmount>{summe}</ram:DuePayableAmount></ram:SpecifiedTradeSettlementHeaderMonetarySummation>
</ram:ApplicableHeaderTradeSettlement>
</rsm:SupplyChainTradeTransaction>
</rsm:CrossIndustryInvoice>
"""
    return xml.encode("utf-8")


def einbetten(pdf, xml, nummer, firma, kunde_name):
    import facturx  # aus der venv ~/.venvs/pgh
    meta = {"author": firma["inhaber"], "keywords": "Rechnung, Factur-X, ZUGFeRD",
            "title": f"{firma['name']}: Rechnung {nummer}", "subject": f"Rechnung {nummer} an {kunde_name}"}
    return facturx.generate_from_binary(pdf, xml, flavor="factur-x", level="en16931", check_xsd=True,
                                        pdf_metadata=meta, lang="de-DE")


def pruefen(pdf):
    """Mustang-Validierung. Gibt (gueltig: bool, kurzbericht: str) zurück."""
    if not MUSTANG:
        return False, "Mustang-Validator fehlt (~/tools/mustang/Mustang-CLI-*.jar)"
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "rechnung.pdf")
        open(p, "wb").write(pdf)
        erg = subprocess.run(["java", "-jar", MUSTANG[-1], "--no-notices", "--action", "validate", "--source", p],
                             capture_output=True, text=True, timeout=300)
    bericht = erg.stdout + erg.stderr
    gueltig = bool(re.search(r'<summary status="valid"', bericht))
    fehler = re.findall(r"<error[^>]*>(.*?)</error>", bericht, re.S)
    kurz = "gültig" if gueltig else "UNGÜLTIG: " + " | ".join(f.strip()[:300] for f in fehler[:8])
    return gueltig, kurz if (gueltig or fehler) else ("UNGÜLTIG (Bericht ohne Einzelfehler): " + bericht[-800:])
