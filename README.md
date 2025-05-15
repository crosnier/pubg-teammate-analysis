# PUBG Teammate Analysis

*Analyze and display stats of your PUBG teammate(s).*

## Overview  
As I join a round I like to know who I'm playing with. This project leverages the PUBG APIs to parse and analyze teammate performance, match history, and player statistics. It's designed to help players make informed decisions about who they team up with (or not).

> Note: PC (steam) only!

---

## 🔧 Features

- [ ] Player Stats Data Query
- [ ] Player Status by Game Mode
- [ ] Player Index
- [ ] Player Match History
- [ ] Combat Stats by Player : Eliminations + Deaths
- [ ] Match Telemetry Data Query

> 💡 See the [Project Board](https://github.com/YOUR_USERNAME/pubg-teammate-analysis/projects/1) for a live view of the backlog and active features.

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
python main.py
```

