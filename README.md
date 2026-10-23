# print-guard

Computer-vision print-failure detection for a Klipper 3D printer, built on the Roboflow stack.

A camera on a Raspberry Pi (Klipper + Moonraker + Crowsnest) is polled by a detector running Roboflow Inference on a GPU desktop. After several consecutive failure detections, the detector notifies an n8n workflow, which pauses the print through Moonraker and sends a Slack alert. OctoApp stays the phone-side monitor.

```
Pi (Klipper/Moonraker/Crowsnest)
   |  snapshot URL                    ^ POST /printer/print/pause
   v                                  |
Desktop: Roboflow Inference --> detector.py --> n8n webhook --> Slack alert
                                       |
                                       +--> metrics (latency, detections) --> Prometheus/Grafana
```

## Goals
- Hands-on experience with the Roboflow workflow: capture, annotate, train, deploy, monitor.
- A documented set of failures and root-cause write-ups (see `docs/incidents/`).
- Safe-fail behavior: pause only, never cancel; require N consecutive detections.

## Layout
- `docs/setup-steps.md` - step-by-step start guide
- `docs/incidents/` - one write-up per problem hit (symptom, cause, fix, prevention)
- `scripts/detector.py` - polls the camera, runs inference, alerts n8n
- `scripts/moonraker_pause.py` - test the pause/resume API by hand
- `.env.example` - configuration

## Quick start
```bash
cp .env.example .env        # fill in values
pip install -r requirements.txt
python scripts/moonraker_pause.py status
python scripts/detector.py --dry-run
```

## Status
- [ ] Camera streaming from the Pi
- [ ] Dataset collected and labeled in Roboflow
- [ ] Model trained (v1)
- [ ] Inference server running on desktop
- [ ] Detector dry-run working
- [ ] n8n workflow wired to Moonraker + Slack
- [ ] Metrics into Grafana
- [ ] First real failure caught
