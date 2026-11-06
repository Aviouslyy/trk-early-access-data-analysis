"""One-shot fetch of pick-by-pick data and decklists for TRK Premier Draft trophy decks.

Writes docs/data/drafts.json. Draft ids, screen names and ranks are not saved; each draft is kept only
as its colours, record, picks and deck. Cards are stored once and referenced by index.
Two requests per draft (picks and deck) with a pause between them. Please don't schedule this.

Decks come from the 17Lands deck page (main deck and sideboard of the deck the run ended with).

Rarity comes from Scryfall (https://scryfall.com), looked up by the card id in each image URL.

Data source: 17Lands (https://www.17lands.com).
"""
import json
import re
import time
import urllib.request
from pathlib import Path

from fetch_snapshot import BASE, EXPANSION, get_json

OUT = Path(__file__).resolve().parent.parent / "docs" / "data" / "drafts.json"
MAX_DRAFTS = 40


def add_rarity(cards):
    """Fill in each card's rarity from Scryfall, 75 cards per request."""
    ids = {}
    for c in cards:
        m = re.search(r"/([0-9a-f-]{36})\.", c["img"])
        if m and "rarity" not in c:
            ids[m.group(1)] = c
    keys = list(ids)
    for i in range(0, len(keys), 75):
        body = json.dumps({"identifiers": [{"id": k} for k in keys[i:i + 75]]}).encode()
        req = urllib.request.Request("https://api.scryfall.com/cards/collection", data=body, method="POST",
                                     headers={"User-Agent": "trk-early-access-snapshot/1.0",
                                              "Accept": "application/json", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            for found in json.load(r)["data"]:
                ids[found["id"]]["rarity"] = found["rarity"]
        time.sleep(0.2)


def main():
    trophies = get_json(f"{BASE}/api/trophies/", {"expansion": EXPANSION, "event_type": "PremierDraft",
                                                  "card_names": [], "ranks": [], "deck_colors": []})["data"]
    trophies = [t for t in trophies if t.get("has_draft")][:MAX_DRAFTS]
    cards, index, drafts = [], {}, []

    def card(c):
        if c["name"] not in index:
            index[c["name"]] = len(cards)
            cards.append({"name": c["name"], "img": c["image_url"], "cost": c.get("mana_cost", "")})
        return index[c["name"]]

    for t in trophies:
        try:
            time.sleep(2)
            d = get_json(f"{BASE}/data/draft?draft_id={t['aggregate_id']}")
            time.sleep(2)
            deck = get_json(f"{BASE}/api/deck/draft/?draft_id={t['aggregate_id']}&deck_index={t.get('deck_index') or 0}")["data"]
        except Exception as e:  # skip a draft that fails rather than lose the rest
            print("skipped a draft:", e)
            continue
        picks = [{"pack": p["pack_number"], "pick": p["pick_number"],
                  "available": [card(c) for c in p["available"]], "picked": card(p["pick"])}
                 for p in d["picks"] if p.get("pick") and p.get("available")]
        if len(picks) < 39:  # 3 packs of 13-14; skip drafts 17Lands only has partly
            continue
        groups = {}
        for g in deck["groups"]:
            counts = {}
            for cid in g["cards"]:
                c = deck["cards"][str(cid)]
                k = card(c)
                cards[k].setdefault("rarity", c.get("rarity"))
                cards[k].setdefault("cmc", c.get("cmc"))
                cards[k].setdefault("types", " ".join(c.get("types") or []))
                counts[k] = counts.get(k, 0) + 1
            groups[g["name"]] = [[k, n] for k, n in counts.items()]
        drafts.append({"colors": t["colors"], "record": f'{t["wins"]}-{t["losses"]}', "time": t["time"],
                       "picks": picks, "main": groups.get("Maindeck", []), "side": groups.get("Sideboard", [])})
    add_rarity(cards)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"expansion": EXPANSION, "cards": cards, "drafts": drafts}, separators=(",", ":")))
    print("wrote", OUT, len(drafts), "drafts,", len(cards), "cards")
    for d in drafts:
        print(d["colors"], d["record"], sum(n for _, n in d["main"]), "main,", sum(n for _, n in d["side"]), "side")

if __name__ == "__main__":
    main()
