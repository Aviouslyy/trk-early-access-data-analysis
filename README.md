# Star Trek (TRK) early access analysis

A small GitHub Pages site summarising MTG Arena results from the *Magic: The Gathering | Star Trek*
early access event. It's shared with a small testing group.

**Data source: [17Lands](https://www.17lands.com)** ([trophy decks](https://www.17lands.com/trophy_decks),
[leaderboard](https://www.17lands.com/leaderboard)). This is not endorsed by 17Lands. Use 17Lands for live and complete data.

## What's here

| Path | What it is |
|---|---|
| `scripts/fetch_snapshot.py` | One-off snapshot of TRK trophy decks and leaderboard totals for Premier Draft and Sealed. Player screen names, ranks and draft IDs are removed before saving. |
| `data/snapshot.json` | The anonymised snapshot. |
| `scripts/build_stats.py` | Turns the snapshot into `docs/data/stats.json`. |
| `scripts/fetch_drafts.py` | One-off fetch of pick-by-pick data and decklists (main deck and sideboard) for Premier Draft trophy decks, written to `docs/data/drafts.json` without draft IDs, screen names or ranks. Card rarity comes from [Scryfall](https://scryfall.com). |
| `docs/` | The static site: `index.html`, `follow.html` (follow a trophy draft pick by pick and see how often you match), `cards.html` (cards in trophy main decks: decks, copies, share played, average pick, take rate; open a card to browse the decks that played it) and `data/`. |

## Metrics on the site

- Trophy decks by colour pair, colour presence (main colour vs splash only), deck width and splash colours
- Trophy records (7-0 / 7-1 / 7-2)
- Win-rate distribution among players listed on the 17Lands leaderboard
- A full list of trophy-winning colour combinations

17Lands doesn't publish card-level and colour-pair win rates for TRK yet. The 17Lands
[public datasets](https://www.17lands.com/public_datasets) (CC BY 4.0) are the place for deeper
analysis once they're released, about two weeks after the set launches.

## Refreshing

```sh
python3 scripts/fetch_snapshot.py   # a single request per endpoint; please don't schedule this
python3 scripts/build_stats.py
python3 scripts/fetch_drafts.py    # two requests per trophy draft (picks, deck), 2 s apart
```

## Publishing

In GitHub, go to **Settings → Pages → Build and deployment**. Choose *Deploy from a branch* and pick this branch with the `/docs` folder.
