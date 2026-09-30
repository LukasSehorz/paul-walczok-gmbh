"""Sprite der Bildmarke: Drehteller-Rotation wie im SOLIDWORKS-Video.

AUFRUF (erzeugt assets/img/logo-spin3d.webp, 120 Lagen, 11 Spalten, 168 px):
    python3 build_turn.py 120 11 168 ../../assets/img/logo-spin3d.webp
    optional als 5. Argument ein Stil aus STILE (Standard: STIL)
Der Kontaktabzug landet neben der WebP-Datei (*-contact.png) und gehoert
nicht ins Repo; am besten in einen Ordner ausserhalb bauen und nur die
WebP-Datei kopieren.
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

Darstellung "schattiert mit Kanten" wie im Video (Kundenwunsch 29.09.2026:
"kraeftigere Kanten"): dunkelblaue Linien an allen Grenzen zwischen
B-Rep-Flaechen, keine Linie auf der Aussenkontur. Warum ohne Aussenkontur:
auf dem dunklen Navbar-Grund (#111318) verschwindet eine dunkle Kontur im
Hintergrund, das Logo wirkt kleiner und duenne Teile (Spindel, Buegel
hochkant) werden aufgefressen. Die Kontur entsteht dort schon durch den
Kontrast Blau gegen Grund. Verglichen wurden die Stile in STILE.
"""
import sys
import os
import numpy as np
from PIL import Image

import mesh
import render3

STEP_DEG_SIGN = -1.0     # Drehrichtung aus dem Video (siehe oben)
ANZEIGE_PX = 84          # so gross zeigt die Navbar eine Kachel (CSS-Pixel)
SUPERSAMPLE = 4          # 4 statt 3: feinere Stufen fuer die Linienbreite

# Linienbreiten hier in Anzeigepixeln bei ANZEIGE_PX; build() rechnet sie in
# Kachelpixel um. line_rgb aus der Akzentfamilie, bewusst kein Schwarz.
STILE = {
    # feine Linie, eher Zeichnung als Umriss
    "fein": dict(line_px=1.0, line_rgb=render3._hex("#101A4A")),
    # kraeftige Linie: bei 84 px auf normalen Bildschirmen noch sicher
    # sichtbar, auf Retina (volle 168 px) klar wie im SOLIDWORKS-Video
    "kraeftig": dict(line_px=1.5, line_rgb=render3._hex("#0A1440")),
    # wie kraeftig, dazu eine helle Lichtkante auf der Aussenkontur.
    # Verworfen: doppelte Linie am Rand (hell aussen, dunkel innen) wirkt
    # unruhig und aufgeklebt
    "lichtkante": dict(line_px=1.25, line_rgb=render3._hex("#0C1648"),
                       sil_rgb=render3._hex("#A9BBFF"), sil_px=0.6, sil_alpha=0.85),
}
STIL = "kraeftig"
GRUND = (0x11, 0x13, 0x18, 255)   # Navbar-Hintergrund fuer den Kontaktabzug


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


def style_for(name, tile):
    """Stil aus STILE mit Linienbreiten in Kachelpixeln."""
    st = dict(STILE[name])
    k = tile / float(ANZEIGE_PX)
    for key in ("line_px", "sil_px"):
        if key in st:
            st[key] = st[key] * k
    return st


def build(frames, cols, tile, out_webp, quality=86, contact=None, stil=STIL):
    V, F, FID = mesh.load_mesh(face_ids=True)
    V = mesh.centered(V)                     # Drehachse durch die Bauteilmitte
    N = render3.vertex_normals(V, F)
    table = render3.line_table(V, F, FID, N)  # welche Flaechengrenzen eine Linie bekommen
    N = render3.weld_normals(V, N)            # keine Schattierungsnaht an geteilten Zylindern
    scale = turn_scale(V, tile)
    style = style_for(stil, tile)

    rows = (frames + cols - 1) // cols
    sheet = Image.new("RGBA", (tile * cols, tile * rows), (0, 0, 0, 0))
    drift_x = []
    for k in range(frames):
        yaw = STEP_DEG_SIGN * k * 360.0 / frames
        img = render3.render_frame(V, N, F, 0.0, yaw, 0.0, tile, scale,
                                   supersample=SUPERSAMPLE, fid=FID, table=table, style=style)
        sheet.paste(img, ((k % cols) * tile, (k // cols) * tile))
        a = np.asarray(img)[:, :, 3]
        xs = np.nonzero(a.max(axis=0) > 8)[0]
        drift_x.append((xs.min() + xs.max()) / 2.0 - tile / 2.0)
        if k % 12 == 0:
            print("  Lage %3d/%d  yaw %+7.1f" % (k, frames, yaw), flush=True)

    sheet.save(out_webp, "WEBP", quality=quality, method=6, exact=True)
    drift_x = np.array(drift_x)
    print("Stil %s, Raster %dx%d, %dx%d px, %.0f KB" % (stil, cols, rows, sheet.width, sheet.height,
                                                     os.path.getsize(out_webp) / 1024))
    print("seitliche Drift der Silhouette: %+.1f .. %+.1f px bei Kachel %d (bei 84 px: %.2f px)"
          % (drift_x.min(), drift_x.max(), tile, (drift_x.max() - drift_x.min()) * 84 / tile))

    if contact:
        # 12 Lagen nebeneinander auf dem Navbar-Grund, einmal in voller
        # Kachelgroesse (so sieht es ein Retina-Bildschirm) und einmal auf
        # ANZEIGE_PX verkleinert (so sieht es ein normaler Bildschirm).
        # Gelesen wird aus der gespeicherten WebP, also mit deren Verlusten.
        saved = Image.open(out_webp).convert("RGBA")
        idx = list(range(0, frames, max(1, frames // 12)))
        for size, path in ((tile, contact), (ANZEIGE_PX, contact.replace(".png", "-%d.png" % ANZEIGE_PX))):
            strip = Image.new("RGBA", (size * len(idx), size), GRUND)
            for i, k in enumerate(idx):
                x = (k % cols) * tile; y = (k // cols) * tile
                t = saved.crop((x, y, x + tile, y + tile))
                if size != tile:
                    t = t.resize((size, size), Image.LANCZOS)
                strip.alpha_composite(t, (i * size, 0))
            strip.convert("RGB").save(path)
            print("Kontaktabzug:", path)
    return sheet


if __name__ == "__main__":
    frames = int(sys.argv[1]) if len(sys.argv) > 1 else 72
    cols = int(sys.argv[2]) if len(sys.argv) > 2 else 9
    tile = int(sys.argv[3]) if len(sys.argv) > 3 else 200
    out = sys.argv[4] if len(sys.argv) > 4 else "logo-turn.webp"
    stil = sys.argv[5] if len(sys.argv) > 5 else STIL
    build(frames, cols, tile, out, contact=out.replace(".webp", "-contact.png"), stil=stil)
