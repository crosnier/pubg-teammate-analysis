# PUBG Teammate Analysis

*Analyze and display stats of your PUBG teammate(s).*

---

## 🚀 Getting Started

Clone the repo and install dependencies:

```bash
git clone git@github.com:crosnier/pubg-teammate-analysis.git
cd pubg-teammate-analysis
pip install -r requirements.txt
```

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

## 🧭 System Flow

1. CLI entry point — `main.py`  
2. Loads player index — `player-index.json`  
3. Loops through telemetry files — `match-telemetry/`  
4. Parses and detects bots — `main.py`  
5. Aggregates teammate stats — `utils/io_helpers.py`  
6. Displays match summaries — `utils/display_match_history.py`  
7. Displays game mode stats — `utils/display_stats_by_mode.py`  

---

## 📂 File Structure Overview

```
├── main.py                      # Entry point to analyze telemetry and player stats
├── match-telemetry/            # Raw match telemetry JSON files
├── matches/                    # Placeholder for match-level outputs
├── playerstats/                # Cached player stats (by username)
├── utils/                      # Helper modules and tools
│   ├── display_match_history.py       # Functions for visualizing match summaries
│   ├── display_stats_by_mode.py       # Functions for mode-specific stat summaries
│   ├── io_helpers.py                  # JSON I/O utilities
│   └── suppress_warnings.py           # Context manager to suppress noisy output
├── player-index.json           # Index of players to track
├── requirements.txt            # Python dependencies
├── tests/                      # Unit tests
│   └── test_player_stats.py
└── README.md                   # Project overview and usage guide
```

---

## ✅ Requirements

```
requests
python-dotenv
aiohttp
```

---

## 🔧 Features

- Player Stats Data Query
- Player Status by Game Mode
- Player Index
- Player Match History
- Combat Stats by Player : Eliminations + Deaths
- Match Telemetry Data Query

---

## 📸 Example Use Cases

- Visualize who’s worth squadding with (or not)
- Build up an anonymized teammate performance dataset

- **Bot Detection:**  
  Quickly identify matches with high bot counts to evaluate teammate skill more accurately.

- **Teammate Performance:**  
  Analyze your friends' stats over multiple matches to decide who to squad up with.

- **Mode Comparison:**  
  See how your teammates perform differently in Solo, Duo, and Squad modes.

- **Match Summaries:**  
  Review past match details and teammate contributions visually for better insights.

---

## 🔍 Feature: Player Stats — Data Query

Query the full set of lifetime PUBG stats for a specified player and store the result locally for future analysis or integration.


### ▶️ Example Usage

```bash
python main.py 7h3Cr0
```

This will save `./playerstats/7h3Cr0.json` and print a success message to confirm the query succeeded.

---

## 🛠 Notes

- Only telemetry files are required to analyze bot/player behavior.
- Ensure each telemetry file is formatted as raw JSON.
- Add or remove usernames from `player-index.json` to focus the analysis.

---

## 📬 Contact

For questions, suggestions, or contributions, feel free to open an issue or contact me directly at [your.email@example.com](mailto:your.email@example.com).

---

## 📬 Contact

Built by Crosnier.  
For questions or ideas, feel free to fork and contribute!