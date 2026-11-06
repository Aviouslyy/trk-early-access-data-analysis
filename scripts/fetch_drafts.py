"""One-shot fetch of pick-by-pick data for TRK Premier Draft trophy decks, for the follow-along page.

Writes docs/data/drafts.json. Draft ids and screen names are not saved; each draft is kept only as
its colours, record, starting rank and picks. Cards are stored once and referenced by index.
One request per draft with a pause between them. Please don't schedule this.

Data source: 17Lands (https://www.17lands.com).
"""
import json
import time
from pathlib import Path

from fetch_snapshot import BASE, EXPANSION, get_json

OUT = Path(__file__).resolve().parent.parent / "docs" / "data" / "drafts.json"
MAX_DRAFTS = 40


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
        time.sleep(2)
        try:
            d = get_json(f"{BASE}/data/draft?draft_id={t['aggregate_id']}")
        except Exception as e:  # skip a draft that fails rather than lose the rest
            print("skipped a draft:", e)
            continue
        picks = [{"pack": p["pack_number"], "pick": p["pick_number"],
                  "available": [card(c) for c in p["available"]], "picked": card(p["pick"])}
                 for p in d["picks"] if p.get("pick") and p.get("available")]
        if len(picks) >= 39:  # 3 packs of 13-14; skip drafts 17Lands only has partly
            drafts.append({"colors": t["colors"], "record": f'{t["wins"]}-{t["losses"]}',
                           "start_rank": t["start_rank"], "time": t["time"], "picks": picks})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"expansion": EXPANSION, "cards": cards, "drafts": drafts}, separators=(",", ":")))
    print("wrote", OUT, len(drafts), "drafts,", len(cards), "cards")


if __name__ == "__main__":
    main()
