# ==============================
# api/player_stats.py
# ==============================
import os
from dotenv import load_dotenv
from api.player_index import update_player_index
from api.rate_limiter import player_api_queue

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
