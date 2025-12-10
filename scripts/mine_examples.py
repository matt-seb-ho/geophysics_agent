import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, List, Optional, Dict, Any


# extract examples from .rst sphinx doc files


# ---------- Data structures ----------


@dataclass
class ExampleGroundTruth:
    """
    Structured representation of one GEOS documentation example.

    This is what you'll later serialize to JSON and feed into your
    evaluation harness.
    """

    example_id: str  # e.g. "basic/multiphaseFlow"
    title: str  # "Multiphase Flow"
    category: str  # "basic" or "advanced"
    rst_path: str  # relative path from repo root

    # Natural-language text to use as prompt context
    context: str
    objectives: str
    description: str  # optional extra free text

    # Ground truth "code" the agent should recover
    input_files: List[str]  # XML decks and any other required inputs
    aux_files: List[str]  # tables, meshes, helper scripts, etc.
    run_commands: List[str]  # canonical geosx / MPI / python commands
    postprocess_commands: List[str]  # python plotting scripts or similar
    expected_outputs: List[str]  # files or glob patterns

    def to_jsonable(self) -> Dict[str, Any]:
        d = asdict(self)
        # Make sure everything is JSON-serializable
        return d


# ---------- Low-level utilities ----------

SECTION_HEADERS = [
    "Context",
    "Objective",
    "Objectives",
    "Input file",
    "Input files",
    "Running GEOS",
    "Running TriaxialDriver",
    "Running",
    "Inspecting results",
    "Results",
]

FILE_PATH_RE = re.compile(
    r"""
    (?P<path>
        (?:\.\./)*inputFiles/[^\s`]+ |
        src/docs/sphinx/[^\s`]+     |
        GEOSDATA[^\s`]*             |
        [A-Za-z0-9_.\-/]+\.xml      |
        [A-Za-z0-9_.\-/]+\.py       |
        [A-Za-z0-9_.\-/]+\.txt      |
        [A-Za-z0-9_.\-/]+\.vtu      |
        [A-Za-z0-9_.\-/]+\.vtk      |
        [A-Za-z0-9_.\-/]+\.csv      |
        [A-Za-z0-9_.\-/]+\.h5       |
        [A-Za-z0-9_.\-/]+\.xdmf     |
        [A-Za-z0-9_.\-/]+\.xmf
    )
    """,
    re.VERBOSE,
)

RUN_CMD_RE = re.compile(
    r"""
    ^\s*
    (?:
        (?:mpirun|mpiexec)[^\n]*geosx[^\n]* |
        (?:\$\s*)?(?:\S*/)?geosx[^\n]*-i[^\n]* |
        python\s+[^\n]*\.py[^\n]*
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Very loose heuristic: expected outputs are files mentioned
# in a section whose header contains "Inspecting results" or "Results".
OUTPUT_SECTION_HINTS = {"inspecting results", "results"}


def _read_text(path: Path) -> List[str]:
    text = path.read_text(encoding="utf-8")
    return text.splitlines()


def _find_section_indices(lines: List[str]) -> Dict[str, int]:
    """
    Return a map from header name (as in SECTION_HEADERS) to the
    line index where that header appears.

    We treat a line that matches the header *exactly* as the header.
    """
    indices: Dict[str, int] = {}
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped in SECTION_HEADERS and stripped not in indices:
            indices[stripped] = i
    return indices


def _slice_section(lines: List[str], start_idx: int, end_idx: Optional[int]) -> str:
    if end_idx is None:
        end = len(lines)
    else:
        end = end_idx
    # Skip the header line itself
    body = lines[start_idx + 1 : end]
    return "\n".join(body).strip()


def _extract_first_matching_section(
    lines: List[str],
    header_map: Dict[str, int],
    names: List[str],
    next_section_start: int | None,
) -> str:
    """
    Return the concatenated body of the first section found among `names`.
    """
    for name in names:
        if name in header_map:
            start_idx = header_map[name]
            end_idx: Optional[int] = None
            if next_section_start is not None and next_section_start > start_idx:
                end_idx = next_section_start
            return _slice_section(lines, start_idx, end_idx)
    return ""


def _extract_all_paths(text: str) -> List[str]:
    paths = []
    for m in FILE_PATH_RE.finditer(text):
        paths.append(m.group("path"))
    # Deduplicate while preserving order
    seen = set()
    unique = []
    for p in paths:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return unique


def _extract_run_commands(text: str) -> List[str]:
    cmds = []
    for line in text.splitlines():
        m = RUN_CMD_RE.match(line)
        if m:
            cmd = line.strip()
            if cmd.startswith("$"):
                cmd = cmd.lstrip("$").strip()
            if cmd and cmd not in cmds:
                cmds.append(cmd)
    return cmds


# ---------- Example-level parsing ----------


def parse_example_rst(
    rst_path: Path,
    category: str,
    repo_root: Path,
) -> ExampleGroundTruth:
    """
    Parse a single Example.rst-like file into an ExampleGroundTruth object.

    This uses simple heuristics tailored to the GEOS docs; you can
    refine the regexes once you've inspected more examples.
    """
    lines = _read_text(rst_path)
    header_map = _find_section_indices(lines)

    # Title: first non-empty line
    title = ""
    for line in lines:
        if line.strip():
            title = line.strip()
            break

    # To find section boundaries, we sort headers by line index.
    header_items = sorted(header_map.items(), key=lambda kv: kv[1])
    header_starts = [idx for _, idx in header_items]

    def next_header_after(idx: int) -> Optional[int]:
        for h in header_starts:
            if h > idx:
                return h
        return None

    # Context / Objectives section bodies
    context = ""
    if any(h in header_map for h in ("Context",)):
        idx = min(header_map[h] for h in ("Context",) if h in header_map)
        next_idx = next_header_after(idx)
        context = _slice_section(lines, idx, next_idx)

    objectives = ""
    if any(h in header_map for h in ("Objective", "Objectives")):
        idx = min(header_map[h] for h in ("Objective", "Objectives") if h in header_map)
        next_idx = next_header_after(idx)
        objectives = _slice_section(lines, idx, next_idx)

    # For description, just grab a bit more of the file (optional)
    description = ""
    if "Context" in header_map:
        start = header_map["Context"]
        # up to e.g. "Input file" if present
        end = header_map.get("Input file", header_map.get("Input files"))
        description = _slice_section(lines, start, end)

    full_text = "\n".join(lines)

    # Input files: prioritize paths near the "Input file(s)" section if present
    input_files: List[str] = []
    aux_files: List[str] = []

    if "Input file" in header_map or "Input files" in header_map:
        header_name = "Input file" if "Input file" in header_map else "Input files"
        idx = header_map[header_name]
        next_idx = next_header_after(idx)
        input_section_text = _slice_section(lines, idx, next_idx)
        input_paths = _extract_all_paths(input_section_text)
        input_files.extend(input_paths)

    # If we didn't find any, fall back to scanning entire file
    if not input_files:
        input_files = _extract_all_paths(full_text)

    # Run commands: look for commands in "Running..." / "Inspecting results" first
    run_commands: List[str] = []
    postprocess_commands: List[str] = []

    for hname in header_map:
        lower = hname.lower()
        idx = header_map[hname]
        next_idx = next_header_after(idx)
        sec_text = _slice_section(lines, idx, next_idx)

        cmds = _extract_run_commands(sec_text)
        if "running" in lower:
            for c in cmds:
                if "geosx" in c and c not in run_commands:
                    run_commands.append(c)
                elif c not in postprocess_commands:
                    postprocess_commands.append(c)
        elif "inspect" in lower or "results" in lower:
            for c in cmds:
                if "python" in c and c not in postprocess_commands:
                    postprocess_commands.append(c)

    # Fallback: scan whole file for run commands
    if not run_commands and not postprocess_commands:
        cmds = _extract_run_commands(full_text)
        for c in cmds:
            if "geosx" in c:
                run_commands.append(c)
            else:
                postprocess_commands.append(c)

    # Expected outputs: from "Inspecting results" / "Results" sections
    expected_outputs: List[str] = []
    for hname, idx in header_map.items():
        if hname.lower() in OUTPUT_SECTION_HINTS:
            next_idx = next_header_after(idx)
            sec_text = _slice_section(lines, idx, next_idx)
            paths = _extract_all_paths(sec_text)
            for p in paths:
                if p not in expected_outputs:
                    expected_outputs.append(p)

    # Aux files: everything that isn't clearly a primary input deck
    # (This is a heuristic; you can refine it later.)
    primary_ext = {".xml"}
    for p in _extract_all_paths(full_text):
        suffix = Path(p).suffix
        if (
            suffix not in primary_ext
            and p not in input_files
            and p not in expected_outputs
        ):
            aux_files.append(p)
    # Dedup
    aux_files = list(dict.fromkeys(aux_files))

    # Example ID: e.g. "basic/multiphaseFlow"
    # Use path naming convention:
    #   src/docs/sphinx/basicExamples/<name>/Example.rst
    rel = rst_path.relative_to(repo_root).as_posix()
    parts = rst_path.parts
    # ... basicExamples/<name>/Example.rst
    example_name = "unknown"
    if "basicExamples" in parts:
        idx = parts.index("basicExamples")
        if idx + 1 < len(parts):
            example_name = parts[idx + 1]
    elif "advancedExamples" in parts:
        idx = parts.index("advancedExamples")
        if idx + 1 < len(parts):
            example_name = parts[idx + 1]

    example_id = f"{category}/{example_name}"

    return ExampleGroundTruth(
        example_id=example_id,
        title=title,
        category=category,
        rst_path=rel,
        context=context,
        objectives=objectives,
        description=description,
        input_files=input_files,
        aux_files=aux_files,
        run_commands=run_commands,
        postprocess_commands=postprocess_commands,
        expected_outputs=expected_outputs,
    )


# ---------- Top-level API ----------


def iter_example_rst_paths(
    repo_root: Path,
) -> Iterable[tuple[Path, str]]:
    """
    Yield (rst_path, category) for all Example.rst files under
    basicExamples and advancedExamples.
    """
    basic_root = repo_root / "src" / "docs" / "sphinx" / "basicExamples"
    adv_root = repo_root / "src" / "docs" / "sphinx" / "advancedExamples"

    if basic_root.is_dir():
        for path in basic_root.rglob("Example.rst"):
            yield path, "basic"

    if adv_root.is_dir():
        for path in adv_root.rglob("Example.rst"):
            yield path, "advanced"


def load_all_examples(repo_root: Path) -> List[ExampleGroundTruth]:
    """
    Discover and parse all GEOS example docs into structured ground truth.
    """
    examples: List[ExampleGroundTruth] = []
    for rst_path, category in iter_example_rst_paths(repo_root):
        try:
            ex = parse_example_rst(rst_path, category=category, repo_root=repo_root)
            examples.append(ex)
        except Exception as e:
            # You can decide whether to raise or just log a warning.
            # For now, we just print and skip.
            print(f"[warn] Failed to parse {rst_path}: {e}")
    return examples


def dump_examples_to_json(
    repo_root: Path,
    out_path: Path,
) -> None:
    """
    Convenience function to create a JSON file with all mined examples.
    """
    import json

    examples = load_all_examples(repo_root)
    data = [ex.to_jsonable() for ex in examples]
    out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


# If you want a small CLI:
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Mine GEOS documentation examples into JSON ground truth."
    )
    parser.add_argument(
        "repo_root",
        type=Path,
        help="Path to the GEOS repo root (containing src/docs/sphinx).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("geos_example_ground_truth.json"),
        help="Output JSON path.",
    )
    args = parser.parse_args()

    dump_examples_to_json(args.repo_root, args.out)
    print(f"Wrote mined examples to {args.out}")
