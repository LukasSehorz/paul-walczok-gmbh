"""Bildmarke aus der Vektordatei des Kunden, in zwei Teilen (Bolzen und Buegel).

Quelle: ../../../Unterlagen Kunden/Patch Arbeitskleidung (Vektor).svg
(Patch der Arbeitskleidung, vom Kunden am 13.11.2026 geschickt).

Optik wie auf dem Patch: heller Koerper, blaue Linien. Auf dem Patch ist der
Grund weiss und die Flaechen sind deshalb "leer"; auf der dunklen Seite werden
sie hell gefuellt, sonst stuende die Marke als duenne Strichzeichnung da und
der Bolzen koennte den Buegel beim Drehen nicht verdecken.

Zwei Teile, weil sich die Marke beim Scrollen dreht (js/main.js): der Buegel
(Buegelmessschraube) schwenkt um die senkrechte Achse, der Bolzen in der Mitte
ist ein Drehteil und sieht aus jeder Richtung gleich aus, er bleibt stehen.

Ablauf je Teil:
 1. Pfade des Teils schwarz auf weiss mit Chrome in 4000 px zeichnen (render.js).
 2. "Aussen" ist alles, was vom Bildrand ohne Linie erreichbar ist, beim Buegel
    dazu die fuenf Bohrungen. Der Rest ist der Koerper.
 3. Koerper hell als Bild unter die Linien legen. Die Fuellung reicht bis in
    die Linien, nie darueber hinaus: die Aussenkante bildet allein die
    Vektorlinie, deshalb bleibt die Marke in jeder Groesse scharf.

Ergebnis in assets/img/:
  marke-bolzen.svg, marke-buegel.svg  (Kopfzeile, gleiche viewBox, deckungsgleich)
  marke-buegel-kante.svg              (19.11.2026: einfarbige Silhouette des
                                       Buegels in der Kantenfarbe, ohne Linien;
                                       daraus schichtet js/main.js die Dicke
                                       der Platte beim Drehen)
  logo-mark-vektor.svg                (beides zusammen: Fusszeile, Favicons)
Braucht: numpy, scipy, pillow; node mit puppeteer-core (siehe render.js).
"""
import base64, io, os, re, subprocess, tempfile
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HIER = os.path.dirname(os.path.abspath(__file__))
QUELLE = os.environ.get("PATCH_SVG") or os.path.normpath(os.path.join(
    HIER, "..", "..", "..", "Unterlagen Kunden", "Patch Arbeitskleidung (Vektor).svg"))
ZIEL = os.environ.get("ZIEL_DIR") or os.path.join(HIER, "..", "..", "assets", "img")

LINIE = os.environ.get("LINIE", "#1F4FD8")     # Blau der Linien
KOERPER = os.environ.get("KOERPER", "#F3F5F8") # helle Flaechen (--fg)
# Kantenfarbe: mittleres, helles Blau zwischen Koerper und Linie. Die
# Stirnseite der Platte soll beim Drehen als Band sichtbar sein, sich aber vom
# hellen Koerper und von den blauen Linien abheben.
KANTE = os.environ.get("KANTE", "#8FA3E3")
VB = (29.04, 60.28, 139.02, 89.82)   # Umriss der Marke im Patch + 0,6 Rand
ACHSE_X = 86.3                       # Drehachse = Mitte Bolzen = Mitte Buegelbogen
BOHRUNGEN = [(87.4, 138.9), (110.1, 132.3), (62.9, 132.1), (45.9, 115.0), (126.6, 115.0)]
RENDER_B = 4000
FUELL_B = 1400


def hexrgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


src = open(QUELLE, encoding="utf-8").read()
gruppe = src.split('<g class="cls-5">')[1].split("</g>")[0]
pfade = [p.replace('class="cls-1" ', "") for p in re.findall(r'<path class="cls-1" d="[^"]+"/>', gruppe)]
rechteck = re.search(r'<rect class="cls-1"[^>]+/>', src).group(0).replace('class="cls-1" ', "")
# Pfad 1 ist der Bolzen, Pfad 2 der Buegel, 3-7 die Bohrungen, 8 und das
# Rechteck zwei Striche an den Messflaechen.
TEILE = {
    "bolzen": ([pfade[0]], []),
    "buegel": (pfade[1:] + [rechteck], BOHRUNGEN),
}
vb = " ".join(str(v) for v in VB)


def fuellung(pfad_svg, loecher, tmp):
    schwarz = os.path.join(tmp, "s.svg"); png = os.path.join(tmp, "s.png")
    open(schwarz, "w").write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}"><g fill="#000">{pfad_svg}</g></svg>')
    subprocess.run(["node", os.path.join(HIER, "render.js"), schwarz, png, str(RENDER_B)], check=True)
    tinte = 1 - np.asarray(Image.open(png).convert("L")).astype(np.float32) / 255
    frei = tinte <= 0.5
    lab, _ = ndi.label(frei)
    H, W = frei.shape
    aussen_ids = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])).tolist()) - {0}
    for x, y in loecher:
        r = int((y - VB[1]) / VB[3] * H); c = int((x - VB[0]) / VB[2] * W)
        assert frei[r, c], f"Bohrung {x},{y} trifft eine Linie"
        aussen_ids.add(int(lab[r, c]))
    aussen = np.isin(lab, list(aussen_ids))
    innen = (~aussen) & frei
    assert innen.mean() > 0.02, "Teil hat keine geschlossene Flaeche"
    fuell = ndi.binary_dilation(innen, iterations=9) & (~aussen)
    h = round(H * FUELL_B / W)
    alpha = Image.fromarray((fuell * 255).astype(np.uint8)).resize((FUELL_B, h), Image.LANCZOS)
    bild = Image.new("RGBA", (FUELL_B, h), hexrgb(KOERPER) + (0,)); bild.putalpha(alpha)
    bild = bild.quantize(colors=16, method=Image.Quantize.FASTOCTREE)
    buf = io.BytesIO(); bild.save(buf, "PNG", optimize=True)
    # Silhouette fuer die Kante: Koerper plus Linien, Bohrungen bleiben offen
    sil = Image.fromarray(((fuell | (tinte > 0.5)) * 255).astype(np.uint8)).resize((FUELL_B, h), Image.LANCZOS)
    kante = Image.new("RGBA", (FUELL_B, h), hexrgb(KANTE) + (0,)); kante.putalpha(sil)
    kante = kante.quantize(colors=16, method=Image.Quantize.FASTOCTREE)
    kbuf = io.BytesIO(); kante.save(kbuf, "PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode(), base64.b64encode(kbuf.getvalue()).decode()


def ebene(b64, pfad_svg):
    return (f'<image x="{VB[0]}" y="{VB[1]}" width="{VB[2]}" height="{VB[3]}" preserveAspectRatio="none" '
            f'xlink:href="data:image/png;base64,{b64}"/>\n<g fill="{LINIE}">\n{pfad_svg}\n</g>')


def datei(name, inhalt, hinweis):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
           f'viewBox="{vb}" width="{VB[2]}" height="{VB[3]}">\n'
           f'<!-- Bildmarke der Paul Walczok GmbH, {hinweis}. Linien 1:1 aus der Vektordatei des\n'
           f'     Kunden (Patch Arbeitskleidung), Koerper {KOERPER}, Linien {LINIE}.\n'
           f'     Erzeugt mit tools/logo-vektor/build.py, nicht von Hand aendern. -->\n{inhalt}\n</svg>\n')
    ziel = os.path.join(ZIEL, name)
    open(ziel, "w", encoding="utf-8").write(svg)
    print(f"{name}: {len(svg)//1024} kB")


with tempfile.TemporaryDirectory() as tmp:
    eb, kanten = {}, {}
    for teil, (pf, loecher) in TEILE.items():
        ps = "\n".join(pf)
        b64, kanten[teil] = fuellung(ps, loecher, tmp)
        eb[teil] = ebene(b64, ps)
datei("marke-bolzen.svg", eb["bolzen"], "nur der Bolzen")
datei("marke-buegel.svg", eb["buegel"], "nur der Buegel")
datei("logo-mark-vektor.svg", eb["buegel"] + "\n" + eb["bolzen"], "ganz")
datei("marke-buegel-kante.svg",
      f'<image x="{VB[0]}" y="{VB[1]}" width="{VB[2]}" height="{VB[3]}" preserveAspectRatio="none" '
      f'xlink:href="data:image/png;base64,{kanten["buegel"]}"/>',
      f"Silhouette des Buegels in der Kantenfarbe {KANTE}, ohne Linien (Dicke beim Drehen)")
print(f"Drehachse bei {(ACHSE_X - VB[0]) / VB[2] * 100:.2f} % der Breite")
