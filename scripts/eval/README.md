# LLM-Based Evaluation Pipeline

This directory contains scripts for evaluating GEOS agent outputs using LLM-as-a-judge.

## Overview

The evaluation pipeline compares agent-generated XML files against ground truth using an LLM judge. It handles XML imports/includes and provides structured scoring across multiple dimensions.

## Scripts

### 1. `compute_agent_metrics.py` - Agent Execution Metrics

Analyzes JSONL logs to compute tool error rates and RAG retrieval accuracy.

```bash
# Analyze a single log
uv run python scripts/eval/compute_agent_metrics.py \
    --log data/eval/logs/ExampleEDPWellbore.jsonl

# With RAG accuracy (requires expected source path)
uv run python scripts/eval/compute_agent_metrics.py \
    --log data/eval/logs/ExampleEDPWellbore.jsonl \
    --source-path "src/docs/sphinx/advancedExamples/edpWellbore/Example.rst"

# Batch analysis
uv run python scripts/eval/compute_agent_metrics.py \
    --logs-dir data/eval/logs \
    --output data/eval/agent_metrics.json
```

**Metrics Computed:**

**Tool Error Tracking:**
- Total tool calls and errors
- Per-tool error rates
- Error messages with context
- Success/failure breakdown

**RAG Retrieval Accuracy** (if `--source-path` provided):
- % of retrieved chunks from the expected document
- Total searches and chunks retrieved
- Per-tool retrieval statistics
- Searches that found relevant chunks

### 2. `setup_ground_truth.py` - Prepare Evaluation Directories

Creates ground truth directories and manifest files for experiments.

```bash
# Set up a single experiment
uv run python scripts/eval/setup_ground_truth.py \
    --experiment data/eval/experiments_subset/ExampleEDPWellbore \
    --entry-point main.xml

# Auto-detect XML files from inputs/ directory
uv run python scripts/eval/setup_ground_truth.py \
    --experiment data/eval/experiments_subset/ExampleEDPWellbore \
    --auto-detect

# Batch setup for all experiments
uv run python scripts/eval/setup_ground_truth.py \
    --experiments-dir data/eval/experiments_subset \
    --auto-detect
```

**After running:** Copy your ground truth XML files into the created `ground_truth/` directories.

### 3. `llm_judge_xml.py` - Single File Comparison

Compares a single generated XML against ground truth using LLM evaluation.

```bash
# Basic comparison
uv run python scripts/eval/llm_judge_xml.py \
    --ground-truth data/eval/experiments_subset/Example1/ground_truth/main.xml \
    --generated data/eval/experiments_subset/Example1/inputs/simulation.xml

# With import resolution (resolves <Included> tags)
uv run python scripts/eval/llm_judge_xml.py \
    --ground-truth data/eval/experiments_subset/Example1/ground_truth/main.xml \
    --generated data/eval/experiments_subset/Example1/inputs/simulation.xml \
    --resolve-imports

# Custom model and save results
uv run python scripts/eval/llm_judge_xml.py \
    --ground-truth gt.xml \
    --generated gen.xml \
    --model "anthropic/claude-3.5-sonnet" \
    --output evaluation_results.json
```

**Scoring Dimensions:**
- **Structural Correctness** (0-10): XML structure, tags, hierarchy
- **Parameter Accuracy** (0-10): Parameter values, units, names
- **Completeness** (0-10): All necessary components present
- **Semantic Equivalence** (0-10): Accomplishes same simulation goals

### 4. `batch_evaluate.py` - Evaluate Multiple Experiments

Runs LLM judge across multiple experiments and aggregates results.

```bash
# Evaluate all experiments
uv run python scripts/eval/batch_evaluate.py \
    --experiments-dir data/eval/experiments_subset

# Evaluate specific experiments
uv run python scripts/eval/batch_evaluate.py \
    --experiments-dir data/eval/experiments_subset \
    --experiments ExampleEDPWellbore TutorialDeadOilEgg

# Verbose output with detailed scores
uv run python scripts/eval/batch_evaluate.py \
    --experiments-dir data/eval/experiments_subset \
    --verbose \
    --output data/eval/batch_results.json

# Use a different model
uv run python scripts/eval/batch_evaluate.py \
    --experiments-dir data/eval/experiments_subset \
    --model "anthropic/claude-3.5-sonnet"

# Include agent metrics from JSONL logs
uv run python scripts/eval/batch_evaluate.py \
    --experiments-dir data/eval/experiments_subset \
    --jsonl-log-dir data/eval/jsonl_logs \
    --source-path "src/docs/sphinx/advancedExamples/edpWellbore/Example.rst"
```

When `--jsonl-log-dir` is provided, the batch evaluator will automatically compute agent metrics (tool errors and RAG accuracy) alongside XML evaluation scores.

## Directory Structure

Expected structure for each experiment:

```
experiments_subset/
├── ExampleEDPWellbore/
│   ├── instructions.txt          # Natural language specification
│   ├── ground_truth/             # Ground truth files
│   │   ├── manifest.json         # Defines which files to compare
│   │   ├── main.xml              # Ground truth XML
│   │   └── base.xml              # Optional: imported files
│   └── inputs/                   # Agent-generated files
│       └── simulation.xml
└── TutorialDeadOilEgg/
    └── ...
```

## Manifest Format

The `manifest.json` file defines which files to compare:

```json
{
  "entry_point": "main.xml",
  "additional_files": ["base.xml"],
  "ground_truth_dir": "ground_truth",
  "generated_dir": "inputs"
}
```

**Fields:**
- `entry_point`: Main XML file to compare (required)
- `additional_files`: List of additional files to compare (optional)
- `ground_truth_dir`: Directory with ground truth files (default: `ground_truth`)
- `generated_dir`: Directory with generated files (default: `inputs`)

## XML Import Resolution

The evaluation scripts can resolve XML imports/includes (e.g., GEOS `<Included>` tags) before comparison:

```xml
<!-- main.xml -->
<Problem>
  <Included File="base.xml"/>
  <!-- other content -->
</Problem>
```

Use the `--resolve-imports` flag to flatten the XML tree before comparison. This ensures that imports are properly handled.

## Complete Evaluation Metrics

The evaluation pipeline now tracks three types of metrics:

### 1. **XML Quality** (LLM-as-judge)
- Structural correctness
- Parameter accuracy
- Completeness
- Semantic equivalence

### 2. **Tool Execution** (from JSONL logs)
- Error rates per tool
- Total failures and successes
- Error messages with context

### 3. **RAG Retrieval Accuracy** (from JSONL logs)
- % of chunks from expected source document
- Total chunks retrieved
- Search effectiveness

## Workflow

### 1. Set up ground truth directories

```bash
uv run python scripts/eval/setup_ground_truth.py \
    --experiments-dir data/eval/experiments_subset \
    --auto-detect
```

### 2. Copy ground truth XML files

Manually copy your reference XML files into each `ground_truth/` directory.

### 3. Run batch evaluation

```bash
uv run python scripts/eval/batch_evaluate.py \
    --experiments-dir data/eval/experiments_subset \
    --verbose \
    --output data/eval/results.json
```

### 4. Analyze results

Review the JSON output and console summary. The evaluation includes:
- Overall scores per experiment
- Per-file detailed evaluations
- Critical errors and minor issues
- Strengths identified by the LLM judge

## Environment Variables

- `OPENROUTER_API_KEY`: Required for LLM evaluation (set in `.env` file)

## Exit Codes

- `0`: All evaluations successful (score >= 7.0)
- `1`: One or more evaluations failed or scored < 7.0

## Example Output

```
================================================================================
LLM EVALUATION REPORT
================================================================================

OVERALL SCORE:                 8.5/10

DIMENSION SCORES:
  Structural Correctness:      9.0/10
  Parameter Accuracy:          8.5/10
  Completeness:                8.0/10
  Semantic Equivalence:        8.5/10

STRENGTHS:
  ✓ Correct solver configuration and numerical methods
  ✓ Proper mesh definition with wellbore generator
  ✓ Accurate boundary conditions and initial stress state

MINOR ISSUES:
  - Time function could use more data points for smoother interpolation
  - Missing optional output specification for stress visualization

DETAILED EXPLANATION:
The generated XML demonstrates a strong understanding of the GEOS framework...
```

## Notes

- The LLM judge is lenient with minor formatting differences (whitespace, attribute order)
- Semantically equivalent values (e.g., `1e-3` vs `0.001`) are treated as correct
- Focus is on whether the XML would produce a valid, equivalent simulation
- Different but reasonable naming conventions are acceptable
