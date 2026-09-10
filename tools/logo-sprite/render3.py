"""Rasterizer fuer die Bildmarke (numpy, ohne 3D-Engine).

Orthografische Projektion, z-Puffer, Gouraud-artige Schattierung ueber
Knotennormalen, damit Rundungen bei kleiner Kachel nicht facettig wirken.
Darstellung: gefuellter Koerper wie im SOLIDWORKS-Video des Kunden,
eingefaerbt in die Akzentfarben der Seite (--accent / --accent-hi).
pitch/yaw/roll sind vorhanden; build_turn.py nutzt nur yaw.
"""
import numpy as np
from PIL import Image

ACCENT = np.array([0x2E, 0x5B, 0xFF], dtype=np.float64)
ACCENT_HI = np.array([0x77, 0x96, 0xFF], dtype=np.float64)

LIGHT = np.array([-0.40, 0.62, 0.68])
LIGHT = LIGHT / np.linalg.norm(LIGHT)


def _rx(d):
    a = np.radians(d); c, s = np.cos(a), np.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def _ry(d):
    a = np.radians(d); c, s = np.cos(a), np.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def _rz(d):
    a = np.radians(d); c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def vertex_normals(V, F):
    """Knotennormalen aus flaechengewichteten Dreiecksnormalen."""
    N = np.zeros_like(V)
    e1 = V[F[:, 1]] - V[F[:, 0]]
    e2 = V[F[:, 2]] - V[F[:, 0]]
    fn = np.cross(e1, e2)          # Laenge = 2 * Flaeche, also automatisch gewichtet
    for k in range(3):
        np.add.at(N, F[:, k], fn)
    ln = np.linalg.norm(N, axis=1)
    ok = ln > 1e-12
    N[ok] /= ln[ok, None]
    return N


def fit_scale(V, size, margin=0.92):
    """Ein Massstab fuer ALLE Lagen: der groesste Radius um den Ursprung.

    Bei freiem Taumeln kann jede Richtung zur Bildebene werden, deshalb der
    volle 3D-Radius und nicht nur ein Achsenpaar. Sonst pumpt das Logo.
    """
    r = np.linalg.norm(V, axis=1).max()
    return (size * margin / 2.0) / r


def render_frame(V, N, F, pitch, yaw, roll, size, scale, supersample=3):
    S = size * supersample
    sc = scale * supersample

    M = _rz(roll) @ _rx(pitch) @ _ry(yaw)
    P = V @ M.T
    Nr = N @ M.T

    xs = P[:, 0] * sc + S / 2.0
    ys = -P[:, 1] * sc + S / 2.0
    zs = P[:, 2]

    # Beleuchtung je Knoten, dann ueber die Dreiecksflaeche interpoliert.
    lam = np.clip(Nr @ LIGHT, 0.0, 1.0)
    shade = 0.26 + 0.74 * lam
    vcol = ACCENT[None, :] * (1.0 - shade[:, None]) + ACCENT_HI[None, :] * shade[:, None]

    e1 = P[F[:, 1]] - P[F[:, 0]]
    e2 = P[F[:, 2]] - P[F[:, 0]]
    fn = np.cross(e1, e2)
    front = fn[:, 2] > 0.0

    rgb = np.zeros((S, S, 3), dtype=np.float64)
    alpha = np.zeros((S, S), dtype=bool)
    zbuf = np.full((S, S), -np.inf, dtype=np.float64)

    tx, ty, tz = xs[F], ys[F], zs[F]

    for i in np.nonzero(front)[0]:
        x0, x1, x2 = tx[i]; y0, y1, y2 = ty[i]; z0, z1, z2 = tz[i]

        lo_x = int(np.floor(min(x0, x1, x2))); hi_x = int(np.ceil(max(x0, x1, x2)))
        lo_y = int(np.floor(min(y0, y1, y2))); hi_y = int(np.ceil(max(y0, y1, y2)))
        if hi_x < 0 or hi_y < 0 or lo_x >= S or lo_y >= S:
            continue
        lo_x = max(lo_x, 0); hi_x = min(hi_x, S - 1)
        lo_y = max(lo_y, 0); hi_y = min(hi_y, S - 1)
        if lo_x > hi_x or lo_y > hi_y:
            continue

        gx, gy = np.meshgrid(np.arange(lo_x, hi_x + 1) + 0.5,
                             np.arange(lo_y, hi_y + 1) + 0.5)

        d = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if abs(d) < 1e-12:
            continue
        w0 = ((y1 - y2) * (gx - x2) + (x2 - x1) * (gy - y2)) / d
        w1 = ((y2 - y0) * (gx - x2) + (x0 - x2) * (gy - y2)) / d
        w2 = 1.0 - w0 - w1

        inside = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
        if not inside.any():
            continue

        z = w0 * z0 + w1 * z1 + w2 * z2
        sub_z = zbuf[lo_y:hi_y + 1, lo_x:hi_x + 1]
        hit = inside & (z > sub_z)
        if not hit.any():
            continue
        sub_z[hit] = z[hit]
        zbuf[lo_y:hi_y + 1, lo_x:hi_x + 1] = sub_z

        c0, c1, c2 = vcol[F[i, 0]], vcol[F[i, 1]], vcol[F[i, 2]]
        col = (w0[..., None] * c0 + w1[..., None] * c1 + w2[..., None] * c2)

        sub_rgb = rgb[lo_y:hi_y + 1, lo_x:hi_x + 1]
        sub_rgb[hit] = col[hit]
        rgb[lo_y:hi_y + 1, lo_x:hi_x + 1] = sub_rgb

        sub_a = alpha[lo_y:hi_y + 1, lo_x:hi_x + 1]
        sub_a[hit] = True
        alpha[lo_y:hi_y + 1, lo_x:hi_x + 1] = sub_a

    img = np.dstack([np.clip(rgb, 0, 255), alpha.astype(np.float64) * 255.0]).astype(np.uint8)
    out = Image.fromarray(img, mode="RGBA")
    if supersample > 1:
        out = out.resize((size, size), Image.LANCZOS)
    return out
