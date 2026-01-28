#!/usr/bin/env python3
"""
Knowledge Pipeline: Transform raw GEOS docs into clean, atomic RAG knowledge base.

This script orchestrates the transformation from "Messy Human Docs" (source/)
to "Clean Machine Docs" (processed/) following llms.txt principles.

Key transformations:
1. RST → Markdown conversion
2. Large files → Atomic chunks (H2/H3 headers)
3. Context injection (breadcrumbs for each chunk)
4. Example colocating (inline XML with explanations)
5. Master index generation (llms.txt)

Usage:
    python scripts/build_knowledge.py [--geos-repo PATH]
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

# Add project root to Python path to enable imports from src/
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.geos_agent.constants import (
    CONCEPTS_DIR,
    EXAMPLES_DIR,
    PROCESSED_DOCS_DIR,
    SOURCE_DOCS_DIR,
)


# ============================================================================
# Data Structures
# ============================================================================


@dataclass
class AtomicConcept:
    """Represents a single atomic concept chunk."""

    concept_id: str  # e.g., "solvers/mechanics/overview"
    title: str  # Human-readable title
    breadcrumbs: str  # Parent context, e.g., "Solvers > Mechanics"
    content: str  # Markdown content
    source_file: str  # Original RST file path


@dataclass
class ProcessedExample:
    """Represents a processed example with inlined XML."""

    example_id: str  # e.g., "basic/multiphaseFlow"
    title: str  # "Multiphase Flow"
    category: str  # "basic" or "advanced"
    explanation: str  # Markdown explanation
    xml_content: str  # Inlined XML code
    objectives: str  # What this example demonstrates
    source_file: str  # Original RST file path


# ============================================================================
# Literalinclude Processing
# ============================================================================


def parse_literalinclude_block(block: str) -> dict:
    """
    Parse a literalinclude directive block and extract all options.
    
    Args:
        block: Complete directive block including `.. literalinclude::` line and options
        
    Returns:
        Dict with keys: file_path, language, start_after, end_before, lines
    """
    result = {
        "file_path": None,
        "language": None,
        "start_after": None,
        "end_before": None,
        "lines": None,
    }
    
    lines = block.strip().split("\n")
    if not lines:
        return result
    
    # First line: .. literalinclude:: path/to/file
    first_line = lines[0]
    match = re.match(r"\.\.\s+literalinclude::\s*(.+)", first_line)
    if match:
        result["file_path"] = match.group(1).strip()
    
    # Parse options from subsequent lines
    for line in lines[1:]:
        line = line.strip()
        if line.startswith(":language:"):
            result["language"] = line.split(":", 2)[2].strip()
        elif line.startswith(":start-after:"):
            result["start_after"] = line.split(":", 2)[2].strip()
        elif line.startswith(":end-before:"):
            result["end_before"] = line.split(":", 2)[2].strip()
        elif line.startswith(":lines:"):
            result["lines"] = line.split(":", 2)[2].strip()
    
    return result


def extract_content_between_markers(
    content: str, start_marker: Optional[str], end_marker: Optional[str]
) -> Optional[str]:
    """
    Extract content between start and end markers (exclusive).
    
    Args:
        content: Full file content
        start_marker: Marker after which to start extraction (exclusive)
        end_marker: Marker before which to stop extraction (exclusive)
        
    Returns:
        Extracted content or None if markers not found
    """
    if start_marker is None and end_marker is None:
        return content
    
    start_idx = 0
    end_idx = len(content)
    
    if start_marker:
        pos = content.find(start_marker)
        if pos == -1:
            return None
        # Find end of the line containing the marker
        newline_pos = content.find("\n", pos)
        start_idx = newline_pos + 1 if newline_pos != -1 else pos + len(start_marker)
    
    if end_marker:
        pos = content.find(end_marker, start_idx)
        if pos == -1:
            return None
        # Find start of the line containing the marker
        end_idx = content.rfind("\n", start_idx, pos)
        if end_idx == -1:
            end_idx = pos
    
    extracted = content[start_idx:end_idx]
    # Strip leading/trailing empty lines but preserve internal structure
    lines = extracted.split("\n")
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    
    return "\n".join(lines)


def search_source_for_markers(
    source_root: Path, start_marker: str, end_marker: str
) -> Optional[str]:
    """
    Search all files in source directory for content matching markers.
    
    Args:
        source_root: Root directory to search
        start_marker: The start-after marker to find
        end_marker: The end-before marker to find
        
    Returns:
        Extracted content or None if not found
    """
    # Search in inputFiles directory first (most likely location)
    search_dirs = [
        source_root / "inputFiles",
        source_root / "src",
        source_root,
    ]
    
    extensions = [".xml", ".hpp", ".cpp", ".py"]
    
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        for ext in extensions:
            for file_path in search_dir.rglob(f"*{ext}"):
                try:
                    content = file_path.read_text(encoding="utf-8")
                    if start_marker in content and end_marker in content:
                        extracted = extract_content_between_markers(
                            content, start_marker, end_marker
                        )
                        if extracted:
                            return extracted
                except Exception:
                    continue
    
    return None


def resolve_literalinclude_path(
    file_path: str, rst_file: Path, source_root: Path
) -> Optional[Path]:
    """
    Resolve a literalinclude file path relative to the RST file.
    
    Args:
        file_path: The path from the literalinclude directive
        rst_file: Path to the RST file containing the directive
        source_root: Root of the source documentation
        
    Returns:
        Resolved absolute path or None if not found
    """
    # Try resolving relative to RST file's directory
    rst_dir = rst_file.parent
    resolved = (rst_dir / file_path).resolve()
    if resolved.exists():
        return resolved
    
    # Try resolving relative to source root
    resolved = (source_root / file_path).resolve()
    if resolved.exists():
        return resolved
    
    # Try finding file by name in inputFiles
    filename = Path(file_path).name
    input_files_dir = source_root / "inputFiles"
    if input_files_dir.exists():
        for found in input_files_dir.rglob(filename):
            return found
    
    return None


def process_literalinclude(
    block: str, rst_file: Path, source_root: Path
) -> str:
    """
    Process a literalinclude directive and return markdown code block.
    
    Args:
        block: The complete literalinclude directive block
        rst_file: Path to the RST file containing the directive
        source_root: Root of source documentation
        
    Returns:
        Markdown code block with embedded content
    """
    parsed = parse_literalinclude_block(block)
    
    language = parsed.get("language") or "text"
    start_marker = parsed.get("start_after")
    end_marker = parsed.get("end_before")
    
    content = None
    
    # Try to resolve file path and read content
    if parsed.get("file_path"):
        resolved_path = resolve_literalinclude_path(
            parsed["file_path"], rst_file, source_root
        )
        if resolved_path:
            try:
                file_content = resolved_path.read_text(encoding="utf-8")
                content = extract_content_between_markers(
                    file_content, start_marker, end_marker
                )
            except Exception:
                pass
    
    # Fallback: search source files for markers
    if content is None and start_marker and end_marker:
        content = search_source_for_markers(source_root, start_marker, end_marker)
    
    if content is None:
        # Return a placeholder comment
        marker_info = f"start={start_marker}, end={end_marker}" if start_marker else ""
        return f"<!-- Code snippet not found: {parsed.get('file_path', 'unknown')} {marker_info} -->\n"
    
    return f"```{language}\n{content}\n```\n"


# ============================================================================
# RST to Markdown Conversion
# ============================================================================


def rst_to_markdown(
    rst_content: str,
    rst_file: Optional[Path] = None,
    source_root: Optional[Path] = None,
) -> str:
    """
    Convert RST content to Markdown.

    This is a simplified converter. For production, consider using
    pandoc or a more robust library like rst2mdown.
    """
    md = rst_content

    # Convert RST headers to Markdown
    # RST uses underlines: Title\n====== → # Title
    md = re.sub(r"^(.+)\n=+\s*$", r"# \1", md, flags=re.MULTILINE)
    md = re.sub(r"^(.+)\n-+\s*$", r"## \1", md, flags=re.MULTILINE)
    md = re.sub(r"^(.+)\n~+\s*$", r"### \1", md, flags=re.MULTILINE)
    md = re.sub(r"^(.+)\n\^+\s*$", r"#### \1", md, flags=re.MULTILINE)

    # Convert code blocks: .. code-block:: language → ```language
    md = re.sub(
        r"\.\. code-block::\s*(\w+)\s*\n\s*\n",
        r"```\1\n",
        md,
    )

    # Convert literal blocks: :: → ```
    md = re.sub(r"::\s*\n\s*\n", r"```\n", md)

    # Convert inline code: ``code`` → `code`
    md = re.sub(r"``([^`]+)``", r"`\1`", md)

    # Convert bold: **text** stays the same
    # Convert italic: *text* stays the same

    # Convert RST links: `text <url>`_ → [text](url)
    md = re.sub(r"`([^<]+)<([^>]+)>`_", r"[\1](\2)", md)

    # Convert bullet lists (already compatible with Markdown)
    # RST: * item or - item

    # Process literalinclude directives - embed code inline
    if rst_file is not None and source_root is not None:
        # Pattern to match literalinclude blocks with their options
        # Matches: .. literalinclude:: path\n  :option: value\n  :option2: value2
        literalinclude_pattern = re.compile(
            r"(\.\.\s+literalinclude::\s*[^\n]+\n(?:\s+:[^\n]+\n)*)",
            re.MULTILINE
        )
        
        def replace_literalinclude(match):
            block = match.group(1)
            return process_literalinclude(block, rst_file, source_root)
        
        md = literalinclude_pattern.sub(replace_literalinclude, md)
    
    # Remove remaining RST directives that don't translate well
    # (skip literalinclude since we processed it above)
    md = re.sub(r"\.\.\s+(?!literalinclude)\w+::\s*.*$", "", md, flags=re.MULTILINE)
    
    # Clean up orphaned directive options (lines starting with :option:)
    md = re.sub(r"^\s+:[a-z-]+:\s*.*$", "", md, flags=re.MULTILINE)

    return md


# ============================================================================
# Concept Chunking
# ============================================================================


def split_by_headers(md_content: str, level: int = 2) -> List[tuple[str, str]]:
    """
    Split Markdown content by headers of a specific level.

    Args:
        md_content: The Markdown content to split
        level: Header level to split on (2 for ##, 3 for ###)

    Returns:
        List of (title, content) tuples
    """
    header_pattern = r"^" + "#" * level + r"\s+(.+)$"
    lines = md_content.split("\n")

    chunks = []
    current_title = None
    current_content = []

    for line in lines:
        match = re.match(header_pattern, line)
        if match:
            # Save previous chunk
            if current_title is not None:
                chunks.append((current_title, "\n".join(current_content)))

            # Start new chunk
            current_title = match.group(1).strip()
            current_content = [line]
        else:
            if current_title is not None:
                current_content.append(line)
            # If no title yet, skip preamble

    # Save last chunk
    if current_title is not None:
        chunks.append((current_title, "\n".join(current_content)))

    return chunks


def create_breadcrumbs(file_path: Path, section_title: str) -> str:
    """
    Generate breadcrumb context from file path and section.

    Example: "User Guide > Solvers > Mechanics > Overview"
    """
    parts = file_path.parts
    breadcrumb_parts = []

    # Extract meaningful path components
    for i, part in enumerate(parts):
        if part in ("docs", "sphinx", "src"):
            continue
        if part.endswith(".rst") or part.endswith(".md"):
            # Use filename without extension
            breadcrumb_parts.append(part.rsplit(".", 1)[0])
        else:
            breadcrumb_parts.append(part.replace("_", " ").title())

    # Add section title
    breadcrumb_parts.append(section_title)

    return " > ".join(breadcrumb_parts)


def process_user_guide_to_concepts(
    rst_file: Path,
    source_root: Path,
) -> List[AtomicConcept]:
    """
    Process a User Guide RST file into atomic concept chunks.

    Args:
        rst_file: Path to the RST file
        source_root: Root directory of source docs

    Returns:
        List of AtomicConcept objects
    """
    rst_content = rst_file.read_text(encoding="utf-8")
    md_content = rst_to_markdown(rst_content, rst_file=rst_file, source_root=source_root)

    # Try splitting by H2 headers first (##), then H1 (#) if no H2 found
    chunks = split_by_headers(md_content, level=2)
    if not chunks:
        # If no H2 headers, try H1 headers
        chunks = split_by_headers(md_content, level=1)

    # If still no chunks but has content, treat whole file as one chunk
    if not chunks and md_content.strip():
        # Extract title from first line or filename
        lines = md_content.strip().split("\n")
        title = lines[0].lstrip("#").strip() if lines else rst_file.stem
        chunks = [(title, md_content)]

    concepts = []
    for title, content in chunks:
        # Generate concept ID from file path and title
        rel_path = rst_file.relative_to(source_root)
        concept_id = (
            str(rel_path.parent / rel_path.stem)
            .replace("\\", "/")
            .lower()
            .replace(" ", "_")
        )
        concept_id = f"{concept_id}/{title.lower().replace(' ', '_')}"

        # Generate breadcrumbs
        breadcrumbs = create_breadcrumbs(rel_path, title)

        # Prepend metadata to content
        enriched_content = f"**Context:** {breadcrumbs}\n\n{content}"

        concepts.append(
            AtomicConcept(
                concept_id=concept_id,
                title=title,
                breadcrumbs=breadcrumbs,
                content=enriched_content,
                source_file=str(rel_path),
            )
        )

    return concepts


# ============================================================================
# Example Processing with Inline XML
# ============================================================================


def find_xml_file(
    example_dir: Path, rst_content: str, source_root: Path
) -> Optional[Path]:
    """
    Find the XML input file referenced in the example.

    Looks for:
    1. Explicit references in the RST content
    2. inputFiles/{example_name}/ directory
    3. Example directory itself
    4. Common naming patterns
    """
    # Get example name from directory
    example_name = example_dir.name

    # Try to find XML reference in content
    xml_pattern = r"(?:inputFiles/|\.\./)([^\s`]+\.xml)"
    matches = re.findall(xml_pattern, rst_content)

    # Possible search locations
    search_dirs = [
        source_root / "inputFiles" / example_name,  # GEOS typical location
        example_dir,  # Same directory as Example.rst
        example_dir.parent / "inputFiles",  # Sibling inputFiles directory
    ]

    if matches:
        # Try to find the referenced XML file
        for match in matches:
            xml_filename = Path(match).name

            # Search in all possible directories
            for search_dir in search_dirs:
                if search_dir.exists():
                    xml_path = search_dir / xml_filename
                    if xml_path.exists():
                        return xml_path

                    # Also try finding any file with similar name
                    for xml_file in search_dir.glob("*.xml"):
                        if xml_filename.lower() in xml_file.name.lower():
                            return xml_file

    # Fallback: look for any XML file in search directories
    for search_dir in search_dirs:
        if search_dir.exists():
            xml_files = list(search_dir.glob("*.xml"))
            if xml_files:
                # Prefer files with 'benchmark' or 'base' in the name
                for xml_file in xml_files:
                    if "benchmark" in xml_file.name.lower():
                        return xml_file
                # Otherwise return the first one
                return xml_files[0]

    return None


def process_example_with_inline_xml(
    example_rst: Path,
    category: str,
    source_root: Path,
) -> Optional[ProcessedExample]:
    """
    Process an example RST file with inlined XML content.

    Args:
        example_rst: Path to Example.rst file
        category: "basic" or "advanced"
        source_root: Root directory of source docs

    Returns:
        ProcessedExample object or None if processing fails
    """
    try:
        rst_content = example_rst.read_text(encoding="utf-8")
        md_content = rst_to_markdown(rst_content, rst_file=example_rst, source_root=source_root)

        # Extract title (first non-empty line)
        title = "Unknown Example"
        for line in md_content.split("\n"):
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                title = stripped.lstrip("#").strip()
                break

        # Extract objectives section
        objectives = ""
        obj_match = re.search(
            r"##\s+Objectives?\s*\n(.*?)(?=\n##|\Z)",
            md_content,
            re.DOTALL | re.IGNORECASE,
        )
        if obj_match:
            objectives = obj_match.group(1).strip()

        # Find and read XML file
        example_dir = example_rst.parent
        xml_file = find_xml_file(example_dir, rst_content, source_root)

        xml_content = ""
        if xml_file:
            xml_content = xml_file.read_text(encoding="utf-8")
        else:
            xml_content = "<!-- XML file not found -->"

        # Generate example ID
        parts = example_rst.parts
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

        # Remove objectives section from explanation (we'll store it separately)
        explanation = re.sub(
            r"##\s+Objectives?\s*\n.*?(?=\n##|\Z)",
            "",
            md_content,
            flags=re.DOTALL | re.IGNORECASE,
        )

        rel_path = example_rst.relative_to(source_root)

        return ProcessedExample(
            example_id=example_id,
            title=title,
            category=category,
            explanation=explanation.strip(),
            xml_content=xml_content,
            objectives=objectives,
            source_file=str(rel_path),
        )

    except Exception as e:
        print(f"[warn] Failed to process example {example_rst}: {e}")
        return None


# ============================================================================
# llms.txt Generation
# ============================================================================


def generate_llms_txt(
    concepts: List[AtomicConcept],
    examples: List[ProcessedExample],
    output_path: Path,
) -> None:
    """
    Generate the master llms.txt index file.

    This file provides a high-level map of the knowledge base for the agent.
    """
    lines = [
        "# GEOS Documentation Knowledge Base",
        "",
        "This knowledge base contains processed GEOS documentation optimized for LLM retrieval.",
        "",
        "## Structure",
        "",
        "- `concepts/`: Atomic concept definitions from user guides",
        "- `examples/`: Example simulations with inlined XML code",
        "",
        "## High-Value Files",
        "",
        "### Concepts",
        "",
    ]

    # List top concepts (you might want to prioritize certain ones)
    for concept in concepts[:20]:  # Limit to top 20
        rel_path = f"concepts/{concept.concept_id}.md"
        lines.append(f"- [{concept.title}]({rel_path}) - {concept.breadcrumbs}")

    if len(concepts) > 20:
        lines.append(f"\n... and {len(concepts) - 20} more concepts\n")

    lines.extend(["", "### Examples", ""])

    # List all examples
    for example in examples:
        rel_path = f"examples/{example.example_id}.md"
        lines.append(f"- [{example.title}]({rel_path}) - {example.category}")

    lines.extend(
        [
            "",
            "## Usage",
            "",
            "When searching for information:",
            "1. Check `concepts/` for theoretical understanding",
            "2. Check `examples/` for practical implementations",
            "3. Each example includes complete XML code for reference",
            "",
        ]
    )

    output_path.write_text("\n".join(lines), encoding="utf-8")


# ============================================================================
# File Output
# ============================================================================


def write_concept_to_file(concept: AtomicConcept, output_dir: Path) -> None:
    """Write an AtomicConcept to a Markdown file."""
    # Create subdirectories based on concept_id
    concept_path = output_dir / f"{concept.concept_id}.md"
    concept_path.parent.mkdir(parents=True, exist_ok=True)

    concept_path.write_text(concept.content, encoding="utf-8")


def write_example_to_file(example: ProcessedExample, output_dir: Path) -> None:
    """Write a ProcessedExample to a Markdown file.
    
    Note: XML code snippets are now embedded inline within the explanation
    via literalinclude processing, so we no longer append the full XML file.
    """
    example_path = output_dir / f"{example.example_id}.md"
    example_path.parent.mkdir(parents=True, exist_ok=True)

    # Build content with explanation (XML is embedded inline via literalinclude)
    content_parts = [
        f"# {example.title}",
        "",
        f"**Category:** {example.category}",
        "",
    ]

    if example.objectives:
        content_parts.extend(["## Objectives", "", example.objectives, ""])

    content_parts.extend(
        [
            "## Explanation",
            "",
            example.explanation,
            "",
        ]
    )

    example_path.write_text("\n".join(content_parts), encoding="utf-8")


# ============================================================================
# Main Pipeline
# ============================================================================


def build_knowledge_base(
    geos_repo: Optional[Path] = None,
    source_dir: Optional[Path] = None,
) -> None:
    """
    Main orchestrator: Transform source docs to processed knowledge base.

    Args:
        geos_repo: Path to GEOS repository (if provided, copies docs to source/)
        source_dir: Use this as source if geos_repo not provided
    """
    if source_dir is None:
        source_dir = SOURCE_DOCS_DIR

    # If GEOS repo provided, copy relevant docs to source/
    if geos_repo:
        print(f"Copying docs from {geos_repo} to {source_dir}...")
        import shutil

        sphinx_dir = geos_repo / "src" / "docs" / "sphinx"
        if sphinx_dir.exists():
            # Copy user guides and examples
            for subdir in ["basicExamples", "advancedExamples", "userGuide"]:
                src = sphinx_dir / subdir
                if src.exists():
                    dst = source_dir / subdir
                    if dst.exists():
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
        else:
            print(f"[error] Sphinx directory not found: {sphinx_dir}")
            return

    # Verify source directory exists
    if not source_dir.exists():
        print(f"[error] Source directory does not exist: {source_dir}")
        print("Please provide --geos-repo to populate source docs.")
        return

    print("\n=== Phase 1: Processing User Guide Concepts ===\n")

    concepts = []

    # Look for documentation in multiple locations
    doc_search_paths = [
        source_dir / "src" / "coreComponents",  # Component-specific docs
        source_dir / "src" / "docs" / "sphinx",  # Sphinx docs
        source_dir / "coreComponents",  # Alternative location
        source_dir / "userGuide",  # If copied directly
    ]

    # Collect all RST files from documentation directories
    rst_files = set()
    for search_path in doc_search_paths:
        if search_path.exists():
            for rst_file in search_path.rglob("*.rst"):
                # Skip index files that are just TOCs
                if rst_file.name.lower() in ["index.rst", "contents.rst"]:
                    continue
                # Skip files in example directories (case-insensitive substring match)
                if any("example" in part.lower() for part in rst_file.parts):
                    continue
                rst_files.add(rst_file)

    print(f"Found {len(rst_files)} documentation files to process\n")

    # Process each RST file
    for rst_file in sorted(rst_files):
        # Find the root to calculate relative path
        file_root = source_dir
        for search_path in doc_search_paths:
            if search_path.exists() and rst_file.is_relative_to(search_path):
                file_root = search_path
                break

        print(f"Processing: {rst_file.relative_to(source_dir)}")
        file_concepts = process_user_guide_to_concepts(rst_file, file_root)
        concepts.extend(file_concepts)
        if len(file_concepts) > 0:
            print(f"  → Generated {len(file_concepts)} concept chunks")

    print(f"\nTotal concepts: {len(concepts)}")

    # Write concepts to files
    print("\nWriting concepts to disk...")
    for concept in concepts:
        write_concept_to_file(concept, CONCEPTS_DIR)

    print("\n=== Phase 2: Processing Examples with Inline XML ===\n")

    examples = []

    # Process basic examples
    basic_dir = source_dir / "basicExamples"
    if basic_dir.exists():
        for example_rst in basic_dir.rglob("Example.rst"):
            print(f"Processing: {example_rst.relative_to(source_dir)}")
            example = process_example_with_inline_xml(
                example_rst, "basic", source_dir
            )
            if example:
                examples.append(example)

    # Process advanced examples
    adv_dir = source_dir / "advancedExamples"
    if adv_dir.exists():
        for example_rst in adv_dir.rglob("Example.rst"):
            print(f"Processing: {example_rst.relative_to(source_dir)}")
            example = process_example_with_inline_xml(
                example_rst, "advanced", source_dir
            )
            if example:
                examples.append(example)

    print(f"\nTotal examples: {len(examples)}")

    # Write examples to files
    print("\nWriting examples to disk...")
    for example in examples:
        write_example_to_file(example, EXAMPLES_DIR)

    print("\n=== Phase 3: Generating llms.txt Index ===\n")

    llms_txt_path = PROCESSED_DOCS_DIR / "llms.txt"
    generate_llms_txt(concepts, examples, llms_txt_path)
    print(f"Generated: {llms_txt_path}")

    print("\n=== Knowledge Base Build Complete ===\n")
    print(f"Concepts: {len(concepts)}")
    print(f"Examples: {len(examples)}")
    print(f"Output: {PROCESSED_DOCS_DIR}")


# ============================================================================
# CLI
# ============================================================================


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build the GEOS knowledge base from source documentation."
    )
    parser.add_argument(
        "--geos-repo",
        type=Path,
        help="Path to GEOS repository (will copy docs to data/source/)",
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=SOURCE_DOCS_DIR,
        help="Source documentation directory (default: data/source/)",
    )

    args = parser.parse_args()

    build_knowledge_base(
        geos_repo=args.geos_repo,
        source_dir=args.source_dir,
    )


if __name__ == "__main__":
    main()
