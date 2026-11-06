"""One-shot snapshot of 17Lands Star Trek (TRK) early-access results.

Pulls the trophy-deck list and leaderboard for each format ONCE, strips anything
that identifies an individual player or draft (screen names, aggregate ids, ranks), and
writes data/snapshot.json. Not meant to be run on a schedule.

Data source: 17Lands (https://www.17lands.com) - see trophy_decks and leaderboard pages.
"""
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = "https://www.17lands.com"
EXPANSION = "TRK"
FORMATS = ["PremierDraft", "Sealed"]
OUT = Path(__file__).resolve().parent.parent / "data" / "snapshot.json"
UA = {"User-Agent": "trk-early-access-snapshot/1.0", "Content-Type": "application/json"}


def get_json(url, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=UA, method="POST" if data else "GET")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def main():
    snap = {"expansion": EXPANSION, "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "source": BASE, "formats": {}}
    for fmt in FORMATS:
        trophies = get_json(f"{BASE}/api/trophies/", {"expansion": EXPANSION, "event_type": fmt,
                                                      "card_names": [], "ranks": [], "deck_colors": []})["data"]
        time.sleep(2)
        lb = get_json(f"{BASE}/data/leaderboard?expansion={EXPANSION}&format={fmt}")
        time.sleep(2)
        # Leaderboard: merge the per-metric lists into one anonymous row per player.
        players = {}
        for lst in lb.values():
            for row in lst:
                players[row["screen_name"]] = {k: row.get(k) for k in ("wins", "win_rate", "trophies", "trophy_rate")}
        snap["formats"][fmt] = {
            "trophy_decks": [{k: d.get(k) for k in ("wins", "losses", "colors", "time")}
                             for d in trophies],
            "leaderboard_players": sorted(players.values(), key=lambda p: (-(p["wins"] or 0), -(p["win_rate"] or 0))),
        }
        print(fmt, len(trophies), "trophy decks,", len(players), "leaderboard players")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(snap, indent=1))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
