"""Poll the Pi camera, run Roboflow Inference, alert n8n after N consecutive failure detections.

Safe-fail design: this script never talks to the printer directly. It only notifies n8n,
which decides whether to pause (pause only, never cancel).
"""
import argparse
import os
import time

import requests
from dotenv import load_dotenv
from inference_sdk import InferenceHTTPClient

load_dotenv()

API_KEY = os.environ["ROBOFLOW_API_KEY"]
MODEL_ID = os.environ["MODEL_ID"]
INFERENCE_URL = os.getenv("INFERENCE_URL", "http://localhost:9001")
SNAPSHOT_URL = os.environ["SNAPSHOT_URL"]
WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "")
FAILURE_CLASSES = {c.strip() for c in os.getenv("FAILURE_CLASSES", "spaghetti,detached").split(",")}
CONFIDENCE = float(os.getenv("CONFIDENCE", "0.6"))
CONSECUTIVE_HITS = int(os.getenv("CONSECUTIVE_HITS", "5"))
POLL_SECONDS = float(os.getenv("POLL_SECONDS", "5"))
COOLDOWN_SECONDS = float(os.getenv("COOLDOWN_SECONDS", "600"))


def grab_frame(path="/tmp/print_guard_frame.jpg"):
    r = requests.get(SNAPSHOT_URL, timeout=10)
    r.raise_for_status()
    with open(path, "wb") as f:
        f.write(r.content)
    return path


def failures_in(result):
    return [
        p for p in result.get("predictions", [])
        if p["class"] in FAILURE_CLASSES and p["confidence"] >= CONFIDENCE
    ]


def notify(hits, dry_run):
    payload = {
        "event": "print_failure_suspected",
        "classes": sorted({h["class"] for h in hits}),
        "max_confidence": max(h["confidence"] for h in hits),
        "consecutive_hits": CONSECUTIVE_HITS,
        "ts": time.time(),
    }
    if dry_run or not WEBHOOK_URL:
        print(f"[dry-run] would notify n8n: {payload}")
        return
    requests.post(WEBHOOK_URL, json=payload, timeout=10).raise_for_status()
    print(f"notified n8n: {payload}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="print detections, never notify")
    args = ap.parse_args()

    client = InferenceHTTPClient(api_url=INFERENCE_URL, api_key=API_KEY)
    streak = 0
    last_alert = 0.0

    while True:
        t0 = time.time()
        try:
            frame = grab_frame()
            result = client.infer(frame, model_id=MODEL_ID)
        except Exception as e:  # network blips are expected; log and keep going
            print(f"frame/inference error: {e}")
            streak = 0
            time.sleep(POLL_SECONDS)
            continue

        hits = failures_in(result)
        streak = streak + 1 if hits else 0
        latency_ms = (time.time() - t0) * 1000
        print(f"hits={len(hits)} streak={streak}/{CONSECUTIVE_HITS} latency={latency_ms:.0f}ms")

        if streak >= CONSECUTIVE_HITS and time.time() - last_alert > COOLDOWN_SECONDS:
            notify(hits, args.dry_run)
            last_alert = time.time()
            streak = 0

        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
