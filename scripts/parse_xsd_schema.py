#!/usr/bin/env python3
"""
Parse geosx_schema.xsd into per-element chunks for the geos_schema RAG collection.

One chunk is produced per xsd:complexType.  Each chunk captures:
  - The element name (e.g. "ViscoDruckerPrager")
  - Every attribute: name, XSD type, default value, required flag, and the
    inline documentation comment immediately preceding it in the XSD.

The inline docs follow the pattern:
    <!--attrName => Human-readable description of the attribute-->

Embedding text is rich natural language so that queries like
  "what parameters does ViscoDruckerPrager take?"
  "relaxation time constitutive model"
  "targetRegions solver attribute"
all hit the right element.

Output: data/chunks/schema/chunks.json

Usage:
    uv run python scripts/parse_xsd_schema.py
    uv run python scripts/parse_xsd_schema.py --xsd /path/to/geosx_schema.xsd
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

from lxml import etree

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.geos_agent.constants import SCHEMA_CHUNKS_DIR, SCHEMA_XSD_PATH

XSD_NS = "http://www.w3.org/2001/XMLSchema"


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class AttributeSpec:
    name: str
    xsd_type: str
    default: Optional[str]
    required: bool
    description: str   # from <!--name => desc--> comment


@dataclass
class SchemaChunk:
    chunk_id: str
    chunk_type: str        # always "schema"
    element_name: str      # e.g. "ViscoDruckerPrager"
    type_name: str         # e.g. "ViscoDruckerPragerType"
    attributes: list       # list of dicts (AttributeSpec.asdict())
    embedding_text: str    # rich text for vector embedding
    source_path: str       # "geosx_schema.xsd"
    title: str             # "{element_name} XML element"
    breadcrumbs: str       # "GEOS Schema"


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

_COMMENT_RE = re.compile(r"^\s*(\w+)\s*=>\s*(.+)$", re.DOTALL)


def _parse_comment(comment_text: str) -> tuple[str, str]:
    """
    Parse '<!-- attrName => description -->' comment text.
    Returns (attr_name, description) or ("", comment_text) if format is unexpected.
    """
    text = comment_text.strip()
    m = _COMMENT_RE.match(text)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return "", text


def _clean_type(xsd_type: str) -> str:
    """Return a human-readable type alias, stripping XSD namespace prefix if present."""
    # Strip xs: / xsd: prefix
    if ":" in xsd_type:
        xsd_type = xsd_type.split(":", 1)[1]
    return xsd_type


def parse_complex_type(ct_elem: etree._Element) -> SchemaChunk | None:
    """
    Parse a single xsd:complexType element into a SchemaChunk.
    Returns None if the type has no attributes (e.g. purely structural types).
    """
    type_name = ct_elem.get("name", "")
    if not type_name:
        return None

    # Derive element name: strip trailing "Type"
    element_name = type_name[:-4] if type_name.endswith("Type") else type_name

    attributes: list[AttributeSpec] = []
    pending_doc: tuple[str, str] | None = None  # (attr_name_hint, description)

    for child in ct_elem:
        tag = child.tag if isinstance(child.tag, str) else ""

        # Comment node (lxml represents them as callable tags)
        if callable(child.tag):
            # lxml comment: child.tag is the Comment function, child.text is the text
            doc_attr, doc_desc = _parse_comment(child.text or "")
            pending_doc = (doc_attr, doc_desc)
            continue

        local = tag.split("}")[-1] if "}" in tag else tag  # strip namespace

        if local == "attribute":
            attr_name = child.get("name", "")
            attr_type = _clean_type(child.get("type", "string"))
            attr_default = child.get("default")
            required = child.get("use", "") == "required"

            # Associate pending comment if the attr name matches (or accept any)
            description = ""
            if pending_doc is not None:
                hint, desc = pending_doc
                if not hint or hint == attr_name:
                    description = desc
            pending_doc = None

            attributes.append(AttributeSpec(
                name=attr_name,
                xsd_type=attr_type,
                default=attr_default,
                required=required,
                description=description,
            ))

        else:
            # Any other child (choice, sequence, etc.) resets pending comment
            pending_doc = None

    if not attributes:
        return None

    # Build embedding text
    lines = [f"{element_name}: GEOS XML element."]
    attr_parts = []
    for a in attributes:
        parts = [f"{a.name} ({a.xsd_type}"]
        if a.required:
            parts.append(", REQUIRED")
        elif a.default is not None:
            parts.append(f", default={a.default}")
        parts.append(")")
        if a.description:
            parts.append(f": {a.description}")
        attr_parts.append("".join(parts))
    lines.append("Attributes: " + ". ".join(attr_parts) + ".")
    embedding_text = " ".join(lines)

    return SchemaChunk(
        chunk_id=f"schema:{element_name}",
        chunk_type="schema",
        element_name=element_name,
        type_name=type_name,
        attributes=[asdict(a) for a in attributes],
        embedding_text=embedding_text,
        source_path="geosx_schema.xsd",
        title=f"{element_name} XML element",
        breadcrumbs="GEOS Schema",
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build_schema_chunks(xsd_path: Path) -> list[SchemaChunk]:
    """Parse all xsd:complexType elements in the XSD file."""
    tree = etree.parse(str(xsd_path))
    root = tree.getroot()

    chunks: list[SchemaChunk] = []
    for ct in root.iter(f"{{{XSD_NS}}}complexType"):
        chunk = parse_complex_type(ct)
        if chunk is not None:
            chunks.append(chunk)

    return chunks


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse GEOS XSD schema into RAG chunks")
    parser.add_argument(
        "--xsd", type=Path, default=SCHEMA_XSD_PATH,
        help=f"Path to geosx_schema.xsd (default: {SCHEMA_XSD_PATH})",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=SCHEMA_CHUNKS_DIR,
        help=f"Output directory for chunks.json (default: {SCHEMA_CHUNKS_DIR})",
    )
    args = parser.parse_args()

    if not args.xsd.exists():
        print(f"[error] XSD file not found: {args.xsd}")
        sys.exit(1)

    print(f"Parsing: {args.xsd}")
    chunks = build_schema_chunks(args.xsd)
    print(f"  Parsed {len(chunks)} element types")

    # Sample stats
    total_attrs = sum(len(c.attributes) for c in chunks)
    print(f"  Total attributes documented: {total_attrs}")
    with_docs = sum(
        sum(1 for a in c.attributes if a["description"])
        for c in chunks
    )
    print(f"  Attributes with descriptions: {with_docs} ({100*with_docs//total_attrs}%)")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    out_path = args.output_dir / "chunks.json"
    out_path.write_text(json.dumps([asdict(c) for c in chunks], indent=2))
    print(f"  Saved {len(chunks)} chunks → {out_path}")


if __name__ == "__main__":
    main()
