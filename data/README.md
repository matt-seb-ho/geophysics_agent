# GEOS Agent Data Directory

This directory contains all data for the GEOS Agent system, organized into separate directories for different purposes.

## Directory Structure

```
data/
├── source/              # Raw GEOS documentation (RST files from GEOS repo)
├── processed/           # Cleaned, atomic RAG knowledge base (Markdown)
│   ├── llms.txt        # Master index for the agent
│   ├── concepts/       # Atomic concept definitions
│   └── examples/       # Examples with inlined XML code
├── vector_index/       # Vector embeddings (Chroma/FAISS)
├── inputs/             # Runtime: Generated XML simulation inputs
└── outputs/            # Runtime: GEOS simulation results
```

## Usage

### Building the Knowledge Base

**Prerequisites:**
- Python 3.11+
- GEOS repository cloned (see main README for instructions)

**Quick Start:**
```bash
# One-step build (recommended)
python scripts/build_knowledge.py --geos-repo ~/repos/GEOS
```

**What happens:**
1. **Copy Phase**: Documentation copied from GEOS repo → `data/source/`
   - `src/docs/sphinx/basicExamples/`
   - `src/docs/sphinx/advancedExamples/`
   - `src/coreComponents/*/docs/` (all component documentation)

2. **Processing Phase**: Raw RST files → Processed Markdown
   - **Concepts**: 115 RST files → 388 atomic concept chunks
   - **Examples**: 46 Example.rst files → 7 combined files with inlined XML

3. **Index Generation**: Creates `data/processed/llms.txt` master index

**Expected Output:**
```
=== Phase 1: Processing User Guide Concepts ===
Found 115 documentation files to process
Processing: src/coreComponents/constitutive/docs/BiotPorosity.rst
  → Generated 3 concept chunks
[...]
Total concepts: 388

=== Phase 2: Processing Examples with Inline XML ===
Processing: basicExamples/hydraulicFracturing/Example.rst
[...]
Total examples: 46

=== Phase 3: Generating llms.txt Index ===
Generated: data/processed/llms.txt

Knowledge Base Build Complete
Concepts: 388
Examples: 46
```

### Knowledge Base Contents (After Building)

**Concepts** (`processed/concepts/`):
- Atomic Markdown chunks split by H2/H3 headers
- Each chunk includes breadcrumb context (e.g., "User Guide > Solvers > Mechanics")
- Optimized for RAG retrieval

**Examples** (`processed/examples/`):
- Complete example documentation in single files
- Explanation + full XML code inlined
- No need to fetch external files during retrieval

**llms.txt** (`processed/llms.txt`):
- Master index listing high-value files
- Roadmap for agent navigation
- Follows llms.txt principles for machine readability

### Runtime Usage

When running simulations, the agent will:
- Generate XML files → `data/inputs/{run_id}.xml`
- Execute GEOS solver
- Store results → `data/outputs/{run_id}/`

## Git Tracking

Only directory structure (`.gitkeep` files) is tracked in git:
- `source/*` - Ignored (avoid bloating repo)
- `processed/*` - Ignored (regenerated from source)
- `vector_index/*` - Ignored (regenerated from processed)
- `inputs/*` - Ignored (runtime artifacts)
- `outputs/*` - Ignored (runtime artifacts)

## Next Steps

1. Clone the GEOS repository
2. Run `python scripts/build_knowledge.py --geos-repo /path/to/GEOS`
3. The knowledge base will be ready for RAG-based retrieval
