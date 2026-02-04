#!/usr/bin/env python3
"""
Hierarchical RST Parser for GEOS Documentation.

Extracts multi-level chunks for dual-collection RAG:
- Navigator Collection: Document/Section chunks from RST prose
- Technical Collection: Component/Example chunks with XML shadow embeddings

Usage:
    python scripts/parse_rst_chunks.py [--source-dir PATH]
"""

import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Literal, Optional, Set

import sys
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.geos_agent.constants import (
    GEOS_SOURCE_DIR,
    NAVIGATOR_CHUNKS_DIR,
    TECHNICAL_CHUNKS_DIR,
    NAV_GRAPH_PATH,
)


# ============================================================================
# Data Structures
# ============================================================================

@dataclass
class Chunk:
    """Represents a single chunk for embedding."""
    chunk_id: str
    chunk_type: Literal["document", "section", "component", "example"]
    embedding_text: str           # What we embed (enriched/shadow text)
    source_path: str              # Original RST file (absolute)
    parent_id: Optional[str]      # For hierarchy
    title: str
    breadcrumbs: str              # "Basic Examples > Hydraulic Fracturing"
    xml_reference: Optional[str]  # For lazy loading
    line_range: Optional[str]     # "start_marker,end_marker" or "L20-L40"


@dataclass
class NavNode:
    """Node in the navigation graph from toctree."""
    node_id: str
    title: str
    path: str
    children: List[str]  # List of child node IDs


# ============================================================================
# Toctree Parsing -> Navigation Graph
# ============================================================================

def parse_toctree(index_rst: Path) -> List[NavNode]:
    """
    Parse toctree directives from an index.rst file.
    Returns a list of NavNodes representing the navigation structure.
    """
    content = index_rst.read_text(encoding="utf-8")
    nodes = []
    
    # Extract title (first underlined header)
    title_match = re.search(r"^(.+)\n[=]+\s*$", content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else index_rst.parent.name
    
    parent_id = str(index_rst.relative_to(GEOS_SOURCE_DIR))
    
    # Find toctree entries
    toctree_pattern = re.compile(
        r"\.\.\s+toctree::\s*\n(?:\s+:\w+:.*\n)*\s*\n((?:\s+\S+\n?)+)",
        re.MULTILINE
    )
    
    children = []
    for match in toctree_pattern.finditer(content):
        entries = match.group(1).strip().split("\n")
        for entry in entries:
            entry = entry.strip()
            if entry and not entry.startswith(":"):
                child_path = (index_rst.parent / entry).with_suffix(".rst")
                if child_path.exists():
                    children.append(str(child_path.relative_to(GEOS_SOURCE_DIR)))
    
    nodes.append(NavNode(
        node_id=parent_id,
        title=title,
        path=str(index_rst),
        children=children
    ))
    
    return nodes


def build_navigation_graph(sphinx_dir: Path) -> dict:
    """
    Build complete navigation graph from all Index.rst files.
    """
    graph = {"nodes": {}, "root": None}
    
    for index_rst in sphinx_dir.rglob("Index.rst"):
        nodes = parse_toctree(index_rst)
        for node in nodes:
            graph["nodes"][node.node_id] = asdict(node)
        
        # First Index.rst found becomes root (or use main docs index)
        if graph["root"] is None or "sphinx/Index.rst" in str(index_rst):
            graph["root"] = nodes[0].node_id if nodes else None
    
    return graph


# ============================================================================
# RST Header Parsing
# ============================================================================

def extract_title_and_intro(content: str) -> tuple[str, str]:
    """Extract document title and introductory paragraph."""
    lines = content.split("\n")
    title = ""
    intro_lines = []
    
    # RST title patterns (text followed by underline of =, -, #)
    i = 0
    while i < len(lines):
        line = lines[i]
        # Check for underlined title
        if i + 1 < len(lines):
            next_line = lines[i + 1]
            if re.match(r"^[=#\-~^]+$", next_line) and len(next_line) >= len(line.strip()):
                if not title:  # First title is document title
                    title = line.strip().strip("#")
                    i += 2
                    continue
        i += 1
    
    # Get first paragraph after title
    in_paragraph = False
    for line in lines:
        stripped = line.strip()
        # Skip directives and headers
        if stripped.startswith("..") or re.match(r"^[=#\-~^]+$", stripped):
            if in_paragraph:
                break
            continue
        if stripped.startswith(":"):  # Directive option
            continue
        if stripped and not stripped.startswith(".."):
            in_paragraph = True
            intro_lines.append(stripped)
        elif in_paragraph and not stripped:
            break
    
    intro = " ".join(intro_lines[:3])  # First 3 lines max
    return title, intro


def extract_sections(content: str) -> List[tuple[str, str, int, int]]:
    """
    Extract sections delimited by headers.
    Returns list of (title, first_sentences, start_line, end_line).
    """
    sections = []
    lines = content.split("\n")
    
    current_section = None
    section_start = 0
    section_content = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check for section header (text followed by -, ~, or ^)
        if i + 1 < len(lines):
            next_line = lines[i + 1]
            if line.strip() and re.match(r"^[\-~^]+$", next_line) and len(next_line) >= len(line.strip()):
                # Save previous section
                if current_section:
                    content_text = " ".join(section_content)
                    # Get first 2 sentences
                    sentences = re.split(r"(?<=[.!?])\s+", content_text)[:2]
                    sections.append((
                        current_section,
                        " ".join(sentences),
                        section_start,
                        i - 1
                    ))
                
                current_section = line.strip()
                section_start = i
                section_content = []
                i += 2
                continue
        
        if current_section and line.strip() and not line.strip().startswith(".."):
            section_content.append(line.strip())
        
        i += 1
    
    # Don't forget last section
    if current_section:
        content_text = " ".join(section_content)
        sentences = re.split(r"(?<=[.!?])\s+", content_text)[:2]
        sections.append((current_section, " ".join(sentences), section_start, len(lines) - 1))
    
    return sections


# ============================================================================
# Literalinclude / Example Extraction
# ============================================================================

def extract_literalincludes(content: str, rst_path: Path) -> List[dict]:
    """
    Extract literalinclude directives and their context.
    Returns list of dicts with xml_path, context_text, markers.
    """
    examples = []
    lines = content.split("\n")
    
    pattern = re.compile(r"\.\.\s+literalinclude::\s*(.+)")
    
    for i, line in enumerate(lines):
        match = pattern.match(line.strip())
        if not match:
            continue
        
        file_ref = match.group(1).strip()
        
        # Get 3 preceding non-empty lines as context
        context_lines = []
        for j in range(i - 1, max(0, i - 10), -1):
            stripped = lines[j].strip()
            if stripped and not stripped.startswith("..") and not re.match(r"^[\-=~^]+$", stripped):
                context_lines.insert(0, stripped)
                if len(context_lines) >= 3:
                    break
        
        # Parse options (start-after, end-before)
        start_marker = None
        end_marker = None
        language = "xml"
        
        for j in range(i + 1, min(len(lines), i + 10)):
            opt_line = lines[j].strip()
            if not opt_line.startswith(":"):
                break
            if opt_line.startswith(":start-after:"):
                start_marker = opt_line.split(":", 2)[2].strip()
            elif opt_line.startswith(":end-before:"):
                end_marker = opt_line.split(":", 2)[2].strip()
            elif opt_line.startswith(":language:"):
                language = opt_line.split(":", 2)[2].strip()
        
        # Resolve file path
        resolved_path = (rst_path.parent / file_ref).resolve()
        if not resolved_path.exists():
            # Try from source root
            resolved_path = (GEOS_SOURCE_DIR / file_ref.lstrip("../")).resolve()
        
        examples.append({
            "file_path": str(resolved_path) if resolved_path.exists() else file_ref,
            "context_text": " ".join(context_lines),
            "start_marker": start_marker,
            "end_marker": end_marker,
            "language": language,
            "line_number": i + 1,
        })
    
    return examples


# ============================================================================
# XML Shadow Embedding Extraction
# ============================================================================

def extract_xml_shadow_tags(xml_path: Path) -> str:
    """
    Extract XML tag names for shadow embedding.
    Returns comma-separated list of unique tags found.
    """
    if not xml_path.exists():
        return ""
    
    try:
        content = xml_path.read_text(encoding="utf-8")
        # Simple regex extraction (handles malformed XML better than ET)
        tags: Set[str] = set()
        for match in re.finditer(r"<(\w+)[\s/>]", content):
            tag = match.group(1)
            if tag not in ["xml", "!--"]:
                tags.add(tag)
        return ", ".join(sorted(tags)[:20])  # Limit to top 20 tags
    except Exception:
        return ""


def extract_xml_key_attributes(xml_path: Path, start_marker: str = None, end_marker: str = None) -> str:
    """
    Extract key XML attributes and their values for shadow embedding.
    """
    if not xml_path.exists():
        return ""
    
    try:
        content = xml_path.read_text(encoding="utf-8")
        
        # If markers provided, extract only that section
        if start_marker and end_marker:
            start_idx = content.find(start_marker)
            end_idx = content.find(end_marker)
            if start_idx != -1 and end_idx != -1:
                content = content[start_idx:end_idx]
        
        # Extract name attributes (very common in GEOS XML)
        names = re.findall(r'name\s*=\s*["\']([^"\']+)["\']', content)
        types = re.findall(r'type\s*=\s*["\']([^"\']+)["\']', content)
        
        parts = []
        if names:
            parts.append(f"names: {', '.join(names[:5])}")
        if types:
            parts.append(f"types: {', '.join(types[:5])}")
        
        return "; ".join(parts)
    except Exception:
        return ""


# ============================================================================
# Main Chunk Generators
# ============================================================================

def generate_breadcrumbs(rst_path: Path) -> str:
    """Generate breadcrumb path from file location."""
    try:
        rel = rst_path.relative_to(GEOS_SOURCE_DIR / "src" / "docs" / "sphinx")
    except ValueError:
        rel = rst_path.relative_to(GEOS_SOURCE_DIR)
    
    parts = []
    for part in rel.parent.parts:
        # Clean up part names
        clean = part.replace("_", " ").replace("-", " ")
        if clean.lower() not in ["src", "docs", "sphinx"]:
            parts.append(clean.title())
    
    return " > ".join(parts) if parts else "Documentation"


def process_rst_for_navigator(rst_path: Path) -> List[Chunk]:
    """
    Process an RST file and generate Navigator collection chunks.
    Generates Document-level and Section-level chunks.
    """
    chunks = []
    content = rst_path.read_text(encoding="utf-8")
    breadcrumbs = generate_breadcrumbs(rst_path)
    
    # Create unique base ID from relative path
    try:
        rel_path = rst_path.relative_to(GEOS_SOURCE_DIR / "src" / "docs" / "sphinx")
    except ValueError:
        rel_path = rst_path.relative_to(GEOS_SOURCE_DIR)
    path_id = str(rel_path.with_suffix("")).replace("/", "_").replace(" ", "_")
    
    # 1. Document-level chunk
    title, intro = extract_title_and_intro(content)
    if not title:
        title = rst_path.stem
    
    doc_id = f"doc:{path_id}"
    chunks.append(Chunk(
        chunk_id=doc_id,
        chunk_type="document",
        embedding_text=f"{title}. {intro}",
        source_path=str(rst_path),
        parent_id=None,
        title=title,
        breadcrumbs=breadcrumbs,
        xml_reference=None,
        line_range=None,
    ))
    
    # 2. Section-level chunks
    sections = extract_sections(content)
    for section_title, first_sentences, start_line, end_line in sections:
        section_slug = section_title.lower().replace(' ', '_')[:30]
        section_id = f"sec:{path_id}:{section_slug}:L{start_line}"
        chunks.append(Chunk(
            chunk_id=section_id,
            chunk_type="section",
            embedding_text=f"{section_title}. {first_sentences}",
            source_path=str(rst_path),
            parent_id=doc_id,
            title=section_title,
            breadcrumbs=f"{breadcrumbs} > {title}",
            xml_reference=None,
            line_range=f"L{start_line}-L{end_line}",
        ))
    
    return chunks


def process_rst_for_technical(rst_path: Path) -> List[Chunk]:
    """
    Process an RST file and generate Technical collection chunks.
    Generates Example-level chunks with XML shadow embeddings.
    """
    chunks = []
    content = rst_path.read_text(encoding="utf-8")
    breadcrumbs = generate_breadcrumbs(rst_path)
    title, _ = extract_title_and_intro(content)
    
    # Create unique base ID from relative path
    try:
        rel_path = rst_path.relative_to(GEOS_SOURCE_DIR / "src" / "docs" / "sphinx")
    except ValueError:
        rel_path = rst_path.relative_to(GEOS_SOURCE_DIR)
    path_id = str(rel_path.with_suffix("")).replace("/", "_").replace(" ", "_")
    
    literalincludes = extract_literalincludes(content, rst_path)
    
    for i, lit in enumerate(literalincludes):
        xml_path = Path(lit["file_path"])
        
        # Generate shadow embedding with XML tags
        shadow_tags = extract_xml_shadow_tags(xml_path)
        key_attrs = extract_xml_key_attributes(
            xml_path, 
            lit.get("start_marker"), 
            lit.get("end_marker")
        )
        
        # Build embedding text: context + shadow tags
        embedding_parts = [lit["context_text"]]
        if shadow_tags:
            embedding_parts.append(f"Uses XML tags: {shadow_tags}")
        if key_attrs:
            embedding_parts.append(key_attrs)
        
        example_id = f"ex:{path_id}:{i}"
        chunks.append(Chunk(
            chunk_id=example_id,
            chunk_type="example",
            embedding_text=" ".join(embedding_parts),
            source_path=str(rst_path),
            parent_id=f"doc:{path_id}",
            title=f"{title} - Example {i+1}",
            breadcrumbs=breadcrumbs,
            xml_reference=str(xml_path) if xml_path.exists() else None,
            line_range=f"{lit.get('start_marker')},{lit.get('end_marker')}" if lit.get("start_marker") else None,
        ))
    
    return chunks


# ============================================================================
# Main Pipeline
# ============================================================================

def build_chunks(source_dir: Path = None):
    """Main pipeline to parse all RST files and generate chunks."""
    if source_dir is None:
        source_dir = GEOS_SOURCE_DIR
    
    sphinx_dir = source_dir / "src" / "docs" / "sphinx"
    if not sphinx_dir.exists():
        print(f"[error] Sphinx directory not found: {sphinx_dir}")
        return
    
    print("=== Phase 1: Building Navigation Graph ===\n")
    nav_graph = build_navigation_graph(sphinx_dir)
    NAV_GRAPH_PATH.write_text(json.dumps(nav_graph, indent=2))
    print(f"Navigation graph saved to: {NAV_GRAPH_PATH}")
    print(f"  Nodes: {len(nav_graph['nodes'])}")
    
    print("\n=== Phase 2: Processing RST Files for Navigator Collection ===\n")
    navigator_chunks = []
    
    for rst_file in sphinx_dir.rglob("*.rst"):
        if rst_file.name.lower() == "index.rst":
            continue  # Skip index files
        
        print(f"Processing: {rst_file.relative_to(sphinx_dir)}")
        chunks = process_rst_for_navigator(rst_file)
        navigator_chunks.extend(chunks)
    
    print(f"\nTotal Navigator chunks: {len(navigator_chunks)}")
    
    # Save navigator chunks
    nav_output = NAVIGATOR_CHUNKS_DIR / "chunks.json"
    with open(nav_output, "w") as f:
        json.dump([asdict(c) for c in navigator_chunks], f, indent=2)
    print(f"Saved to: {nav_output}")
    
    print("\n=== Phase 3: Processing RST Files for Technical Collection ===\n")
    technical_chunks = []
    
    # Focus on example files which have literalinclude
    for rst_file in sphinx_dir.rglob("Example.rst"):
        print(f"Processing: {rst_file.relative_to(sphinx_dir)}")
        chunks = process_rst_for_technical(rst_file)
        technical_chunks.extend(chunks)
    
    print(f"\nTotal Technical chunks: {len(technical_chunks)}")
    
    # Save technical chunks
    tech_output = TECHNICAL_CHUNKS_DIR / "chunks.json"
    with open(tech_output, "w") as f:
        json.dump([asdict(c) for c in technical_chunks], f, indent=2)
    print(f"Saved to: {tech_output}")
    
    print("\n=== Chunk Generation Complete ===")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Parse RST files into hierarchical chunks")
    parser.add_argument("--source-dir", type=Path, default=GEOS_SOURCE_DIR)
    args = parser.parse_args()
    
    build_chunks(args.source_dir)
