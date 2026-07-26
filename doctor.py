# ==============================
# doctor.py - environment health check
# ==============================
# Run after setup (or any time) to confirm the local environment is ready
# to run main.py: python doctor.py
import asyncio
import importlib.util
import os
import sys

import aiohttp
from dotenv import dotenv_values, load_dotenv

REQUIRED_PACKAGES = ["dotenv", "aiohttp"]
REQUIRED_DIRS = ["playerstats", "match-telemetry"]
STATUS_URL = "https://api.pubg.com/status"


def _read_expected_python_version(version_file):
    try:
        with open(version_file) as f:
            return f.read().strip()
    except FileNotFoundError:
        return None


def check_python_version(version_file=".python-version"):
    expected = _read_expected_python_version(version_file)
    actual = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if expected is None:
        return True, f"Python {actual} (no .python-version to compare against)"
    actual_major_minor = f"{sys.version_info.major}.{sys.version_info.minor}"
    expected_major_minor = ".".join(expected.split(".")[:2])
    if actual_major_minor == expected_major_minor:
        return True, f"Python {actual}"
    return False, (
        f"Python {actual}, this project targets {expected_major_minor}.x "
        f"(see .python-version) - a different patch version is fine, but "
        f"a different major/minor version may not have all dependencies "
        f"available"
    )


def check_virtual_env():
    in_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    if in_venv:
        return True, f"Active venv: {sys.prefix}"
    return False, "No virtual environment active - run setup.ps1 or `python -m venv .venv` first"


def check_packages(packages=REQUIRED_PACKAGES):
    missing = [pkg for pkg in packages if importlib.util.find_spec(pkg) is None]
    if missing:
        return False, f"Missing packages: {', '.join(missing)} - run `pip install -r requirements.txt`"
    return True, f"All required packages installed ({', '.join(packages)})"


def check_env_file(env_path=".env"):
    if not os.path.exists(env_path):
        return False, f"{env_path} not found - copy .env.example to {env_path} and add your PUBG API key"
    if not dotenv_values(env_path).get("PUBG_API_KEY"):
        return False, "PUBG_API_KEY not set in .env"
    return True, "PUBG_API_KEY is set"


def check_data_dirs(dirs=REQUIRED_DIRS, base_dir="."):
    created = []
    for directory in dirs:
        path = os.path.join(base_dir, directory)
        if not os.path.isdir(path):
            os.makedirs(path, exist_ok=True)
            created.append(directory)
    if created:
        return True, f"Created missing directories: {', '.join(created)}"
    return True, f"All data directories present ({', '.join(dirs)})"


async def _ping_pubg_api():
    api_key = os.getenv("PUBG_API_KEY")
    headers = {"Accept": "application/vnd.api+json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    async with aiohttp.ClientSession() as session:
        async with session.get(STATUS_URL, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            return resp.status


def check_api_heartbeat():
    try:
        status = asyncio.run(_ping_pubg_api())
    except Exception as e:
        return False, f"Could not reach PUBG API: {e}"
    if status == 200:
        return True, "PUBG API reachable (status 200)"
    return False, f"PUBG API returned status {status}"


CHECKS = [
    ("Python version", check_python_version),
    ("Virtual environment", check_virtual_env),
    ("Dependencies", check_packages),
    ("Environment file", check_env_file),
    ("Data directories", check_data_dirs),
    ("PUBG API heartbeat", check_api_heartbeat),
]


def main():
    load_dotenv()

    print("=============================")
    print("🩺 Environment Doctor")
    print("=============================")

    all_ok = True
    for label, check in CHECKS:
        ok, message = check()
        icon = "✅" if ok else "❌"
        print(f"{icon} {label:<22}: {message}")
        all_ok = all_ok and ok

    print()
    if all_ok:
        print("All checks passed - ready to run: python main.py <playername>")
        sys.exit(0)
    else:
        print("One or more checks failed - fix the issues above before running main.py")
        sys.exit(1)


if __name__ == "__main__":
    main()
