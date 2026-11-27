#!/usr/bin/env python3
"""Kontaktbogen der Pinbilder zum Prüfen: python3 tools/vorschau.py hh-016 hh-017 ...
Ohne IDs: die 15 neuesten. Schreibt vorschau.jpg (nicht eingecheckt)."""
import os, sys
from PIL import Image

HIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ordner = os.path.join(HIER, "pins/bilder")
ids = sys.argv[1:] or sorted(f[:-4] for f in os.listdir(ordner) if f.endswith(".png"))[-15:]
b, h, spalten = 250, 375, 5
zeilen = (len(ids) + spalten - 1) // spalten
bogen = Image.new("RGB", (spalten * b + (spalten + 1) * 10, zeilen * h + (zeilen + 1) * 10), "white")
for i, pid in enumerate(ids):
    bild = Image.open(os.path.join(ordner, pid + ".png")).convert("RGB").resize((b, h))
    bogen.paste(bild, (10 + (i % spalten) * (b + 10), 10 + (i // spalten) * (h + 10)))
bogen.save(os.path.join(HIER, "vorschau.jpg"), quality=85)
print("vorschau.jpg mit", len(ids), "Pins")
