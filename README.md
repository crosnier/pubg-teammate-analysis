<p align="center">
  <img src="images/pubg-teammate-analysis-banner.jpg" alt="PUBG Teammate Analysis banner" width="100%">
</p>

# PUBG Teammate Analysis

**Know who you're playing with, before you land.**

Squads lock in on the plane. From that point until the match ends, you're
stuck with whoever loaded in, and you know nothing about them. This tool
pulls PUBG stats and match history for your squad and turns raw numbers into
an actual profile: playstyle, tendencies, and what happened in their last
match. Console output today; automatic in-game detection and a real UI are
where this is headed.

📖 Full direction: [docs/vision.md](docs/vision.md) · Live status:
[Project board](https://github.com/users/crosnier/projects/2)

---

## Getting Started

### macOS / dev machine

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
python main.py PlayerName
```

To profile a whole squad at once (2+ players, you first) instead:

```bash
python squad.py YourName Teammate1 Teammate2
```

### Windows / live-test machine

There's no dev environment on Windows - just a cold `git pull` of `main`.
One script handles the rest:

```powershell
git pull
.\setup.ps1
```

`setup.ps1` creates `.venv`, installs dependencies, creates `.env` from
`.env.example` if it doesn't exist yet, and runs `doctor.py` at the end to
confirm everything (Python version, dependencies, `.env`, data directories,
and a live PUBG API heartbeat) is actually working before you run
`main.py`.

If PowerShell blocks the script from running (`cannot be loaded because
running scripts is disabled on this system`), run it with:

```powershell
powershell -ExecutionPolicy Bypass -File setup.ps1
```

Re-run `python doctor.py` any time to re-check the environment without
redoing setup.

## How It Works

```text
main.py
 ├──▶ Load player name from CLI, cross-reference player-index.json
 ├──▶ Fetch lifetime stats via the PUBG API        → api/player_stats.py
 ├──▶ Render categorized stat tables by mode       → utils/display_stats_by_mode.py
 ├──▶ Display match history, grouped by mode       → utils/display_match_history.py
 ├──▶ Fetch match telemetry for cached matches     → api/telemetry_fetcher.py
 ├──▶ Combat stats: eliminations/deaths breakdown  → utils/combat_stats.py
 ├──▶ Archetype Tag: tempo + range + weapon        → utils/archetype_tag.py
 │     ├─ time-to-first-contact tempo bucket       → utils/tempo_signal.py
 │     ├─ median kill-distance range bucket        → utils/range_signal.py
 │     └─ weapon-class preference / Wildcard       → utils/weapon_signature.py
 ├──▶ Headline Number: confidence-gated "so-what"  → utils/headline_number.py
 ├──▶ Last match brief for this player             → utils/last_match_brief.py
 └──▶ Bot detection for the most recent match       → utils/bot_detection.py
```

Archetype Tag and the Headline Number both scope each player to their own
recent matches (see `utils/match_scope.py`) - a widening 30-90 day recency
window, capped at a configurable match count - rather than scanning every
cached match, since telemetry caching is shared across all players ever
looked up. `main.py` resolves this scoped match set once per run and
reuses it across both, rather than each rescanning the cache separately.

`squad.py` is a separate multi-player entry point (`main.py`'s
single-player flow is untouched) for profiling a whole squad in one run:
`utils/squad_read.py` + `utils/squad_roster.py` combine each teammate's
Archetype Tag into a synergy/coverage read, bolstered with a data-backed
"who opens first" line when the pattern is consistent enough. Player-stats
fetches run concurrently across the squad, and telemetry is fetched once
per unique match across the whole squad rather than once per player, so a
match two teammates shared only gets pulled once.

## Project Structure

```
├── main.py                 # CLI entry point (single player)
├── squad.py                 # CLI entry point (2+ players at once)
├── doctor.py                # Environment health check (Python, deps, .env, API heartbeat)
├── setup.ps1                # One-click Windows setup (venv, deps, .env, doctor)
├── api/                     # PUBG API client: player stats, telemetry, player index, rate limiter
├── utils/                   # Signal computation (tempo/range/weapon/combat/bots) + display formatting
├── tests/                   # Unit tests
├── docs/                    # Vision, design specs, sample output
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

See [tests/README.md](tests/README.md) for the testing standard (unit vs.
integration vs. live smoke test). Run the automated suite with:

```bash
python -m unittest discover tests
```

Any PR touching API-facing behavior (`api/` or code that changes what's
sent to or parsed from a live response) also expects one manual smoke-test
run (`python main.py <player>`) against the real API before merging - that
step isn't part of the automated suite.

## Sample Output

See [docs/sample-output.md](docs/sample-output.md) for a full example run.

## License

PUBG Teammate Analysis
Copyright (C) 2026 crosnier

Licensed under the [GNU Affero General Public License v3.0](LICENSE). You're
free to use, fork, and modify this project - including running a modified
version as a network service - as long as your source stays available under
the same license.
