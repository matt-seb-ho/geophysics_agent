#!/usr/bin/env python3
"""
LLM-based XML evaluation for GEOS agent outputs.

Compares agent-generated XML files against ground truth using an LLM judge.
Supports both single-file and multi-file (directory) comparison modes.

Usage:
    # Compare single files
    uv run python scripts/eval/llm_judge_xml.py \
        --ground-truth path/to/ground_truth.xml \
        --generated path/to/generated.xml

    # Compare directories of XML files (multi-file mode)
    uv run python scripts/eval/llm_judge_xml.py \
        --ground-truth-dir data/eval/experiments_gt/ExampleFoo/inputs \
        --generated-dir data/eval/experiments_subset/ExampleFoo/inputs

    # Use specific model
    uv run python scripts/eval/llm_judge_xml.py \
        --ground-truth-dir gt_dir --generated-dir gen_dir \
        --model "anthropic/claude-4.6-sonnet"
"""

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, Optional
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def resolve_xml_imports(xml_path: Path, base_dir: Optional[Path] = None) -> str:
    """
    Resolve XML imports recursively and return flattened XML as string.

    Handles GEOS <Included> tags that reference other XML files.

    Args:
        xml_path: Path to the XML file
        base_dir: Base directory for resolving relative imports (defaults to xml_path parent)

    Returns:
        String representation of resolved XML
    """
    if base_dir is None:
        base_dir = xml_path.parent

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Find all <Included> tags (GEOS uses this for imports)
        included_tags = root.findall('.//Included')

        if not included_tags:
            # No imports, return as-is
            return ET.tostring(root, encoding='unicode')

        # Process each included file
        for included in included_tags:
            # Get the file path from the tag
            file_attr = included.get('File') or included.get('file')
            if not file_attr:
                continue

            # Resolve the import path
            import_path = base_dir / file_attr
            if not import_path.exists():
                # Try relative to current file
                import_path = xml_path.parent / file_attr

            if import_path.exists():
                # Recursively resolve the imported file
                imported_content = resolve_xml_imports(import_path, base_dir)
                imported_root = ET.fromstring(imported_content)

                # Replace <Included> tag with imported content
                parent = root
                for ancestor in root.iter():
                    if included in list(ancestor):
                        parent = ancestor
                        break

                # Insert imported elements at the position of <Included>
                idx = list(parent).index(included)
                parent.remove(included)
                for i, child in enumerate(imported_root):
                    parent.insert(idx + i, child)

        return ET.tostring(root, encoding='unicode')

    except ET.ParseError as e:
        # If XML parsing fails, return raw content
        print(f"Warning: XML parse error in {xml_path}: {e}")
        return xml_path.read_text()


def load_xml(xml_path: Path, resolve_imports: bool = False) -> str:
    """
    Load XML file, optionally resolving imports.

    Args:
        xml_path: Path to XML file
        resolve_imports: Whether to resolve <Included> tags

    Returns:
        XML content as string
    """
    if not xml_path.exists():
        raise FileNotFoundError(f"XML file not found: {xml_path}")

    if resolve_imports:
        return resolve_xml_imports(xml_path)
    else:
        return xml_path.read_text()


def collect_xml_bundle(directory: Path) -> str:
    """
    Collect all XML files from a directory into a single labeled bundle.

    Recursively finds all .xml files, reads each one, and concatenates them
    with file path headers so the LLM judge can see the full multi-file
    configuration.

    Args:
        directory: Path to directory containing XML files

    Returns:
        Concatenated string with labeled XML file contents.
        Returns empty string if no XML files found.
    """
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    xml_files = sorted(directory.rglob("*.xml"))
    if not xml_files:
        return ""

    parts = []
    for xml_file in xml_files:
        rel_path = xml_file.relative_to(directory)
        content = xml_file.read_text()
        parts.append(f"=== {rel_path} ===\n{content}")

    return "\n\n".join(parts)


def create_judge_prompt(ground_truth_xml: str, generated_xml: str) -> str:
    """
    Create the LLM judge prompt for comparing XMLs.

    Args:
        ground_truth_xml: Ground truth XML content
        generated_xml: Generated XML content

    Returns:
        Prompt string for the LLM
    """
    prompt = f"""You are an expert evaluator for GEOS (a geophysics simulation framework) XML configuration files.

Your task is to compare a GROUND TRUTH XML file against a GENERATED XML file produced by an AI agent.

Evaluate the generated XML on these dimensions:
1. **Structural Correctness** (0-10): Does it have the right XML structure, tags, and hierarchy?
2. **Parameter Accuracy** (0-10): Are parameter values, units, and names correct?
3. **Completeness** (0-10): Does it include all necessary components from the ground truth?
4. **Semantic Equivalence** (0-10): Does it accomplish the same simulation goals, even if syntax differs?

IMPORTANT EVALUATION GUIDELINES:
- Minor formatting differences (whitespace, attribute order) should NOT reduce scores
- Different but semantically equivalent values (e.g., "1e-3" vs "0.001") should NOT reduce scores
- Missing optional elements that don't affect simulation validity should have minimal impact
- Focus on whether the generated XML would produce a valid, equivalent simulation
- Be lenient with naming conventions if they're reasonable alternatives

Return your evaluation as JSON with this EXACT structure:
{{
    "overall_score": <float 0-10>,
    "structural_correctness": <float 0-10>,
    "parameter_accuracy": <float 0-10>,
    "completeness": <float 0-10>,
    "semantic_equivalence": <float 0-10>,
    "explanation": "<detailed explanation of scores>",
    "critical_errors": ["<list of serious errors, empty if none>"],
    "minor_issues": ["<list of minor issues, empty if none>"],
    "strengths": ["<list of things done well>"]
}}

## GROUND TRUTH XML

```xml
{ground_truth_xml}
```

## GENERATED XML

```xml
{generated_xml}
```

Provide your evaluation as JSON:"""

    return prompt


def create_multi_file_judge_prompt(ground_truth_bundle: str, generated_bundle: str) -> str:
    """
    Create the LLM judge prompt for comparing multi-file XML bundles.

    Each bundle contains multiple XML files concatenated with path headers.
    The judge evaluates the generated set as a whole against the ground truth set.

    Args:
        ground_truth_bundle: Labeled ground truth XML bundle
        generated_bundle: Labeled generated XML bundle

    Returns:
        Prompt string for the LLM
    """
    prompt = f"""You are an expert evaluator for GEOS (a geophysics simulation framework) XML configuration files.

Your task is to compare a set of GROUND TRUTH XML files against a set of GENERATED XML files produced by an AI agent.

IMPORTANT CONTEXT: GEOS simulations typically use multiple XML files. One main XML file is passed to the
simulator, and it imports/includes from other XML files. The filenames and how the configuration is split
across files may differ between the ground truth and generated sets — what matters is whether the overall
simulation configuration is equivalent.

Each file in the bundles below is labeled with its relative path (e.g., "=== filename.xml ===").

Evaluate the generated XML set on these dimensions:
1. **Structural Correctness** (0-10): Do the files have correct XML structure, tags, and hierarchy? Are includes/imports properly structured?
2. **Parameter Accuracy** (0-10): Are parameter values, units, and names correct across all files?
3. **Completeness** (0-10): Does the generated set include all necessary components from the ground truth? Are any important sections or files missing?
4. **Semantic Equivalence** (0-10): Does the generated set accomplish the same simulation goals, even if the file organization or syntax differs?

IMPORTANT EVALUATION GUIDELINES:
- The generated set may split configuration differently across files — this is fine if the total configuration is equivalent
- The generated set may use different filenames — focus on content, not naming
- Minor formatting differences (whitespace, attribute order) should NOT reduce scores
- Different but semantically equivalent values (e.g., "1e-3" vs "0.001") should NOT reduce scores
- Missing optional elements that don't affect simulation validity should have minimal impact
- Focus on whether the generated XML set would produce a valid, equivalent simulation
- Be lenient with naming conventions if they're reasonable alternatives

Return your evaluation as JSON with this EXACT structure:
{{
    "overall_score": <float 0-10>,
    "structural_correctness": <float 0-10>,
    "parameter_accuracy": <float 0-10>,
    "completeness": <float 0-10>,
    "semantic_equivalence": <float 0-10>,
    "explanation": "<detailed explanation of scores>",
    "critical_errors": ["<list of serious errors, empty if none>"],
    "minor_issues": ["<list of minor issues, empty if none>"],
    "strengths": ["<list of things done well>"]
}}

## GROUND TRUTH XML FILES

```
{ground_truth_bundle}
```

## GENERATED XML FILES

```
{generated_bundle}
```

Provide your evaluation as JSON:"""

    return prompt


def _call_llm_judge(
    prompt: str,
    model: str = "anthropic/claude-4.6-sonnet",
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send a judge prompt to the LLM and parse the JSON evaluation response.

    Args:
        prompt: The full judge prompt
        model: OpenRouter model name
        api_key: OpenRouter API key (defaults to OPENROUTER_API_KEY env var)

    Returns:
        Dictionary with evaluation scores and explanation
    """
    if api_key is None:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set")

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key
    )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=4000
        )

        content = response.choices[0].message.content.strip()

        # Sometimes LLMs wrap JSON in markdown code blocks
        if content.startswith("```"):
            lines = content.split('\n')
            content = '\n'.join(lines[1:-1]) if len(lines) > 2 else content
            content = content.replace("```json", "").replace("```", "").strip()

        evaluation = json.loads(content)

        required_fields = [
            "overall_score", "structural_correctness", "parameter_accuracy",
            "completeness", "semantic_equivalence", "explanation"
        ]
        for field in required_fields:
            if field not in evaluation:
                raise ValueError(f"Missing required field in evaluation: {field}")

        return evaluation

    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse LLM response as JSON: {e}")
        print(f"Raw response: {content}")
        raise
    except Exception as e:
        print(f"Error calling LLM: {e}")
        raise


def judge_xml_with_llm(
    ground_truth_xml: str,
    generated_xml: str,
    model: str = "anthropic/claude-4.6-sonnet",
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Use an LLM to judge a single generated XML against ground truth.

    Args:
        ground_truth_xml: Ground truth XML content
        generated_xml: Generated XML content
        model: OpenRouter model name
        api_key: OpenRouter API key (defaults to OPENROUTER_API_KEY env var)

    Returns:
        Dictionary with evaluation scores and explanation
    """
    prompt = create_judge_prompt(ground_truth_xml, generated_xml)
    return _call_llm_judge(prompt, model, api_key)


def judge_xml_bundle_with_llm(
    ground_truth_bundle: str,
    generated_bundle: str,
    model: str = "anthropic/claude-4.6-sonnet",
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Use an LLM to judge a set of generated XML files against ground truth.

    Both bundles are labeled concatenations of XML files (produced by
    collect_xml_bundle). The judge evaluates the overall configuration
    equivalence regardless of how files are named or split.

    Args:
        ground_truth_bundle: Labeled ground truth XML bundle
        generated_bundle: Labeled generated XML bundle
        model: OpenRouter model name
        api_key: OpenRouter API key (defaults to OPENROUTER_API_KEY env var)

    Returns:
        Dictionary with evaluation scores and explanation
    """
    prompt = create_multi_file_judge_prompt(ground_truth_bundle, generated_bundle)
    return _call_llm_judge(prompt, model, api_key)


def print_evaluation_report(evaluation: Dict[str, Any], verbose: bool = True):
    """
    Print a formatted evaluation report.

    Args:
        evaluation: Evaluation dictionary from judge_xml_with_llm
        verbose: Whether to print detailed explanation
    """
    print("\n" + "=" * 80)
    print("LLM EVALUATION REPORT")
    print("=" * 80)

    # Overall score
    overall = evaluation["overall_score"]
    print(f"\n{'OVERALL SCORE:':<30} {overall:.1f}/10")

    # Individual dimensions
    print(f"\n{'DIMENSION SCORES:':}")
    print(f"  {'Structural Correctness:':<28} {evaluation['structural_correctness']:.1f}/10")
    print(f"  {'Parameter Accuracy:':<28} {evaluation['parameter_accuracy']:.1f}/10")
    print(f"  {'Completeness:':<28} {evaluation['completeness']:.1f}/10")
    print(f"  {'Semantic Equivalence:':<28} {evaluation['semantic_equivalence']:.1f}/10")

    # Strengths
    if "strengths" in evaluation and evaluation["strengths"]:
        print(f"\n{'STRENGTHS:':}")
        for strength in evaluation["strengths"]:
            print(f"  ✓ {strength}")

    # Critical errors
    if "critical_errors" in evaluation and evaluation["critical_errors"]:
        print(f"\n{'CRITICAL ERRORS:':}")
        for error in evaluation["critical_errors"]:
            print(f"  ✗ {error}")

    # Minor issues
    if "minor_issues" in evaluation and evaluation["minor_issues"]:
        print(f"\n{'MINOR ISSUES:':}")
        for issue in evaluation["minor_issues"]:
            print(f"  - {issue}")

    # Detailed explanation
    if verbose:
        print(f"\n{'DETAILED EXPLANATION:':}")
        print(f"{evaluation['explanation']}")

    print("\n" + "=" * 80 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="LLM-based XML evaluation for GEOS agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    # Single-file mode arguments
    parser.add_argument(
        "--ground-truth",
        "-g",
        type=Path,
        help="Path to a single ground truth XML file"
    )
    parser.add_argument(
        "--generated",
        "-e",
        type=Path,
        help="Path to a single generated XML file"
    )

    # Multi-file (directory) mode arguments
    parser.add_argument(
        "--ground-truth-dir",
        type=Path,
        help="Path to directory containing ground truth XML files"
    )
    parser.add_argument(
        "--generated-dir",
        type=Path,
        help="Path to directory containing generated XML files"
    )

    # Optional arguments
    parser.add_argument(
        "--resolve-imports",
        "-r",
        action="store_true",
        help="Resolve XML imports/includes before comparison (single-file mode only)"
    )
    parser.add_argument(
        "--model",
        "-m",
        type=str,
        default="anthropic/claude-4.6-sonnet",
        help="OpenRouter model name (default: anthropic/claude-4.6-sonnet)"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Path to save evaluation JSON (optional)"
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Only print overall score, not detailed report"
    )

    args = parser.parse_args()

    # Determine mode: directory (multi-file) or single-file
    dir_mode = args.ground_truth_dir is not None or args.generated_dir is not None
    file_mode = args.ground_truth is not None or args.generated is not None

    if dir_mode and file_mode:
        print("Error: Cannot mix single-file (--ground-truth/--generated) and directory (--ground-truth-dir/--generated-dir) modes")
        sys.exit(1)

    if dir_mode:
        if not args.ground_truth_dir or not args.generated_dir:
            print("Error: Both --ground-truth-dir and --generated-dir are required for directory mode")
            sys.exit(1)

        # Multi-file bundle mode
        try:
            print(f"Collecting ground truth XMLs from: {args.ground_truth_dir}")
            gt_bundle = collect_xml_bundle(args.ground_truth_dir)
            gt_count = len(list(args.ground_truth_dir.rglob("*.xml")))

            print(f"Collecting generated XMLs from: {args.generated_dir}")
            gen_bundle = collect_xml_bundle(args.generated_dir)
            gen_count = len(list(args.generated_dir.rglob("*.xml")))

            if not gt_bundle:
                print(f"Error: No XML files found in {args.ground_truth_dir}")
                sys.exit(1)
            if not gen_bundle:
                print(f"Error: No XML files found in {args.generated_dir}")
                sys.exit(1)

            print(f"Found {gt_count} ground truth XML file(s), {gen_count} generated XML file(s)")

        except Exception as e:
            print(f"Error collecting XML files: {e}")
            sys.exit(1)

        try:
            print(f"Running LLM evaluation with model: {args.model}")
            evaluation = judge_xml_bundle_with_llm(
                gt_bundle,
                gen_bundle,
                model=args.model
            )
        except Exception as e:
            print(f"Error during evaluation: {e}")
            sys.exit(1)

    else:
        if not args.ground_truth or not args.generated:
            print("Error: Either --ground-truth and --generated (single-file) or --ground-truth-dir and --generated-dir (multi-file) are required")
            sys.exit(1)

        # Single-file mode (original behavior)
        try:
            print(f"Loading ground truth: {args.ground_truth}")
            ground_truth_xml = load_xml(args.ground_truth, args.resolve_imports)

            print(f"Loading generated XML: {args.generated}")
            generated_xml = load_xml(args.generated, args.resolve_imports)

            if args.resolve_imports:
                print("Imports resolved")

        except Exception as e:
            print(f"Error loading XML files: {e}")
            sys.exit(1)

        try:
            print(f"Running LLM evaluation with model: {args.model}")
            evaluation = judge_xml_with_llm(
                ground_truth_xml,
                generated_xml,
                model=args.model
            )
        except Exception as e:
            print(f"Error during evaluation: {e}")
            sys.exit(1)

    # Print report
    if args.quiet:
        print(f"\nOverall Score: {evaluation['overall_score']:.1f}/10")
    else:
        print_evaluation_report(evaluation, verbose=True)

    # Save to file if requested
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, 'w') as f:
            json.dump(evaluation, f, indent=2)
        print(f"Evaluation saved to: {args.output}")

    # Exit with error code if score is below threshold
    if evaluation["overall_score"] < 7.0:
        sys.exit(1)


if __name__ == "__main__":
    main()
