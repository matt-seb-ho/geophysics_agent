#!/usr/bin/env python3
"""
Baseline single-turn evaluation: base model + GEOS primer, no agentic scaffolding.

Sends each experiment's instructions to a plain chat completion (no tools, no
agent loop). The model is asked to produce GEOS XML files inside markdown
```xml fenced blocks. Each block must start with a `<!-- filename: foo.xml -->`
comment so we can reconstruct a multi-file workspace.

After generation the script:
  1. Extracts all XML fenced blocks from the response.
  2. Writes them to `<output-dir>/<experiment>/inputs/<filename>.xml`.
  3. Runs lxml_xml_eval against the ground-truth inputs directory.
  4. Saves per-experiment `*_baseline_lxml.json` files.
  5. Prints an aggregated summary.

Usage:
    # Evaluate all 46 experiments (default paths, 8 parallel workers)
    uv run python scripts/eval/run_baseline_eval.py

    # Custom model / directories / concurrency
    uv run python scripts/eval/run_baseline_eval.py \\
        --model "anthropic/claude-opus-4-5" \\
        --workers 4 \\
        --experiments-dir data/eval/experiments \\
        --ground-truth-dir data/eval/experiments_gt \\
        --output-dir data/eval/baseline_experiments \\
        --results-dir data/eval/eval_v2_results

    # Quick smoke test on a subset
    uv run python scripts/eval/run_baseline_eval.py \\
        --experiments ExampleEDPWellbore TutorialDeadOilEgg \\
        --workers 2
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Project root & imports
# ---------------------------------------------------------------------------

_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = (_SCRIPT_DIR / "../..").resolve()

sys.path.insert(0, str(_PROJECT_ROOT / "src"))
sys.path.insert(0, str(_SCRIPT_DIR))

load_dotenv(_PROJECT_ROOT / ".env")


# Defer heavy imports so --help is instant.
def _import_openai():
    from openai import OpenAI
    return OpenAI


def _import_eval():
    from lxml_xml_eval import evaluate_directories
    return evaluate_directories


# ---------------------------------------------------------------------------
# Constants / defaults
# ---------------------------------------------------------------------------

PRIMER_PATH = _PROJECT_ROOT / "src" / "geos_agent" / "prompts" / "GEOS_PRIMER.md"

DEFAULT_EXPERIMENTS_DIR = _PROJECT_ROOT / "data/eval/experiments"
DEFAULT_GT_DIR          = _PROJECT_ROOT / "data/eval/experiments_gt"
DEFAULT_OUTPUT_DIR      = _PROJECT_ROOT / "data/eval/baseline_experiments"
DEFAULT_RESULTS_DIR     = _PROJECT_ROOT / "data/eval/eval_v2_results"
DEFAULT_MODEL           = "moonshotai/kimi-k2.5"
DEFAULT_WORKERS         = 8
DEFAULT_MAX_TOKENS      = 32000

EVAL_PREAMBLE = """\
You are being evaluated on your ability to author GEOS XML input files from \
a natural language specification. Write the XML files yourself based on your \
knowledge of GEOS and the primer above — do NOT reference external files or \
assume any tools are available.

--- BEGIN SIMULATION SPECIFICATION ---
"""

SYSTEM_PROMPT_TEMPLATE = """\
You are an expert GEOS (Geomechanics and EOS Simulator) simulation engineer.
Your task is to produce GEOS XML input files from a natural language simulation \
specification.

OUTPUT FORMAT RULES — follow these exactly:
1. Output every XML file as a separate fenced code block tagged ```xml.
2. The VERY FIRST LINE inside each block must be a filename comment:
       <!-- filename: main.xml -->
   Use descriptive names (e.g. main.xml, constitutive.xml, functions.xml).
   If only one file is needed, name it main.xml.
3. Do not output any other code blocks (no JSON, no bash, etc.).
4. Write complete, valid GEOS XML — do not truncate or use placeholders.
5. After all code blocks you may add a short prose explanation, but keep XML \
complete and self-contained first.

---

{primer}
"""


# ---------------------------------------------------------------------------
# Terminal colours
# ---------------------------------------------------------------------------

class C:
    HEADER  = "\033[95m"
    BLUE    = "\033[94m"
    CYAN    = "\033[96m"
    GREEN   = "\033[92m"
    WARNING = "\033[93m"
    FAIL    = "\033[91m"
    ENDC    = "\033[0m"
    BOLD    = "\033[1m"


# ---------------------------------------------------------------------------
# XML fence extraction
# ---------------------------------------------------------------------------

# Matches  ```xml\n<!-- filename: foo.xml -->\n...\n```
_FENCE_RE = re.compile(
    r"```xml\s*\n(.*?)```",
    re.DOTALL,
)

# Matches the optional filename comment that must be the first non-empty line.
_FILENAME_RE = re.compile(
    r"^\s*<!--\s*filename\s*:\s*([^\s>]+\.xml)\s*-->",
    re.IGNORECASE,
)


def extract_xml_files(response_text: str) -> list[tuple[str, str]]:
    """
    Return a list of (filename, xml_content) pairs extracted from markdown
    ```xml fenced blocks.

    If a block has no filename comment we auto-assign names
    (main.xml, part2.xml, part3.xml …).
    """
    blocks = _FENCE_RE.findall(response_text)
    results: list[tuple[str, str]] = []
    auto_idx = 1

    for block in blocks:
        lines = block.splitlines(keepends=True)
        if not lines:
            continue

        # Try to pull filename from first non-blank line.
        first_line = lines[0]
        m = _FILENAME_RE.match(first_line)
        if m:
            filename = m.group(1)
            content  = "".join(lines[1:]).lstrip("\n")
        else:
            filename = "main.xml" if auto_idx == 1 else f"part{auto_idx}.xml"
            content  = block
            auto_idx += 1

        content = content.strip()
        if content:
            results.append((filename, content))

    return results


# ---------------------------------------------------------------------------
# Single experiment runner
# ---------------------------------------------------------------------------

def run_one_experiment(
    experiment_name: str,
    instructions_file: Path,
    output_inputs_dir: Path,
    gt_inputs_dir: Path,
    results_dir: Path,
    model: str,
    max_tokens: int,
    api_key: str,
    primer_text: str,
    save_results: bool,
    log_dir: Optional[Path],
) -> dict:
    """
    Run the baseline for a single experiment (synchronous; called from thread pool).
    Returns a result dict.
    """
    result: dict = {
        "experiment": experiment_name,
        "model": model,
        "status": "pending",
        "xml_files_generated": 0,
        "errors": [],
    }

    # ── 1. Read instructions ──────────────────────────────────────────────
    if not instructions_file.exists():
        result["status"] = "error"
        result["errors"].append(f"instructions.txt not found: {instructions_file}")
        return result

    instructions = instructions_file.read_text().strip()
    user_message = EVAL_PREAMBLE + "\n\n" + instructions

    # ── 2. Call the LLM ──────────────────────────────────────────────────
    OpenAI = _import_openai()
    client = OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
    )

    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(primer=primer_text)

    t0 = time.monotonic()
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_message},
            ],
            max_tokens=max_tokens,
            temperature=0.2,
        )
    except Exception as exc:
        result["status"] = "error"
        result["errors"].append(f"API error: {exc}")
        return result

    elapsed = time.monotonic() - t0
    result["api_latency_s"] = round(elapsed, 2)

    response_text = response.choices[0].message.content or ""
    result["response_length"] = len(response_text)

    # Optionally save raw response for debugging.
    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        (log_dir / f"{experiment_name}.txt").write_text(response_text)

    # ── 3. Extract XML files ──────────────────────────────────────────────
    xml_files = extract_xml_files(response_text)
    result["xml_files_generated"] = len(xml_files)

    if not xml_files:
        result["status"] = "error"
        result["errors"].append("No ```xml fenced blocks found in model response")
        return result

    # ── 4. Write XML to output inputs dir ────────────────────────────────
    output_inputs_dir.mkdir(parents=True, exist_ok=True)
    # Clear any previous run's files so stale XMLs don't pollute the eval.
    for old in output_inputs_dir.glob("*.xml"):
        old.unlink()

    written: list[str] = []
    for filename, content in xml_files:
        out_path = output_inputs_dir / filename
        out_path.write_text(content)
        written.append(filename)
    result["xml_files_written"] = written

    # ── 5. lxml evaluation ────────────────────────────────────────────────
    if not gt_inputs_dir.exists():
        result["status"] = "error"
        result["errors"].append(f"Ground-truth inputs not found: {gt_inputs_dir}")
        return result

    evaluate_directories = _import_eval()
    try:
        eval_result = evaluate_directories(gt_inputs_dir, output_inputs_dir)
    except FileNotFoundError as exc:
        result["status"] = "error"
        result["errors"].append(str(exc))
        return result
    except Exception as exc:
        result["status"] = "error"
        result["errors"].append(f"lxml eval error: {exc}")
        return result

    result.update(eval_result)
    result["status"] = "success"

    # ── 6. Save per-experiment JSON ───────────────────────────────────────
    if save_results:
        results_dir.mkdir(parents=True, exist_ok=True)
        out_json = results_dir / f"{experiment_name}_baseline_lxml.json"
        out_json.write_text(json.dumps(result, indent=2))

    return result


# ---------------------------------------------------------------------------
# Async parallel runner
# ---------------------------------------------------------------------------

async def run_all(
    experiment_names: list[str],
    experiments_dir: Path,
    gt_dir: Path,
    output_dir: Path,
    results_dir: Path,
    model: str,
    max_tokens: int,
    workers: int,
    api_key: str,
    primer_text: str,
    save_results: bool,
    log_dir: Optional[Path],
) -> list[dict]:
    semaphore = asyncio.Semaphore(workers)
    loop = asyncio.get_running_loop()

    async def run_one_async(name: str) -> dict:
        async with semaphore:
            return await loop.run_in_executor(
                None,
                run_one_experiment,
                name,
                experiments_dir / name / "instructions.txt",
                output_dir / name / "inputs",
                gt_dir / name / "inputs",
                results_dir,
                model,
                max_tokens,
                api_key,
                primer_text,
                save_results,
                log_dir,
            )

    tasks = []
    for name in experiment_names:
        task = asyncio.create_task(run_one_async(name))
        task.set_name(name)
        tasks.append((name, task))

    results = []
    for name, task in tasks:
        print(f"{C.CYAN}  waiting: {name}{C.ENDC}", flush=True)
        result = await task
        r = result
        if r["status"] == "success":
            s = r["overall_score"]
            color = C.GREEN if s >= 7.0 else (C.WARNING if s >= 4.0 else C.FAIL)
            n_xml = r.get("xml_files_generated", 0)
            lat   = r.get("api_latency_s", 0)
            print(
                f"{C.CYAN}✓ {name:<55}{C.ENDC}  "
                f"{color}{s:.2f}/10{C.ENDC}  "
                f"({n_xml} xml file{'s' if n_xml != 1 else ''},  {lat:.1f}s)",
                flush=True,
            )
        else:
            err = r["errors"][0] if r["errors"] else "unknown"
            print(f"{C.FAIL}✗ {name}: {err}{C.ENDC}", flush=True)
        results.append(r)

    return results


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def print_summary(results: list[dict]) -> None:
    import statistics as st

    successful = [r for r in results if r["status"] == "success"]
    failed     = [r for r in results if r["status"] != "success"]

    W = 80
    print(f"\n{C.BOLD}{C.HEADER}{'=' * W}{C.ENDC}")
    print(f"{C.BOLD}{C.HEADER}  BASELINE EVAL SUMMARY  (model + primer, no tools){C.ENDC}")
    print(f"{C.BOLD}{C.HEADER}{'=' * W}{C.ENDC}")
    print(f"  Total      : {len(results)}")
    print(f"  {C.GREEN}Successful : {len(successful)}{C.ENDC}")
    if failed:
        print(f"  {C.FAIL}Failed     : {len(failed)}{C.ENDC}")

    if successful:
        scores = [r["overall_score"] for r in successful]
        print(f"\n  {C.BOLD}Score statistics (0–10):{C.ENDC}")
        print(f"    Mean   : {st.mean(scores):.2f}")
        print(f"    Median : {st.median(scores):.2f}")
        if len(scores) > 1:
            print(f"    Std    : {st.stdev(scores):.2f}")
        print(f"    Range  : {min(scores):.2f} – {max(scores):.2f}")
        print(f"    Pass≥7 : {sum(1 for s in scores if s >= 7.0)}/{len(scores)}")

        # Dimension averages
        dims = ["structural_completeness", "element_type_match",
                "attribute_accuracy", "critical_param_accuracy", "tag_coverage"]
        print(f"\n  {C.BOLD}Average dimension scores:{C.ENDC}")
        for d in dims:
            vals = [r["dimension_scores"][d] for r in successful if "dimension_scores" in r]
            if vals:
                print(f"    {d:<30} {st.mean(vals):.3f}")

        # Per-experiment table
        print(f"\n  {C.BOLD}Per-experiment (sorted by score):{C.ENDC}")
        for r in sorted(successful, key=lambda x: x["overall_score"], reverse=True):
            s    = r["overall_score"]
            name = r["experiment"]
            n    = r.get("xml_files_generated", "?")
            color = C.GREEN if s >= 7.0 else (C.WARNING if s >= 4.0 else C.FAIL)
            print(f"  {color}{s:5.2f}{C.ENDC}  {name:<55}  ({n} xml)")

    if failed:
        print(f"\n  {C.FAIL}Failed:{C.ENDC}")
        for r in failed:
            print(f"    {r['experiment']}: {r['errors'][0] if r['errors'] else '?'}")

    print(f"\n{C.BOLD}{C.HEADER}{'=' * W}{C.ENDC}\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Baseline eval: base model + GEOS primer, no agentic scaffolding",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--experiments-dir", type=Path, default=DEFAULT_EXPERIMENTS_DIR,
                        help=f"Experiment instructions directory (default: data/eval/experiments)")
    parser.add_argument("--ground-truth-dir", "-g", type=Path, default=DEFAULT_GT_DIR,
                        help="Ground-truth base directory (default: data/eval/experiments_gt)")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR,
                        help="Where to write generated XML files (default: data/eval/baseline_experiments)")
    parser.add_argument("--results-dir", "-r", type=Path, default=DEFAULT_RESULTS_DIR,
                        help="Where to save *_baseline_lxml.json files (default: data/eval/eval_v2_results)")
    parser.add_argument("--model", "-m", type=str, default=DEFAULT_MODEL,
                        help=f"OpenRouter model name (default: {DEFAULT_MODEL})")
    parser.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS,
                        help=f"Max tokens for completion (default: {DEFAULT_MAX_TOKENS})")
    parser.add_argument("--workers", "-w", type=int, default=DEFAULT_WORKERS,
                        help=f"Parallel API workers (default: {DEFAULT_WORKERS})")
    parser.add_argument("--experiments", "-e", nargs="+", metavar="NAME",
                        help="Specific experiment names to run (default: all)")
    parser.add_argument("--primer", type=Path, default=PRIMER_PATH,
                        help=f"Path to GEOS primer markdown (default: {PRIMER_PATH})")
    parser.add_argument("--no-save", action="store_true",
                        help="Do not save per-experiment JSON result files")
    parser.add_argument("--output", "-o", type=Path, default=None,
                        help="Save aggregated results to this JSON file")
    parser.add_argument("--log-dir", type=Path, default=None,
                        help="Directory to save raw model responses for debugging")

    args = parser.parse_args()

    # Validate inputs.
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        print(f"{C.FAIL}Error: OPENROUTER_API_KEY not set in environment or .env{C.ENDC}")
        sys.exit(1)

    if not args.experiments_dir.exists():
        print(f"{C.FAIL}Error: experiments dir not found: {args.experiments_dir}{C.ENDC}")
        sys.exit(1)
    if not args.ground_truth_dir.exists():
        print(f"{C.FAIL}Error: ground-truth dir not found: {args.ground_truth_dir}{C.ENDC}")
        sys.exit(1)
    if not args.primer.exists():
        print(f"{C.FAIL}Error: primer not found: {args.primer}{C.ENDC}")
        sys.exit(1)

    primer_text = args.primer.read_text()

    # Discover experiments.
    all_dirs = sorted(d for d in args.experiments_dir.iterdir() if d.is_dir())
    if args.experiments:
        experiment_names = [d.name for d in all_dirs if d.name in args.experiments]
        missing = set(args.experiments) - set(experiment_names)
        if missing:
            print(f"{C.WARNING}Warning: not found: {', '.join(sorted(missing))}{C.ENDC}")
    else:
        experiment_names = [d.name for d in all_dirs]

    if not experiment_names:
        print(f"{C.WARNING}No experiments found.{C.ENDC}")
        sys.exit(1)

    print(f"\n{C.BOLD}{C.HEADER}{'=' * 80}{C.ENDC}")
    print(f"{C.BOLD}{C.HEADER}  GEOS Baseline Eval  —  model + primer only{C.ENDC}")
    print(f"{C.BOLD}{C.HEADER}{'=' * 80}{C.ENDC}")
    print(f"  Model          : {args.model}")
    print(f"  Max tokens     : {args.max_tokens}")
    print(f"  Workers        : {args.workers}")
    print(f"  Experiments    : {len(experiment_names)}")
    print(f"  Output dir     : {args.output_dir}")
    print(f"  Results dir    : {args.results_dir if not args.no_save else '(not saving)'}")
    print(f"{C.BOLD}{C.HEADER}{'=' * 80}{C.ENDC}\n")

    results = asyncio.run(run_all(
        experiment_names=experiment_names,
        experiments_dir=args.experiments_dir,
        gt_dir=args.ground_truth_dir,
        output_dir=args.output_dir,
        results_dir=args.results_dir,
        model=args.model,
        max_tokens=args.max_tokens,
        workers=args.workers,
        api_key=api_key,
        primer_text=primer_text,
        save_results=not args.no_save,
        log_dir=args.log_dir,
    ))

    print_summary(results)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "timestamp": datetime.now().isoformat(),
            "model": args.model,
            "experiments_dir": str(args.experiments_dir),
            "ground_truth_dir": str(args.ground_truth_dir),
            "total": len(results),
            "successful": sum(1 for r in results if r["status"] == "success"),
            "results": results,
        }
        args.output.write_text(json.dumps(payload, indent=2))
        print(f"Aggregated results saved to: {args.output}")

    if any(r["status"] == "error" for r in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
