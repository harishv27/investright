"""
Thin CLI wrapper around app.risk_calibration.recalibrate().

Run from backend/:
    python -m scripts.calibrate_risk_thresholds

Regenerates backend/app/risk_bands.json, which app/risk.py loads at import
time. Re-run this whenever the questionnaire length changes, or replace the
call below with `recalibrate_from_samples(real_response_data)` once real,
anonymized user response data is available.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.risk_calibration import recalibrate

if __name__ == "__main__":
    bands = recalibrate()
    print(json.dumps(bands, indent=2))
