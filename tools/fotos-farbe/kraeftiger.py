"""Fotos kraeftiger in der Farbe (Hinweise Homepage-2 des Kunden, 13.11.2026:
"Die Fotos duerfen dann schon kraeftig in der Farbe sein. Die sind jetzt eher
blass und farblos.").

Die Werkstattfotos sind von Haus aus grau (Metall, Maschinen, Hallenlicht),
auf der Seite liegt kein Filter darauf. Deshalb werden die Dateien selbst
bearbeitet, nicht per CSS-Filter: so sieht jedes Geraet dasselbe Bild.

Methode "Lebendigkeit" statt pauschaler Saettigung: blasse Farben gewinnen viel,
schon kraeftige kaum (sonst kippen die roten Lichtmaschinenhalter und die
Titan-Teile ins Grelle). Dazu etwas Kontrast und Helligkeit. Zweite Runde am
13.11.2026 (Lukas: "noch mal farbkraeftiger"): Staerke 1,0 -> 1,6. Die
endgueltigen Fotos kommen noch, dann neu einstellen. Grauwerte bleiben grau, es wird
keine Farbe erfunden.

Gelesen wird IMMER das Original aus dem Git-Stand vor der Bearbeitung
(ORIGINAL_REF), nie die schon bearbeitete Datei: ein zweiter Lauf mit anderen
Werten setzt also neu auf und verstaerkt nicht doppelt.

Aufruf im Projektordner:  python3 tools/fotos-farbe/kraeftiger.py
Braucht: numpy, pillow.
"""
import io, os, subprocess
import numpy as np
from PIL import Image

ORIGINAL_REF = "0742ca6"          # letzter Stand mit unbearbeiteten Fotos
STAERKE = 1.6                      # Lebendigkeit: s' = s * (1 + STAERKE * (1 - s)); 13.11. frueh 1.0
KONTRAST = 1.10                    # um die Bildmitte, sanft
HELL = 0.94                        # Gamma auf die Helligkeit, unter 1 = heller (Stimmung der Seite)
QUALITAET = 86

# Alle Fotos, die eine Seite wirklich zeigt. Nicht dabei: hero-poster.jpg
# (Standbild des Hero-Videos, muss zum Video passen).
FOTOS = """branche-automobil branche-luftfahrt branche-maschinenbau branche-medizintechnik
branche-motorsport branche-pruefinstitute cta-bg eigen-schraubstock eigen-schweisstisch
halle-dreherei halle-fraeserei halle-messraum leistung-cad leistung-drehen leistung-fraesen
leistung-laser leistung-schleifen leistung-zugproben-quer leistung-zugproben mp-fraeszentrum
mp-halle mp-materiallager mp-messtechnik mp-voreinstellung ref-baugruppe-q ref-bremstopf
ref-lima-nachher ref-lima-vorher ref-motorsport-2 ref-motorsport ref-riemenscheibe ref-titan-q
ref-zahnrad team-mitarbeiter""".split()

WURZEL = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))


def original(name):
    pfad = f"assets/img/{name}.jpg"
    roh = subprocess.run(["git", "show", f"{ORIGINAL_REF}:{pfad}"], cwd=WURZEL,
                         check=True, capture_output=True).stdout
    return Image.open(io.BytesIO(roh)).convert("RGB")


def kraeftiger(im):
    hsv = np.asarray(im.convert("HSV")).astype(np.float32) / 255
    s = hsv[..., 1]
    hsv[..., 1] = np.clip(s * (1 + STAERKE * (1 - s)), 0, 1)
    hsv[..., 2] = np.clip(hsv[..., 2] ** HELL, 0, 1)
    out = Image.fromarray((hsv * 255 + 0.5).astype(np.uint8), "HSV").convert("RGB")
    rgb = np.asarray(out).astype(np.float32)
    rgb = (rgb - 128) * KONTRAST + 128
    return Image.fromarray(np.clip(rgb + 0.5, 0, 255).astype(np.uint8), "RGB")


if __name__ == "__main__":
    for name in FOTOS:
        im = original(name)
        ziel = os.path.join(WURZEL, "assets", "img", f"{name}.jpg")
        kraeftiger(im).save(ziel, "JPEG", quality=QUALITAET, optimize=True, progressive=True)
        print(f"{name:26s} {os.path.getsize(ziel)//1024:5d} kB")
