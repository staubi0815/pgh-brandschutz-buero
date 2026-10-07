#!/home/claude/.venvs/pgh/bin/python
"""Anrufbeantworter-Ansage mit freier Sprachsynthese (Piper) erzeugen – im FritzBox-Format.

  ansage.py --stimme de_DE-thorsten-high --aus /tmp/ansage.wav [--tempo 1.12] [--sprecher neutral]
            [--text-datei ansage.txt] [--vorschau /tmp/ansage_hq.wav]

Text: eine Zeile je Satzteil, optional mit Pause in Sekunden am Ende: „Satzteil | 0.5“.
Ausgabe: WAV PCM 16 bit, mono, 8000 Hz (von AVM empfohlen, max. 60 s) – direkt in der FritzBox hochladbar
(Telefonie → Anrufbeantworter → Einstellungen → Ansage ändern → Eigene Ansage → Datei hochladen).
Stimmen liegen in ~/tools/piper-voices (Thorsten/Kerstin: CC0; Karlsson/Eva/Ramona: M-AILABS, Quellenangabe).
Aussprache-Tricks: „P G H“ (mit Leerzeichen) statt „PGH“, „Gehr-häuser“ für ein langes „e“.
"""
import argparse
import os
import unicodedata
import wave

import numpy as np
from piper import PiperVoice, SynthesisConfig
from scipy.signal import butter, resample_poly, sosfilt

STIMMEN = os.path.expanduser("~/tools/piper-voices")
STANDARD_TEXT = """Guten Tag, Sie sind verbunden mit P G H Brandschutz, | 0.25
Patrick Gehr-häuser. | 0.6
Ich bin gerade bei einem Kunden und kann Ihren Anruf leider nicht persönlich annehmen. | 0.5
Bitte hinterlassen Sie nach dem Signalton Ihren Namen, Ihre Telefonnummer und kurz Ihr Anliegen. | 0.45
Ich rufe Sie so schnell wie möglich zurück. | 0.45
Vielen Dank für Ihren Anruf. | 0.3"""


def segmente(text):
    for zeile in text.strip().splitlines():
        teil, _, pause = zeile.partition("|")
        if teil.strip():
            yield teil.strip(), float(pause or 0.4)


def _laute(voice, satz):
    """Phonemisieren und abgetrennte Kombinationszeichen wieder zusammensetzen (z. B. c + ̧ → ç im „ich“),
    falls das Stimmmodell nur das zusammengesetzte Zeichen kennt – sonst spricht es „ik“ statt „ich“."""
    karte = voice.config.phoneme_id_map
    for satzlaute in voice.phonemize(satz):
        zusammen = []
        for p in satzlaute:
            if zusammen and unicodedata.combining(p) and p not in karte:
                verbunden = unicodedata.normalize("NFC", zusammen[-1] + p)
                if verbunden in karte:
                    zusammen[-1] = verbunden
                    continue
            zusammen.append(p)
        yield zusammen


def _sprechen(voice, satz, cfg):
    teile = [voice.phoneme_ids_to_audio(voice.phonemes_to_ids(l), cfg) for l in _laute(voice, satz)]
    return np.concatenate([np.asarray(t, dtype=np.float32).reshape(-1) for t in teile])


def synthese(stimme, text, tempo, sprecher):
    voice = PiperVoice.load(os.path.join(STIMMEN, f"{stimme}.onnx"))
    sid = voice.config.speaker_id_map.get(sprecher) if sprecher else None
    cfg = SynthesisConfig(speaker_id=sid, length_scale=tempo, noise_scale=0.6, noise_w_scale=0.75)
    rate = voice.config.sample_rate
    teile = [np.zeros(int(0.35 * rate), dtype=np.float32)]  # kurze Stille vor dem ersten Wort
    for satz, pause in segmente(text):
        audio = _sprechen(voice, satz, cfg)
        teile += [audio, np.zeros(int(pause * rate), dtype=np.float32)]
    return np.concatenate(teile), rate


def aufbereiten(audio, rate, ziel_rate):
    sos = butter(2, 120, btype="highpass", fs=rate, output="sos")       # Brummen/Atem unter 120 Hz weg
    audio = sosfilt(sos, audio)
    if ziel_rate != rate:
        g = np.gcd(rate, ziel_rate)
        audio = resample_poly(audio, ziel_rate // g, rate // g)          # mit Anti-Aliasing-Filter
    audio = audio / max(1e-9, np.max(np.abs(audio))) * 0.89              # Spitze auf -1 dBFS
    blende = int(0.01 * ziel_rate)
    audio[:blende] *= np.linspace(0, 1, blende)
    audio[-blende:] *= np.linspace(1, 0, blende)
    return (audio * 32767).astype(np.int16)


def schreiben(pfad, pcm, rate):
    with wave.open(pfad, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm.tobytes())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stimme", default="de_DE-thorsten-high")
    ap.add_argument("--sprecher", help="nur bei Mehrsprecher-Stimmen, z. B. neutral/amused bei thorsten_emotional")
    ap.add_argument("--tempo", type=float, default=1.12, help="length_scale: >1 = langsamer")
    ap.add_argument("--text-datei")
    ap.add_argument("--aus", required=True, help="FritzBox-Datei (8 kHz)")
    ap.add_argument("--vorschau", help="optional zusätzlich in Originalqualität")
    a = ap.parse_args()
    text = open(a.text_datei, encoding="utf-8").read() if a.text_datei else STANDARD_TEXT
    audio, rate = synthese(a.stimme, text, a.tempo, a.sprecher)
    schreiben(a.aus, aufbereiten(audio.copy(), rate, 8000), 8000)
    if a.vorschau:
        schreiben(a.vorschau, aufbereiten(audio.copy(), rate, rate), rate)
    sek = len(audio) / rate
    print(f"{a.aus}: {sek:.1f} s, 8000 Hz mono 16 bit" + ("  (über 60 s – FritzBox lehnt ab!)" if sek > 60 else ""))


if __name__ == "__main__":
    main()
