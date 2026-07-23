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

1. Clone the repo and set up a virtual environment:

```bash
git clone https://github.com/crosnier/pubg-teammate-analysis.git
cd pubg-teammate-analysis
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt  # requests, python-dotenv, aiohttp
```

3. Set up a `.env` file with your PUBG API key:

```
PUBG_API_KEY=your_api_key_here
```

4. Run it against a player name:

```bash
python main.py PlayerName
```

## How It Works

```text
main.py
 ├──▶ Load player name from CLI, cross-reference player-index.json
 ├──▶ Fetch lifetime stats via the PUBG API      → utils/io_helpers.py
 ├──▶ Display match history, grouped by mode     → utils/display_match_history.py
 ├──▶ (optional) Fetch match telemetry           → api/telemetry_fetcher.py
 └──▶ Render categorized stat tables by mode     → utils/display_stats_by_mode.py
```

## Project Structure

```
├── main.py                 # CLI entry point
├── api/                     # PUBG API client: player stats, telemetry, player index
├── utils/                   # Display formatting + I/O helpers
├── tests/                   # Unit tests
├── docs/                    # Vision, design specs, sample output
├── images/                  # README and design assets
├── match-telemetry/          # Cached raw telemetry JSON (local only, gitignored)
├── playerstats/              # Cached player stat JSON (local only, gitignored)
├── player-index.json         # Known player lookup (local only, gitignored)
└── requirements.txt
```

## Notes

- Only telemetry files are required to analyze bot/player behavior.
- Match IDs come from cached stats, not fresh API calls, to avoid rate
  limits - match JSON doesn't change once a match is generated.

## Sample Output

See [docs/sample-output.md](docs/sample-output.md) for a full example run.

## License

PUBG Teammate Analysis
Copyright (C) 2026 crosnier

Licensed under the [GNU Affero General Public License v3.0](LICENSE). You're
free to use, fork, and modify this project - including running a modified
version as a network service - as long as your source stays available under
the same license.
