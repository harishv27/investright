"""
Generates every figure used in the research package from the real result
JSON files already produced by run_synthetic_evaluation.py,
run_retrieval_experiment.py, and calibrate_risk_thresholds.py.

Run from backend/:  python -m scripts.generate_figures
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(__file__)
RESULTS_DIR = os.path.join(HERE, "synthetic_evaluation_results")
FIG_DIR = os.path.join(RESULTS_DIR, "figures")
os.makedirs(FIG_DIR, exist_ok=True)

COLORS = {"Conservative": "#4C72B0", "Moderate": "#DD8452", "Aggressive": "#C44E52"}


def load(name):
    with open(os.path.join(RESULTS_DIR, name)) as f:
        return json.load(f)


def fig_risk_distribution(summary, filename, title):
    dist = summary["fig2_risk_category_distribution"]
    cats = ["Conservative", "Moderate", "Aggressive"]
    counts = [dist[c]["count"] for c in cats]
    pcts = [dist[c]["pct"] for c in cats]

    fig, ax = plt.subplots(figsize=(6.5, 4.6))
    bars = ax.bar(cats, counts, color=[COLORS[c] for c in cats], width=0.55)
    for bar, pct, count in zip(bars, pcts, counts):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 3,
                 f"{count} ({pct}%)", ha="center", va="bottom", fontsize=10)
    ax.set_ylabel("Number of profiles")
    ax.set_title(title, fontsize=11, wrap=True)
    ax.set_ylim(0, max(counts) * 1.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, filename), dpi=200)
    plt.close(fig)


def fig_recommendation_distribution(summary, filename, title):
    rows = summary["table_v_recommended_category_distribution"]
    labels = [r["category"] for r in rows]
    counts = [r["count"] for r in rows]

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    bars = ax.barh(labels, counts, color="#4C72B0")
    for bar, count in zip(bars, counts):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                 str(count), va="center", fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel("Number of profiles (N=240)")
    ax.set_title(title)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, filename), dpi=200)
    plt.close(fig)


def fig_band_comparison(original, calibrated):
    cats = ["Conservative", "Moderate", "Aggressive"]
    orig_pct = [original["fig2_risk_category_distribution"][c]["pct"] for c in cats]
    calib_pct = [calibrated["fig2_risk_category_distribution"][c]["pct"] for c in cats]

    x = range(len(cats))
    width = 0.35
    fig, ax = plt.subplots(figsize=(6.5, 4.3))
    ax.bar([i - width / 2 for i in x], orig_pct, width, label="Original bands (44% / 72%)", color="#C44E52")
    ax.bar([i + width / 2 for i in x], calib_pct, width, label="Calibrated bands (57.5% / 62.5%)", color="#4C72B0")
    ax.axhline(33.3, color="gray", linestyle="--", linewidth=1, label="33% target (tertile)")
    ax.set_xticks(list(x))
    ax.set_xticklabels(cats)
    ax.set_ylabel("% of 240 profiles")
    ax.set_title("Effect of risk-band calibration on classifier skew")
    ax.legend(fontsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig3_band_calibration_effect.png"), dpi=200)
    plt.close(fig)


def fig_retrieval_comparison():
    with open(os.path.join(HERE, "retrieval_experiment_results.json")) as f:
        r = json.load(f)

    fig, axes = plt.subplots(1, 3, figsize=(12, 4))

    modes = ["lexical_rag", "most_recent_k", "random_k"]
    prec = [r["precision_at_k"][m] for m in modes]
    axes[0].bar(modes, prec, color=["#4C72B0", "#DD8452", "#C44E52"])
    axes[0].set_title("Precision@4")
    axes[0].set_ylim(0, 1.05)
    for i, v in enumerate(prec):
        axes[0].text(i, v + 0.02, f"{v:.2f}", ha="center", fontsize=9)

    cs = r["context_size"]
    labels = ["no_memory", "lexical_rag", "full_history"]
    values = [cs["no_memory_chars"], cs["lexical_rag_chars"], cs["full_history_chars"]]
    axes[1].bar(labels, values, color=["#8172B2", "#4C72B0", "#C44E52"])
    axes[1].set_title("Context size attached (chars)")
    for i, v in enumerate(values):
        axes[1].text(i, v + max(values) * 0.02, str(v), ha="center", fontsize=9)

    stale = r["staleness_exposure"]
    labels2 = ["full_history", "most_recent_k", "lexical_rag"]
    values2 = [stale["stale_items_in_full_history"], stale["stale_items_in_most_recent_k"], stale["stale_items_in_lexical_rag_top_k"]]
    axes[2].bar(labels2, values2, color=["#C44E52", "#DD8452", "#4C72B0"])
    axes[2].set_title("Stale items surfaced (of 10 seeded)")
    for i, v in enumerate(values2):
        axes[2].text(i, v + 0.2, str(v), ha="center", fontsize=9)

    for ax in axes:
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.tick_params(axis="x", labelrotation=20)

    fig.suptitle("Retrieval-mode comparison: lexical_rag vs. full_history vs. baselines")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig4_retrieval_comparison.png"), dpi=200)
    plt.close(fig)


def main():
    original = load("original_bands_44_72_summary.json")
    calibrated = load("calibrated_bands_summary.json")

    fig_risk_distribution(
        original, "fig2_risk_distribution_original_bands.png",
        "Fig. 2 — Risk category distribution (N=240, original 44%/72% bands)"
    )
    fig_risk_distribution(
        calibrated, "fig2b_risk_distribution_calibrated_bands.png",
        "Risk category distribution (N=240, calibrated bands)"
    )
    fig_recommendation_distribution(
        original, "fig_recommendation_distribution_original.png",
        "Recommended investment category distribution (original bands)"
    )
    fig_recommendation_distribution(
        calibrated, "fig_recommendation_distribution_calibrated.png",
        "Recommended investment category distribution (calibrated bands)"
    )
    fig_band_comparison(original, calibrated)
    fig_retrieval_comparison()

    print("Figures written to", FIG_DIR)
    for f in sorted(os.listdir(FIG_DIR)):
        print(" -", f)


if __name__ == "__main__":
    main()
