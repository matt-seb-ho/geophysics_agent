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
- 4 dimensions: structural_completeness (w=0.167), element_type_match (w=0.333),
  attribute_accuracy (w=0.278), tag_coverage (w=0.222)
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

## RAG Collections (ChromaDB at data/vector_db/)
| Collection | Purpose | Chunks |
|---|---|---|
| `geos_navigator` | RST prose for conceptual navigation (doc/section chunks) | 571 |
| `geos_technical` | XML shadow embeddings from `literalinclude` in Example.rst | 334 |
| `geos_schema` | Per-element attribute specs parsed from XSD | 250 |

- `geos_schema` source XSD: `data/geos_schema.xsd` (8938 lines, 2541 documented attrs, 250 complexTypes)
- `/home/brianliu/geosx_schema.xsd` = slightly older version (263 types); `/home/brianliu/geosx_schema.xsd.other` = stripped (no xsd:unique, mangled C++ type names) — neither used
- Schema chunks contain full attribute specs inline — no `fetch_code` needed after schema search
- `xml_reference` removed from navigator collection (was always null there)
- `fetch_code` blocks both `.xml` AND `.rst` from excluded experiment dirs (RAG contamination prevention)
- Build pipeline: `parse_xsd_schema.py` → `build_schema_index.py`
- Tool: `SearchSchemaTool` (search_schema) registered in utils.py

## Notes
- Always use `uv run python ...` for running scripts
- HydroFrac GT has a malformed XML comment (double hyphen) — lxml skips that file with a warning
- lxml eval scores 0-1 internally; `overall_score` is 0-10
- Exit code 1 from lxml eval = score < 7.0 (not an error)
