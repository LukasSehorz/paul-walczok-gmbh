"""Bildbearbeitung mit GPT Image 2.6 ueber kie.ai (23.11.2026, Lukas' Auftrag).

Aufruf:  python3 kie_bild.py <ziel.png> <seitenverh.> <prompt-datei> <bild1> [<bild2> ...]
  seitenverh. z. B. 1:1, 3:4, 4:3
Die Eingabebilder werden zu kie.ai hochgeladen und als Bezug mitgegeben.
Schluessel aus ~/.config/kie/.env (nie ausgeben). Ein Bild in 2K kostet rund
10 bis 20 Credits. Ergebnis immer mit dem Original vergleichen: das Modell
darf nur den Hintergrund/Ausschnitt aendern, nie das Bauteil selbst.
"""
import base64, json, os, sys, time, urllib.request, urllib.parse

env = {}
for line in open(os.path.expanduser("~/.config/kie/.env")):
    if "=" in line:
        k, v = line.strip().split("=", 1); env[k] = v.strip().strip('"')
API = env.get("KIE_API", "https://api.kie.ai/api/v1")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"
HDR = {"Authorization": "Bearer " + env["KIE_API_KEY"], "Content-Type": "application/json", "User-Agent": UA}


def req(url, body=None):
    r = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None, headers=HDR,
                               method="POST" if body is not None else "GET")
    with urllib.request.urlopen(r, timeout=120) as f:
        return json.loads(f.read().decode())


def guthaben():
    return req(API + "/chat/credit").get("data")


def hochladen(pfad):
    mime = "image/png" if pfad.lower().endswith(".png") else "image/jpeg"
    b64 = base64.b64encode(open(pfad, "rb").read()).decode()
    r = req("https://kieai.redpandaai.co/api/file-base64-upload",
            {"base64Data": f"data:{mime};base64,{b64}", "uploadPath": "images/walczok", "fileName": os.path.basename(pfad)})
    url = (r.get("data") or {}).get("downloadUrl") or (r.get("data") or {}).get("fileUrl")
    if not url: raise RuntimeError("Upload fehlgeschlagen: " + json.dumps(r)[:300])
    return url


def bearbeiten(ziel, ar, prompt, bilder, res=os.environ.get("KIE_RES", "1K")):
    urls = [hochladen(b) for b in bilder]
    r = req(API + "/jobs/createTask", {"model": "gpt-image-2-6/sunburst-image-to-image",
            "input": {"prompt": prompt, "input_urls": urls, "aspect_ratio": ar, "resolution": res, "quality": "high"}})
    tid = (r.get("data") or {}).get("taskId")
    if not tid: raise RuntimeError("Auftrag abgelehnt: " + json.dumps(r, ensure_ascii=False)[:400])
    for _ in range(120):
        time.sleep(6)
        d = req(API + "/jobs/recordInfo?" + urllib.parse.urlencode({"taskId": tid}))["data"]
        if d["state"] == "success":
            u = json.loads(d["resultJson"])["resultUrls"][0]
            urllib.request.urlretrieve(u, ziel); return ziel
        if d["state"] in ("fail", "failed"):
            raise RuntimeError(f"fehlgeschlagen: {d.get('failCode')} {d.get('failMsg')}")
    raise RuntimeError("Zeitueberschreitung")


if __name__ == "__main__":
    ziel, ar, pdatei, *bilder = sys.argv[1:]
    vor = guthaben()
    bearbeiten(ziel, ar, open(pdatei, encoding="utf-8").read().strip(), bilder)
    print(f"fertig: {os.path.basename(ziel)} | Guthaben {vor} -> {guthaben()}", flush=True)
