"""Fotos vom Termin vor Ort (18.11.2026) fuer die Seite aufbereiten, 19.11.2026.

Quelle sind die Originale der DJI-Kamera unter
"Bilder & Videos/Bilder vor Ort 2026-11-18/" (nicht im Repo, .gitignore). Sie
werden nur GELESEN, nie veraendert. Gesucht wird ueber die vierstellige Nummer
im Dateinamen (DJI_<Zeit>_<NNNN>_D.JPG).

Rueckmeldung des Kunden zur letzten Runde: "Die Bilder sehen aus, als waere ein
Filter drauf, alles wirkt leblos." Deshalb bleiben diese Fotos NATUERLICH:
- kein Saettigungs- oder "Lebendigkeit"-Trick, kein Kontrast-Look;
- erlaubt ist nur die Grundkorrektur eines Fotografen: zu dunkle Aufnahmen
  leicht aufhellen (HELL < 1 hebt die Mitten, Lichter und Schatten bleiben),
  nach dem Verkleinern sauber nachschaerfen (bei jedem Bild gleich, mild);
- im Zweifel unbearbeitet (HELL = 1.0).

Jede Zeile der Tabelle BILDER beschreibt ein Bild der Seite:
  Zielname -> (Nummer, x0, y0, Breitenanteil, Seitenverhaeltnis, Zielbreite, HELL)
x0/y0/Breitenanteil sind Anteile am gedrehten Original (0..1); die Hoehe des
Ausschnitts folgt aus dem Seitenverhaeltnis (Breite/Hoehe). Liegt ein
Ausschnitt ausserhalb des Bildes, bricht das Skript ab statt still zu
verschieben. Ein zweiter Lauf erzeugt Byte fuer Byte dasselbe.

Standbilder aus Videos (Poster, Karriere) entstehen in videos.sh daneben.

Aufruf im Projektordner:  python3 tools/fotos-vor-ort/bauen.py
Braucht: pillow.
"""
import glob, os, sys
from PIL import Image, ImageOps, ImageFilter

WURZEL = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
QUELLE = os.path.join(WURZEL, "Bilder & Videos", "Bilder vor Ort 2026-11-18")
ZIEL = os.path.join(WURZEL, "assets", "img")
QUALITAET = 82

Q169, Q43, Q21, Q1610, Q11, Q12 = 16 / 9, 4 / 3, 2 / 1, 16 / 10, 1 / 1, 1 / 2

#            Zielname                  Nr.     x0    y0    Breite  Format  px    HELL
BILDER = {
    # Leistungen, Karten 4:3 (Korrekturrunde 1: hoeher als vorher 16:9;
    # am Handy zeigt die Karte 3:2 aus der Bildmitte)
    "vo-drehen":            ("0131", 0.12, 0.00, 0.75, Q43,  1000, 1.00),
    "vo-fraesen":           ("0123", 0.08, 0.00, 0.75, Q43,  1000, 1.00),
    "vo-laser":             ("0207", 0.12, 0.00, 0.75, Q43,  1000, 1.00),
    "vo-flachschleifen":    ("0157", 0.20, 0.00, 0.75, Q43,  1000, 1.00),
    "vo-rundschleifen":     ("0163", 0.10, 0.00, 0.75, Q43,  1000, 1.00),
    "vo-messen":            ("0169", 0.12, 0.00, 0.75, Q43,  1000, 1.00),
    "vo-zugproben":         ("0198", 0.14, 0.00, 0.75, Q43,  1000, 1.00),
    "vo-cad":               ("0177", 0.20, 0.00, 0.75, Q43,  1000, 0.90),   # Buero dunkler als die Halle
    # Laserschweissen, eigener Block
    "vo-laser-anlage":      ("0204", 0.00, 0.00, 1.00, Q169, 1400, 1.00),
    "vo-laser-kopf":        ("0206", 0.00, 0.00, 1.00, Q169, 1400, 1.00),
    # Unternehmen: Teamfoto gross, alle neun Personen ganz im Bild
    "vo-team":              ("0117", 0.14, 0.09, 0.76, Q21,  2000, 1.00),
    # Blick in die Halle, Karten 4:3
    "vo-halle-galerie":     ("0182", 0.00, 0.00, 0.75, Q43,  1000, 1.00),
    "vo-halle":             ("0186", 0.10, 0.00, 0.75, Q43,  1000, 0.92),
    "vo-saegerei":          ("0193", 0.00, 0.33, 1.00, Q43,  1000, 1.00),   # hochkant, Saege und Lager
    "vo-voreinstellung":    ("0172", 0.00, 0.40, 1.00, Q43,  1000, 1.00),   # hochkant, Werkzeug im Geraet
    "vo-halle-tor":         ("0112", 0.10, 0.00, 0.75, Q43,  1000, 1.00),
    # Kennzahlen-Hintergrund. Seit 23.11.2026 laeuft dort der Hallenfilm
    # (assets/video/vo-halle*.mp4), das Bild wird auf der Seite nicht mehr gezeigt.
    "vo-halle-weit":        ("0188", 0.00, 0.00, 1.00, Q169, 1920, 1.00),
    # Referenzen: Maschine und Teil, je Zeile ein 16:9- und ein 4:3-Bild
    "vo-ref-drehen":        ("0132", 0.00, 0.00, 1.00, Q169, 1100, 1.00),
    "vo-ref-scheibe":       ("0139", 0.10, 0.00, 0.75, Q43,  1000, 1.00),
    "vo-ref-fraesen":       ("0124", 0.15, 0.00, 0.75, Q43,  1000, 1.00),
    "vo-ref-arm":           ("0142", 0.05, 0.14, 0.86, Q169, 1100, 1.00),
    "vo-ref-flachschleifen":("0160", 0.00, 0.00, 1.00, Q169, 1100, 1.00),
    "vo-ref-magnetplatte":  ("0154", 0.00, 0.10, 1.00, Q43,  1000, 1.00),   # hochkant
    "vo-ref-messraum":      ("0168", 0.00, 0.00, 1.00, Q169, 1100, 1.00),
    "vo-ref-messuhr":       ("0171", 0.00, 0.17, 1.00, Q43,  1000, 1.00),   # hochkant
    # Flansch und Taschen-Bauteil: seit 23.11.2026 zeigt die Seite die KI-Fassungen
    # mit blauem Grund (assets/img/ki-ref-*.jpg, tools/ki-bilder/). Diese beiden
    # Ausschnitte sind nur noch die Vorlage dafuer und liegen nicht mehr in assets.
    # Referenz-Raster: Flansch auf weissem Tuch, quadratisch, ganz im Bild
    "vo-ref-flansch":       ("0149", 0.25, 0.00, 0.5625, Q11, 1000, 1.00),
    # Ersatz fuer den Bremsscheibentopf (Vignette, wirkte gefiltert). Korrekturrunde 2:
    # 0147 (hochkant) statt 0145, im Quadrat liegt das ganze Bauteil auf dem Tuch
    "vo-ref-taschen":       ("0147", 0.00, 0.232, 1.00, Q11, 1000, 1.00),
    # Kontakt: CAD-Arbeitsplatz, 16:10 (Korrekturrunde 1, vorher der Flansch)
    "vo-kontakt-cad":       ("0179", 0.10, 0.00, 0.90, Q1610, 1400, 0.95),
    # Eigenentwicklungen: je ein 16:10-Hauptfeld und zwei 4:3-Details.
    # 16:10, damit der Schweisstisch 0210 ganz von vorn ins Bild passt.
    "vo-tisch":             ("0210", 0.07, 0.00, 0.90, Q1610, 1200, 1.00),
    "vo-tisch-panel":       ("0212", 0.25, 0.00, 0.75, Q43,  900,  1.00),
    "vo-tisch-laser":       ("0205", 0.25, 0.00, 0.75, Q43,  900,  1.00),
    "vo-stock":             ("0231", 0.07, 0.00, 0.90, Q1610, 1200, 1.00),
    "vo-stock-2":           ("0233", 0.20, 0.00, 0.75, Q43,  900,  1.00),
    "vo-stock-3":           ("0228", 0.00, 0.38, 1.00, Q43,  900,  1.00),   # hochkant
    #   Gasflaschenwagen: hochkant, das Hauptfeld teilen sich drei schmale
    #   Hochformate 1:2 in voller Bildhoehe, so ist der Wagen ganz zu sehen
    "vo-wagen":             ("0220", 0.056, 0.00, 0.889, Q12, 520,  1.00),
    "vo-wagen-2":           ("0221", 0.111, 0.00, 0.889, Q12, 520,  1.00),   # Korrekturrunde 2: statt 0225 (Flasche oben angeschnitten)
    "vo-wagen-3":           ("0222", 0.00, 0.00, 0.889, Q12, 520,  1.00),
    "vo-wagen-rollen":      ("0224", 0.00, 0.05, 1.00, Q43,  900,  1.00),
    "vo-wagen-einsatz":     ("0203", 0.00, 0.00, 0.75, Q43,  900,  1.00),
}


def original(nr):
    treffer = glob.glob(os.path.join(QUELLE, f"DJI_*_{nr}_D.JPG"))
    if len(treffer) != 1:
        sys.exit(f"Original {nr}: {len(treffer)} Treffer")
    # exif_transpose: hochkant aufgenommene Fotos stehen danach richtig
    return ImageOps.exif_transpose(Image.open(treffer[0])).convert("RGB")


def aufhellen(im, gamma):
    """Mitten anheben, Schwarz und Weiss bleiben. Gleich auf allen drei Kanaelen,
    damit sich die Farbe nicht verschiebt."""
    if gamma == 1.0:
        return im
    lut = [round(255 * (i / 255) ** gamma) for i in range(256)]
    return im.point(lut * 3)


def bauen(name, nr, x0, y0, wanteil, fmt, px, hell):
    im = original(nr)
    W, H = im.size
    w = wanteil * W
    h = w / fmt
    box = (round(x0 * W), round(y0 * H), round(x0 * W + w), round(y0 * H + h))
    if box[2] > W + 1 or box[3] > H + 1:
        sys.exit(f"{name}: Ausschnitt {box} liegt ausserhalb von {W}x{H}")
    box = (box[0], box[1], min(box[2], W), min(box[3], H))
    im = im.crop(box)
    hoehe = round(px / fmt)
    im = im.resize((px, hoehe), Image.LANCZOS)
    im = aufhellen(im, hell)
    # Nach dem Verkleinern einmal mild nachschaerfen, wie ein Fotograf es tut
    im = im.filter(ImageFilter.UnsharpMask(radius=0.8, percent=45, threshold=2))
    ziel = os.path.join(ZIEL, f"{name}.jpg")
    # Ohne exif-Argument schreibt Pillow keine Kameradaten mit
    im.save(ziel, "JPEG", quality=QUALITAET, optimize=True, progressive=True)
    return ziel, im.size


if __name__ == "__main__":
    summe = 0
    for name, werte in BILDER.items():
        ziel, groesse = bauen(name, *werte)
        kb = os.path.getsize(ziel) / 1024
        summe += kb
        print(f"{name:24s} {werte[0]}  {groesse[0]:4d}x{groesse[1]:<4d} {kb:6.0f} kB")
    print(f"{'Summe':24s}            {summe:8.0f} kB")
