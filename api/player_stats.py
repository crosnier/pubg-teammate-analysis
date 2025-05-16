# ==============================
# api/player_stats.py
# ==============================
import os
import requests
from dotenv import load_dotenv
from api.player_index import update_player_index

load_dotenv()

API_KEY = os.getenv("PUBG_API_KEY")
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/vnd.api+json"
}
BASE_URL = "https://api.pubg.com/shards/steam"


def fetch_player_stats(playername):
    # Get account ID from player name
    player_url = f"{BASE_URL}/players?filter[playerNames]={playername}"
    resp = requests.get(player_url, headers=HEADERS)
    resp.raise_for_status()
    player_data = resp.json()
    player_id = player_data["data"][0]["id"]

    # Update the player index (no match_ids yet)
    update_player_index(account_id=player_id, playername=playername)

    # Get lifetime stats
    stats_url = f"{BASE_URL}/players/{player_id}/seasons/lifetime"
    resp = requests.get(stats_url, headers=HEADERS)
    resp.raise_for_status()
    return resp.json(), player_id