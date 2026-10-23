"""Hand-test Moonraker's print state and pause/resume endpoints.

Usage: python scripts/moonraker_pause.py [status|pause|resume]
Cancel is intentionally not implemented.
"""
import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()
BASE = os.environ["MOONRAKER_URL"].rstrip("/")


def status():
    r = requests.get(f"{BASE}/printer/objects/query?print_stats", timeout=10)
    r.raise_for_status()
    stats = r.json()["result"]["status"]["print_stats"]
    print(f"state={stats['state']} file={stats.get('filename')}")


def post(path):
    r = requests.post(f"{BASE}{path}", timeout=10)
    r.raise_for_status()
    print(r.json())


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "status":
        status()
    elif cmd == "pause":
        post("/printer/print/pause")
    elif cmd == "resume":
        post("/printer/print/resume")
    else:
        sys.exit("usage: moonraker_pause.py [status|pause|resume]")
