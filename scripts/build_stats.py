"""Turn data/snapshot.json into docs/data/stats.json for the GitHub Pages site."""
import json
from collections import Counter
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parent.parent
WUBRG = "WUBRG"
COLOR_NAMES = {"W": "White", "U": "Blue", "B": "Black", "R": "Red", "G": "Green"}
PAIR_NAMES = {"WU": "Azorius", "UB": "Dimir", "BR": "Rakdos", "RG": "Gruul", "WG": "Selesnya",
              "WB": "Orzhov", "UR": "Izzet", "BG": "Golgari", "WR": "Boros", "UG": "Simic"}
TIERS = ["Bronze", "Silver", "Gold", "Platinum", "Diamond", "Mythic"]


def order(cs):
    return "".join(sorted(set(cs), key=WUBRG.index))


def tier(rank):
    if not rank:
        return None
    t = rank.replace("-", " ").split()[0]
    return t if t in TIERS else None


def deck_stats(decks):
    n = len(decks)
    main = [order(c for c in d["colors"] if c.isupper()) for d in decks]
    splash = [order(c.upper() for c in d["colors"] if c.islower()) for d in decks]
    pairs = Counter(m for m in main if len(m) == 2)
    archetypes = Counter(main)
    width = Counter("Mono" if len(m) == 1 else "Two colour" if len(m) == 2 else "Three+ colour" for m in main)
    presence = {c: sum(c in m for m in main) for c in WUBRG}
    presence_any = {c: sum(c in m or c in s for m, s in zip(main, splash)) for c in WUBRG}
    splash_colors = Counter(c for s in splash for c in s)
    records = Counter(f'{d["wins"]}-{d["losses"]}' for d in decks)
    start_tiers = Counter(tier(d["start_rank"]) for d in decks if tier(d["start_rank"]))
    times = sorted(d["time"] for d in decks)
    return {
        "count": n,
        "first": times[0] if times else None,
        "last": times[-1] if times else None,
        "records": [{"record": r, "count": records.get(r, 0)} for r in ("7-0", "7-1", "7-2")],
        "avg_losses": round(sum(d["losses"] for d in decks) / n, 2) if n else None,
        "pairs": [{"code": p, "name": PAIR_NAMES[p], "count": pairs.get(p, 0)}
                  for p in sorted(PAIR_NAMES, key=lambda p: (-pairs.get(p, 0), list(PAIR_NAMES).index(p)))],
        "archetypes": [{"code": a, "count": c} for a, c in archetypes.most_common()],
        "width": [{"label": k, "count": width.get(k, 0)} for k in ("Mono", "Two colour", "Three+ colour")],
        "splash_decks": sum(bool(s) for s in splash),
        "splash_colors": [{"code": c, "name": COLOR_NAMES[c], "count": splash_colors.get(c, 0)} for c in WUBRG],
        "presence": [{"code": c, "name": COLOR_NAMES[c], "main": presence[c], "any": presence_any[c]} for c in WUBRG],
        "start_tiers": [{"tier": t, "count": start_tiers.get(t, 0)} for t in TIERS if start_tiers.get(t)],
    }


def leaderboard_stats(players):
    wr = [p["win_rate"] for p in players if p["win_rate"] is not None]
    wins = [p["wins"] or 0 for p in players]
    bins = [(0, .4), (.4, .5), (.5, .55), (.55, .6), (.6, .65), (.65, .7), (.7, 1.01)]
    labels = ["<40%", "40–50%", "50–55%", "55–60%", "60–65%", "65–70%", "70%+"]
    tiers = Counter(tier(p["rank"]) for p in players if tier(p["rank"]))
    return {
        "players": len(players),
        "total_wins": sum(wins),
        "total_trophies": sum(p["trophies"] or 0 for p in players),
        "players_with_trophy": sum(1 for p in players if (p["trophies"] or 0) > 0),
        "median_wins": median(wins) if wins else None,
        "max_wins": max(wins) if wins else None,
        "median_win_rate": round(median(wr), 4) if wr else None,
        "max_win_rate": round(max(wr), 4) if wr else None,
        "win_rate_hist": [{"label": l, "count": sum(lo <= w < hi for w in wr)} for (lo, hi), l in zip(bins, labels)],
        "rank_tiers": [{"tier": t, "count": tiers.get(t, 0)} for t in TIERS if tiers.get(t)],
    }


def main():
    snap = json.loads((ROOT / "data" / "snapshot.json").read_text())
    out = {"expansion": snap["expansion"], "fetched_at": snap["fetched_at"], "formats": {}}
    for fmt, v in snap["formats"].items():
        out["formats"][fmt] = {"trophies": deck_stats(v["trophy_decks"]),
                               "leaderboard": leaderboard_stats(v["leaderboard_players"])}
    dest = ROOT / "docs" / "data" / "stats.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=1))
    print("wrote", dest)


if __name__ == "__main__":
    main()
