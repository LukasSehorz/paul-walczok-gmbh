"""STEP -> Dreiecksnetz (numpy).

Liest die Kundendatei 3d-logo.STEP, vernetzt sie mit OCCT und gibt die
Dreiecke als reine numpy-Arrays zurueck. Bewusst ohne cadquery: nur die
OCP-Bindings, die im venv liegen.

Rueckgabe von load_mesh():
    V  (n,3) float64  Knoten in Modellkoordinaten
    F  (m,3) int32    Dreiecksindizes, gegen den Uhrzeigersinn von aussen
"""
import numpy as np

from OCP.STEPControl import STEPControl_Reader
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_FACE, TopAbs_REVERSED
from OCP.TopoDS import TopoDS
from OCP.BRep import BRep_Tool
from OCP.TopLoc import TopLoc_Location

import os
# Die Kundendatei liegt ausserhalb des Repos (Unterlagen Kunden, eine Ebene
# ueber dem Projektordner). Ueberschreibbar per Umgebungsvariable LOGO_STEP.
STEP_PATH = os.environ.get("LOGO_STEP") or os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "..", "Unterlagen Kunden", "3d-logo.STEP"))


def load_mesh(path=STEP_PATH, deflection=0.12, angular=0.25):
    """Vernetzt das Modell und sammelt alle Faces zu einem Netz.

    deflection ist die Sehnentoleranz in mm. 0.12 bei 135 mm Bauteilgroesse
    ergibt an den Rundungen keine sichtbaren Facetten mehr, wenn das Bild am
    Ende nur 300 px breit ist.
    """
    reader = STEPControl_Reader()
    reader.ReadFile(path)
    reader.TransferRoots()
    shape = reader.OneShape()

    BRepMesh_IncrementalMesh(shape, deflection, False, angular, True)

    verts = []
    faces = []
    offset = 0

    exp = TopExp_Explorer(shape, TopAbs_FACE)
    while exp.More():
        face = TopoDS.Face(exp.Current())
        loc = TopLoc_Location()
        tri = BRep_Tool.Triangulation_s(face, loc)
        if tri is not None:
            trsf = loc.Transformation()
            n = tri.NbNodes()

            # Knoten in Weltkoordinaten bringen: die Location des Face ist
            # nicht zwingend die Identitaet.
            block = np.empty((n, 3), dtype=np.float64)
            for i in range(1, n + 1):
                p = tri.Node(i).Transformed(trsf)
                block[i - 1] = (p.X(), p.Y(), p.Z())
            verts.append(block)

            # REVERSED-Faces haben umgekehrte Umlaufrichtung. Ohne das Drehen
            # zeigen ihre Normalen nach innen und die Schattierung kippt.
            reversed_face = face.Orientation() == TopAbs_REVERSED
            for i in range(1, tri.NbTriangles() + 1):
                a, b, c = tri.Triangle(i).Get()
                if reversed_face:
                    a, c = c, a
                faces.append((a - 1 + offset, b - 1 + offset, c - 1 + offset))

            offset += n
        exp.Next()

    V = np.concatenate(verts, axis=0)
    F = np.asarray(faces, dtype=np.int32)
    return V, F


def centered(V):
    """Verschiebt das Netz so, dass die Bounding-Box-Mitte im Ursprung liegt."""
    lo = V.min(axis=0)
    hi = V.max(axis=0)
    return V - (lo + hi) / 2.0


if __name__ == "__main__":
    V, F = load_mesh()
    print("Knoten:", len(V), " Dreiecke:", len(F))
    print("BBox min", V.min(axis=0))
    print("BBox max", V.max(axis=0))
