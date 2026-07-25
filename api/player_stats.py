# ==============================
# api/player_stats.py
# ==============================
import os
from dotenv import load_dotenv
from api.player_index import update_player_index
from api.rate_limiter import player_api_queue
from utils.io_helpers import save_json

load_dotenv()

API_KEY = os.getenv("PUBG_API_KEY")
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/vnd.api+json"
}
BASE_URL = "https://api.pubg.com/shards/steam"


async def fetch_player_stats(playername):
    # Get account ID from player name
    player_url = f"{BASE_URL}/players?filter[playerNames]={playername}"
    player_data = await player_api_queue.request("GET", player_url, headers=HEADERS)
    player_id = player_data["data"][0]["id"]

    # Update the player index (no match_ids yet)
    update_player_index(account_id=player_id, playername=playername)

    # Get lifetime stats
    stats_url = f"{BASE_URL}/players/{player_id}/seasons/lifetime"
    stats_data = await player_api_queue.request("GET", stats_url, headers=HEADERS)
    return stats_data, player_id


async def fetch_player_and_match_ids(playername):
    """Resolve a player's account ID, save their lifetime stats, and
    return their known match ID list - the shared first step needed by
    both the single-player CLI (main.py) and multi-player squad lookups
    (squad.py), so both stay behaviorally identical for this step.
    """
    data, player_id = await fetch_player_stats(playername)
    save_json(data, f"playerstats/{playername}.json")

    match_ids = []
    for key, relationship in data["data"]["relationships"].items():
        if key.startswith("matches"):
            match_ids.extend([entry["id"] for entry in relationship.get("data", [])])

    return player_id, match_ids
