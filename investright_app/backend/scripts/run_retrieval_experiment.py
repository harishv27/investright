"""
Offline RAG comparison experiment (no LLM calls, no API key required).

Run from backend/:
    python -m scripts.run_retrieval_experiment

Wraps app.retrieval_eval.run_all() and writes the result to
scripts/retrieval_experiment_results.json alongside a printed summary. See
app/retrieval_eval.py for the full methodology of each metric, and
scripts/run_rag_experiment.py for the companion LLM-dependent experiment
(unsupported-number rate, faithfulness, latency, token cost) which does
require GROQ_API_KEY.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.retrieval_eval import run_all

if __name__ == "__main__":
    results = run_all()
    out_path = Path(__file__).resolve().parent / "retrieval_experiment_results.json"
    out_path.write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))
    print(f"\nSaved to {out_path}")
