"""Farbe der aelteren Fotos, die auf der Seite bleiben (Stand 19.11.2026).

Geschichte: Am 13.11.2026 wollte der Kunde kraeftigere Fotos ("eher blass und
farblos"), damals wurden alle Fotos mit "Lebendigkeit" Staerke 1,6, Kontrast
1,10 und Gamma 0,94 aufgedreht. Am 19.11.2026 kam die Gegenrueckmeldung: "Die
Bilder sehen aus, als waere ein Filter drauf, alles wirkt leblos." Seitdem
stehen fast ueberall echte Fotos vom Termin vor Ort (tools/fotos-vor-ort/,
ohne Farbtrick). Die Fotos hier bleiben, weil es dafuer noch keinen Ersatz
gibt: Lichtmaschinenhalter vorher/nachher, die sechs Referenzteile und die
sechs Branchenbilder (Riemenrad, Baugruppe, Zahnrad und Bremsscheibentopf sind
inzwischen entfallen). Sie werden jetzt zurueckhaltend und natuerlich
eingestellt, damit sie neben den neuen Fotos nicht kuenstlich wirken:
Lebendigkeit hoechstens 0,6, Kontrast 1,03, keine Aufhellung per Gamma.

Ausnahme Branchenbilder: Sie sind sehr dunkel (Mittelwert um 40 von 255) und
deutlich blaustichig. Dort hebt ein Gamma die Mitten moderat an, und der
Blaustich wird zur Haelfte neutralisiert (Kanalmittel von Rot und Blau halb
an Gruen angeglichen). Schwarz bleibt schwarz, es wird keine Farbe erfunden.
(Kurz entfallen in Korrekturrunde 1, auf Kundenwunsch am 19.11.2026 zurueck.)

Methode "Lebendigkeit" statt pauschaler Saettigung: blasse Farben gewinnen,
schon kraeftige kaum. Grauwerte bleiben grau.

Gelesen wird IMMER das Original aus dem Git-Stand vor der Bearbeitung
(ORIGINAL_REF), nie die schon bearbeitete Datei: ein zweiter Lauf setzt neu
auf und verstaerkt nicht doppelt.

Aufruf im Projektordner:  python3 tools/fotos-farbe/kraeftiger.py
Braucht: numpy, pillow.
"""
import io, os, subprocess
import numpy as np
from PIL import Image

ORIGINAL_REF = "0742ca6"          # letzter Stand mit unbearbeiteten Fotos
QUALITAET = 86

# Foto -> (Lebendigkeit, Kontrast, Gamma, Anteil Farbstich-Ausgleich)
# Gamma unter 1 hebt die Mitten an; 1.0 = keine Aufhellung.
NATUERLICH = (0.6, 1.03, 1.00, 0.0)
BRANCHE    = (0.4, 1.03, 0.72, 0.5)   # Runde 3: Gamma 0,78 -> 0,72, etwas heller

# Alle aelteren Fotos, die eine Seite noch zeigt (Stand 19.11.2026, Runde 3:
# die Branchenbilder sind auf Kundenwunsch zurueck; Riemenrad, Komplett-
# baugruppe, Zahnrad und Bremsscheibentopf bleiben entfallen).
# 23.11.2026: ref-lima-*, ref-titan-q und ref-motorsport-2 zeigt die Seite nicht
# mehr (ersetzt durch die KI-Fassungen ki-ref-*.jpg mit blauem Grund). Die
# Eintraege bleiben, falls die Originale wieder gebraucht werden.
FOTOS = {
    "ref-lima-vorher": NATUERLICH, "ref-lima-nachher": NATUERLICH,
    "ref-titan-q": NATUERLICH, "ref-motorsport-2": NATUERLICH,
    "branche-automobil": BRANCHE, "branche-motorsport": BRANCHE,
    "branche-luftfahrt": BRANCHE, "branche-maschinenbau": BRANCHE,
    "branche-pruefinstitute": BRANCHE, "branche-medizintechnik": BRANCHE,
}

WURZEL = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))


def original(name):
    pfad = f"assets/img/{name}.jpg"
    roh = subprocess.run(["git", "show", f"{ORIGINAL_REF}:{pfad}"], cwd=WURZEL,
                         check=True, capture_output=True).stdout
    return Image.open(io.BytesIO(roh)).convert("RGB")


def einstellen(im, staerke, kontrast, gamma, ausgleich):
    rgb = np.asarray(im).astype(np.float32) / 255
    if ausgleich:
        m = rgb.reshape(-1, 3).mean(0)
        faktor = 1 + ausgleich * (m[1] / m - 1)          # Rot und Blau Richtung Gruen
        rgb = np.clip(rgb * faktor, 0, 1)
    if gamma != 1.0:
        rgb = rgb ** gamma                                 # gleich auf allen Kanaelen
    im = Image.fromarray((rgb * 255 + 0.5).astype(np.uint8), "RGB")
    hsv = np.asarray(im.convert("HSV")).astype(np.float32) / 255
    s = hsv[..., 1]
    hsv[..., 1] = np.clip(s * (1 + staerke * (1 - s)), 0, 1)
    out = np.asarray(Image.fromarray((hsv * 255 + 0.5).astype(np.uint8), "HSV").convert("RGB")).astype(np.float32)
    out = (out - 128) * kontrast + 128
    return Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8), "RGB")


if __name__ == "__main__":
    for name, werte in FOTOS.items():
        ziel = os.path.join(WURZEL, "assets", "img", f"{name}.jpg")
        einstellen(original(name), *werte).save(ziel, "JPEG", quality=QUALITAET, optimize=True, progressive=True)
        print(f"{name:26s} {os.path.getsize(ziel)//1024:5d} kB")
