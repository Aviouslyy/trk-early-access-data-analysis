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


def order(cs):
    return "".join(sorted(set(cs), key=WUBRG.index))


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
    }


CURVE_BUCKETS = ["0–1", "2", "3", "4", "5", "6", "7+"]


def curve_stats(drafts):
    """Average mana value and curve of non-land main-deck cards across trophy decklists."""
    cards = drafts["cards"]
    per_deck = []
    for d in drafts["drafts"]:
        creatures, other = [0] * len(CURVE_BUCKETS), [0] * len(CURVE_BUCKETS)
        total_mv = spells = lands = 0
        for k, n in d["main"]:
            c = cards[k]
            if "Land" in c["types"].split(" - ")[0]:
                lands += n
                continue
            mv = c.get("cmc") or 0
            b = min(max(int(mv), 1), 7) - 1
            (creatures if "Creature" in c["types"].split(" - ")[0] else other)[b] += n
            total_mv += mv * n
            spells += n
        if spells:
            per_deck.append({"avg": total_mv / spells, "spells": spells, "lands": lands,
                             "creatures": creatures, "other": other})
    n = len(per_deck)
    if not n:
        return None
    avgs = [d["avg"] for d in per_deck]
    mean = lambda xs: round(sum(xs) / n, 2)
    return {
        "decks": n,
        "avg_mv": round(sum(avgs) / n, 2),
        "median_mv": round(median(avgs), 2),
        "min_mv": round(min(avgs), 2),
        "max_mv": round(max(avgs), 2),
        "avg_spells": mean([d["spells"] for d in per_deck]),
        "avg_lands": mean([d["lands"] for d in per_deck]),
        "curve": [{"label": l, "creatures": mean([d["creatures"][i] for d in per_deck]),
                   "other": mean([d["other"][i] for d in per_deck])}
                  for i, l in enumerate(CURVE_BUCKETS)],
    }


def leaderboard_stats(players):
    wr = [p["win_rate"] for p in players if p["win_rate"] is not None]
    wins = [p["wins"] or 0 for p in players]
    bins = [(0, .4), (.4, .5), (.5, .55), (.55, .6), (.6, .65), (.65, .7), (.7, 1.01)]
    labels = ["<40%", "40–50%", "50–55%", "55–60%", "60–65%", "65–70%", "70%+"]
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
    }


def main():
    snap = json.loads((ROOT / "data" / "snapshot.json").read_text())
    out = {"expansion": snap["expansion"], "fetched_at": snap["fetched_at"], "formats": {}}
    for fmt, v in snap["formats"].items():
        out["formats"][fmt] = {"trophies": deck_stats(v["trophy_decks"]),
                               "leaderboard": leaderboard_stats(v["leaderboard_players"])}
    drafts_path = ROOT / "docs" / "data" / "drafts.json"
    if drafts_path.exists() and "PremierDraft" in out["formats"]:
        out["formats"]["PremierDraft"]["curve"] = curve_stats(json.loads(drafts_path.read_text()))
    dest = ROOT / "docs" / "data" / "stats.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=1))
    print("wrote", dest)


if __name__ == "__main__":
    main()
