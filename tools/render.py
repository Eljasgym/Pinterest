#!/usr/bin/env python3
"""Baut Pinbilder aus pins/quelle.json und schreibt pins/pins.json.

python3 tools/render.py            alle fehlenden Bilder bauen
python3 tools/render.py hh-003     ein Bild neu bauen
python3 tools/render.py --alle     alle neu bauen

Braucht Google Chrome (headless) und Internet für die Schriften.
"""
import html, json, os, subprocess, sys, tempfile

HIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
SHOP = "https://elipen11.mymonat.com/de/{}/"
KONTO = "hashtag-hairs"

# Hintergründe ("Vibes"). Neue einfach hier ergänzen.
BG = {
    "leinen":    {"farbe": "#EEE4D6", "text": "#4A1832", "akzent": "#5C1E3E", "fein": "#7A5A66",
                  "ebene": "linear-gradient(118deg, transparent 0 18%, rgba(255,251,244,.75) 18% 24%, transparent 24% 33%, rgba(255,251,244,.75) 33% 39%, transparent 39% 48%, rgba(255,251,244,.7) 48% 54%, transparent 54%)",
                  "schatten": "rgba(120,90,70,.10)"},
    "aubergine": {"farbe": "#4A1832", "text": "#F6EDE6", "akzent": "#E9D7F0", "fein": "#D9C2CF",
                  "ebene": "radial-gradient(ellipse 60% 45% at 70% 72%, rgba(255,214,236,.22), transparent 70%)",
                  "schatten": "rgba(0,0,0,.18)"},
    "lavendel":  {"farbe": "#DDD5EC", "text": "#3F1730", "akzent": "#5C1E3E", "fein": "#6B5878",
                  "ebene": "linear-gradient(62deg, transparent 0 40%, rgba(250,246,255,.7) 40% 46%, transparent 46% 55%, rgba(250,246,255,.65) 55% 60%, transparent 60%), radial-gradient(ellipse 70% 50% at 80% 10%, rgba(255,255,255,.35), transparent 70%)",
                  "schatten": "rgba(70,50,100,.10)"},
    "marmor":    {"farbe": "#F2EFEB", "text": "#3F1730", "akzent": "#5C1E3E", "fein": "#7A6A70",
                  "ebene": "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='1000' height='1500'><filter id='f'><feTurbulence type='fractalNoise' baseFrequency='.006' numOctaves='3' seed='3'/><feColorMatrix values='0 0 0 0 .6  0 0 0 0 .58  0 0 0 0 .58  0 0 0 .9 -.25'/></filter><filter id='b'><feGaussianBlur stdDeviation='1.6'/></filter><rect width='100%' height='100%' filter='url(%23f)' opacity='.25'/><g fill='none' stroke='%23A89C9C' filter='url(%23b)' opacity='.55'><path stroke-width='3' d='M-40 380 C 180 300, 260 520, 470 470 S 760 300, 1060 420'/><path stroke-width='1.6' d='M300 460 C 360 600, 520 640, 600 820 S 820 1000, 1040 980'/><path stroke-width='2.4' d='M-40 1180 C 220 1100, 380 1260, 620 1180 S 900 1080, 1060 1140'/><path stroke-width='1.2' d='M620 1180 C 660 1300, 760 1380, 900 1540'/></g></svg>\")",
                  "schatten": "rgba(90,80,80,.10)"},
    "sand":      {"farbe": "#E7D3BE", "text": "#4A1832", "akzent": "#5C1E3E", "fein": "#7A5A50",
                  "ebene": "radial-gradient(circle at 50% 100%, #F1E4D5 0 38%, transparent 38.2%)",
                  "schatten": "rgba(120,80,50,.12)"},
}

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Bodoni+Moda:ital,opsz,wght@1,6..96,500&family=Jost:wght@400;500&display=block');
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:1000px;height:1500px;overflow:hidden}
body{background:var(--farbe);color:var(--text);font-family:Jost,sans-serif;position:relative}
.ebene{position:absolute;inset:0;background:var(--ebene);filter:blur(var(--blur,0px))}
.rahmen{position:absolute;inset:0;padding:84px 80px 70px;display:flex;flex-direction:column}
.kopfzeile{display:flex;justify-content:space-between;align-items:center;font-size:22px;letter-spacing:.32em;text-transform:uppercase;color:var(--fein)}
.werbung{border:1.5px solid var(--fein);border-radius:999px;padding:6px 16px;letter-spacing:.2em;font-size:18px}
h1{font-family:'Bodoni Moda',serif;font-style:italic;font-weight:500;font-size:86px;line-height:1.02;letter-spacing:-.01em;margin-top:70px;color:var(--akzent)}
.linie{width:90px;height:2px;background:var(--fein);margin:44px 0 40px;opacity:.6}
ol{list-style:none;counter-reset:n}
ol li{counter-increment:n;font-size:38px;line-height:1.25;padding:16px 0 16px 78px;position:relative;max-width:620px}
ol li::before{content:counter(n);position:absolute;left:0;top:12px;font-family:'Bodoni Moda',serif;font-style:italic;font-size:52px;line-height:1;color:var(--akzent)}
.routine li::before{content:counter(n);width:52px;height:52px;border:1.5px solid var(--akzent);border-radius:50%;display:flex;align-items:center;justify-content:center;font-family:Jost;font-style:normal;font-size:24px;top:14px}
.mf{max-width:640px}
.mf .lab{font-size:22px;letter-spacing:.3em;text-transform:uppercase;color:var(--fein);margin-bottom:12px}
.mf p{font-size:40px;line-height:1.28}
.mf .alt p{text-decoration:line-through;text-decoration-thickness:2px;text-decoration-color:var(--fein);opacity:.75}
.mf .neu{margin-top:48px}
.mf .neu p{font-weight:500}
.produkt{position:absolute;right:70px;bottom:150px;display:flex;flex-direction:column;align-items:center}
.produkt img{display:block;object-fit:contain;filter:drop-shadow(14px 18px 22px var(--schatten))}
.podest{width:340px;height:46px;margin-top:-22px;border-radius:50%;background:radial-gradient(ellipse at center, var(--schatten), transparent 70%)}
.fuss{position:absolute;left:80px;right:80px;bottom:62px;display:flex;justify-content:space-between;align-items:center;font-size:24px;color:var(--fein)}
.fuss b{font-weight:500;color:var(--akzent)}
.gross .produkt{left:0;right:0;bottom:340px}
.gross h1{text-align:center;margin-top:60px}
.gross .name{position:absolute;left:80px;right:80px;bottom:190px;text-align:center}
.gross .name div{font-size:30px;letter-spacing:.14em;text-transform:uppercase;font-weight:500;color:var(--akzent)}
.gross .name p{font-size:32px;margin-top:12px;color:var(--fein)}
.knopf{background:var(--akzent);color:var(--farbe);border-radius:999px;padding:16px 34px;font-size:24px;letter-spacing:.08em}
"""


def seite(pin):
    b = BG[pin["bg"]]
    e = html.escape
    vars_ = ";".join(f"--{k}:{v}" for k, v in b.items())
    blur = "--blur:14px" if pin["bg"] in ("leinen", "lavendel") else ""
    img = os.path.join(HIER, "assets/produkte", pin["produkt"] + ".png")
    f = pin["format"]
    if f == "produkt":
        inhalt = f"""<h1>{e(pin['kopf'])}</h1>
<div class="produkt"><img src="file://{img}" style="max-height:640px;max-width:620px"><div class="podest" style="width:460px"></div></div>
<div class="name"><div>{e(pin['name'])}</div><p>{e(pin['zeile'])}</p></div>"""
    else:
        if f == "liste":
            mitte = "<ol>" + "".join(f"<li>{e(p)}</li>" for p in pin["punkte"]) + "</ol>"
        elif f == "routine":
            mitte = '<ol class="routine">' + "".join(f"<li>{e(p)}</li>" for p in pin["schritte"]) + "</ol>"
        else:
            mitte = f"""<div class="mf"><div class="alt"><div class="lab">Mythos</div><p>{e(pin['mythos'])}</p></div>
<div class="neu"><div class="lab">Fakt</div><p>{e(pin['fakt'])}</p></div></div>"""
        inhalt = f"""<h1>{e(pin['kopf'])}</h1><div class="linie"></div>{mitte}
<div class="produkt"><img src="file://{img}" style="max-height:400px;max-width:380px"><div class="podest"></div></div>"""
    return f"""<!doctype html><html lang="de"><head><meta charset="utf-8"><style>{CSS}
body{{{vars_};{blur}}}</style></head>
<body class="{'gross' if f == 'produkt' else ''}"><div class="ebene"></div>
<div class="rahmen"><div class="kopfzeile"><span>Hashtag Hairs</span><span class="werbung">Werbung</span></div>{inhalt}</div>
<div class="fuss"><span>Mehr Haar-Tipps: <b>Hashtag Hairs</b></span><span class="knopf">Im Shop ansehen</span></div>
</body></html>"""


def baue(pin):
    ziel = os.path.join(HIER, "pins/bilder", pin["id"] + ".png")
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as t:
        t.write(seite(pin))
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--allow-file-access-from-files", "--force-device-scale-factor=1",
                    "--window-size=1000,1500", "--virtual-time-budget=8000",
                    f"--screenshot={ziel}", "file://" + t.name],
                   check=True, capture_output=True)
    os.unlink(t.name)
    print("gebaut", ziel)


def main():
    quelle = json.load(open(os.path.join(HIER, "pins/quelle.json"), encoding="utf-8"))
    alle = "--alle" in sys.argv
    nur = [a for a in sys.argv[1:] if not a.startswith("--")]
    for pin in quelle:
        bild = os.path.join(HIER, "pins/bilder", pin["id"] + ".png")
        if alle or pin["id"] in nur or (not nur and not os.path.exists(bild)):
            baue(pin)
    pins = [{"id": p["id"], "account": p.get("account", KONTO), "format": p["format"],
             "image": f"pins/bilder/{p['id']}.png", "title": p["title"], "text": p["text"],
             "link": SHOP.format(p["produkt"]), "alt": p["alt"]} for p in quelle]
    with open(os.path.join(HIER, "pins/pins.json"), "w", encoding="utf-8") as f:
        json.dump(pins, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(len(pins), "Pins in pins/pins.json")


if __name__ == "__main__":
    main()
