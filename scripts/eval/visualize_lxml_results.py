#!/usr/bin/env python3
"""
Publication-quality visualization of lxml XML evaluation results for GEOS agent benchmarking.

Five figures are generated, each saved as both 300-dpi PNG and vector PDF:

  fig01_performance_ranking.{png,pdf}    Ranked composite scores across all experiments
  fig02_dimension_heatmap.{png,pdf}      Per-experiment × dimension score heatmap
  fig03_score_distributions.{png,pdf}    Violin + strip distributions per dimension
  fig04_weighted_decomposition.{png,pdf} Stacked weighted contribution of each dimension
  fig05_aggregate_statistics.{png,pdf}   Score histogram, empirical CDF, dimension summary

Usage:
    uv run python scripts/eval/visualize_lxml_results.py \\
        --results-dir data/eval/eval_v2_results \\
        --output-dir  data/eval/eval_v2_results/figures
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.lines import Line2D
import numpy as np


# ──────────────────────────────────────────────────────────────────────────────
# Publication style
# ──────────────────────────────────────────────────────────────────────────────

def apply_style() -> None:
    """Apply a clean, journal-ready matplotlib style (no chartjunk)."""
    plt.rcParams.update({
        # Figure
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "savefig.dpi": 300,
        "figure.dpi": 120,
        # Axes — only bottom/left spines by default
        "axes.facecolor": "white",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.8,
        "axes.grid": False,
        # Ticks
        "xtick.direction": "out",
        "ytick.direction": "out",
        "xtick.major.size": 3.0,
        "ytick.major.size": 3.0,
        "xtick.major.width": 0.8,
        "ytick.major.width": 0.8,
        # Font — prefer a clean sans-serif
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica Neue", "Helvetica", "DejaVu Sans"],
        "font.size": 8,
        "axes.titlesize": 9,
        "axes.titleweight": "bold",
        "axes.labelsize": 8,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "legend.fontsize": 7,
        "legend.framealpha": 0.92,
        "legend.edgecolor": "#cccccc",
        "legend.handlelength": 1.6,
        # Lines / patches
        "lines.linewidth": 1.2,
        "patch.linewidth": 0.4,
        # Embed TrueType fonts in PDF/PS output
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })


# ──────────────────────────────────────────────────────────────────────────────
# Constants — mirror the evaluator's definitions
# ──────────────────────────────────────────────────────────────────────────────

DIMS = [
    "structural_completeness",
    "element_type_match",
    "attribute_accuracy",
    "tag_coverage",
]

DIM_LABELS_SHORT = [
    "Struct. Completeness",
    "Elem. Type Match",
    "Attr. Accuracy",
    "Tag Coverage",
]

DIM_LABELS_WRAPPED = [
    "Structural\nCompleteness",
    "Element\nType Match",
    "Attribute\nAccuracy",
    "Tag\nCoverage",
]

# Weights defined in lxml_xml_eval.py
WEIGHTS = {
    "structural_completeness": 0.15,
    "element_type_match":      0.40,
    "attribute_accuracy":      0.30,
    "tag_coverage":            0.15,
}

# Okabe–Ito colorblind-safe palette (one color per dimension)
DIM_COLORS = {
    "structural_completeness": "#0072B2",  # blue
    "element_type_match":      "#E69F00",  # orange
    "attribute_accuracy":      "#009E73",  # green
    "tag_coverage":            "#D55E00",  # vermillion
}

# Score-quality tiers (applied to 0–10 overall scores)
TIER_THRESHOLDS = [(7.0, "#009E73"), (5.0, "#E69F00"), (0.0, "#D55E00")]

PASS_THRESHOLD    = 7.0   # overall score (0–10)
PASS_THRESHOLD_01 = 0.70  # overall_01   (0–1)

_GREY_GRID = dict(linewidth=0.45, alpha=0.55, color="#cccccc")


# ──────────────────────────────────────────────────────────────────────────────
# Utility functions
# ──────────────────────────────────────────────────────────────────────────────

_NAME_MAP = {
    "AdvancedExampleViscoDruckerPrager": "ViscoDruckerPrager",
    "AdvancedWellboreExampleNonLinearThermalDiffusionTemperatureDependentVolumetricHeatCapacity":
        "ThermalDiffusion-HeatCap",
    "AdvancedExampleWellboreNonLinearThermalDiffusionTemperatureDependentSinglePhaseThermalConductivity":
        "ThermalDiffusion-Cond",
    "ExampleEDPWellbore": "EDPWellbore",
    "TutorialDeadOilBottomLayersSPE10": "DeadOilSPE10",
    "TutorialDeadOilEgg": "DeadOilEgg",
    "TutorialHydraulicFractureWithAdvancedXML": "HydroFracXML",
    "ExampleThermoporoelasticConsolidation": "Thermoporoelastic",
}


def experiment_name(result: dict) -> str:
    if "experiment" in result:
        return result["experiment"]
    for key in ("gt_dir", "gen_dir"):
        if key in result:
            parts = Path(result[key]).parts
            for i, part in enumerate(parts):
                if part == "inputs" and i > 0:
                    return parts[i - 1]
            return parts[-1]
    return "unknown"


def short_name(name: str, max_len: int = 30) -> str:
    abbrev = _NAME_MAP.get(name, name)
    return abbrev if len(abbrev) <= max_len else abbrev[: max_len - 1] + "\u2026"


def tier_color(score: float) -> str:
    for threshold, color in TIER_THRESHOLDS:
        if score >= threshold:
            return color
    return TIER_THRESHOLDS[-1][1]


def save_figure(fig: plt.Figure, out_dir: Path, stem: str) -> None:
    for ext in ("png", "pdf"):
        fig.savefig(out_dir / f"{stem}.{ext}", dpi=300, bbox_inches="tight")
    print(f"  Saved  {stem}.{{png,pdf}}")
    plt.close(fig)


def load_results(results_dir: Path, glob_pattern: str) -> list[dict]:
    files = sorted(results_dir.glob(glob_pattern))
    if not files:
        raise FileNotFoundError(
            f"No files matching '{glob_pattern}' in {results_dir}"
        )
    results = []
    for fp in files:
        data = json.loads(fp.read_text())
        if "experiment" not in data:
            data["experiment"] = fp.stem.replace("_lxml", "").replace("_lxml_eval", "")
        if data.get("status", "success") == "success" and "overall_score" in data:
            results.append(data)
            print(f"  Loaded  {fp.name}  (score={data['overall_score']:.2f})")
        else:
            print(f"  Skipped {fp.name}  (status={data.get('status', 'unknown')})")
    return sorted(results, key=lambda r: r["overall_score"], reverse=True)


def dim_matrix(results: list[dict]) -> np.ndarray:
    """Return an (N, 4) array of raw dimension scores (0–1)."""
    return np.array(
        [[r["dimension_scores"][d] for d in DIMS] for r in results]
    )


def _bar_height(n: int) -> float:
    return max(4.5, n * 0.22 + 1.6)


# ──────────────────────────────────────────────────────────────────────────────
# Figure 1 — Performance ranking
# ──────────────────────────────────────────────────────────────────────────────

def fig01_performance_ranking(results: list[dict], out_dir: Path) -> None:
    """Ranked horizontal bar chart of composite scores (0–10)."""
    N = len(results)
    names  = [short_name(experiment_name(r)) for r in results]
    scores = np.array([r["overall_score"] for r in results])
    mean_s = float(np.mean(scores))
    sd_s   = float(np.std(scores, ddof=1)) if N > 1 else 0.0
    n_pass = int(np.sum(scores >= PASS_THRESHOLD))

    fig, ax = plt.subplots(figsize=(5.8, _bar_height(N)))
    y = np.arange(N)

    ax.barh(
        y, scores,
        color=[tier_color(s) for s in scores],
        height=0.68, edgecolor="white", linewidth=0.4, zorder=3,
    )
    for yi, s in zip(y, scores):
        ax.text(
            s + 0.10, yi, f"{s:.2f}",
            va="center", ha="left", fontsize=6.5, fontweight="bold", color="#333333",
        )

    # Mean ± 1 SD band
    ax.axvspan(
        max(0, mean_s - sd_s), min(10, mean_s + sd_s),
        alpha=0.10, color="#444444", zorder=1,
    )
    ax.axvline(mean_s, color="#333333", lw=1.0, ls="--", zorder=4)
    ax.axvline(PASS_THRESHOLD, color="#D55E00", lw=1.0, ls=":", zorder=4)

    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=7)
    ax.invert_yaxis()
    ax.set_xlim(0, 11.0)
    ax.set_xlabel("Composite XML quality score (0–10)")
    ax.set_title("GEOS Agent XML Evaluation — Ranked Performance", pad=8)
    ax.set_axisbelow(True)
    ax.xaxis.grid(True, **_GREY_GRID)

    legend_handles = [
        mpatches.Patch(color="#009E73", label="Score \u2265 7  (high)"),
        mpatches.Patch(color="#E69F00", label="Score 5–7  (marginal)"),
        mpatches.Patch(color="#D55E00", label="Score < 5  (low)"),
        Line2D([0], [0], color="#333333", ls="--", lw=1.0,
               label=f"Mean = {mean_s:.2f}"),
        mpatches.Patch(facecolor="#888888", alpha=0.18,
                       label=f"Mean \u00b1 SD (\u00b1{sd_s:.2f})"),
        Line2D([0], [0], color="#D55E00", ls=":", lw=1.0,
               label=f"Pass threshold ({PASS_THRESHOLD:.0f})"),
    ]
    ax.legend(handles=legend_handles, loc="lower right", fontsize=6.5, ncol=1)
    ax.text(
        0.02, 0.01,
        f"n = {N}  \u00b7  pass = {n_pass}/{N} ({n_pass/N:.0%})"
        f"  \u00b7  range {scores.min():.2f}\u2013{scores.max():.2f}",
        transform=ax.transAxes, fontsize=6.5, color="#555555", va="bottom",
    )

    fig.tight_layout()
    save_figure(fig, out_dir, "fig01_performance_ranking")


# ──────────────────────────────────────────────────────────────────────────────
# Figure 2 — Dimension heatmap
# ──────────────────────────────────────────────────────────────────────────────

def fig02_dimension_heatmap(results: list[dict], out_dir: Path) -> None:
    """Annotated heatmap: experiments (rows) × evaluation dimensions (cols)."""
    N      = len(results)
    matrix = dim_matrix(results)
    row_labels = [
        f"{short_name(experiment_name(r))}  ({r['overall_score']:.2f})"
        for r in results
    ]
    col_labels = [
        f"{DIM_LABELS_SHORT[i]}\n(w = {WEIGHTS[DIMS[i]]:.0%})"
        for i in range(len(DIMS))
    ]

    height = max(5.5, N * 0.30 + 1.5)
    fig, ax = plt.subplots(figsize=(6.8, height))

    im = ax.imshow(
        matrix, cmap="RdYlGn", vmin=0.0, vmax=1.0,
        aspect="auto", interpolation="nearest",
    )

    # Cell text
    for i in range(N):
        for j in range(len(DIMS)):
            v = matrix[i, j]
            txt_col = "white" if v < 0.25 or v > 0.82 else "#222222"
            ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                    fontsize=6.5, fontweight="bold", color=txt_col)

    # White grid lines between cells
    for x in np.arange(-0.5, len(DIMS), 1):
        ax.axvline(x, color="white", lw=1.4)
    for yi in np.arange(-0.5, N, 1):
        ax.axhline(yi, color="white", lw=0.7)

    ax.set_xticks(range(len(DIMS)))
    ax.set_xticklabels(col_labels, fontsize=7.5)
    ax.set_yticks(range(N))
    ax.set_yticklabels(row_labels, fontsize=7)
    ax.tick_params(top=False, bottom=True, labeltop=False, labelbottom=True)

    cbar = fig.colorbar(im, ax=ax, shrink=0.55, pad=0.02, aspect=28)
    cbar.set_label("Dimension score (0–1)", fontsize=7.5)
    cbar.ax.tick_params(labelsize=7)

    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(0.5)
        spine.set_color("#888888")

    ax.set_title(
        "Evaluation Dimension Scores per Experiment\n"
        "(rows sorted by composite score, shown in parentheses)",
        pad=8,
    )
    fig.tight_layout()
    save_figure(fig, out_dir, "fig02_dimension_heatmap")


# ──────────────────────────────────────────────────────────────────────────────
# Figure 3 — Score distributions (violin + strip)
# ──────────────────────────────────────────────────────────────────────────────

def fig03_score_distributions(results: list[dict], out_dir: Path) -> None:
    """Violin + jittered strip plots for each scoring dimension (panels A–D)."""
    matrix = dim_matrix(results)
    N      = len(results)
    rng    = np.random.default_rng(42)

    fig, axes = plt.subplots(1, 4, figsize=(7.2, 3.4), sharey=True)

    for j, (ax, dim) in enumerate(zip(axes, DIMS)):
        values = matrix[:, j]
        color  = DIM_COLORS[dim]
        panel  = "ABCD"[j]

        # Violin body
        vp = ax.violinplot([values], positions=[0], widths=0.72,
                           showmedians=False, showextrema=False)
        for body in vp["bodies"]:
            body.set_facecolor(color)
            body.set_alpha(0.30)
            body.set_edgecolor(color)
            body.set_linewidth(0.9)

        # IQR bar + whiskers
        q1, q2, q3 = np.percentile(values, [25, 50, 75])
        lo, hi = values.min(), values.max()
        ax.vlines(0, lo, hi, color=color, lw=0.9, alpha=0.65, zorder=3)
        ax.vlines(0, q1, q3, color=color, lw=2.5, zorder=4)
        ax.plot(0, q2, "o", color="white", markersize=5.5, zorder=6,
                markeredgecolor=color, markeredgewidth=1.2)

        # Jittered individual points
        xj = rng.uniform(-0.19, 0.19, N)
        ax.scatter(xj, values, s=13, color=color, alpha=0.60,
                   edgecolors="white", linewidths=0.4, zorder=5)

        # Pass threshold reference
        ax.axhline(0.7, color="#D55E00", lw=0.85, ls=":", alpha=0.85, zorder=2)

        # Summary stats
        ax.text(
            0.97, 0.98,
            f"med = {q2:.2f}\nIQR = {q3 - q1:.2f}\nn = {N}",
            transform=ax.transAxes, ha="right", va="top",
            fontsize=6, color="#333333",
            bbox=dict(facecolor="white", edgecolor="#cccccc",
                      boxstyle="round,pad=0.25", linewidth=0.5),
        )

        ax.set_xlim(-0.50, 0.50)
        ax.set_ylim(-0.03, 1.10)
        ax.set_xticks([])
        ax.spines["bottom"].set_visible(False)
        ax.tick_params(bottom=False)

        title = f"{panel}\n{DIM_LABELS_SHORT[j]}\n(w = {WEIGHTS[dim]:.0%})"
        ax.set_title(title, fontsize=8, pad=4)

        if j == 0:
            ax.set_ylabel("Dimension score (0–1)", fontsize=8)
            ax.set_axisbelow(True)
            ax.yaxis.grid(True, **_GREY_GRID)
        else:
            ax.spines["left"].set_visible(False)
            ax.tick_params(left=False)

    fig.suptitle(
        "Distribution of Evaluation Dimension Scores Across Experiments",
        fontsize=9, fontweight="bold", y=1.02,
    )
    fig.tight_layout()
    save_figure(fig, out_dir, "fig03_score_distributions")


# ──────────────────────────────────────────────────────────────────────────────
# Figure 4 — Weighted score decomposition
# ──────────────────────────────────────────────────────────────────────────────

def fig04_weighted_decomposition(results: list[dict], out_dir: Path) -> None:
    """
    Stacked horizontal bars showing each dimension's weighted contribution
    to the composite score (sum of segments = overall score / 10).
    """
    N      = len(results)
    matrix = dim_matrix(results)
    names  = [short_name(experiment_name(r)) for r in results]

    # Contribution of each dimension: score_i × weight_i  (0–1 space)
    contrib = np.array(
        [[matrix[i, j] * WEIGHTS[DIMS[j]] for j in range(len(DIMS))]
         for i in range(N)]
    )

    fig, ax = plt.subplots(figsize=(6.2, _bar_height(N)))
    y     = np.arange(N)
    lefts = np.zeros(N)

    for j, dim in enumerate(DIMS):
        ax.barh(
            y, contrib[:, j], left=lefts, height=0.68,
            color=DIM_COLORS[dim], edgecolor="white", linewidth=0.4, zorder=2,
            label=f"{DIM_LABELS_SHORT[j]}  (w = {WEIGHTS[dim]:.0%})",
        )
        lefts += contrib[:, j]

    # Pass threshold
    ax.axvline(PASS_THRESHOLD_01, color="#333333", lw=1.0, ls=":",
               zorder=4, label=f"Pass threshold ({PASS_THRESHOLD_01:.2f})")

    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=7)
    ax.invert_yaxis()
    ax.set_xlim(0, 1.06)
    ax.set_xlabel(
        "Weighted score contribution (0–1 scale; \u00d710 for 0–10 scale)"
    )
    ax.set_title(
        "Weighted Dimension Contributions to Composite Score\n"
        "(sorted by overall performance)",
        pad=8,
    )
    ax.set_axisbelow(True)
    ax.xaxis.grid(True, **_GREY_GRID)

    # Secondary top x-axis showing 0–10 equivalent
    ax2 = ax.twiny()
    ax2.set_xlim(0, 10.6)
    ax2.set_xlabel("Composite score (0–10 scale)", fontsize=8, labelpad=4)
    ax2.spines["top"].set_visible(True)
    ax2.spines["top"].set_linewidth(0.8)
    ax2.spines["right"].set_visible(False)
    ax2.tick_params(direction="out", labelsize=7)
    ax2.xaxis.set_major_locator(mticker.MultipleLocator(1.0))

    ax.legend(loc="lower right", fontsize=6.5, framealpha=0.92,
              edgecolor="#cccccc", ncol=1)

    fig.tight_layout()
    save_figure(fig, out_dir, "fig04_weighted_decomposition")


# ──────────────────────────────────────────────────────────────────────────────
# Figure 5 — Aggregate statistics (3-panel)
# ──────────────────────────────────────────────────────────────────────────────

def fig05_aggregate_statistics(results: list[dict], out_dir: Path) -> None:
    """
    Three-panel figure:
      A  Score histogram
      B  Empirical cumulative distribution function (ECDF)
      C  Mean ± SD per dimension (horizontal bar chart)
    """
    N      = len(results)
    scores = np.array([r["overall_score"] for r in results])
    matrix = dim_matrix(results)

    mean_s   = float(np.mean(scores))
    median_s = float(np.median(scores))
    sd_s     = float(np.std(scores, ddof=1)) if N > 1 else 0.0
    pass_rate = float(np.mean(scores >= PASS_THRESHOLD))

    fig, (ax_h, ax_e, ax_d) = plt.subplots(
        1, 3, figsize=(7.8, 3.1),
        gridspec_kw={"width_ratios": [1.55, 1.55, 1.9]},
    )

    # ── Panel A: Histogram ─────────────────────────────────────────────────
    bins = np.arange(0, 10.5, 0.5)
    ax_h.hist(scores, bins=bins, color="#0072B2", alpha=0.80,
              edgecolor="white", lw=0.5, zorder=2)
    ax_h.axvline(mean_s,   color="#333333", lw=1.0, ls="--", zorder=3,
                 label=f"Mean = {mean_s:.2f}")
    ax_h.axvline(median_s, color="#009E73", lw=1.0, ls="-.", zorder=3,
                 label=f"Median = {median_s:.2f}")
    ax_h.axvline(PASS_THRESHOLD, color="#D55E00", lw=1.0, ls=":", zorder=3,
                 label=f"Pass = {PASS_THRESHOLD:.0f}")
    ax_h.set_xlim(0, 10)
    ax_h.set_xlabel("Composite XML quality score (0–10)")
    ax_h.set_ylabel("Number of experiments")
    ax_h.set_title("A\nScore distribution")
    ax_h.set_axisbelow(True)
    ax_h.yaxis.grid(True, **_GREY_GRID)
    ax_h.legend(fontsize=6.5, framealpha=0.92, loc="upper left")
    ax_h.text(
        0.98, 0.97,
        f"n = {N}\nSD = {sd_s:.2f}\npass = {pass_rate:.0%}",
        transform=ax_h.transAxes, ha="right", va="top",
        fontsize=6.5, color="#333333",
        bbox=dict(facecolor="white", edgecolor="#cccccc",
                  boxstyle="round,pad=0.3", lw=0.5),
    )

    # ── Panel B: Empirical CDF ─────────────────────────────────────────────
    sorted_s = np.sort(scores)
    ecdf     = np.arange(1, N + 1) / N
    ax_e.step(sorted_s, ecdf, where="post", color="#0072B2", lw=1.5, zorder=3)
    ax_e.scatter(sorted_s, ecdf, s=17, color="#0072B2",
                 edgecolors="white", lw=0.5, zorder=4)
    ax_e.axvline(PASS_THRESHOLD, color="#D55E00", lw=1.0, ls=":", zorder=2)
    ax_e.axhline(pass_rate, color="#D55E00", lw=0.85, ls="--", alpha=0.75,
                 zorder=2, label=f"Pass rate = {pass_rate:.0%}")
    ax_e.set_xlim(0, 10)
    ax_e.set_ylim(0, 1.07)
    ax_e.set_xlabel("Composite XML quality score (0–10)")
    ax_e.set_ylabel("Cumulative proportion")
    ax_e.set_title("B\nEmpirical CDF")
    ax_e.set_axisbelow(True)
    ax_e.xaxis.grid(True, **_GREY_GRID)
    ax_e.yaxis.grid(True, **_GREY_GRID)
    ax_e.legend(fontsize=6.5, loc="lower right", framealpha=0.92)

    # ── Panel C: Dimension mean ± SD ───────────────────────────────────────
    dim_means = matrix.mean(axis=0)
    dim_sds   = matrix.std(axis=0, ddof=1) if N > 1 else np.zeros(len(DIMS))
    order     = np.argsort(dim_means)           # ascending → bottom-to-top

    y_d   = np.arange(len(DIMS))
    means_o   = dim_means[order]
    sds_o     = dim_sds[order]
    colors_o  = [DIM_COLORS[DIMS[i]] for i in order]
    labels_o  = [DIM_LABELS_SHORT[i] for i in order]
    weights_o = [WEIGHTS[DIMS[i]] for i in order]

    ax_d.barh(
        y_d, means_o, xerr=sds_o,
        color=colors_o, height=0.60,
        edgecolor="white", lw=0.4,
        error_kw={"ecolor": "#333333", "elinewidth": 0.9, "capsize": 3.5},
        zorder=2,
    )
    for yi, m, s, w in zip(y_d, means_o, sds_o, weights_o):
        ax_d.text(
            min(1.02, m + s + 0.025), yi,
            f"{m:.2f} \u00b1 {s:.2f}  (w = {w:.0%})",
            va="center", ha="left", fontsize=6.5, color="#333333",
        )

    ax_d.axvline(0.7, color="#D55E00", lw=0.9, ls=":", zorder=3, alpha=0.85)
    ax_d.set_yticks(y_d)
    ax_d.set_yticklabels(labels_o, fontsize=7)
    ax_d.set_xlim(0, 1.65)
    ax_d.set_xlabel("Mean dimension score (0–1) \u00b1 SD")
    ax_d.set_title("C\nDimension summary")
    ax_d.set_axisbelow(True)
    ax_d.xaxis.grid(True, **_GREY_GRID)

    fig.suptitle(
        "Aggregate Evaluation Statistics — GEOS Agent XML Benchmark",
        fontsize=9, fontweight="bold", y=1.02,
    )
    fig.tight_layout()
    save_figure(fig, out_dir, "fig05_aggregate_statistics")


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate publication-quality figures from lxml eval results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--results-dir", "-r",
        type=Path,
        default=Path("data/eval/eval_v2_results"),
        help="Directory containing *_lxml.json result files",
    )
    parser.add_argument(
        "--glob", "-g",
        type=str,
        default="*_lxml.json",
        help="Glob pattern for result files (default: *_lxml.json)",
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=Path,
        default=Path("data/eval/eval_v2_results/figures"),
        help="Output directory for figures",
    )
    args = parser.parse_args()

    apply_style()

    print(f"\nLoading results from: {args.results_dir}  (pattern: {args.glob})")
    results = load_results(args.results_dir, args.glob)
    if not results:
        print("No valid results found — nothing to visualize.")
        return

    args.output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nGenerating 5 figures for {len(results)} experiments ...")
    print(f"Output: {args.output_dir}\n")

    fig01_performance_ranking(results, args.output_dir)
    fig02_dimension_heatmap(results, args.output_dir)
    fig03_score_distributions(results, args.output_dir)
    fig04_weighted_decomposition(results, args.output_dir)
    fig05_aggregate_statistics(results, args.output_dir)

    print(f"\nDone. 5 \u00d7 2 files (PNG + PDF) saved to {args.output_dir}/")


if __name__ == "__main__":
    main()
