# Pinterest MONAT

Plant Pins für MONAT-Partnerlinks über Buffer (Free) auf Pinterest ein. Läuft als GitHub Action alle 4 Stunden.

## Dateien
- `pins/pins.json`: Liste der Pins, Reihenfolge = Postreihenfolge. Felder: `id` (eindeutig, nie wiederverwenden), `account` (Schlüssel aus `config.json`), `image` (Pfad im Repo, z. B. `pins/bilder/x.png`, 1000x1500), `title` (max 100), `text`, `link`, `alt`, optional `boardServiceId`, optional `format`.
- `pins/bilder/`: Pinbilder. Buffer holt sie beim Posten über raw.githubusercontent.com, deshalb müssen sie committet sein, bevor der Pin dran ist.
- `config.json`: Org, Zeitzone, Accounts mit `channelId`, `boardServiceId`, Uhrzeiten (`slots`).
- `state.json`: welcher Pin wann eingeplant wurde. Schreibt nur das Skript, die Action committet ihn.
- `poster.py`: nur Standardbibliothek. `--dry-run` zeigt nur an, `boards` listet die Pinnwand-IDs.

## Regeln im Code
- Jeder Text bekommt "#werbung", falls es fehlt. Text höchstens 500 Zeichen.
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
- Texte im Ton "Tipps an die Girls": duzen ("ihr", "Mädels"), persönlich, ein bis zwei Emojis, keine Heilversprechen. Hashtags in `tags` ohne #, render.py setzt `#werbung` immer als ersten Hashtag davor (Kennzeichnungspflicht, nicht ans Ende schieben).
- Zeilen variabel lang: dreizeilige Überschriften bei `mythos` drücken den Text ins Produkt, dann kürzen.

## Wöchentlicher Nachschub (Aufgabe "pinterest-nachschub", sonntags 18 Uhr)
1. `git pull`. Vorrat zählen: Pins in `pins/pins.json`, die nicht in `state.json` stehen. Ziel: Vorrat für 8 Tage = Slots pro Tag aus `config.json` mal 8, plus die Pins, die schon in Buffer warten, zählen nicht mit. Nur die Differenz bauen, höchstens 80.
2. Ab 11.12.2026 (Woche 3) `slots` in `config.json` auf 10 pro Tag erhöhen: 08:00 09:30 11:00 12:30 14:00 15:30 17:00 18:30 20:00 21:30. Wenn das schon so ist, nichts ändern.
3. Neue Einträge in `pins/quelle.json` anhängen, IDs fortlaufend (nächste freie `hh-0xx`). Vorher alle `kopf` lesen: kein Thema doppelt. Mischung der Formate, jeder fünfte `produkt`. Themen: Haarpflege, Styling, Kopfhaut, Locken, Jahreszeit (Winter: Heizungsluft, Mützenhaare, Kälte), Mythen. Ton und Hashtags wie bei den bisherigen Pins.
4. Jede Woche mindestens einen neuen Hintergrund in `BG` (render.py) ergänzen und für etwa ein Drittel der neuen Pins nutzen, Rest bunt aus den vorhandenen. Immer im MONAT-Look: ruhig, edel, Pflaume und helle Töne. Keine Fotos von Personen, kein Vorher-Nachher.
5. Produkte nur aus `assets/produkte/`. Ein neues Produkt nur mit offiziellem freigestelltem PNG von monatglobal.com, auf die Alpha-Box zugeschnitten, Quelle in `quellen.txt`, und Link `https://elipen11.mymonat.com/de/<slug>/` muss 200 liefern.
6. `python3 tools/render.py`, dann `python3 tools/vorschau.py <neue IDs>` und `vorschau.jpg` ansehen. Text darf nie ins Produkt laufen und nirgends abgeschnitten sein. Sonst Überschrift kürzen und mit `render.py <id>` neu bauen.
7. Prüfen: `set -a; . ~/.config/pinterest/.env; set +a; python3 poster.py --dry-run` darf keine "übersprungen" zeigen.
8. Committen ("Nachschub KW xx") und pushen. Die Action plant dann selbst ein.
