"""
Formats every table used in the research package (paper-numbered where
applicable) as both Markdown and CSV, from the real result JSON files.

Run from backend/:  python -m scripts.generate_tables
"""
import csv
import json
import os

HERE = os.path.dirname(__file__)
RESULTS_DIR = os.path.join(HERE, "synthetic_evaluation_results")
TABLE_DIR = os.path.join(RESULTS_DIR, "tables")
os.makedirs(TABLE_DIR, exist_ok=True)


def load(name, base=RESULTS_DIR):
    with open(os.path.join(base, name)) as f:
        return json.load(f)


def write_md(filename, header, rows):
    path = os.path.join(TABLE_DIR, filename)
    with open(path, "w") as f:
        f.write("| " + " | ".join(header) + " |\n")
        f.write("|" + "|".join(["---"] * len(header)) + "|\n")
        for row in rows:
            f.write("| " + " | ".join(str(c) for c in row) + " |\n")
    return path


def write_csv(filename, header, rows):
    path = os.path.join(TABLE_DIR, filename)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    return path


def table_iv(summary, tag):
    t = summary["table_iv_functional_validation"]
    rows = [
        ["Profiles evaluated", t["profiles_evaluated"]],
        ["Independent recompute mismatches", t["independent_recompute_mismatches"]],
        ["Profiles with negative savings", t["profiles_with_negative_savings"]],
        ["Mean savings rate", f"{t['mean_savings_rate_pct']}%"],
    ]
    write_md(f"table_iv_functional_validation_{tag}.md", ["Test", "Result"], rows)
    write_csv(f"table_iv_functional_validation_{tag}.csv", ["Test", "Result"], rows)


def table_risk_distribution(summary, tag):
    dist = summary["fig2_risk_category_distribution"]
    rows = [[cat, dist[cat]["count"], f"{dist[cat]['pct']}%"] for cat in ["Conservative", "Moderate", "Aggressive"]]
    write_md(f"risk_category_distribution_{tag}.md", ["Risk Category", "Profiles", "%"], rows)
    write_csv(f"risk_category_distribution_{tag}.csv", ["Risk Category", "Profiles", "%"], rows)


def table_v(summary, tag):
    rows = [[r["category"], r["count"], f"{r['pct']}%"] for r in summary["table_v_recommended_category_distribution"]]
    write_md(f"table_v_recommended_category_distribution_{tag}.md", ["Recommended Category", "Profiles", "%"], rows)
    write_csv(f"table_v_recommended_category_distribution_{tag}.csv", ["Recommended Category", "Profiles", "%"], rows)


def table_band_comparison(original, calibrated):
    rows = []
    for cat in ["Conservative", "Moderate", "Aggressive"]:
        rows.append([
            cat,
            f"{original['fig2_risk_category_distribution'][cat]['pct']}%",
            f"{calibrated['fig2_risk_category_distribution'][cat]['pct']}%",
        ])
    header = ["Risk Category", "Original bands (44%/72%)", "Calibrated bands (57.5%/62.5%)"]
    write_md("band_calibration_comparison.md", header, rows)
    write_csv("band_calibration_comparison.csv", header, rows)


def table_retrieval():
    r = load("retrieval_experiment_results.json", base=HERE)
    rows = [
        ["Precision@4", r["precision_at_k"]["lexical_rag"], r["precision_at_k"]["most_recent_k"], r["precision_at_k"]["random_k"]],
        ["Context size attached (chars, 100-conv. history)", r["context_size"]["lexical_rag_chars"], "n/a", "n/a"],
        ["Context size — full_history (chars)", r["context_size"]["full_history_chars"], "-", "-"],
        ["Context-assembly latency (ms, 500-conv. history)", r["latency"]["lexical_rag_ms"], r["latency"]["full_history_ms"], "-"],
        ["Stale items surfaced (of 10 seeded)", r["staleness_exposure"]["stale_items_in_lexical_rag_top_k"], r["staleness_exposure"]["stale_items_in_most_recent_k"], r["staleness_exposure"]["stale_items_in_full_history"]],
    ]
    header = ["Metric", "lexical_rag", "most_recent_k", "full_history"]
    write_md("retrieval_experiment_comparison.md", header, rows)
    write_csv("retrieval_experiment_comparison.csv", header, rows)


def table_risk_calibration():
    b = load("app/risk_bands.json", base=os.path.join(HERE, ".."))
    rows = [
        ["Lower cut", "44% of max score", f"{b['lower_pct']*100:.1f}% of max score"],
        ["Upper cut", "72% of max score", f"{b['upper_pct']*100:.1f}% of max score"],
        ["Methodology", "Illustrative (unstated justification)", b["methodology"]],
    ]
    header = ["Parameter", "Original", "Calibrated"]
    write_md("risk_band_parameters.md", header, rows)
    write_csv("risk_band_parameters.csv", header, rows)


def table_tech_stack():
    rows = [
        ["Frontend", "React 19 (Vite 8)"],
        ["Backend / API", "Python 3.13, FastAPI 0.115"],
        ["Database", "SQLite (dev) / PostgreSQL (prod-ready via SQLAlchemy 2.0)"],
        ["Auth", "JWT (python-jose), bcrypt/passlib password hashing"],
        ["Data processing", "Pure Python deterministic modules (analytics.py, risk.py, capacity.py, recommendation.py)"],
        ["OCR / document extraction", "pypdf, pytesseract, Pillow"],
        ["Agent / LLM", "Groq-hosted LLM, function calling (groq==0.31.0)"],
        ["Testing", "pytest (11/11 backend tests passing)"],
    ]
    write_md("table_iii_technology_stack.md", ["Layer", "Technology"], rows)
    write_csv("table_iii_technology_stack.csv", ["Layer", "Technology"], rows)


def main():
    original = load("original_bands_44_72_summary.json")
    calibrated = load("calibrated_bands_summary.json")

    for summary, tag in [(original, "original_bands"), (calibrated, "calibrated_bands")]:
        table_iv(summary, tag)
        table_risk_distribution(summary, tag)
        table_v(summary, tag)

    table_band_comparison(original, calibrated)
    table_retrieval()
    table_risk_calibration()
    table_tech_stack()

    print("Tables written to", TABLE_DIR)
    for f in sorted(os.listdir(TABLE_DIR)):
        print(" -", f)


if __name__ == "__main__":
    main()
