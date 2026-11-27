# Pinterest MONAT

Plant Pins für MONAT-Partnerlinks über Buffer (Free) auf Pinterest ein. Läuft als GitHub Action alle 4 Stunden.

## Dateien
- `pins/pins.json`: Liste der Pins, Reihenfolge = Postreihenfolge. Felder: `id` (eindeutig, nie wiederverwenden), `account` (Schlüssel aus `config.json`), `image` (Pfad im Repo, z. B. `pins/bilder/x.png`, 1000x1500), `title` (max 100), `text`, `link`, `alt`, optional `boardServiceId`, optional `format`.
- `pins/bilder/`: Pinbilder. Buffer holt sie beim Posten über raw.githubusercontent.com, deshalb müssen sie committet sein, bevor der Pin dran ist.
- `config.json`: Org, Zeitzone, Accounts mit `channelId`, `boardServiceId`, Uhrzeiten (`slots`).
- `state.json`: welcher Pin wann eingeplant wurde. Schreibt nur das Skript, die Action committet ihn.
- `poster.py`: nur Standardbibliothek. `--dry-run` zeigt nur an, `boards` listet die Pinnwand-IDs.

## Regeln im Code
- Jeder Text bekommt "Werbung #werbung", falls das Wort fehlt.
- Wörter in `VERBOTEN` (Heilversprechen, Vorher-Nachher) lassen den Pin aus.
- Buffer Free hält nur 10 geplante Posts pro Kanal. Das Skript zählt über `state.json`, nicht über Buffer. Pins, die jemand von Hand in Buffer plant, zählt es nicht mit.

## Buffer API
- GraphQL `https://api.buffer.com`, `Authorization: Bearer <key>`. Key unter publish.buffer.com/settings/api, als Secret `BUFFER_API_KEY` im Repo.
- Pin: `createPost` mit `mode: customScheduled`, `dueAt`, `needsApproval: false`, `metadata.pinterest { boardServiceId title url }`. Ohne Pinnwand lehnt Pinterest ab.
- Free: 150 Anfragen je 15 min, 600 je Tag.

## Pins bauen
- Inhalte stehen in `pins/quelle.json` (Formate `liste`, `mythos`, `routine`, `produkt`, Hintergrund `bg`, Produkt-Slug `produkt`). `python3 tools/render.py` baut fehlende Bilder mit Chrome headless und schreibt daraus `pins/pins.json` neu. Nie `pins/pins.json` von Hand ändern.
- Hintergründe ("Vibes") im Dict `BG` in `tools/render.py`: leinen, aubergine, lavendel, marmor, sand. Neue Looks dort ergänzen.
- Produktbilder: offizielle, schon freigestellte PNGs von monatglobal.com, zugeschnitten in `assets/produkte/<slug>.png`, Quellen in `assets/produkte/quellen.txt`. Produkt selbst nie verändern.
- Link je Pin: `https://elipen11.mymonat.com/de/<slug>/`. Alle 42 Haarpflege-Slugs stehen im Shop unter `/de/products/?line=haircare` (Liste wird per JS geladen, nur im Browser auslesbar).
- Verhältnis 4 Mehrwert zu 1 Produkt: jeder fünfte Eintrag in `quelle.json` ist `produkt`.
- Zeilen variabel lang: dreizeilige Überschriften bei `mythos` drücken den Text ins Produkt, dann kürzen.
