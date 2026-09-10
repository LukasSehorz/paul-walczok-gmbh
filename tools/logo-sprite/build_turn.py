"""Sprite der Bildmarke: Drehteller-Rotation wie im SOLIDWORKS-Video.

AUFRUF (erzeugt assets/img/logo-spin3d.webp, 120 Lagen, 11 Spalten, 168 px):
    python3 build_turn.py 120 11 168 ../../assets/img/logo-spin3d.webp
BRAUCHT ein venv mit: cadquery-ocp numpy pillow  (STEP-Import ueber OCCT).
Aendert sich Lagenzahl oder Spaltenzahl, muessen css/styles.css (.mark,
background-size) und js/main.js (LAGEN, SPALTEN) mitgezogen werden.

Aus der Bildschirmaufnahme (831 Einzelbilder, 30 fps) ausgemessen:
  - die Hoehe der Silhouette ist in jedem Bild identisch (103 px) -> das
    Bauteil wird NICHT gekippt, es dreht sich ausschliesslich um die
    senkrechte Achse
  - die Breite pendelt 182 -> 60 -> 182 px, dabei wechseln sich Vorder- und
    Rueckseite ab (Schwerpunkt 122 bzw. 145 px) -> volle 360-Grad-Umdrehungen,
    keine Pendelbewegung; eine Umdrehung dauert rund 4 s
  - Richtung: bei 5,5 s laeuft die Messtrommel (rechts) VOR dem Flansch, der
    Amboss (links) wird vom Flansch verdeckt -> die rechte Seite kommt auf
    den Betrachter zu. Im Renderer ist das negatives Gieren.

Lage 0 ist die Frontansicht (= Kundenlogo), Lage k ist um k * 360/N Grad
weitergedreht. N Lagen liegen als Raster in einer WebP-Datei.
"""
import sys
import os
import numpy as np
from PIL import Image

import mesh
import render3

STEP_DEG_SIGN = -1.0     # Drehrichtung aus dem Video (siehe oben)


def turn_scale(V, tile, margin=0.94):
    """Massstab, der fuer jede Drehlage passt.

    Bei reiner Y-Drehung bleibt die Hoehe konstant; die Breite ist hoechstens
    der doppelte groesste Radius um die Y-Achse. Ein Massstab fuer alle Lagen,
    sonst pumpt das Logo beim Drehen.
    """
    r_xz = np.sqrt(V[:, 0] ** 2 + V[:, 2] ** 2).max()
    h = V[:, 1].max() - V[:, 1].min()
    span = max(2.0 * r_xz, h)
    return tile * margin / span


def build(frames, cols, tile, out_webp, quality=86, contact=None):
    V, F = mesh.load_mesh()
    V = mesh.centered(V)                     # Drehachse durch die Bauteilmitte
    N = render3.vertex_normals(V, F)
    scale = turn_scale(V, tile)

    rows = (frames + cols - 1) // cols
    sheet = Image.new("RGBA", (tile * cols, tile * rows), (0, 0, 0, 0))
    drift_x = []
    for k in range(frames):
        yaw = STEP_DEG_SIGN * k * 360.0 / frames
        img = render3.render_frame(V, N, F, 0.0, yaw, 0.0, tile, scale, supersample=3)
        sheet.paste(img, ((k % cols) * tile, (k // cols) * tile))
        a = np.asarray(img)[:, :, 3]
        xs = np.nonzero(a.max(axis=0) > 8)[0]
        drift_x.append((xs.min() + xs.max()) / 2.0 - tile / 2.0)
        if k % 12 == 0:
            print("  Lage %3d/%d  yaw %+7.1f" % (k, frames, yaw), flush=True)

    sheet.save(out_webp, "WEBP", quality=quality, method=6, exact=True)
    drift_x = np.array(drift_x)
    print("Raster %dx%d, %dx%d px, %.0f KB" % (cols, rows, sheet.width, sheet.height,
                                              os.path.getsize(out_webp) / 1024))
    print("seitliche Drift der Silhouette: %+.1f .. %+.1f px bei Kachel %d (bei 84 px: %.2f px)"
          % (drift_x.min(), drift_x.max(), tile, (drift_x.max() - drift_x.min()) * 84 / tile))

    if contact:
        idx = list(range(0, frames, max(1, frames // 12)))
        strip = Image.new("RGBA", (tile * len(idx), tile), (8, 9, 11, 255))
        for i, k in enumerate(idx):
            x = (k % cols) * tile; y = (k // cols) * tile
            strip.alpha_composite(sheet.crop((x, y, x + tile, y + tile)), (i * tile, 0))
        strip.convert("RGB").resize((len(idx) * 140, 140), Image.LANCZOS).save(contact)
        print("Kontaktabzug:", contact)
    return sheet


if __name__ == "__main__":
    frames = int(sys.argv[1]) if len(sys.argv) > 1 else 72
    cols = int(sys.argv[2]) if len(sys.argv) > 2 else 9
    tile = int(sys.argv[3]) if len(sys.argv) > 3 else 200
    out = sys.argv[4] if len(sys.argv) > 4 else "logo-turn.webp"
    build(frames, cols, tile, out, contact=out.replace(".webp", "-contact.png"))
