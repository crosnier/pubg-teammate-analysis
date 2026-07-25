# Development

This doc covers working on the codebase itself: setting up a dev machine,
how the pipeline fits together internally, and running the test suite. If
you just want to run the tool, see the [main README](../README.md) instead
- this is contributor/maintainer documentation.

## macOS / dev machine setup

1. Clone the repo and set up a virtual environment:

```bash
git clone https://github.com/crosnier/pubg-teammate-analysis.git
cd pubg-teammate-analysis
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt  # python-dotenv, aiohttp
```

3. Set up a `.env` file with your PUBG API key - copy `.env.example` to
   `.env` and fill in `PUBG_API_KEY`.

4. Confirm the environment is healthy:

```bash
python doctor.py
```

5. Run it against a player name:

```bash
python solo.py PlayerName
```

Or profile a whole squad at once (2+ players, you first):

```bash
python squad.py YourName Teammate1 Teammate2
```

Want the full raw stats dump instead of the narrative profile? Use
`python main.py PlayerName`.

## How It Works

```text
solo.py
 ├──▶ Load player name from CLI, cross-reference player-index.json
 ├──▶ Fetch lifetime stats via the PUBG API        → api/player_stats.py
 ├──▶ Fetch match telemetry for cached matches     → api/telemetry_fetcher.py
 ├──▶ Archetype Tag: tempo + range + weapon        → utils/archetype_tag.py
 │     ├─ time-to-first-contact tempo bucket       → utils/tempo_signal.py
 │     ├─ median kill-distance range bucket        → utils/range_signal.py
 │     └─ weapon-class preference / Wildcard       → utils/weapon_signature.py
 ├──▶ Headline Number: confidence-gated "so-what"  → utils/headline_number.py
 ├──▶ K/D summary                                  → utils/combat_stats.py
 ├──▶ Coaching Note: stat reframed as a tip, plus  → utils/solo_coaching.py
 │     a confidence-gated per-map performance read
 └──▶ Last match brief for this player             → utils/last_match_brief.py
       └─ squad-status-at-death cross-reference    → (same module)

main.py (full raw stats view - unchanged, still available)
 ├──▶ Render categorized stat tables by mode       → utils/display_stats_by_mode.py
 ├──▶ Display match history, grouped by mode       → utils/display_match_history.py
 ├──▶ Combat stats: eliminations/deaths breakdown  → utils/combat_stats.py
 ├──▶ Archetype Tag, Headline Number, Last Match Brief (same modules as solo.py)
 └──▶ Bot detection for the most recent match       → utils/bot_detection.py
```

Archetype Tag and the Headline Number both scope each player to their own
recent matches (see `utils/match_scope.py`) - a widening 30-90 day recency
window, capped at a configurable match count - using the player's own
known match IDs from the player-stats API response, never scanning the
whole shared telemetry cache (which holds every match ever cached across
every player looked up). Both `solo.py` and `main.py` resolve this scoped
match set once per run and reuse it across signals, rather than each
rescanning separately.

`squad.py` is a separate multi-player entry point for profiling a whole
squad in one run: `utils/squad_read.py` + `utils/squad_roster.py` combine
each teammate's Archetype Tag into a synergy/coverage read, bolstered with
a data-backed "who opens first" line when the pattern is consistent
enough. Player-stats fetches run concurrently across the squad, and
telemetry is fetched once per unique match across the whole squad rather
than once per player, so a match two teammates shared only gets pulled
once.

`solo.py` is the single-player counterpart - narrative Mode 1 slots for
one player, no raw stats table or full match history. Squad Read's
capstone comparison line has no solo equivalent (nothing to compare
against), so `utils/solo_coaching.py` stands in with a self-coaching line
(the Headline Number's stat, reframed as a second-person tip) plus a
confidence-gated per-map performance callout - `main.py`'s raw-stats view
is untouched and still available for anyone who wants the full dump.

A visual diagram of how every local file relates to the API calls that
produce it, plus the actual execution order, lives at
[docs/architecture/data-flow.html](architecture/data-flow.html).

## Project Structure

```
├── main.py                 # CLI entry point (single player, full raw stats view)
├── solo.py                  # CLI entry point (single player, narrative profile)
├── squad.py                 # CLI entry point (2+ players at once)
├── doctor.py                # Environment health check (Python, deps, .env, API heartbeat)
├── setup.ps1                # One-click Windows setup (venv, deps, .env, doctor)
├── api/                     # PUBG API client: player stats, telemetry, player index, rate limiter
├── utils/                   # Signal computation (tempo/range/weapon/combat/bots) + display formatting
├── tests/                   # Unit tests
├── docs/                    # Vision, design specs, architecture diagram, sample output
├── images/                  # README and design assets
├── match-telemetry/          # Cached raw telemetry JSON (local only, gitignored)
├── playerstats/              # Cached player stat JSON (local only, gitignored)
├── player-index.json         # Known player lookup (local only, gitignored)
├── .env.example              # Template for local .env (PUBG_API_KEY, tunables)
└── requirements.txt
```

## Notes

- Only telemetry files are required to analyze bot/player behavior.
- Match IDs come from cached stats, not fresh API calls, to avoid rate
  limits - match JSON doesn't change once a match is generated.
- `/players` and `/seasons` calls are serialized through a request queue
  (`api/rate_limiter.py`) that throttles to the API's live
  `X-RateLimit-*` headers, falling back to `PUBG_RATE_LIMIT_PER_MINUTE`
  until headers are seen. `/matches` and telemetry URLs are not
  rate-limited and bypass the queue.

## Testing

See [tests/README.md](../tests/README.md) for the testing standard (unit
vs. integration vs. live smoke test). Run the automated suite with:

```bash
python -m unittest discover tests
```

Any PR touching API-facing behavior (`api/` or code that changes what's
sent to or parsed from a live response) also expects one manual smoke-test
run (`python main.py <player>`) against the real API before merging - that
step isn't part of the automated suite.
