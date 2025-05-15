# PUBG Teammate Analysis

*Analyze and display stats of your PUBG teammate(s).*

## Overview  
As I join a round I like to know who I'm playing with. This project leverages the PUBG APIs to parse and analyze teammate performance, match history, and player statistics. It's designed to help players make informed decisions about who they team up with (or not).

> Note: PC (steam) only!

---

## 🔧 Features

- [x] Player Stats Data Query
- [ ] Player Status by Game Mode
- [ ] Player Index
- [ ] Player Match History
- [ ] Combat Stats by Player : Eliminations + Deaths
- [ ] Match Telemetry Data Query

> 💡 See the [Project Board](https://github.com/users/crosnier/projects/2) for a live view of the backlog and active features.

---

## 📸 Example Use Cases

- Visualize who’s worth squadding with (or not)
- Build up an anonymized teammate performance dataset

---

## 🚀 Getting Started

*Clone the repo, install dependencies, and create a `.env` file with your PUBG API key.*

```bash
git clone https://github.com/YOUR_USERNAME/pubg-teammate-analysis.git
cd pubg-teammate-analysis
pip install -r requirements.txt
```

Create a .env file
```
PUBG_API_KEY=your_api_key_here
```

Run CLI tool
```
python main.py 7h3Cr0
```

---

## 🔍 Feature: Player Stats — Data Query

Query the full set of lifetime PUBG stats for a specified player and store the result locally for future analysis or integration.

### 🧩 How It Works

1. **CLI Entry**: Run `main.py` and provide a PUBG player name as an argument.  
2. **API Query**: Looks up the player's `account_id` and then fetches their full lifetime stats.  
3. **Storage**: Saves the full JSON response to `./playerstats/{playername}.json` (overwriting any prior snapshot).

### 📂 File Structure Overview

```
pubg-teammate-analysis/
├── api/
│   ├── player_stats.py              # Fetch player stats + account_id
│   ├── player_index.py              # Registry of known players
│   ├── telemetry_fetcher.py         # NEW: Async fetch + save telemetry for match IDs
│   └── match_parser.py              # (optional later): interpret raw telemetry
│
├── utils/
│   ├── display_stats_by_mode.py     # Show stat tables across game modes
│   ├── display_match_history.py     # NEW: Show match IDs by game mode
│   ├── io_helpers.py                # File read/write, JSON load/save
│   └── suppress_warnings.py         # Suppress warnings like NotOpenSSL
│
├── match-telemetry/                 # Fetched telemetry JSON per match
│   └── {match_id}-telemetry.json
│
├── playerstats/                     # Raw player stat dumps (by playername)
│   └── {playername}.json
│
├── player-index.json                # Central index of all queried players
├── main.py                          # CLI entry point
├── requirements.txt
└── README.md
```

### ✅ Requirements

```
requests
python-dotenv
```

### ▶️ Example Usage

```bash
python main.py 7h3Cr0
```

This will save `./playerstats/7h3Cr0.json` and print a success message to confirm the query succeeded.
