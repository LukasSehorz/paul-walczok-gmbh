"""Bildmarke fuer die Kopfzeile aus der Vektordatei des Kunden.

Quelle: ../../../Unterlagen Kunden/Patch Arbeitskleidung (Vektor).svg
(Patch der Arbeitskleidung, vom Kunden am 13.11.2026 geschickt, Hinweise
Homepage-2: das 3D-Logo wirkte "unrund").

Ablauf:
 1. Aus dem Patch nur die Bildmarke nehmen (alle Pfade der ersten Gruppe plus
    das kleine Rechteck am rechten Amboss, ohne Rahmen, Trennlinie und Text).
 2. Marke schwarz auf weiss mit Chrome in 4000 px Breite zeichnen (render.js).
 3. Flaechen bestimmen: alles, was vom Bildrand aus ohne Linie erreichbar ist,
    plus die fuenf Bohrungen im Buegel, ist "aussen" (durchsichtig). Der Rest
    ist der Koerper.
 4. Koerper im Akzentblau als Bild unter die Linien legen. Die Fuellung reicht
    bis in die Linien, nie darueber hinaus: die Aussenkante bildet allein die
    helle Vektorlinie, deshalb bleibt die Marke in jeder Groesse scharf.

Ergebnis: assets/img/logo-mark-vektor.svg
Braucht: numpy, scipy, pillow; node mit puppeteer-core (siehe render.js).
"""
import base64, io, os, re, subprocess, sys, tempfile
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HIER = os.path.dirname(os.path.abspath(__file__))
QUELLE = os.environ.get("PATCH_SVG") or os.path.normpath(os.path.join(
    HIER, "..", "..", "..", "Unterlagen Kunden", "Patch Arbeitskleidung (Vektor).svg"))
ZIEL = os.path.join(HIER, "..", "..", "assets", "img", "logo-mark-vektor.svg")

LINIE = "#F3F5F8"            # --fg
KOERPER = (0x2E, 0x5B, 0xFF)  # --accent
VB = (29.04, 60.28, 139.02, 89.82)   # Umriss der Marke im Patch + 0,6 Rand
BOHRUNGEN = [(87.4, 138.9), (110.1, 132.3), (62.9, 132.1), (45.9, 115.0), (126.6, 115.0)]
RENDER_B = 4000              # Rechenaufloesung
FUELL_B = 1000               # Aufloesung der Fuellung im Ergebnis

src = open(QUELLE, encoding="utf-8").read()
gruppe = src.split('<g class="cls-5">')[1].split("</g>")[0]
pfade = re.findall(r'<path class="cls-1" d="[^"]+"/>', gruppe)
rechteck = re.search(r'<rect class="cls-1"[^>]+/>', src).group(0)
koerper_svg = "\n".join(p.replace('class="cls-1" ', "") for p in pfade + [rechteck])
vb = " ".join(str(v) for v in VB)

with tempfile.TemporaryDirectory() as tmp:
    schwarz = os.path.join(tmp, "schwarz.svg")
    open(schwarz, "w").write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}"><g fill="#000">{koerper_svg}</g></svg>')
    png = os.path.join(tmp, "schwarz.png")
    subprocess.run(["node", os.path.join(HIER, "render.js"), schwarz, png, str(RENDER_B)], check=True)
    tinte = 1 - np.asarray(Image.open(png).convert("L")).astype(np.float32) / 255

frei = tinte <= 0.5
lab, _ = ndi.label(frei)
H, W = frei.shape
aussen_ids = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])).tolist()) - {0}
for x, y in BOHRUNGEN:
    r = int((y - VB[1]) / VB[3] * H); c = int((x - VB[0]) / VB[2] * W)
    assert frei[r, c], f"Bohrung {x},{y} trifft eine Linie"
    aussen_ids.add(int(lab[r, c]))
aussen = np.isin(lab, list(aussen_ids))
innen = (~aussen) & frei
fuell = ndi.binary_dilation(innen, iterations=9) & (~aussen)

h = round(H * FUELL_B / W)
alpha = Image.fromarray((fuell * 255).astype(np.uint8)).resize((FUELL_B, h), Image.LANCZOS)
bild = Image.new("RGBA", (FUELL_B, h), KOERPER + (0,)); bild.putalpha(alpha)
bild = bild.quantize(colors=16, method=Image.Quantize.FASTOCTREE)
buf = io.BytesIO(); bild.save(buf, "PNG", optimize=True)
b64 = base64.b64encode(buf.getvalue()).decode()

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="{vb}" width="{VB[2]}" height="{VB[3]}">
<!-- Bildmarke der Paul Walczok GmbH. Linien 1:1 aus der Vektordatei des Kunden
     (Patch Arbeitskleidung, 13.11.2026), Dunkel-Version: Koerper {'#%02X%02X%02X' % KOERPER},
     Linien {LINIE}. Erzeugt mit tools/logo-vektor/build.py, nicht von Hand aendern. -->
<image x="{VB[0]}" y="{VB[1]}" width="{VB[2]}" height="{VB[3]}" preserveAspectRatio="none" xlink:href="data:image/png;base64,{b64}"/>
<g fill="{LINIE}">
{koerper_svg}
</g>
</svg>
'''
open(ZIEL, "w", encoding="utf-8").write(svg)
print(f"{os.path.normpath(ZIEL)}: {len(svg)//1024} kB (Fuellung {len(buf.getvalue())//1024} kB)")
