"""Rasterizer fuer die Bildmarke (numpy, ohne 3D-Engine).

Orthografische Projektion, z-Puffer, Gouraud-artige Schattierung ueber
Knotennormalen, damit Rundungen bei kleiner Kachel nicht facettig wirken.
Darstellung wie im SOLIDWORKS-Video des Kunden im Modus "schattiert mit
Kanten": gefuellter Koerper in den Akzentfarben der Seite (--accent /
--accent-hi) plus dunkle Kantenlinien.

Kanten (nur wenn render_frame je Dreieck die Flaechennummer bekommt):
  - neben Farbe und z-Puffer wird ein Flaechen-ID-Puffer gerastert
  - Linie = Pixel, dessen Nachbar zu einer ANDEREN B-Rep-Flaeche gehoert.
    Das trifft Bauteilkanten (Absatz, Fase, Gewindeflanke) und innere
    Umrisse (Spindel vor dem Buegel), aber nie die Dreiecksgrenzen innerhalb
    einer glatten Flaeche.
  - Flaechen, die tangential ineinanderlaufen, bekommen keine Linie (siehe
    line_table). Sonst liefe beim Drehen eine Naht ueber jeden Zylinder, den
    der STEP-Export in zwei Haelften teilt.
  - Die Aussenkontur (Nachbar leer) ist getrennt einstellbar: auf dem dunklen
    Navbar-Grund geht eine dunkle Kontur unter und frisst duenne Teile auf.
  - Linien passen sich an: jede Flaeche gibt hoechstens einen Teil ihrer
    oertlichen Breite an Linie her (siehe _edges). Gewinde und Raendel
    werden so zu feinen Strichen statt zu dunklen Klumpen.
  Alles passiert auf der Supersampling-Aufloesung; erst das Herunterrechnen
  macht daraus eine glatte, antialiasierte Linie.

pitch/yaw/roll sind vorhanden; build_turn.py nutzt nur yaw.
"""
import numpy as np
from PIL import Image


def _hex(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], dtype=np.float64)


ACCENT = _hex("#2E5BFF")      # --accent
ACCENT_HI = _hex("#7796FF")   # --accent-hi
# Schattenseite: gleicher Farbton wie --accent, nur dunkler. Vorher lief die
# Schattierung nur zwischen --accent und --accent-hi; beide haben Blau = 255,
# das Bauteil wirkte dadurch flach. Mit der dunkleren Stufe bekommt es Tiefe,
# die Farbwelt bleibt.
ACCENT_LO = _hex("#1D3AC6")

LIGHT = np.array([-0.40, 0.62, 0.68])
LIGHT = LIGHT / np.linalg.norm(LIGHT)

# Voreinstellung fuer render_frame. Linienbreiten in Kachelpixeln (bei
# Kachel 168 und Anzeige 84 px sind 2 Kachelpixel = 1 Anzeigepixel).
# build_turn.py uebergibt seine eigenen Werte.
STYLE = dict(
    lo=ACCENT_LO, mid=ACCENT, hi=ACCENT_HI,
    ambient=0.18,                  # Helligkeit der vom Licht abgewandten Seite
    line_rgb=_hex("#0C1648"),      # Kantenfarbe: dunkles Blau, kein Schwarz
    line_px=2.5, line_alpha=1.0,   # innere Kanten
    sil_rgb=None,                  # Aussenkontur: None = keine
    sil_px=0.0, sil_alpha=1.0,
    fit=0.5,                       # Flaeche gibt hoechstens die Haelfte ihrer Breite an Linie her
)


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


def _position_ids(V):
    """Gleiche Position = gleicher Knoten, egal aus welcher Flaeche."""
    q = np.round(V / 1e-4).astype(np.int64)
    _, vid = np.unique(q, axis=0, return_inverse=True)
    return vid.ravel()


def weld_normals(V, N, crease_deg=22.0):
    """Glaettet die Normalen an tangentialen Flaechengrenzen.

    mesh.py dupliziert die Knoten je Flaeche. An der Naht eines geteilten
    Zylinders hat deshalb jede Haelfte ihre eigene, leicht schiefe
    Randnormale, und die Schattierung springt dort sichtbar (beim Drehen
    wandert ein heller/dunkler Streifen mit). Knoten an derselben Position,
    deren Normalen weniger als crease_deg auseinanderliegen, bekommen die
    gemittelte Normale. Echte Kanten (Absatz, Fase) bleiben scharf.
    """
    vid = _position_ids(V)
    o = np.argsort(vid, kind="stable")
    vs = vid[o]
    acc = N.copy()
    cos_lim = np.cos(np.radians(crease_deg))
    d = 1
    while d < len(o):
        i, j = o[:-d], o[d:]
        same = vs[:-d] == vs[d:]
        if not same.any():
            break
        i, j = i[same], j[same]
        ok = np.einsum("ij,ij->i", N[i], N[j]) > cos_lim
        np.add.at(acc, i[ok], N[j[ok]])
        np.add.at(acc, j[ok], N[i[ok]])
        d += 1
    ln = np.linalg.norm(acc, axis=1)
    ok = ln > 1e-12
    acc[ok] /= ln[ok, None]
    return acc


def line_table(V, F, FID, N, crease_deg=22.0):
    """Welche Flaechenpaare bekommen eine Linie? -> bool-Matrix [a, b].

    Grundsatz: jede Grenze zwischen zwei Flaechen ist eine Linie. Ausnahme:
    zwei Flaechen, die sich eine Kante teilen und dort tangential
    ineinanderlaufen (Knick ueberall unter crease_deg). Das sind geteilte
    Zylinder und Verrundungen; SOLIDWORKS zeigt dort keine Kante.

    Der Knick wird an den gemeinsamen Knoten gemessen. mesh.py dupliziert die
    Knoten je Flaeche, deshalb hat jeder Randknoten eine Normale aus JEDER
    der beiden Flaechen. Beim Logo liegen alle Paare entweder unter 20 Grad
    (tangential, Rest ist Vernetzungsfehler) oder ueber 25 Grad (echte Kante:
    Fase 45, Gewinde 60, Absatz 90), dazwischen ist nichts. Daher 22 Grad.
    Paare, die sich nie beruehren (Verdeckung), bekommen immer eine Linie.
    """
    nf = int(FID.max()) + 1
    table = np.ones((nf, nf), dtype=bool)
    np.fill_diagonal(table, False)

    vid = _position_ids(V)

    # alle Dreieckskanten, sortiert nach dem Knotenpaar (ohne Richtung)
    a = np.concatenate([F[:, 0], F[:, 1], F[:, 2]])
    b = np.concatenate([F[:, 1], F[:, 2], F[:, 0]])
    t = np.concatenate([np.arange(len(F))] * 3)
    ka, kb = vid[a], vid[b]
    key = np.minimum(ka, kb).astype(np.int64) * (len(vid) + 1) + np.maximum(ka, kb)
    o = np.argsort(key, kind="stable")
    a, b, t, key = a[o], b[o], t[o], key[o]

    # Nachbarn in der Sortierung mit gleicher Kante, aber anderer Flaeche
    i = np.nonzero((key[:-1] == key[1:]) & (FID[t[:-1]] != FID[t[1:]]))[0]
    j = i + 1
    same = vid[a[i]] == vid[a[j]]            # gleiche Laufrichtung?
    a2 = np.where(same, a[j], b[j])
    b2 = np.where(same, b[j], a[j])
    c1 = np.einsum("ij,ij->i", N[a[i]], N[a2])
    c2 = np.einsum("ij,ij->i", N[b[i]], N[b2])
    ang = np.degrees(np.arccos(np.clip(np.minimum(c1, c2), -1.0, 1.0)))

    fa, fb = FID[t[i]], FID[t[j]]
    worst = np.zeros((nf, nf))
    np.maximum.at(worst, (fa, fb), ang)
    np.maximum.at(worst, (fb, fa), ang)
    touch = np.zeros((nf, nf), dtype=bool)
    touch[fa, fb] = True
    touch[fb, fa] = True
    table[touch & (worst < crease_deg)] = False
    return table


def fit_scale(V, size, margin=0.92):
    """Ein Massstab fuer ALLE Lagen: der groesste Radius um den Ursprung.

    Bei freiem Taumeln kann jede Richtung zur Bildebene werden, deshalb der
    volle 3D-Radius und nicht nur ein Achsenpaar. Sonst pumpt das Logo.
    """
    r = np.linalg.norm(V, axis=1).max()
    return (size * margin / 2.0) / r


def _dilate(m, r):
    """Verbreitert eine Maske um eine Kreisscheibe mit Radius r (Pixel)."""
    R = int(np.floor(r))
    if R <= 0:
        return m
    H, W = m.shape
    p = np.pad(m, R)
    out = np.zeros_like(m)
    for dy in range(-R, R + 1):
        for dx in range(-R, R + 1):
            if dx * dx + dy * dy <= r * r + 1e-9:
                out |= p[R + dy:R + dy + H, R + dx:R + dx + W]
    return out


def _local_width(ibuf, K):
    """Oertliche Breite der Flaeche an jedem Pixel (Pixel), hoechstens 2K+1.

    Erst der Abstand d zum naechsten Flaechenwechsel (1 am Rand, nach innen
    steigend, durch schrittweises Abtragen), dann innerhalb derselben Flaeche
    K Schritte lang das Maximum von d weitergereicht. Am Rand steht damit die
    halbe Dicke der Flaeche in der Naehe, Breite = 2 * Maximum - 1.

    Oertlich und nicht je Flaeche gemittelt, weil eine Flaeche an einer Stelle
    breit und an einer anderen ein Haarstrich sein kann (die Aussenrundung
    des Buegels: vorne breit, an der Seite nur 1 Pixel). Mit einer
    gemittelten Breite bekam der Haarstrich die volle Linie, und aus seinen
    einzelnen Pixeln wurden dunkle Perlen entlang der Kontur.
    """
    H, W = ibuf.shape
    pad = np.pad(ibuf, 1, constant_values=-2)
    c = pad[1:-1, 1:-1]
    nb = (pad[:-2, 1:-1], pad[2:, 1:-1], pad[1:-1, :-2], pad[1:-1, 2:])
    core = np.ones((H, W), dtype=bool)
    for n in nb:
        core &= n == c
    d = np.ones((H, W), dtype=np.int32)
    for _ in range(K):
        if not core.any():
            break
        d[core] += 1
        p = np.pad(core, 1, constant_values=False)
        core &= p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:]
    M = d
    for _ in range(K):
        pm = np.pad(M, 1, constant_values=0)
        new = M.copy()
        for n, m in zip(nb, (pm[:-2, 1:-1], pm[2:, 1:-1], pm[1:-1, :-2], pm[1:-1, 2:])):
            new = np.where(n == c, np.maximum(new, m), new)
        M = new
    return 2.0 * M - 1.0


def _spread(h, ibuf):
    """Deckkraft (0..1) einer Linie aus Halbbreiten an den Grenzpixeln.

    h: je Grenzpixel, wie weit die Linie von der Grenze aus in DIESE Flaeche
       hineinreicht (Pixel), sonst 0. Die Linie laeuft nur innerhalb der
       eigenen Flaeche weiter (Schritte gerade 1, schraeg 1,41), also nie
       ueber eine andere Kante hinweg. Das Ende wird weich: ein Pixel, das
       die Linie nur halb erreicht, bekommt halbe Deckkraft.
    """
    H, W = ibuf.shape
    B = np.where(h > 0, h - 0.5, -np.inf)
    ok = ibuf >= 0
    steps = [(-1, 0, 1.0), (1, 0, 1.0), (0, -1, 1.0), (0, 1, 1.0),
             (-1, -1, 1.414), (-1, 1, 1.414), (1, -1, 1.414), (1, 1, 1.414)]
    Ip = np.pad(ibuf, 1, constant_values=-2)
    for _ in range(int(np.ceil(h.max())) + 1 if h.size else 0):
        Bp = np.pad(B, 1, constant_values=-np.inf)
        new = B.copy()
        for dy, dx, cost in steps:
            nb = Bp[1 + dy:1 + dy + H, 1 + dx:1 + dx + W]
            same = ok & (Ip[1 + dy:1 + dy + H, 1 + dx:1 + dx + W] == ibuf)
            new = np.where(same, np.maximum(new, nb - cost), new)
        B = new
    return np.clip(B + 0.5, 0.0, 1.0) * ok


def _edges(ibuf, table, want_in, want_sil, fit):
    """Kantenlinien aus dem Flaechen-ID-Puffer (-1 = leer), als Deckkraft.

    want_in / want_sil: gewuenschte Breite innen / Aussenkontur (Pixel)
    fit: Anteil ihrer oertlichen Breite, den eine Flaeche an Linie hergibt.
    Eine Linie an der Grenze A|B ist zwei Haelften: die Haelfte in A ist
    hoechstens fit * (Breite von A) / 2 breit, die in B entsprechend. So
      - bekommen grosse Flaechen die volle Linie,
      - bleibt ein schmaler Streifen zwischen zwei grossen Flaechen sichtbar
        (der Buegel hochkant vor dem Gewinde): die Linien weichen auf die
        grossen Nachbarn aus, statt den Streifen zuzudecken,
      - werden Gewindeflanken und Raendel (nur schmale Flaechen) zu feinen
        Strichen statt zu einem dunklen Klumpen.
    """
    # so weit messen, dass grosse Flaechen sicher die volle Breite bekommen
    K = int(np.ceil(max(want_in, want_sil) / max(fit, 1e-6) / 2.0)) + 1
    lw = _local_width(ibuf, K)

    # Haarstriche direkt an der Aussenkontur zaehlen zur Kontur. Das sind
    # streifend gesehene Flaechen (Rand des Buegels von der Seite), die das
    # Raster nur als einzelne Pixel trifft. Als Flaeche behandelt, saessen
    # an jedem dieser Pixel Linienstuecke wie Perlen auf der Kontur.
    ids = ibuf.copy()
    ids[_dilate(ibuf < 0, 2.0) & (lw <= 3.0) & (ibuf >= 0)] = -1

    h_in = np.zeros(ibuf.shape)
    h_sil = np.zeros(ibuf.shape)
    half = np.minimum(want_in / 2.0, fit * lw / 2.0)   # Halbbreite je Pixel
    edge = np.minimum(want_sil, fit * lw)              # Kontur: einseitig
    for sp, sq in ((np.s_[:, :-1], np.s_[:, 1:]), (np.s_[:-1, :], np.s_[1:, :])):
        p, q = ids[sp], ids[sq]
        full_p, full_q = p >= 0, q >= 0
        both = full_p & full_q
        cut = both & table[np.where(both, p, 0), np.where(both, q, 0)]
        h_in[sp] = np.maximum(h_in[sp], np.where(cut, half[sp], 0.0))
        h_in[sq] = np.maximum(h_in[sq], np.where(cut, half[sq], 0.0))
        h_sil[sp] = np.maximum(h_sil[sp], np.where(full_p & ~full_q, edge[sp], 0.0))
        h_sil[sq] = np.maximum(h_sil[sq], np.where(full_q & ~full_p, edge[sq], 0.0))
    return _spread(h_in, ids), (_spread(h_sil, ids) if want_sil > 0 else None)


def render_frame(V, N, F, pitch, yaw, roll, size, scale, supersample=3,
                 fid=None, table=None, style=None):
    """Rendert eine Lage als RGBA-Bild size x size.

    fid/table: Flaechennummer je Dreieck und line_table(). Ohne beides gibt
    es keine Kanten, nur den schattierten Koerper.
    style: Farben und Linien, siehe STYLE oben (fehlende Schluessel von dort).
    """
    st = dict(STYLE)
    if style:
        st.update(style)

    S = size * supersample
    sc = scale * supersample

    M = _rz(roll) @ _rx(pitch) @ _ry(yaw)
    P = V @ M.T
    Nr = N @ M.T

    xs = P[:, 0] * sc + S / 2.0
    ys = -P[:, 1] * sc + S / 2.0
    zs = P[:, 2]

    # Beleuchtung je Knoten, dann ueber die Dreiecksflaeche interpoliert.
    # Drei Stufen: abgewandt -> ACCENT_LO, mittel -> --accent, zum Licht
    # gewandt -> --accent-hi.
    lam = np.clip(Nr @ LIGHT, 0.0, 1.0)
    shade = st["ambient"] + (1.0 - st["ambient"]) * lam
    t = np.clip(shade * 2.0, 0.0, 1.0)[:, None]
    u = np.clip(shade * 2.0 - 1.0, 0.0, 1.0)[:, None]
    vcol = np.where(shade[:, None] < 0.5,
                    st["lo"] * (1.0 - t) + st["mid"] * t,
                    st["mid"] * (1.0 - u) + st["hi"] * u)

    e1 = P[F[:, 1]] - P[F[:, 0]]
    e2 = P[F[:, 2]] - P[F[:, 0]]
    fn = np.cross(e1, e2)
    front = fn[:, 2] > 0.0

    rgb = np.zeros((S, S, 3), dtype=np.float64)
    alpha = np.zeros((S, S), dtype=bool)
    zbuf = np.full((S, S), -np.inf, dtype=np.float64)
    ibuf = np.full((S, S), -1, dtype=np.int32)       # Flaechen-ID-Puffer

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

        c0, c1, c2 = vcol[F[i, 0]], vcol[F[i, 1]], vcol[F[i, 2]]
        col = (w0[..., None] * c0 + w1[..., None] * c1 + w2[..., None] * c2)

        rgb[lo_y:hi_y + 1, lo_x:hi_x + 1][hit] = col[hit]
        alpha[lo_y:hi_y + 1, lo_x:hi_x + 1][hit] = True
        if fid is not None:
            ibuf[lo_y:hi_y + 1, lo_x:hi_x + 1][hit] = fid[i]

    if fid is not None:
        # Breiten in Supersampling-Pixeln = Kachelpixel * supersample.
        sil_px = st["sil_px"] if st["sil_rgb"] is not None else 0.0
        c_in, c_sil = _edges(ibuf, table, st["line_px"] * supersample,
                             sil_px * supersample, st["fit"])
        if st["line_px"] > 0:
            k = st["line_alpha"] * c_in[..., None]
            rgb = rgb * (1.0 - k) + st["line_rgb"] * k
        if c_sil is not None:
            k = st["sil_alpha"] * c_sil[..., None]
            rgb = rgb * (1.0 - k) + st["sil_rgb"] * k

    img = np.dstack([np.clip(rgb, 0, 255), alpha.astype(np.float64) * 255.0]).astype(np.uint8)
    out = Image.fromarray(img, mode="RGBA")
    if supersample > 1:
        out = out.resize((size, size), Image.LANCZOS)
    return out
