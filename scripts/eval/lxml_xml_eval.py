#!/usr/bin/env python3
"""
Reference-based XML evaluation for GEOS agent outputs using lxml.

Compares agent-generated XML files against ground truth programmatically —
no LLM required. Supports multi-file (directory) mode and resolves GEOS
<Included> imports before comparison.

Scoring dimensions (all 0–1, combined into a weighted overall 0–10):
  1. structural_completeness  — required top-level sections present
  2. element_type_match       — correct element types used (Jaccard similarity)
  3. attribute_accuracy       — attribute values match (with numeric tolerance)
  4. tag_coverage             — recall of GT tag types in generated XML

Usage:
    # Compare two directories
    uv run python scripts/eval/lxml_xml_eval.py \\
        --ground-truth-dir data/eval/experiments_gt/AdvancedExampleViscoDruckerPrager/inputs \\
        --generated-dir    data/eval/experiments_subset/AdvancedExampleViscoDruckerPrager/inputs

    # Compare single files
    uv run python scripts/eval/lxml_xml_eval.py \\
        --ground-truth path/to/gt.xml \\
        --generated    path/to/gen.xml

    # Save JSON result
    uv run python scripts/eval/lxml_xml_eval.py \\
        --ground-truth-dir ... --generated-dir ... \\
        --output results/eval.json
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

from lxml import etree

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# GEOS top-level sections considered "required" for a valid Problem XML.
# The evaluator checks how many of these appear in the resolved output.
REQUIRED_SECTIONS = {
    "Events",
    "Constitutive",
    "Mesh",
    "ElementRegions",
}

# Sections that are "optional but important" (missing penalises less).
OPTIONAL_SECTIONS = {
    "Functions",
    "Tasks",
    "Solvers",
    "NumericalMethods",
    "Geometry",
    "FieldSpecifications",
    "Outputs",
}

# Numeric tolerance for "equivalent" attribute values (relative).
NUMERIC_RTOL = 1e-6

# Weights for the composite score.
WEIGHTS = {
    "structural_completeness": 0.15,
    "element_type_match":      0.40,
    "attribute_accuracy":      0.30,
    "tag_coverage":            0.15,
}

# ---------------------------------------------------------------------------
# XML loading & include resolution (using lxml)
# ---------------------------------------------------------------------------

def _resolve_included(root: etree._Element, base_dir: Path) -> etree._Element:
    """
    Recursively inline all <Included><File name="..."/></Included> blocks
    into `root`, modifying it in-place.  Returns the same element.
    """
    for included in root.findall(".//Included"):
        parent = included.getparent()
        idx = list(parent).index(included)
        parent.remove(included)
        insert_at = idx

        for file_tag in included.findall("File"):
            rel = file_tag.get("name") or file_tag.get("Name", "")
            candidate = base_dir / rel
            if not candidate.exists():
                # try same directory as file being parsed
                continue
            child_tree = etree.parse(str(candidate))
            child_root = child_tree.getroot()
            child_root = _resolve_included(child_root, candidate.parent)
            for elem in child_root:
                parent.insert(insert_at, elem)
                insert_at += 1

    return root


def load_and_resolve_dir(directory: Path) -> etree._Element:
    """
    Load all XML files in `directory`, resolve <Included> imports, and merge
    everything under a single synthetic <Problem> root.

    Strategy: find the "entry-point" file — the one that is NOT referenced by
    any other file's <Included> block.  If we can't determine one uniquely,
    merge all roots.
    """
    xml_files = sorted(directory.rglob("*.xml"))
    if not xml_files:
        raise FileNotFoundError(f"No XML files found in {directory}")

    # Parse all files, collect their roots.
    parsed: dict[Path, etree._Element] = {}
    for f in xml_files:
        try:
            tree = etree.parse(str(f))
            parsed[f] = tree.getroot()
        except etree.XMLSyntaxError as exc:
            print(f"  Warning: failed to parse {f.name}: {exc}")

    # Find files referenced via <Included>.
    referenced: set[Path] = set()
    for f, root in parsed.items():
        for file_tag in root.iter("File"):
            rel = file_tag.get("name") or file_tag.get("Name", "")
            if rel:
                candidate = f.parent / rel
                if candidate.exists():
                    referenced.add(candidate.resolve())

    # Entry points = files not referenced by anyone.
    entries = [f for f in parsed if f.resolve() not in referenced]
    if len(entries) == 1:
        entry = entries[0]
        root = parsed[entry]
        root = _resolve_included(root, entry.parent)
        return root

    # Fallback: merge all roots under a synthetic <Problem>.
    merged = etree.Element("Problem")
    for f, root in parsed.items():
        root = _resolve_included(root, f.parent)
        for child in root:
            merged.append(child)
    return merged


def load_and_resolve_file(xml_path: Path) -> etree._Element:
    """Load a single XML file and resolve its <Included> imports."""
    tree = etree.parse(str(xml_path))
    root = tree.getroot()
    return _resolve_included(root, xml_path.parent)


# ---------------------------------------------------------------------------
# Attribute value comparison helpers
# ---------------------------------------------------------------------------

_SCALAR_RE = re.compile(r"^[+-]?\d+(\.\d*)?([eE][+-]?\d+)?$")


def _parse_scalar(s: str) -> float | None:
    """Return float if `s` is a plain scalar number, else None."""
    s = s.strip()
    if _SCALAR_RE.match(s):
        try:
            return float(s)
        except ValueError:
            return None
    return None


def _parse_list(s: str) -> list[float] | None:
    """
    Try to parse GEOS-style list attributes like '{ 0.0, 1e9 }' or '{ C3D8 }'.
    Returns list of floats if all tokens are numeric, else None.
    """
    s = s.strip().strip("{").strip("}").strip()
    tokens = [t.strip() for t in s.split(",") if t.strip()]
    floats: list[float] = []
    for t in tokens:
        v = _parse_scalar(t)
        if v is None:
            return None
        floats.append(v)
    return floats if floats else None


def values_equivalent(v1: str, v2: str, rtol: float = NUMERIC_RTOL) -> bool:
    """
    Return True if two attribute value strings are semantically equivalent.

    Handles:
      - Exact string match (after strip)
      - Scalar numeric equivalence: '500e6' == '5e8', '2500' == '2500.0'
      - List numeric equivalence: '{ 0.0, 1e9 }' == '{ 0, 1000000000 }'
      - Case-insensitive match for non-numeric strings
    """
    v1, v2 = v1.strip(), v2.strip()
    if v1 == v2:
        return True

    # Scalar comparison
    n1, n2 = _parse_scalar(v1), _parse_scalar(v2)
    if n1 is not None and n2 is not None:
        if n1 == 0.0 and n2 == 0.0:
            return True
        denom = max(abs(n1), abs(n2))
        return abs(n1 - n2) / denom <= rtol

    # List comparison
    l1, l2 = _parse_list(v1), _parse_list(v2)
    if l1 is not None and l2 is not None and len(l1) == len(l2):
        return all(values_equivalent(str(a), str(b), rtol) for a, b in zip(l1, l2))

    # Case-insensitive fallback
    return v1.lower() == v2.lower()


# ---------------------------------------------------------------------------
# Config extraction
# ---------------------------------------------------------------------------

def extract_config(root: etree._Element) -> dict[str, Any]:
    """
    Walk the resolved XML tree and extract a structured config dict:
      {
        "sections": set of top-level tag names (strings only),
        "elements": list of {tag, name, attrs} for every element node,
        "element_types": set of all unique tag names in the tree,
        "named_elements": dict[name -> {tag, attrs}]  (by 'name' attribute),
      }
    """
    sections: set[str] = set()
    elements: list[dict] = []
    element_types: set[str] = set()
    named_elements: dict[str, dict] = {}

    # lxml can yield comment/PI nodes whose .tag is a callable — skip those.
    for child in root:
        if isinstance(child.tag, str):
            sections.add(child.tag)

    for elem in root.iter():
        tag = elem.tag
        # Skip comments, PIs, and namespace-prefixed internal lxml nodes.
        if not isinstance(tag, str):
            continue
        if tag.startswith("{"):
            continue
        element_types.add(tag)
        attrs = dict(elem.attrib)
        entry = {"tag": tag, "name": attrs.get("name", ""), "attrs": attrs}
        elements.append(entry)
        if "name" in attrs:
            named_elements[attrs["name"]] = entry

    return {
        "sections": sections,
        "elements": elements,
        "element_types": element_types,
        "named_elements": named_elements,
    }


# ---------------------------------------------------------------------------
# Scoring functions
# ---------------------------------------------------------------------------

def score_structural_completeness(gt_cfg: dict, gen_cfg: dict) -> tuple[float, dict]:
    """Score 1: Are required top-level sections present?"""
    gt_sections = gt_cfg["sections"]
    gen_sections = gen_cfg["sections"]

    required_in_gt = REQUIRED_SECTIONS & gt_sections
    if not required_in_gt:
        return 1.0, {"note": "GT has no required sections to check"}

    found = required_in_gt & gen_sections
    missing = required_in_gt - gen_sections
    extra_optional = (OPTIONAL_SECTIONS & gen_sections) - gt_sections

    score = len(found) / len(required_in_gt)
    return score, {
        "required_present": sorted(found),
        "required_missing": sorted(missing),
        "optional_extra": sorted(extra_optional),
    }


def score_element_type_match(gt_cfg: dict, gen_cfg: dict) -> tuple[float, dict]:
    """
    Score 2: Jaccard similarity of unique element type sets.

    Ignores the root tag and generic structural tags (Problem, Included).
    """
    ignore = {"Problem", "Included", "File"}
    gt_types = gt_cfg["element_types"] - ignore
    gen_types = gen_cfg["element_types"] - ignore

    if not gt_types:
        return 1.0, {"note": "GT has no typed elements"}

    intersection = gt_types & gen_types
    union = gt_types | gen_types
    jaccard = len(intersection) / len(union) if union else 1.0

    return jaccard, {
        "gt_only": sorted(gt_types - gen_types),
        "gen_only": sorted(gen_types - gt_types),
        "shared": sorted(intersection),
    }


def score_attribute_accuracy(
    gt_cfg: dict, gen_cfg: dict, rtol: float = NUMERIC_RTOL
) -> tuple[float, dict]:
    """
    Score 3: For every named element that exists in both GT and generated,
    compute attribute match ratio.  Averages across all matched elements.
    """
    gt_named = gt_cfg["named_elements"]
    gen_named = gen_cfg["named_elements"]

    common_names = set(gt_named) & set(gen_named)
    if not common_names:
        # Try matching by tag type if no name overlap
        return _score_attrs_by_tag(gt_cfg, gen_cfg, rtol)

    total_attrs = 0
    matched_attrs = 0
    details: list[dict] = []

    for name in sorted(common_names):
        gt_elem = gt_named[name]
        gen_elem = gen_named[name]

        if gt_elem["tag"] != gen_elem["tag"]:
            # Different element type for same name — count as full mismatch
            details.append({
                "name": name,
                "gt_tag": gt_elem["tag"],
                "gen_tag": gen_elem["tag"],
                "note": "tag mismatch",
            })
            total_attrs += 1
            continue

        gt_attrs = gt_elem["attrs"]
        gen_attrs = gen_elem["attrs"]
        all_keys = set(gt_attrs) | set(gen_attrs)
        # Exclude 'name' itself from scoring
        all_keys.discard("name")

        elem_matched = 0
        elem_mismatched: list[str] = []
        for key in all_keys:
            if key in gt_attrs and key in gen_attrs:
                if values_equivalent(gt_attrs[key], gen_attrs[key], rtol):
                    elem_matched += 1
                else:
                    elem_mismatched.append(
                        f"{key}: GT={gt_attrs[key]!r} GEN={gen_attrs[key]!r}"
                    )
            else:
                elem_mismatched.append(
                    f"{key}: {'missing in GEN' if key in gt_attrs else 'extra in GEN'}"
                )

        matched_attrs += elem_matched
        total_attrs += len(all_keys)
        details.append({
            "name": name,
            "tag": gt_elem["tag"],
            "matched": elem_matched,
            "total": len(all_keys),
            "mismatches": elem_mismatched,
        })

    score = matched_attrs / total_attrs if total_attrs else 1.0
    return score, {
        "elements_compared": len(common_names),
        "total_attrs": total_attrs,
        "matched_attrs": matched_attrs,
        "details": details,
    }


def _score_attrs_by_tag(
    gt_cfg: dict, gen_cfg: dict, rtol: float
) -> tuple[float, dict]:
    """Fallback: match elements by tag type (first occurrence each)."""
    gt_by_tag: dict[str, dict] = {}
    for e in gt_cfg["elements"]:
        gt_by_tag.setdefault(e["tag"], e)

    gen_by_tag: dict[str, dict] = {}
    for e in gen_cfg["elements"]:
        gen_by_tag.setdefault(e["tag"], e)

    common_tags = set(gt_by_tag) & set(gen_by_tag)
    total, matched = 0, 0
    for tag in common_tags:
        gt_attrs = gt_by_tag[tag]["attrs"]
        gen_attrs = gen_by_tag[tag]["attrs"]
        for key in set(gt_attrs) | set(gen_attrs):
            total += 1
            if key in gt_attrs and key in gen_attrs:
                if values_equivalent(gt_attrs[key], gen_attrs[key], rtol):
                    matched += 1

    score = matched / total if total else 1.0
    return score, {"note": "matched by tag (no common names)", "total": total, "matched": matched}



def score_tag_coverage(gt_cfg: dict, gen_cfg: dict) -> tuple[float, dict]:
    """
    Score 4: Recall of GT element types in the generated output.

    = |GT_types ∩ GEN_types| / |GT_types|

    (Precision is not penalised here — extra elements in GEN are fine.)
    """
    ignore = {"Problem", "Included", "File"}
    gt_types = gt_cfg["element_types"] - ignore
    gen_types = gen_cfg["element_types"] - ignore

    if not gt_types:
        return 1.0, {"note": "GT has no types"}

    covered = gt_types & gen_types
    missing = gt_types - gen_types
    score = len(covered) / len(gt_types)
    return score, {"covered": sorted(covered), "missing": sorted(missing)}


# ---------------------------------------------------------------------------
# Main evaluation entry point
# ---------------------------------------------------------------------------

def evaluate_xml(
    gt_root: etree._Element,
    gen_root: etree._Element,
    rtol: float = NUMERIC_RTOL,
) -> dict[str, Any]:
    """
    Run all scoring dimensions against two resolved lxml trees.
    Returns a result dict with per-dimension scores and an overall 0–10 score.
    """
    gt_cfg = extract_config(gt_root)
    gen_cfg = extract_config(gen_root)

    s_struct, d_struct   = score_structural_completeness(gt_cfg, gen_cfg)
    s_types,  d_types    = score_element_type_match(gt_cfg, gen_cfg)
    s_attrs,  d_attrs    = score_attribute_accuracy(gt_cfg, gen_cfg, rtol)
    s_cov,    d_cov      = score_tag_coverage(gt_cfg, gen_cfg)

    raw_scores = {
        "structural_completeness": s_struct,
        "element_type_match":      s_types,
        "attribute_accuracy":      s_attrs,
        "tag_coverage":            s_cov,
    }

    overall_01 = sum(raw_scores[k] * WEIGHTS[k] for k in WEIGHTS)
    overall_10 = round(overall_01 * 10, 2)

    return {
        "overall_score": overall_10,            # 0–10, matches LLM judge scale
        "overall_01": round(overall_01, 4),     # 0–1 for programmatic use
        "dimension_scores": {k: round(v, 4) for k, v in raw_scores.items()},
        "weights": WEIGHTS,
        "details": {
            "structural_completeness": d_struct,
            "element_type_match":      d_types,
            "attribute_accuracy":      d_attrs,
            "tag_coverage":            d_cov,
        },
        "gt_sections":      sorted(gt_cfg["sections"]),
        "gen_sections":     sorted(gen_cfg["sections"]),
        "gt_element_types": sorted(gt_cfg["element_types"]),
        "gen_element_types": sorted(gen_cfg["element_types"]),
    }


def evaluate_directories(
    gt_dir: Path, gen_dir: Path, rtol: float = NUMERIC_RTOL
) -> dict[str, Any]:
    """Resolve all XML includes in each directory, then evaluate."""
    gt_root  = load_and_resolve_dir(gt_dir)
    gen_root = load_and_resolve_dir(gen_dir)
    result   = evaluate_xml(gt_root, gen_root, rtol)
    result["mode"] = "directory"
    result["gt_dir"]  = str(gt_dir)
    result["gen_dir"] = str(gen_dir)
    return result


def evaluate_files(
    gt_file: Path, gen_file: Path, rtol: float = NUMERIC_RTOL
) -> dict[str, Any]:
    """Resolve <Included> in each file, then evaluate."""
    gt_root  = load_and_resolve_file(gt_file)
    gen_root = load_and_resolve_file(gen_file)
    result   = evaluate_xml(gt_root, gen_root, rtol)
    result["mode"]    = "file"
    result["gt_file"] = str(gt_file)
    result["gen_file"] = str(gen_file)
    return result


# ---------------------------------------------------------------------------
# Pretty-print report
# ---------------------------------------------------------------------------

DIMENSION_LABELS = {
    "structural_completeness": "Structural Completeness",
    "element_type_match":      "Element Type Match",
    "attribute_accuracy":      "Attribute Accuracy",
    "tag_coverage":            "Tag Coverage",
}


def print_report(result: dict[str, Any], verbose: bool = True) -> None:
    W = 72
    bar = "=" * W
    print(f"\n{bar}")
    print("  LXML REFERENCE-BASED XML EVALUATION REPORT")
    print(bar)

    overall = result["overall_score"]
    symbol = "✓" if overall >= 7.0 else "✗"
    print(f"\n  {symbol} OVERALL SCORE : {overall:.2f} / 10.00")
    print()

    print("  DIMENSION SCORES")
    print("  " + "-" * (W - 2))
    for key, label in DIMENSION_LABELS.items():
        raw = result["dimension_scores"][key]
        w   = result["weights"][key]
        bar_len = int(raw * 20)
        bar_str = "█" * bar_len + "░" * (20 - bar_len)
        print(f"  {label:<28} {raw:.3f}  [{bar_str}]  (w={w:.2f})")

    if verbose:
        print()
        details = result.get("details", {})

        # Structural completeness
        d = details.get("structural_completeness", {})
        if d.get("required_missing"):
            print("  ⚠  Missing required sections:", ", ".join(d["required_missing"]))
        if d.get("required_present"):
            print("  ✓  Required sections present:", ", ".join(d["required_present"]))

        # Element types
        d = details.get("element_type_match", {})
        if d.get("gt_only"):
            print("  ⚠  Element types in GT only:", ", ".join(d["gt_only"]))
        if d.get("gen_only"):
            print("  ℹ  Extra element types in GEN:", ", ".join(d["gen_only"]))

        # Attribute accuracy — show mismatches
        d = details.get("attribute_accuracy", {})
        mismatches_shown = 0
        for elem_detail in d.get("details", []):
            for m in elem_detail.get("mismatches", []):
                if mismatches_shown == 0:
                    print("\n  ATTRIBUTE MISMATCHES")
                    print("  " + "-" * (W - 2))
                print(f"  [{elem_detail.get('name', elem_detail.get('tag', '?'))}] {m}")
                mismatches_shown += 1

        # Tag coverage
        d = details.get("tag_coverage", {})
        if d.get("missing"):
            print("\n  ⚠  Missing tag types (in GT, absent in GEN):", ", ".join(d["missing"]))

    print(f"\n{bar}\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reference-based lxml XML evaluator for GEOS agent outputs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Directory mode
    parser.add_argument("--ground-truth-dir", type=Path,
                        help="Directory of ground-truth XML files")
    parser.add_argument("--generated-dir",    type=Path,
                        help="Directory of generated XML files")

    # Single-file mode
    parser.add_argument("--ground-truth", type=Path,
                        help="Single ground-truth XML file")
    parser.add_argument("--generated",    type=Path,
                        help="Single generated XML file")

    # Options
    parser.add_argument("--output", "-o", type=Path,
                        help="Save full JSON result to this path")
    parser.add_argument("--rtol", type=float, default=NUMERIC_RTOL,
                        help=f"Relative tolerance for numeric comparison (default: {NUMERIC_RTOL})")
    parser.add_argument("--quiet", "-q", action="store_true",
                        help="Only print overall score")
    parser.add_argument("--json", action="store_true",
                        help="Print raw JSON result instead of formatted report")

    args = parser.parse_args()

    dir_mode  = bool(args.ground_truth_dir or args.generated_dir)
    file_mode = bool(args.ground_truth or args.generated)

    if dir_mode and file_mode:
        parser.error("Cannot mix --ground-truth-dir/--generated-dir with --ground-truth/--generated")

    if dir_mode:
        if not (args.ground_truth_dir and args.generated_dir):
            parser.error("Both --ground-truth-dir and --generated-dir are required")
        print(f"Resolving GT  : {args.ground_truth_dir}")
        print(f"Resolving GEN : {args.generated_dir}")
        result = evaluate_directories(args.ground_truth_dir, args.generated_dir, args.rtol)

    elif file_mode:
        if not (args.ground_truth and args.generated):
            parser.error("Both --ground-truth and --generated are required")
        print(f"Resolving GT  : {args.ground_truth}")
        print(f"Resolving GEN : {args.generated}")
        result = evaluate_files(args.ground_truth, args.generated, args.rtol)

    else:
        parser.error("Provide either directory or file arguments")

    if args.json:
        print(json.dumps(result, indent=2))
    elif args.quiet:
        print(f"\nOverall Score: {result['overall_score']:.2f} / 10.00\n")
    else:
        print_report(result, verbose=True)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2))
        print(f"Result saved to: {args.output}")

    sys.exit(0 if result["overall_score"] >= 7.0 else 1)


if __name__ == "__main__":
    main()
