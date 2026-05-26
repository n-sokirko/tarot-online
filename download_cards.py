"""Download all 78 Rider-Waite card images from Wikimedia Commons."""
import json
import os
import time
import urllib.request
import urllib.parse
from pathlib import Path

WIKIMEDIA_API = "https://commons.wikimedia.org/w/api.php"
CARDS_JSON = Path(__file__).parent / "data" / "deck" / "rider-waite.json"
OUT_DIR = Path(__file__).parent / "frontend" / "public" / "cards"

# Major Arcana Wikimedia SVG filenames (number → filename stem)
MAJOR_NAMES = {
    0:  "RWS Tarot 00 Fool",
    1:  "RWS Tarot 01 Magician",
    2:  "RWS Tarot 02 High Priestess",
    3:  "RWS Tarot 03 Empress",
    4:  "RWS Tarot 04 Emperor",
    5:  "RWS Tarot 05 Hierophant",
    6:  "RWS Tarot 06 Lovers",
    7:  "RWS Tarot 07 Chariot",
    8:  "RWS Tarot 08 Strength",
    9:  "RWS Tarot 09 Hermit",
    10: "RWS Tarot 10 Wheel of Fortune",
    11: "RWS Tarot 11 Justice",
    12: "RWS Tarot 12 Hanged Man",
    13: "RWS Tarot 13 Death",
    14: "RWS Tarot 14 Temperance",
    15: "RWS Tarot 15 Devil",
    16: "RWS Tarot 16 Tower",
    17: "RWS Tarot 17 Star",
    18: "RWS Tarot 18 Moon",
    19: "RWS Tarot 19 Sun",
    20: "RWS Tarot 20 Judgement",
    21: "RWS Tarot 21 World",
}

SUIT_MAP = {
    "cups": "Cups",
    "wands": "Wands",
    "swords": "Swords",
    "pentacles": "Pentacles",
}


def wikimedia_url(filename: str) -> str | None:
    enc = urllib.parse.quote(filename, safe="")
    api_url = (
        f"{WIKIMEDIA_API}?action=query&titles=File:{enc}"
        f"&prop=imageinfo&iiprop=url&format=json&redirects=1"
    )
    req = urllib.request.Request(api_url, headers={"User-Agent": "TarotOnline/1.0 (tarot-online-dev; https://github.com/tarot-online)"})
    time.sleep(1.0)
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read())
    pages = data["query"]["pages"]
    for page in pages.values():
        if "imageinfo" in page:
            return page["imageinfo"][0]["url"]
    return None


def svg_to_png_url(svg_url: str, width: int = 500) -> str:
    """Convert Wikimedia SVG URL to PNG thumbnail URL."""
    # e.g. https://upload.wikimedia.org/wikipedia/commons/3/3f/RWS_Tarot_00_Fool.svg
    # ->   https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/RWS_Tarot_00_Fool.svg/512px-RWS_Tarot_00_Fool.svg.png
    parts = svg_url.replace("https://upload.wikimedia.org/wikipedia/commons/", "")
    segments = parts.split("/")
    # segments = ["3", "3f", "RWS_Tarot_00_Fool.svg"]
    hash1, hash2, filename = segments[0], segments[1], segments[2]
    return (
        f"https://upload.wikimedia.org/wikipedia/commons/thumb/"
        f"{hash1}/{hash2}/{filename}/{width}px-{filename}.png"
    )


def download(url: str, dest: Path) -> bool:
    headers = {"User-Agent": "TarotOnline/1.0 (tarot-online-dev; https://github.com/tarot-online)"}
    req = urllib.request.Request(url, headers=headers)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read()
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            return True
        except Exception as e:
            if "429" in str(e) and attempt < 2:
                print(f"    429 rate-limited, waiting 10s...", end=" ", flush=True)
                time.sleep(10)
                continue
            print(f"    ERROR: {e}")
            return False
    return False


def main():
    with open(CARDS_JSON, encoding="utf-8") as f:
        deck = json.load(f)

    ok = 0
    fail = 0

    for card in deck["cards"]:
        slug = card["slug"]
        suit = card["suit"]
        number = card["number"]

        if suit == "major":
            stem = MAJOR_NAMES[number]
            wiki_filename = f"{stem}.svg"
            dest = OUT_DIR / "major" / f"{slug}.png"
        else:
            suit_name = SUIT_MAP[suit]
            wiki_filename = f"RWS1909 - {suit_name} {number:02d}.jpeg"
            dest = OUT_DIR / suit / f"{slug}.jpg"

        if dest.exists():
            print(f"  SKIP (exists): {slug}")
            ok += 1
            continue

        print(f"  Fetching URL: {wiki_filename} ...", end=" ", flush=True)
        raw_url = wikimedia_url(wiki_filename)
        if not raw_url:
            print(f"NOT FOUND on Wikimedia")
            fail += 1
            continue

        if suit == "major":
            dl_url = svg_to_png_url(raw_url, width=500)
        else:
            dl_url = raw_url

        print(f"-> downloading ...", end=" ", flush=True)
        if download(dl_url, dest):
            size_kb = dest.stat().st_size // 1024
            print(f"OK ({size_kb} KB)")
            ok += 1
        else:
            fail += 1

        time.sleep(1.5)  # be polite to Wikimedia (avoid 429)

    print(f"\nDone: {ok} OK, {fail} failed")


if __name__ == "__main__":
    main()
