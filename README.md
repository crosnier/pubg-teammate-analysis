<p align="center">
  <img src="images/pubg-teammate-analysis-banner.jpg" alt="PUBG Teammate Analysis banner" width="100%">
</p>

# PUBG Teammate Analysis

**Know who you're playing with, before you land.**

Squads lock in on the plane. From that point until the match ends, you're
stuck with whoever loaded in, and you know nothing about them. This tool
pulls PUBG stats and match history for your squad and turns raw numbers
into an actual profile: playstyle, tendencies, and what happened in their
last match.

📖 Full direction: [docs/vision.md](docs/vision.md) · Live status:
[Project board](https://github.com/users/crosnier/projects/2)

---

## Getting Started (Windows)

There's no separate setup step to think about - just a cold `git pull` and
one script:

```powershell
git pull
.\setup.ps1
```

`setup.ps1` creates a virtual environment, installs dependencies, creates
your `.env` (you'll need a [PUBG API key](https://developer.pubg.com/)),
and runs a health check at the end to confirm everything's actually
working before you run the tool.

If PowerShell blocks the script from running (`cannot be loaded because
running scripts is disabled on this system`), run it with:

```powershell
powershell -ExecutionPolicy Bypass -File setup.ps1
```

Then profile a player:

```powershell
python main.py PlayerName
```

Or a whole squad at once (2+ players, you first):

```powershell
python squad.py YourName Teammate1 Teammate2
```

Re-run `python doctor.py` any time to re-check your environment without
redoing setup.

📄 See [docs/sample-output.md](docs/sample-output.md) for a full example
of what a run actually looks like.

---

## More

- **Contributing / dev setup (macOS, project internals):**
  [docs/development.md](docs/development.md)
- **How the local files and API calls relate to each other, visually:**
  [docs/architecture/data-flow.html](docs/architecture/data-flow.html)
- **Where this is headed:** [docs/vision.md](docs/vision.md)

## License

PUBG Teammate Analysis
Copyright (C) 2026 crosnier

Licensed under the [GNU Affero General Public License v3.0](LICENSE). You're
free to use, fork, and modify this project - including running a modified
version as a network service - as long as your source stays available under
the same license.
