# Project Memory

## Project Overview
- GEOS geophysics simulation agent — generates XML configuration files for GEOS simulator
- Eval pipeline compares agent-generated XMLs against ground truth

## Key Paths
- Ground truth XMLs: `data/eval/experiments_gt/<ExperimentName>/inputs/`
- Agent-generated XMLs: `data/eval/experiments_subset/<ExperimentName>/inputs/`
- Eval results (v2): `data/eval/eval_v2_results/`  ← renamed from old results folder
- Figures: `data/eval/eval_v2_results/figures/`

## Evaluation Frameworks
### lxml-based (new, preferred)
- Script: `scripts/eval/lxml_xml_eval.py`
- No LLM needed — programmatic comparison using lxml
- 5 dimensions: structural_completeness (w=0.20), element_type_match (w=0.20),
  attribute_accuracy (w=0.25), critical_param_accuracy (w=0.25), tag_coverage (w=0.10)
- Output JSON has: `overall_score` (0-10), `dimension_scores` (0-1 each)
- CLI: `uv run python scripts/eval/lxml_xml_eval.py --ground-truth-dir ... --generated-dir ... --output ...`

### LLM-judge (old)
- Script: `scripts/eval/llm_judge_xml.py`
- Uses OpenRouter API (OPENROUTER_API_KEY env var)
- 4 dimensions: structural_correctness, parameter_accuracy, completeness, semantic_equivalence

## Visualization
- lxml viz script: `scripts/eval/visualize_lxml_results.py`
  - Input: `--results-dir data/eval/eval_v2_results` (loads `*_lxml.json` files)
  - Output: 5 figures — overall_scores, dimension_breakdown, radar_scores, score_heatmap, summary_dashboard
- Old viz script: `scripts/eval/visualize_results.py` (for LLM judge results format)

## Benchmark Results (eval_v2, lxml)
| Experiment | Overall |
|---|---|
| ViscoDruckerPrager | 9.12 |
| ThermalDiffusion | 10.00 |
| EDPWellbore | 9.61 |
| DeadOilEgg | 9.77 |
| HydroFrac | 6.70 (parse warning: double hyphen in comment) |
| **Mean** | **9.04** |

## Notes
- Always use `uv run python ...` for running scripts
- HydroFrac GT has a malformed XML comment (double hyphen) — lxml skips that file with a warning
- lxml eval scores 0-1 internally; `overall_score` is 0-10
- Exit code 1 from lxml eval = score < 7.0 (not an error)
