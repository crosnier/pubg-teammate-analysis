import os
import aiohttp
import asyncio
from dotenv import load_dotenv
from utils.io_helpers import save_json

if not load_dotenv():
    raise RuntimeError("Failed to load .env file")

API_KEY = os.getenv("PUBG_API_KEY")
if not API_KEY:
    raise EnvironmentError("PUBG_API_KEY not found in environment.")
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/vnd.api+json"
}
BASE_URL = "https://api.pubg.com/shards/steam"

TELEMETRY_DIR = "match-telemetry"
os.makedirs(TELEMETRY_DIR, exist_ok=True)


async def fetch_match_metadata(session, match_id):
    url = f"{BASE_URL}/matches/{match_id}"
    async with session.get(url, headers=HEADERS) as response:
        response.raise_for_status()
        return await response.json()


def get_telemetry_url(match_metadata):
    assets = match_metadata.get("included", [])
    for item in assets:
        if item.get("type") == "asset" and "telemetry" in item.get("attributes", {}).get("URL", ""):
            return item["attributes"]["URL"]
    return None


import asyncio

async def fetch_and_save_telemetry(session, match_id, semaphore):
    filepath = os.path.join(TELEMETRY_DIR, f"{match_id}-telemetry.json")
    if os.path.exists(filepath):
        return ("skipped", match_id)

    async with semaphore:
        for attempt in range(3):
            try:
                # print(f"[INFO] Fetching telemetry for {match_id}")
                metadata = await fetch_match_metadata(session, match_id)
                url = get_telemetry_url(metadata)
                if not url:
                    print(f"[WARN] No telemetry URL found for match {match_id}")
                    return ("failed", match_id)

                async with session.get(url) as telemetry_response:
                    telemetry_response.raise_for_status()
                    telemetry_data = await telemetry_response.json()
                    save_json(telemetry_data, filepath)
                    # print(f"[SUCCESS] Saved telemetry: {filepath}")
                    return ("saved", match_id)

            except Exception as e:
                print(f"[WARN] Attempt {attempt + 1} failed for {match_id}: {e}")
                await asyncio.sleep(2 ** attempt)
        print(f"[ERROR] Failed fetching telemetry for {match_id} after 3 attempts.")
        return ("failed", match_id)


async def fetch_telemetry_for_matches(match_ids, concurrency=None):
    if concurrency is None:
        concurrency = int(os.getenv("TELEMETRY_CONCURRENCY", 5))
    semaphore = asyncio.Semaphore(concurrency)
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_and_save_telemetry(session, match_id, semaphore) for match_id in match_ids]
        results = await asyncio.gather(*tasks)

    saved = [m for status, m in results if status == "saved"]
    skipped = [m for status, m in results if status == "skipped"]
    failed = [m for status, m in results if status == "failed"]

    print("\n╔════════════════════════════════════════╗")
    print("║         Telemetry Fetch Summary        ║")
    print("╚════════════════════════════════════════╝")
    # print(f"[INFO] Fetching telemetry for {len(match_ids)} matches...\n")
    print(f"✅ Saved: {len(saved):<3}   ⏭️  Skipped: {len(skipped):<3}   ❌ Failed: {len(failed):<3}")
    print()
    print()


# CLI testing option
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python api/telemetry_fetcher.py <match_id_1> <match_id_2> ...")
        exit()
    asyncio.run(fetch_telemetry_for_matches(sys.argv[1:]))
