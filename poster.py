#!/usr/bin/env python3
"""Plant Pins aus pins/pins.json in Buffer ein.

python3 poster.py            plant fällige Pins ein
python3 poster.py --dry-run  zeigt nur, was passieren würde
python3 poster.py boards     listet die Pinnwände jedes Accounts (für boardServiceId)

Braucht BUFFER_API_KEY in der Umgebung. Nur Standardbibliothek.
"""
import json, os, sys, urllib.request, urllib.error
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

HIER = os.path.dirname(os.path.abspath(__file__))
API = "https://api.buffer.com"
REPO = os.environ.get("GITHUB_REPOSITORY", "Eljasgym/Pinterest")
BILD_URL = f"https://raw.githubusercontent.com/{REPO}/main/"

# Regeln: keine Heilversprechen. Wörter, bei denen ein Pin abgelehnt wird.
VERBOTEN = ["heilt", "heilen", "garantiert", "wundermittel", "stoppt haarausfall",
            "100 % wirksam", "klinisch bewiesen", "vorher-nachher", "vorher nachher"]


def lade(name):
    with open(os.path.join(HIER, name), encoding="utf-8") as f:
        return json.load(f)


def speichere(name, daten):
    with open(os.path.join(HIER, name), "w", encoding="utf-8") as f:
        json.dump(daten, f, ensure_ascii=False, indent=2)
        f.write("\n")


def gql(query):
    key = os.environ.get("BUFFER_API_KEY")
    if not key:
        sys.exit("BUFFER_API_KEY fehlt.")
    req = urllib.request.Request(API, data=json.dumps({"query": query}).encode(),
                                 headers={"Authorization": f"Bearer {key}",
                                          "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            antwort = json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"Buffer HTTP {e.code}: {e.read().decode()[:500]}")
    if antwort.get("errors"):
        sys.exit(f"Buffer Fehler: {antwort['errors']}")
    return antwort["data"]


def s(text):
    """String für GraphQL sicher einbetten."""
    return json.dumps(text, ensure_ascii=False)


def pruefe(pin):
    fehler = []
    for feld in ("id", "account", "image", "title", "text", "link", "alt"):
        if not pin.get(feld):
            fehler.append(f"{feld} fehlt")
    gesamt = f"{pin.get('title', '')} {pin.get('text', '')}".lower()
    fehler += [f"verbotenes Wort: {w}" for w in VERBOTEN if w in gesamt]
    if pin.get("image") and not os.path.exists(os.path.join(HIER, pin["image"])):
        fehler.append(f"Bild fehlt: {pin['image']}")
    if len(pin.get("title", "")) > 100:
        fehler.append("Titel über 100 Zeichen")
    if len(pin.get("text", "")) > 500:
        fehler.append("Text über 500 Zeichen")
    return fehler


def mit_werbung(text):
    # Jeder Pin wird als Werbung gekennzeichnet, auch wenn es im Text vergessen wurde.
    return text if "#werbung" in text.lower() else f"{text}\n\n#werbung"


def naechste_slots(slots, tz, belegt, jetzt, tage=3):
    ergebnis = []
    heute = jetzt.astimezone(tz).date()
    for d in range(tage):
        tag = heute + timedelta(days=d)
        for hhmm in slots:
            h, m = map(int, hhmm.split(":"))
            t = datetime(tag.year, tag.month, tag.day, h, m, tzinfo=tz).astimezone(timezone.utc)
            if t > jetzt + timedelta(minutes=15) and t.isoformat() not in belegt:
                ergebnis.append(t)
    return ergebnis


def plane_ein(pin, konto, board, due, dry):
    text = mit_werbung(pin["text"])
    if dry:
        print(f"  [dry] {due:%d.%m. %H:%M} UTC  {pin['id']}  {pin['title']}")
        return "dry-run"
    q = f"""mutation {{ createPost(input: {{
      text: {s(text)}
      channelId: {s(konto['channelId'])}
      schedulingType: automatic
      mode: customScheduled
      dueAt: {s(due.strftime('%Y-%m-%dT%H:%M:%S.000Z'))}
      needsApproval: false
      assets: [{{ image: {{ url: {s(BILD_URL + pin['image'])}, metadata: {{ altText: {s(pin['alt'])} }} }} }}]
      metadata: {{ pinterest: {{ boardServiceId: {s(board)}, title: {s(pin['title'])}, url: {s(pin['link'])} }} }}
    }}) {{
      ... on PostActionSuccess {{ post {{ id }} }}
      ... on MutationError {{ message }}
    }} }}"""
    r = gql(q)["createPost"]
    if "message" in r:
        sys.exit(f"Pin {pin['id']} abgelehnt: {r['message']}")
    print(f"  {due:%d.%m. %H:%M} UTC  {pin['id']}  {pin['title']}")
    return r["post"]["id"]


def run(dry):
    cfg, pins, state = lade("config.json"), lade("pins/pins.json"), lade("state.json")
    tz = ZoneInfo(cfg["timezone"])
    jetzt = datetime.now(timezone.utc)
    posted = state["posted"]

    for name, konto in cfg["accounts"].items():
        if not konto.get("active"):
            continue
        eigene = {pid: p for pid, p in posted.items() if p["account"] == name}
        wartend = [p for p in eigene.values() if datetime.fromisoformat(p["due"]) > jetzt]
        frei = cfg["queueLimit"] - len(wartend)
        offen = [p for p in pins if p.get("account") == name and p.get("id") not in posted]
        print(f"{name}: {len(wartend)} in der Warteschlange, {len(offen)} Pins übrig")
        if frei <= 0 or not offen:
            continue
        slots = naechste_slots(konto["slots"], tz, {p["due"] for p in eigene.values()}, jetzt)
        slots = iter(slots[:frei])
        for pin in offen:
            fehler = pruefe(pin)
            if fehler:
                print(f"  übersprungen {pin.get('id')}: {', '.join(fehler)}")
                continue
            due = next(slots, None)
            if due is None:
                break
            board = pin.get("boardServiceId") or konto.get("boardServiceId")
            if not board and not dry:
                sys.exit(f"{name}: keine Pinnwand. Erst 'python3 poster.py boards', dann boardServiceId in config.json.")
            post_id = plane_ein(pin, konto, board, due, dry)
            if not dry:
                posted[pin["id"]] = {"account": name, "due": due.isoformat(), "postId": post_id}
                speichere("state.json", state)  # sofort, damit ein Abbruch nichts doppelt postet
        if len(offen) < 10:
            print(f"  Achtung: nur noch {len(offen)} Pins für {name} vorrätig.")


def boards():
    cfg = lade("config.json")
    for name, konto in cfg["accounts"].items():
        d = gql(f"""{{ channel(input: {{ id: {s(konto['channelId'])} }}) {{ name
          metadata {{ ... on PinterestMetadata {{ boards {{ name serviceId }} }} }} }} }}""")["channel"]
        print(f"{name} ({d['name']}):")
        for b in (d.get("metadata") or {}).get("boards", []):
            print(f"  {b['serviceId']}  {b['name']}")


if __name__ == "__main__":
    if "boards" in sys.argv:
        boards()
    else:
        run("--dry-run" in sys.argv)
