#!/usr/bin/env python3
"""
Generate slide-deck-ready visualizations from evaluation results.

Usage:
    uv run python scripts/eval/visualize_results.py \
        --results data/eval/results.json \
        --output-dir data/eval/figures
"""

import argparse
import json
from pathlib import Path
from collections import Counter

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
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
DIM_COLORS = ["#4361ee", "#2ec4b6", "#ff9f1c", "#7209b7"]
EXPERIMENT_COLORS = ["#4361ee", "#2ec4b6", "#ff9f1c", "#e71d36", "#7209b7"]


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


# ── Figure 1: Overall Scores ────────────────────────────────────────────────

def fig_overall_scores(results, out_dir):
    """Horizontal bar chart of overall LLM judge scores."""
    experiments = [short_name(r["experiment"]) for r in results]
    scores = [r["evaluation"]["scores"]["overall"] for r in results]

    fig, ax = plt.subplots(figsize=(9, 4))
    y = np.arange(len(experiments))
    bars = ax.barh(y, scores, height=0.55, color=EXPERIMENT_COLORS[:len(experiments)],
                   edgecolor="white", linewidth=1.2)

    # Score labels on bars
    for bar, s in zip(bars, scores):
        ax.text(bar.get_width() - 0.35, bar.get_y() + bar.get_height() / 2,
                f"{s:.1f}", va="center", ha="right", fontsize=13,
                fontweight="bold", color="white")

    ax.set_yticks(y)
    ax.set_yticklabels(experiments, fontsize=12)
    ax.set_xlim(0, 10.5)
    ax.set_xlabel("LLM Judge Score (0-10)")
    ax.set_title("Overall XML Quality Scores")
    ax.axvline(x=np.mean(scores), color=PALETTE["dark"], linestyle="--",
               linewidth=1.2, alpha=0.6, label=f"Mean: {np.mean(scores):.2f}")
    ax.legend(loc="lower right", fontsize=10)
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(out_dir / "overall_scores.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved overall_scores.png")


# ── Figure 2: Score Dimensions Breakdown ─────────────────────────────────────

def fig_dimension_breakdown(results, out_dir):
    """Grouped bar chart of the 4 scoring dimensions per experiment."""
    experiments = [short_name(r["experiment"]) for r in results]
    dims = ["structural_correctness", "parameter_accuracy", "completeness", "semantic_equivalence"]
    dim_labels = ["Structure", "Parameters", "Completeness", "Semantics"]

    x = np.arange(len(experiments))
    w = 0.18
    fig, ax = plt.subplots(figsize=(10, 5))

    for i, (dim, label, color) in enumerate(zip(dims, dim_labels, DIM_COLORS)):
        vals = [r["evaluation"]["scores"][dim] for r in results]
        offset = (i - 1.5) * w
        bars = ax.bar(x + offset, vals, w, label=label, color=color,
                      edgecolor="white", linewidth=0.8)
        # Value labels
        for bar, v in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.08,
                    f"{v:.0f}", ha="center", va="bottom", fontsize=8, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(experiments, fontsize=11)
    ax.set_ylim(0, 11)
    ax.set_ylabel("Score (0-10)")
    ax.set_title("Score Breakdown by Evaluation Dimension")
    ax.legend(loc="lower right", fontsize=10, ncol=2)
    fig.tight_layout()
    fig.savefig(out_dir / "dimension_breakdown.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved dimension_breakdown.png")


# ── Figure 3: Radar / Spider Chart (aggregate) ──────────────────────────────

def fig_radar(results, out_dir):
    """Radar chart showing each experiment's 4 dimension scores."""
    dims = ["structural_correctness", "parameter_accuracy", "completeness", "semantic_equivalence"]
    dim_labels = ["Structure", "Parameters", "Completeness", "Semantics"]
    n = len(dims)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    angles += angles[:1]  # close polygon

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))

    for i, r in enumerate(results):
        vals = [r["evaluation"]["scores"][d] for d in dims]
        vals += vals[:1]
        ax.plot(angles, vals, "o-", linewidth=2, color=EXPERIMENT_COLORS[i],
                label=short_name(r["experiment"]), markersize=5)
        ax.fill(angles, vals, alpha=0.08, color=EXPERIMENT_COLORS[i])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(dim_labels, fontsize=11)
    ax.set_ylim(0, 10.5)
    ax.set_yticks([2, 4, 6, 8, 10])
    ax.set_yticklabels(["2", "4", "6", "8", "10"], fontsize=8, color="grey")
    ax.set_title("Multi-Dimension Quality Profile", pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.1), fontsize=9)
    fig.tight_layout()
    fig.savefig(out_dir / "radar_scores.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved radar_scores.png")


# ── Figure 4: Tool Usage & Errors ────────────────────────────────────────────

def fig_tool_usage(results, out_dir):
    """Stacked bar chart of tool calls per experiment, with error overlay."""
    experiments = [short_name(r["experiment"]) for r in results]

    # Collect all tool names across experiments
    all_tools = set()
    for r in results:
        if "agent_metrics" in r:
            all_tools.update(r["agent_metrics"]["tool_errors"]["tool_stats"].keys())
    # Clean up tool names (e.g., " fetch_code" → "fetch_code")
    tool_order = sorted({t.strip() for t in all_tools})

    # Build data matrix: experiments × tools
    calls_matrix = []
    errors_matrix = []
    for r in results:
        calls_row = []
        errors_row = []
        if "agent_metrics" in r:
            stats = r["agent_metrics"]["tool_errors"]["tool_stats"]
            for tool in tool_order:
                # Check both stripped and unstripped names
                s = stats.get(tool, stats.get(f" {tool}", {"calls": 0, "errors": 0}))
                calls_row.append(s["calls"])
                errors_row.append(s["errors"])
        else:
            calls_row = [0] * len(tool_order)
            errors_row = [0] * len(tool_order)
        calls_matrix.append(calls_row)
        errors_matrix.append(errors_row)

    calls_arr = np.array(calls_matrix)
    errors_arr = np.array(errors_matrix)

    # Assign a color per tool
    tool_cmap = plt.cm.Set3(np.linspace(0, 1, len(tool_order)))

    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(experiments))
    bottoms = np.zeros(len(experiments))

    for j, tool in enumerate(tool_order):
        ax.bar(x, calls_arr[:, j], bottom=bottoms, width=0.6,
               label=tool, color=tool_cmap[j], edgecolor="white", linewidth=0.5)
        bottoms += calls_arr[:, j]

    # Overlay total errors as text
    for i in range(len(experiments)):
        total_errors = int(errors_arr[i].sum())
        total_calls = int(calls_arr[i].sum())
        if total_errors > 0:
            ax.text(x[i], bottoms[i] + 0.8,
                    f"{total_errors} err\n({total_errors/total_calls:.0%})",
                    ha="center", va="bottom", fontsize=9, color=PALETTE["danger"],
                    fontweight="bold")
        else:
            ax.text(x[i], bottoms[i] + 0.8, "0 err", ha="center", va="bottom",
                    fontsize=9, color=PALETTE["success"], fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(experiments, fontsize=11)
    ax.set_ylabel("Tool Calls")
    ax.set_title("Agent Tool Usage by Experiment")
    ax.legend(loc="upper right", fontsize=8, ncol=2,
              bbox_to_anchor=(1.0, 1.0))
    fig.tight_layout()
    fig.savefig(out_dir / "tool_usage.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved tool_usage.png")


# ── Figure 5: Error Rate Lollipop ────────────────────────────────────────────

def fig_error_rates(results, out_dir):
    """Lollipop chart of per-experiment tool error rates."""
    experiments = []
    error_rates = []
    total_calls_list = []

    for r in results:
        if "agent_metrics" in r:
            experiments.append(short_name(r["experiment"]))
            er = r["agent_metrics"]["tool_errors"]["error_rate"]
            error_rates.append(er * 100)  # percent
            total_calls_list.append(r["agent_metrics"]["tool_errors"]["total_tool_calls"])

    fig, ax = plt.subplots(figsize=(8, 4))
    y = np.arange(len(experiments))

    # Stems
    for i in range(len(experiments)):
        color = PALETTE["success"] if error_rates[i] < 5 else (
            PALETTE["warning"] if error_rates[i] < 10 else PALETTE["danger"])
        ax.hlines(y[i], 0, error_rates[i], color=color, linewidth=2.5)
        ax.plot(error_rates[i], y[i], "o", color=color, markersize=10, zorder=5)
        ax.text(error_rates[i] + 0.4, y[i],
                f"{error_rates[i]:.1f}%  ({total_calls_list[i]} calls)",
                va="center", fontsize=10, color=PALETTE["dark"])

    ax.set_yticks(y)
    ax.set_yticklabels(experiments, fontsize=11)
    ax.set_xlabel("Tool Error Rate (%)")
    ax.set_title("Agent Tool Error Rates")
    ax.set_xlim(-0.5, max(error_rates) + 5)
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(out_dir / "error_rates.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved error_rates.png")


# ── Figure 6: Summary Dashboard ─────────────────────────────────────────────

def fig_summary_dashboard(results, out_dir):
    """Single-slide summary with key metrics in large KPI boxes + score chart."""
    fig = plt.figure(figsize=(12, 6))

    # Compute aggregate metrics
    scores = [r["evaluation"]["scores"]["overall"] for r in results]
    mean_score = np.mean(scores)
    min_score = min(scores)

    total_calls = sum(
        r["agent_metrics"]["tool_errors"]["total_tool_calls"]
        for r in results if "agent_metrics" in r)
    total_errors = sum(
        r["agent_metrics"]["tool_errors"]["total_errors"]
        for r in results if "agent_metrics" in r)
    overall_error_rate = total_errors / total_calls if total_calls else 0

    n_success = sum(1 for r in results if r["status"] == "success")
    n_critical = sum(
        len(r["evaluation"].get("critical_errors", []))
        for r in results if r["status"] == "success")

    # KPI boxes (top row)
    kpis = [
        ("Mean Score", f"{mean_score:.1f}/10", PALETTE["primary"]),
        ("Min Score", f"{min_score:.1f}/10", PALETTE["success"]),
        ("Success Rate", f"{n_success}/{len(results)}", PALETTE["success"]),
        ("Error Rate", f"{overall_error_rate:.1%}", PALETTE["warning"]),
        ("Critical Errors", str(n_critical), PALETTE["danger"] if n_critical else PALETTE["success"]),
    ]

    for i, (label, value, color) in enumerate(kpis):
        ax_kpi = fig.add_axes([0.02 + i * 0.196, 0.72, 0.176, 0.24])
        ax_kpi.set_xlim(0, 1)
        ax_kpi.set_ylim(0, 1)
        ax_kpi.add_patch(mpatches.FancyBboxPatch(
            (0.02, 0.02), 0.96, 0.96, boxstyle="round,pad=0.05",
            facecolor=color, alpha=0.12, edgecolor=color, linewidth=2))
        ax_kpi.text(0.5, 0.62, value, ha="center", va="center",
                    fontsize=22, fontweight="bold", color=color)
        ax_kpi.text(0.5, 0.25, label, ha="center", va="center",
                    fontsize=10, color=PALETTE["dark"])
        ax_kpi.axis("off")

    # Score bar chart (bottom row)
    ax_bar = fig.add_axes([0.08, 0.08, 0.87, 0.55])
    experiments = [short_name(r["experiment"]) for r in results]
    x = np.arange(len(experiments))
    bars = ax_bar.bar(x, scores, width=0.55, color=EXPERIMENT_COLORS[:len(experiments)],
                      edgecolor="white", linewidth=1.2)
    for bar, s in zip(bars, scores):
        ax_bar.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                    f"{s:.1f}", ha="center", va="bottom", fontsize=11, fontweight="bold")

    ax_bar.set_xticks(x)
    ax_bar.set_xticklabels(experiments, fontsize=11)
    ax_bar.set_ylim(0, 11)
    ax_bar.set_ylabel("Score")
    ax_bar.axhline(y=mean_score, color=PALETTE["dark"], linestyle="--",
                   linewidth=1, alpha=0.5)
    ax_bar.set_title("Per-Experiment Overall Scores", fontsize=13, fontweight="bold")

    fig.suptitle("GEOS Agent Evaluation Summary", fontsize=17, fontweight="bold",
                 y=0.99, color=PALETTE["dark"])
    fig.savefig(out_dir / "summary_dashboard.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved summary_dashboard.png")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Visualize GEOS agent evaluation results")
    parser.add_argument("--results", "-r", type=Path, default=Path("data/eval/results.json"),
                        help="Path to results JSON")
    parser.add_argument("--output-dir", "-o", type=Path, default=Path("data/eval/figures"),
                        help="Output directory for figures")
    args = parser.parse_args()

    with open(args.results) as f:
        data = json.load(f)

    results = [r for r in data["results"] if r["status"] == "success"]
    if not results:
        print("No successful experiments to visualize.")
        return

    args.output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating figures for {len(results)} experiments...")
    print(f"Model: {data.get('model', 'unknown')}")
    print(f"Output: {args.output_dir}\n")

    fig_overall_scores(results, args.output_dir)
    fig_dimension_breakdown(results, args.output_dir)
    fig_radar(results, args.output_dir)
    fig_tool_usage(results, args.output_dir)
    fig_error_rates(results, args.output_dir)
    fig_summary_dashboard(results, args.output_dir)

    print(f"\nDone! {6} figures saved to {args.output_dir}/")


if __name__ == "__main__":
    main()
