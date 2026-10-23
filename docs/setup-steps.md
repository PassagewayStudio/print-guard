# Setup steps

## 1. Roboflow account and project
1. Log in at roboflow.com (check whether your existing account works; reset password if not).
2. Create a workspace and a new project: type **Object Detection**, name `print-failures`.
3. Classes to start with: `spaghetti`, `detached`, `good_print` (keep it small; add `blob` or `layer_shift` later).
4. Copy your API key from workspace settings into `.env` (never commit it).

## 2. Camera on the Pi
1. Confirm Crowsnest is running and the webcam works in Mainsail/Fluidd.
2. Find the snapshot URL, usually `http://<pi-ip>/webcam/?action=snapshot`. Open it in a browser to test.
3. Put it in `.env` as `SNAPSHOT_URL`.
4. Note lighting: use a consistent light source. Lighting changes are the top cause of drift.

## 3. Collect data
1. Record snapshots every 10-30 seconds during prints (a simple cron or script on the Pi, or pull from the desktop).
2. Include plenty of normal prints, not just failures.
3. Safely induce failures: print without bed adhesion, or intentionally pause/unstick a test part. Keep it safe and supervised.
4. Upload to the Roboflow project (web upload or the `roboflow` pip package).

## 4. Label and train
1. Annotate with bounding boxes in Roboflow.
2. Generate a dataset version (train/valid/test split, light augmentation: brightness, slight rotation).
3. Train with Roboflow's hosted training, then note the model ID, e.g. `print-failures/1`.
4. Review metrics and false positives; write up what you learn in `docs/incidents/`.

## 5. Run Inference on the desktop
```bash
pip install inference-cli inference-sdk
inference server start        # serves on http://localhost:9001 (Docker required)
```
Set `ROBOFLOW_API_KEY` and `MODEL_ID` in `.env`.

## 6. Run the detector
```bash
python scripts/detector.py --dry-run     # prints detections only
python scripts/detector.py               # posts to n8n after N consecutive hits
```

## 7. n8n workflow
Nodes: **Webhook** (POST) -> **IF** (print state is `printing`) -> **HTTP Request** (`POST http://<pi-ip>:7125/printer/print/pause`) -> **Slack** message with the detection details.
Test the pause call first with `scripts/moonraker_pause.py`.

## 8. Metrics (later)
Expose latency, FPS, detection counts, and consecutive-hit gauge from the detector (e.g., `prometheus_client`) and scrape into your Grafana stack.

## Safety notes
- Pause only; a human decides to resume or cancel.
- Keep printer thermal protections and never leave heaters on unattended because a model says things are fine.
- Start in dry-run until false-positive rate is acceptable.
