# B6 317 → SQ23 delay tracker

This repository is an append-only, leakage-controlled forecasting scaffold for the
August 5–14, 2026 evaluation window.  It deliberately renders unavailable source
evidence as unavailable instead of inventing observations.

## Reproduce

```bash
python3 pipeline.py build --as-of 2026-08-11T12:00:00Z
python3 -m unittest discover -s tests -v
python3 -m http.server 8000
```

Open <http://localhost:8000/>. `build` deterministically regenerates the public
derivative and model reports. `append --as-of …` appends checkpoints eligible at
that instant; an existing logical checkpoint is never overwritten.

Source acquisition is intentionally adapter-based. This first draft contains no
paid credentials or scraped restricted data; source failures and unverified
schedules remain explicit in the source manifest and dashboard.

