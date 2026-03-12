#!/usr/bin/env python3
"""
Generate analysis-oriented visualizations from lxml-based XML evaluation results.

The output is designed for interpretability first:
- ranked overall performance across simulations
- dimension score distributions and heatmaps
- explicit aggregate performance summaries
- clear top/bottom performer comparisons

Usage:
    uv run python scripts/eval/visualize_lxml_results.py \
        --results-dir data/eval/eval_v2_results \
        --output-dir data/eval/eval_v2_results/figures
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "#f8f9fa",
    "axes.grid": True,
    "grid.alpha": 0.25,
    "grid.color": "#cfd6df",
    "font.family": "sans-serif",
    "font.size": 11,
    "axes.titlesize": 14,
    "axes.titleweight": "bold",
    "axes.labelsize": 11,
})

PALETTE = {
    "primary": "#3366cc",
    "success": "#2a9d8f",
    "warning": "#f4a261",
    "danger": "#d1495b",
    "dark": "#243b53",
    "light": "#7b8da1",
}
DIM_COLORS = ["#2a9d8f", "#3366cc", "#f4a261", "#d1495b", "#6c5ce7"]

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
        "AdvancedWellboreExampleNonLinearThermalDiffusionTemperatureDependentVolumetricHeatCapacity": "ThermalDiffusionHeatCap",
        "AdvancedExampleWellboreNonLinearThermalDiffusionTemperatureDependentSinglePhaseThermalConductivity": "ThermalDiffusionCond",
        "ExampleEDPWellbore": "EDPWellbore",
        "TutorialDeadOilBottomLayersSPE10": "DeadOilSPE10",
        "TutorialDeadOilEgg": "DeadOilEgg",
        "TutorialHydraulicFractureWithAdvancedXML": "HydroFracXML",
        "ExampleThermoporoelasticConsolidation": "Thermoporoelastic",
    }
    return mapping.get(name, name[:28])


def infer_experiment_name(result: dict) -> str:
    """Infer experiment name from the result dict."""
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


def sort_results(results: list[dict]) -> list[dict]:
    """Sort results from strongest to weakest overall score."""
    return sorted(results, key=lambda r: r["overall_score"], reverse=True)


def dimension_matrix(results: list[dict]) -> np.ndarray:
    """Return dimension scores scaled from 0-1 to 0-10."""
    return np.array([
        [r["dimension_scores"][dim] * 10 for dim in DIMS]
        for r in results
    ])


def score_color(score: float) -> str:
    """Color overall scores by performance band."""
    if score >= 9.0:
        return "#1b9e77"
    if score >= 7.0:
        return "#3b82c4"
    if score >= 5.0:
        return "#f39c12"
    return "#d1495b"


def fig_overall_scores(results: list[dict], out_dir: Path) -> None:
    """Ranked overall scores for every simulation."""
    experiments = [short_name(infer_experiment_name(r)) for r in results]
    scores = np.array([r["overall_score"] for r in results])
    mean_score = float(np.mean(scores))
    pass_rate = float(np.mean(scores >= 7.0))

    fig, ax = plt.subplots(figsize=(11, max(10, len(results) * 0.3)))
    y = np.arange(len(results))
    bars = ax.barh(
        y,
        scores,
        color=[score_color(score) for score in scores],
        edgecolor="white",
        linewidth=1.0,
    )

    for bar, score in zip(bars, scores):
        ax.text(
            min(10.15, score + 0.08),
            bar.get_y() + bar.get_height() / 2,
            f"{score:.2f}",
            va="center",
            ha="left",
            fontsize=9,
            fontweight="bold",
            color=PALETTE["dark"],
        )

    ax.set_yticks(y)
    ax.set_yticklabels(experiments, fontsize=9)
    ax.set_xlim(0, 10.6)
    ax.set_xlabel("Overall lxml Score (0-10)")
    ax.set_title("Overall XML Quality by Simulation (ranked)")
    ax.axvline(mean_score, color=PALETTE["dark"], linestyle="--", linewidth=1.4, label=f"Mean: {mean_score:.2f}")
    ax.axvline(7.0, color=PALETTE["danger"], linestyle=":", linewidth=1.4, label="Pass threshold (7.0)")
    ax.text(
        0.015,
        0.012,
        f"{len(results)} simulations | pass rate {pass_rate:.0%} | "
        f"range {scores.min():.2f}-{scores.max():.2f}",
        transform=ax.transAxes,
        fontsize=10,
        color=PALETTE["dark"],
        bbox={"facecolor": "white", "edgecolor": "#d9dee7", "boxstyle": "round,pad=0.3"},
    )
    ax.legend(loc="lower right", fontsize=9)
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(out_dir / "overall_scores.png", dpi=220, bbox_inches="tight")
    plt.close(fig)
    print("  Saved overall_scores.png")


def fig_dimension_breakdown(results: list[dict], out_dir: Path) -> None:
    """Distribution of each scoring dimension across simulations."""
    matrix = dimension_matrix(results)
    means = matrix.mean(axis=0)
    stds = matrix.std(axis=0)

    fig, ax = plt.subplots(figsize=(10, 5.5))
    box = ax.boxplot(
        [matrix[:, i] for i in range(len(DIMS))],
        labels=DIM_LABELS,
        patch_artist=True,
        showmeans=True,
        meanprops={"marker": "o", "markerfacecolor": PALETTE["dark"], "markeredgecolor": "white"},
        medianprops={"color": PALETTE["dark"], "linewidth": 2},
    )

    for patch, color in zip(box["boxes"], DIM_COLORS):
        patch.set_facecolor(color)
        patch.set_alpha(0.4)
        patch.set_edgecolor("white")
        patch.set_linewidth(1.0)

    for i, (mean, std, dim) in enumerate(zip(means, stds, DIMS), start=1):
        ax.text(
            i,
            10.7,
            f"mean {mean:.2f}\nsd {std:.2f}\nw={DIM_WEIGHTS[dim]:.0%}",
            ha="center",
            va="top",
            fontsize=9,
            color=PALETTE["dark"],
        )

    ax.set_ylim(0, 11.0)
    ax.set_ylabel("Dimension Score (0-10)")
    ax.set_title("Distribution of Dimension Scores Across Simulations")
    ax.tick_params(axis="x", rotation=15)
    fig.tight_layout()
    fig.savefig(out_dir / "dimension_breakdown.png", dpi=220, bbox_inches="tight")
    plt.close(fig)
    print("  Saved dimension_breakdown.png")


def fig_top_bottom_performers(results: list[dict], out_dir: Path) -> None:
    """Side-by-side comparison of strongest and weakest simulations."""
    top = results[:10]
    bottom = list(reversed(results[-10:]))

    fig, (ax_top, ax_bottom) = plt.subplots(1, 2, figsize=(14, 6), sharex=True)

    for ax, subset, title in (
        (ax_top, top, "Top 10 Simulations"),
        (ax_bottom, bottom, "Bottom 10 Simulations"),
    ):
        labels = [short_name(infer_experiment_name(r)) for r in subset]
        scores = np.array([r["overall_score"] for r in subset])
        y = np.arange(len(subset))
        bars = ax.barh(
            y,
            scores,
            color=[score_color(score) for score in scores],
            edgecolor="white",
            linewidth=1.0,
        )
        for bar, score in zip(bars, scores):
            ax.text(
                min(10.05, score + 0.08),
                bar.get_y() + bar.get_height() / 2,
                f"{score:.2f}",
                va="center",
                ha="left",
                fontsize=9,
                fontweight="bold",
            )
        ax.set_yticks(y)
        ax.set_yticklabels(labels, fontsize=9)
        ax.set_xlim(0, 10.6)
        ax.axvline(7.0, color=PALETTE["danger"], linestyle=":", linewidth=1.2)
        ax.set_title(title)
        ax.set_xlabel("Overall Score")
        ax.invert_yaxis()

    fig.tight_layout()
    fig.savefig(out_dir / "top_bottom_performers.png", dpi=220, bbox_inches="tight")
    plt.close(fig)
    print("  Saved top_bottom_performers.png")


def fig_score_heatmap(results: list[dict], out_dir: Path) -> None:
    """Heatmap of dimension scores sorted by overall performance."""
    matrix = dimension_matrix(results)
    labels = [
        f"{short_name(infer_experiment_name(r))}  ({r['overall_score']:.2f})"
        for r in results
    ]

    fig, ax = plt.subplots(figsize=(10, max(8, len(results) * 0.34)))
    im = ax.imshow(matrix, cmap="RdYlGn", vmin=0, vmax=10, aspect="auto")

    ax.set_xticks(range(len(DIMS)))
    ax.set_xticklabels(DIM_LABELS, rotation=18, ha="right", fontsize=10)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=8.5)

    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            value = matrix[i, j]
            text_color = "white" if value < 3.5 or value > 8.0 else "black"
            ax.text(j, i, f"{value:.1f}", ha="center", va="center", fontsize=8, fontweight="bold", color=text_color)

    cbar = fig.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
    cbar.set_label("Score (0-10)")
    ax.set_title("Dimension Heatmap Sorted by Overall Score")
    fig.tight_layout()
    fig.savefig(out_dir / "score_heatmap.png", dpi=220, bbox_inches="tight")
    plt.close(fig)
    print("  Saved score_heatmap.png")


def fig_aggregate_performance(results: list[dict], out_dir: Path) -> None:
    """Overall aggregate performance across simulations."""
    scores = np.array([r["overall_score"] for r in results])
    mean_score = float(np.mean(scores))
    median_score = float(np.median(scores))
    sorted_scores = np.sort(scores)
    ecdf = np.arange(1, len(sorted_scores) + 1) / len(sorted_scores)

    fig, (ax_hist, ax_ecdf) = plt.subplots(
        2, 1, figsize=(9, 7), gridspec_kw={"height_ratios": [3, 1.6]}
    )

    bins = np.arange(0, 10.5, 0.5)
    ax_hist.hist(scores, bins=bins, color=PALETTE["primary"], edgecolor="white", linewidth=1.0, alpha=0.9)
    ax_hist.axvline(mean_score, color=PALETTE["dark"], linestyle="--", linewidth=1.4, label=f"Mean: {mean_score:.2f}")
    ax_hist.axvline(median_score, color=PALETTE["success"], linestyle="-.", linewidth=1.4, label=f"Median: {median_score:.2f}")
    ax_hist.axvline(7.0, color=PALETTE["danger"], linestyle=":", linewidth=1.4, label="Pass threshold (7.0)")
    ax_hist.set_xlim(0, 10)
    ax_hist.set_ylabel("Simulation Count")
    ax_hist.set_title("Aggregate Overall Performance Across Simulations")
    ax_hist.legend(fontsize=9)
    ax_hist.text(
        0.98,
        0.93,
        f"n = {len(scores)}\npass = {np.mean(scores >= 7.0):.0%}\n"
        f"IQR = {np.percentile(scores, 75) - np.percentile(scores, 25):.2f}",
        transform=ax_hist.transAxes,
        ha="right",
        va="top",
        fontsize=10,
        bbox={"facecolor": "white", "edgecolor": "#d9dee7", "boxstyle": "round,pad=0.3"},
    )

    ax_ecdf.step(sorted_scores, ecdf, where="post", color=PALETTE["primary"], linewidth=2.0)
    ax_ecdf.scatter(sorted_scores, ecdf, color=PALETTE["primary"], s=18, zorder=3)
    ax_ecdf.axvline(7.0, color=PALETTE["danger"], linestyle=":", linewidth=1.2)
    ax_ecdf.axhline(np.mean(scores >= 7.0), color=PALETTE["success"], linestyle="--", linewidth=1.2, label=f"Pass rate: {np.mean(scores >= 7.0):.0%}")
    ax_ecdf.set_xlim(0, 10)
    ax_ecdf.set_ylim(0, 1.02)
    ax_ecdf.set_xlabel("Overall lxml Score (0-10)")
    ax_ecdf.set_ylabel("Cumulative Share")
    ax_ecdf.legend(loc="lower right", fontsize=9)

    fig.tight_layout()
    fig.savefig(out_dir / "aggregate_performance.png", dpi=220, bbox_inches="tight")
    plt.close(fig)
    print("  Saved aggregate_performance.png")


def fig_aggregate_dimensions(results: list[dict], out_dir: Path) -> None:
    """Mean dimension performance with variability across simulations."""
    matrix = dimension_matrix(results)
    means = matrix.mean(axis=0)
    stds = matrix.std(axis=0)
    order = np.argsort(means)

    labels = [DIM_LABELS[i] for i in order]
    means_sorted = means[order]
    stds_sorted = stds[order]
    colors = [DIM_COLORS[i] for i in order]
    weights = [DIM_WEIGHTS[DIMS[i]] for i in order]

    fig, ax = plt.subplots(figsize=(9, 4.8))
    y = np.arange(len(labels))
    bars = ax.barh(
        y,
        means_sorted,
        xerr=stds_sorted,
        color=colors,
        edgecolor="white",
        linewidth=1.0,
        alpha=0.95,
        error_kw={"ecolor": PALETTE["dark"], "elinewidth": 1.1, "capsize": 4},
    )

    for bar, mean, std, weight in zip(bars, means_sorted, stds_sorted, weights):
        ax.text(
            min(10.15, mean + std + 0.1),
            bar.get_y() + bar.get_height() / 2,
            f"{mean:.2f} +/- {std:.2f}  (w={weight:.0%})",
            va="center",
            ha="left",
            fontsize=9,
            fontweight="bold",
        )

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=10)
    ax.set_xlim(0, 10.8)
    ax.set_xlabel("Mean Dimension Score (0-10)")
    ax.set_title("Average Dimension Performance Across Simulations")
    ax.axvline(means.mean(), color=PALETTE["dark"], linestyle="--", linewidth=1.2, label=f"Overall dimension mean: {means.mean():.2f}")
    ax.legend(loc="lower right", fontsize=9)

    fig.tight_layout()
    fig.savefig(out_dir / "aggregate_dimensions.png", dpi=220, bbox_inches="tight")
    plt.close(fig)
    print("  Saved aggregate_dimensions.png")


def fig_summary_dashboard(results: list[dict], out_dir: Path) -> None:
    """Compact analytical summary dashboard."""
    scores = np.array([r["overall_score"] for r in results])
    matrix = dimension_matrix(results)
    pass_count = int(np.sum(scores >= 7.0))
    weakest_idx = np.argmin(matrix, axis=1)
    weakest_counts = np.bincount(weakest_idx, minlength=len(DIMS))

    score_band_counts = np.array([
        np.sum(scores < 5.0),
        np.sum((scores >= 5.0) & (scores < 7.0)),
        np.sum((scores >= 7.0) & (scores < 9.0)),
        np.sum(scores >= 9.0),
    ])
    score_band_labels = ["< 5", "5-7", "7-9", ">= 9"]
    score_band_colors = [
        PALETTE["danger"],
        PALETTE["warning"],
        PALETTE["primary"],
        PALETTE["success"],
    ]

    fig, axes = plt.subplots(2, 2, figsize=(13, 8))
    ax_kpi, ax_bands, ax_weakest, ax_dims = axes.ravel()

    ax_kpi.axis("off")
    kpi_lines = [
        ("Simulations", f"{len(results)}"),
        ("Mean score", f"{np.mean(scores):.2f}/10"),
        ("Median score", f"{np.median(scores):.2f}/10"),
        ("Pass rate", f"{pass_count}/{len(results)} ({pass_count / len(results):.0%})"),
        ("Best simulation", f"{short_name(infer_experiment_name(results[0]))} ({scores.max():.2f})"),
        ("Worst simulation", f"{short_name(infer_experiment_name(results[-1]))} ({scores.min():.2f})"),
    ]
    ax_kpi.text(
        0.02,
        0.98,
        "\n".join(f"{label}: {value}" for label, value in kpi_lines),
        va="top",
        ha="left",
        fontsize=12,
        color=PALETTE["dark"],
        bbox={"facecolor": "white", "edgecolor": "#d9dee7", "boxstyle": "round,pad=0.5"},
    )
    ax_kpi.set_title("Key Numbers", loc="left")

    y_bands = np.arange(len(score_band_labels))
    ax_bands.barh(y_bands, score_band_counts, color=score_band_colors, edgecolor="white")
    for y_val, count in zip(y_bands, score_band_counts):
        ax_bands.text(count + 0.2, y_val, str(int(count)), va="center", ha="left", fontsize=10, fontweight="bold")
    ax_bands.set_yticks(y_bands)
    ax_bands.set_yticklabels(score_band_labels)
    ax_bands.set_xlabel("Simulation Count")
    ax_bands.set_title("Score Bands")

    y_weak = np.arange(len(DIMS))
    ax_weakest.barh(y_weak, weakest_counts, color=DIM_COLORS, edgecolor="white")
    for y_val, count in zip(y_weak, weakest_counts):
        ax_weakest.text(count + 0.2, y_val, str(int(count)), va="center", ha="left", fontsize=10, fontweight="bold")
    ax_weakest.set_yticks(y_weak)
    ax_weakest.set_yticklabels(DIM_LABELS)
    ax_weakest.set_xlabel("Count")
    ax_weakest.set_title("Most Common Weakest Dimension")

    dim_means = matrix.mean(axis=0)
    y_dims = np.arange(len(DIMS))
    ax_dims.barh(y_dims, dim_means, color=DIM_COLORS, edgecolor="white")
    for y_val, mean in zip(y_dims, dim_means):
        ax_dims.text(mean + 0.08, y_val, f"{mean:.2f}", va="center", ha="left", fontsize=10, fontweight="bold")
    ax_dims.set_yticks(y_dims)
    ax_dims.set_yticklabels(DIM_LABELS)
    ax_dims.set_xlim(0, 10.8)
    ax_dims.set_xlabel("Mean Score (0-10)")
    ax_dims.set_title("Average Dimension Scores")

    fig.suptitle("GEOS Agent Evaluation Summary [lxml eval]", fontsize=17, fontweight="bold", y=0.98, color=PALETTE["dark"])
    fig.tight_layout()
    fig.savefig(out_dir / "summary_dashboard.png", dpi=220, bbox_inches="tight")
    plt.close(fig)
    print("  Saved summary_dashboard.png")


def load_results(results_dir: Path, glob_pattern: str) -> list[dict]:
    """Load JSON result files from a directory."""
    files = sorted(results_dir.glob(glob_pattern))
    if not files:
        raise FileNotFoundError(f"No files matching '{glob_pattern}' found in {results_dir}")

    results = []
    for file_path in files:
        data = json.loads(file_path.read_text())
        if "experiment" not in data:
            data["experiment"] = file_path.stem.replace("_lxml", "").replace("_lxml_eval", "")
        results.append(data)
        print(f"  Loaded {file_path.name}  (score={data['overall_score']:.2f})")
    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Visualize lxml-based GEOS XML evaluation results",
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
        help="Glob pattern to match result files (default: *_lxml.json)",
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=Path,
        default=Path("data/eval/eval_v2_results/figures"),
        help="Output directory for figures",
    )
    args = parser.parse_args()

    print(f"\nLoading results from: {args.results_dir} (pattern: {args.glob})")
    results = sort_results(load_results(args.results_dir, args.glob))
    if not results:
        print("No results to visualize.")
        return

    args.output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nGenerating figures for {len(results)} experiments...")
    print(f"Output: {args.output_dir}\n")

    fig_overall_scores(results, args.output_dir)
    fig_dimension_breakdown(results, args.output_dir)
    fig_top_bottom_performers(results, args.output_dir)
    fig_score_heatmap(results, args.output_dir)
    fig_aggregate_performance(results, args.output_dir)
    fig_aggregate_dimensions(results, args.output_dir)
    fig_summary_dashboard(results, args.output_dir)

    print(f"\nDone! 7 figures saved to {args.output_dir}/")


if __name__ == "__main__":
    main()
