#!/usr/bin/env python3
"""
Generate slide-deck-ready visualizations from lxml-based XML evaluation results.

Follows the same visual style as visualize_results.py but adapted for the
5-dimension lxml evaluation framework (no LLM / no agent metrics).

Usage:
    uv run python scripts/eval/visualize_lxml_results.py \
        --results-dir data/eval/eval_v2_results \
        --output-dir  data/eval/eval_v2_results/figures

    # Or pass individual JSON files:
    uv run python scripts/eval/visualize_lxml_results.py \
        --results-dir data/eval/eval_v2_results \
        --glob "*_lxml.json"
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np

# ── Style ────────────────────────────────────────────────────────────────────
plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "#f8f9fa",
    "axes.grid": True,
    "grid.alpha": 0.3,
    "font.family": "sans-serif",
    "font.size": 12,
    "axes.titlesize": 15,
    "axes.titleweight": "bold",
    "axes.labelsize": 12,
})

PALETTE = {
    "primary": "#4361ee",
    "success": "#2ec4b6",
    "warning": "#ff9f1c",
    "danger": "#e71d36",
    "dark": "#2b2d42",
    "light": "#8d99ae",
}
DIM_COLORS = ["#4361ee", "#2ec4b6", "#ff9f1c", "#7209b7", "#e71d36"]
EXPERIMENT_COLORS = ["#4361ee", "#2ec4b6", "#ff9f1c", "#e71d36", "#7209b7"]

DIMS = [
    "structural_completeness",
    "element_type_match",
    "attribute_accuracy",
    "critical_param_accuracy",
    "tag_coverage",
]
DIM_LABELS = [
    "Struct. Complete.",
    "Elem. Type Match",
    "Attr. Accuracy",
    "Critical Params",
    "Tag Coverage",
]
DIM_WEIGHTS = {
    "structural_completeness": 0.20,
    "element_type_match": 0.20,
    "attribute_accuracy": 0.25,
    "critical_param_accuracy": 0.25,
    "tag_coverage": 0.10,
}


def short_name(name: str) -> str:
    """Shorten long experiment names for chart labels."""
    mapping = {
        "AdvancedExampleViscoDruckerPrager": "ViscoDruckerPrager",
        "AdvancedWellboreExampleNonLinearThermalDiffusionTemperatureDependentVolumetricHeatCapacity": "ThermalDiffusion",
        "ExampleEDPWellbore": "EDPWellbore",
        "TutorialDeadOilEgg": "DeadOilEgg",
        "TutorialHydraulicFractureWithAdvancedXML": "HydroFrac",
    }
    return mapping.get(name, name[:25])


def infer_experiment_name(result: dict) -> str:
    """Infer the experiment name from the result dict."""
    if "experiment" in result:
        return result["experiment"]
    # Derive from gt_dir or gen_dir path
    for key in ("gt_dir", "gen_dir"):
        if key in result:
            parts = Path(result[key]).parts
            # Find the experiment folder (parent of 'inputs')
            for i, p in enumerate(parts):
                if p == "inputs" and i > 0:
                    return parts[i - 1]
            return parts[-1]
    return "unknown"


# ── Figure 1: Overall Scores ─────────────────────────────────────────────────

def fig_overall_scores(results: list[dict], out_dir: Path) -> None:
    """Horizontal bar chart of overall lxml scores (0-10)."""
    experiments = [short_name(infer_experiment_name(r)) for r in results]
    scores = [r["overall_score"] for r in results]

    fig, ax = plt.subplots(figsize=(9, 4))
    y = np.arange(len(experiments))
    bars = ax.barh(
        y, scores, height=0.55,
        color=EXPERIMENT_COLORS[: len(experiments)],
        edgecolor="white", linewidth=1.2,
    )

    for bar, s in zip(bars, scores):
        ax.text(
            bar.get_width() - 0.35,
            bar.get_y() + bar.get_height() / 2,
            f"{s:.2f}",
            va="center", ha="right", fontsize=13,
            fontweight="bold", color="white",
        )

    ax.set_yticks(y)
    ax.set_yticklabels(experiments, fontsize=12)
    ax.set_xlim(0, 10.5)
    ax.set_xlabel("lxml Reference Score (0-10)")
    ax.set_title("Overall XML Quality Scores  [lxml eval]")
    ax.axvline(
        x=np.mean(scores), color=PALETTE["dark"], linestyle="--",
        linewidth=1.2, alpha=0.6, label=f"Mean: {np.mean(scores):.2f}",
    )
    ax.legend(loc="lower right", fontsize=10)
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(out_dir / "overall_scores.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("  Saved overall_scores.png")


# ── Figure 2: Dimension Breakdown ────────────────────────────────────────────

def fig_dimension_breakdown(results: list[dict], out_dir: Path) -> None:
    """Grouped bar chart of the 5 scoring dimensions per experiment."""
    experiments = [short_name(infer_experiment_name(r)) for r in results]
    x = np.arange(len(experiments))
    w = 0.14

    fig, ax = plt.subplots(figsize=(11, 5))
    n_dims = len(DIMS)
    offsets = np.linspace(-(n_dims - 1) / 2, (n_dims - 1) / 2, n_dims) * w

    for i, (dim, label, color, offset) in enumerate(
        zip(DIMS, DIM_LABELS, DIM_COLORS, offsets)
    ):
        vals = [r["dimension_scores"][dim] * 10 for r in results]  # 0-1 → 0-10
        bars = ax.bar(
            x + offset, vals, w,
            label=f"{label}  (w={DIM_WEIGHTS[dim]:.0%})",
            color=color, edgecolor="white", linewidth=0.8,
        )
        for bar, v in zip(bars, vals):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.08,
                f"{v:.1f}",
                ha="center", va="bottom", fontsize=7.5, fontweight="bold",
            )

    ax.set_xticks(x)
    ax.set_xticklabels(experiments, fontsize=11)
    ax.set_ylim(0, 11.5)
    ax.set_ylabel("Score (0-10)")
    ax.set_title("Score Breakdown by Evaluation Dimension  [lxml eval]")
    ax.legend(loc="lower right", fontsize=8.5, ncol=2)
    fig.tight_layout()
    fig.savefig(out_dir / "dimension_breakdown.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("  Saved dimension_breakdown.png")


# ── Figure 3: Radar / Spider Chart ───────────────────────────────────────────

def fig_radar(results: list[dict], out_dir: Path) -> None:
    """Radar chart — each experiment's 5 dimension scores."""
    n = len(DIMS)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))

    for i, r in enumerate(results):
        vals = [r["dimension_scores"][d] * 10 for d in DIMS]
        vals += vals[:1]
        ax.plot(
            angles, vals, "o-", linewidth=2,
            color=EXPERIMENT_COLORS[i],
            label=short_name(infer_experiment_name(r)),
            markersize=5,
        )
        ax.fill(angles, vals, alpha=0.08, color=EXPERIMENT_COLORS[i])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(DIM_LABELS, fontsize=10)
    ax.set_ylim(0, 10.5)
    ax.set_yticks([2, 4, 6, 8, 10])
    ax.set_yticklabels(["2", "4", "6", "8", "10"], fontsize=8, color="grey")
    ax.set_title("Multi-Dimension Quality Profile  [lxml eval]", pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.45, 1.12), fontsize=9)
    fig.tight_layout()
    fig.savefig(out_dir / "radar_scores.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("  Saved radar_scores.png")


# ── Figure 4: Score Heatmap ──────────────────────────────────────────────────

def fig_score_heatmap(results: list[dict], out_dir: Path) -> None:
    """Heatmap of all experiments × dimensions (replaces tool-usage chart)."""
    experiments = [short_name(infer_experiment_name(r)) for r in results]
    # Build matrix: rows=experiments, cols=dims
    matrix = np.array([
        [r["dimension_scores"][d] * 10 for d in DIMS]
        for r in results
    ])

    fig, ax = plt.subplots(figsize=(9, max(3, len(experiments) * 0.9 + 1.5)))
    im = ax.imshow(matrix, cmap="RdYlGn", vmin=0, vmax=10, aspect="auto")

    ax.set_xticks(range(len(DIMS)))
    ax.set_xticklabels(DIM_LABELS, fontsize=10, rotation=20, ha="right")
    ax.set_yticks(range(len(experiments)))
    ax.set_yticklabels(experiments, fontsize=11)

    # Annotate each cell with the value
    for i in range(len(experiments)):
        for j in range(len(DIMS)):
            val = matrix[i, j]
            text_color = "white" if val < 3.5 or val > 8 else "black"
            ax.text(j, i, f"{val:.1f}", ha="center", va="center",
                    fontsize=10, fontweight="bold", color=text_color)

    cbar = fig.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
    cbar.set_label("Score (0-10)", fontsize=10)

    ax.set_title("Score Heatmap: Experiments × Dimensions  [lxml eval]")
    fig.tight_layout()
    fig.savefig(out_dir / "score_heatmap.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("  Saved score_heatmap.png")


# ── Figure 5: Summary Dashboard ──────────────────────────────────────────────

def fig_summary_dashboard(results: list[dict], out_dir: Path) -> None:
    """Single-slide summary — KPI boxes on top, score bar chart below."""
    fig = plt.figure(figsize=(12, 6))

    scores = [r["overall_score"] for r in results]
    mean_score = float(np.mean(scores))
    min_score = float(min(scores))
    max_score = float(max(scores))
    n_pass = sum(1 for s in scores if s >= 7.0)

    # Perfect-dim rate: fraction of (experiment, dim) pairs scoring 1.0
    all_dim_vals = [
        r["dimension_scores"][d]
        for r in results
        for d in DIMS
    ]
    perfect_pct = sum(1 for v in all_dim_vals if v >= 0.999) / len(all_dim_vals)

    kpis = [
        ("Mean Score",    f"{mean_score:.2f}/10", PALETTE["primary"]),
        ("Min Score",     f"{min_score:.2f}/10",  PALETTE["danger"]),
        ("Max Score",     f"{max_score:.2f}/10",  PALETTE["success"]),
        ("Pass Rate\n(≥7)", f"{n_pass}/{len(results)}", PALETTE["success"]),
        ("Perfect Dims",  f"{perfect_pct:.0%}",   PALETTE["warning"]),
    ]

    for i, (label, value, color) in enumerate(kpis):
        ax_kpi = fig.add_axes([0.02 + i * 0.196, 0.72, 0.176, 0.24])
        ax_kpi.set_xlim(0, 1)
        ax_kpi.set_ylim(0, 1)
        ax_kpi.add_patch(mpatches.FancyBboxPatch(
            (0.02, 0.02), 0.96, 0.96,
            boxstyle="round,pad=0.05",
            facecolor=color, alpha=0.12,
            edgecolor=color, linewidth=2,
        ))
        ax_kpi.text(0.5, 0.62, value, ha="center", va="center",
                    fontsize=20, fontweight="bold", color=color)
        ax_kpi.text(0.5, 0.25, label, ha="center", va="center",
                    fontsize=10, color=PALETTE["dark"])
        ax_kpi.axis("off")

    # Score bar chart (bottom)
    ax_bar = fig.add_axes([0.08, 0.08, 0.87, 0.55])
    experiments = [short_name(infer_experiment_name(r)) for r in results]
    x = np.arange(len(experiments))
    bars = ax_bar.bar(
        x, scores, width=0.55,
        color=EXPERIMENT_COLORS[: len(experiments)],
        edgecolor="white", linewidth=1.2,
    )
    for bar, s in zip(bars, scores):
        ax_bar.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.1,
            f"{s:.2f}",
            ha="center", va="bottom", fontsize=11, fontweight="bold",
        )

    ax_bar.set_xticks(x)
    ax_bar.set_xticklabels(experiments, fontsize=11)
    ax_bar.set_ylim(0, 11)
    ax_bar.set_ylabel("Score (0-10)")
    ax_bar.axhline(y=mean_score, color=PALETTE["dark"], linestyle="--",
                   linewidth=1, alpha=0.5, label=f"Mean: {mean_score:.2f}")
    ax_bar.axhline(y=7.0, color=PALETTE["danger"], linestyle=":",
                   linewidth=1, alpha=0.5, label="Pass threshold (7.0)")
    ax_bar.legend(fontsize=9)
    ax_bar.set_title("Per-Experiment Overall Scores", fontsize=13, fontweight="bold")

    fig.suptitle("GEOS Agent Evaluation Summary  [lxml eval]",
                 fontsize=17, fontweight="bold", y=0.99, color=PALETTE["dark"])
    fig.savefig(out_dir / "summary_dashboard.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("  Saved summary_dashboard.png")


# ── Main ─────────────────────────────────────────────────────────────────────

def load_results(results_dir: Path, glob_pattern: str) -> list[dict]:
    """Load all matching JSON result files from a directory."""
    files = sorted(results_dir.glob(glob_pattern))
    if not files:
        raise FileNotFoundError(
            f"No files matching '{glob_pattern}' found in {results_dir}"
        )
    results = []
    for f in files:
        data = json.loads(f.read_text())
        # Inject the experiment name from the filename if absent
        if "experiment" not in data:
            # Filename pattern: <ExperimentName>_lxml.json
            stem = f.stem  # e.g. "AdvancedExampleViscoDruckerPrager_lxml"
            data["experiment"] = stem.replace("_lxml", "").replace("_lxml_eval", "")
        results.append(data)
        print(f"  Loaded {f.name}  (score={data['overall_score']:.2f})")
    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Visualize lxml-based GEOS XML evaluation results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--results-dir", "-r", type=Path,
        default=Path("data/eval/eval_v2_results"),
        help="Directory containing *_lxml.json result files",
    )
    parser.add_argument(
        "--glob", "-g", type=str,
        default="*_lxml.json",
        help="Glob pattern to match result files (default: *_lxml.json)",
    )
    parser.add_argument(
        "--output-dir", "-o", type=Path,
        default=Path("data/eval/eval_v2_results/figures"),
        help="Output directory for figures",
    )
    args = parser.parse_args()

    print(f"\nLoading results from: {args.results_dir} (pattern: {args.glob})")
    results = load_results(args.results_dir, args.glob)
    if not results:
        print("No results to visualize.")
        return

    args.output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nGenerating figures for {len(results)} experiments...")
    print(f"Output: {args.output_dir}\n")

    fig_overall_scores(results, args.output_dir)
    fig_dimension_breakdown(results, args.output_dir)
    fig_radar(results, args.output_dir)
    fig_score_heatmap(results, args.output_dir)
    fig_summary_dashboard(results, args.output_dir)

    print(f"\nDone! 5 figures saved to {args.output_dir}/")


if __name__ == "__main__":
    main()
