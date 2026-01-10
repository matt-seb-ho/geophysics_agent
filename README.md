# Geophysicist.ai

A minimal AI agent for GEOS/GEOSX geophysics workflows.

## Setup

1. Install dependencies:
   ```bash
   uv sync
   ```

2. Set your OpenRouter API key in `.env`:
   ```
   OPENROUTER_API_KEY=your_key_here
   ```

3. Run the agent:
   ```bash
   uv run geos-agent "your instruction here"
   ```

## Project Structure

```
geophysics_agent/
├── src/geos_agent/     # Agent source code
├── scripts/
│   ├── mine_examples.py      # Parse GEOS examples from Sphinx docs
│   └── build_knowledge.py    # Build RAG knowledge base from GEOS docs
├── data/
│   ├── source/               # Raw GEOS docs (RST files from GEOS repo)
│   ├── processed/            # Cleaned atomic RAG knowledge base
│   │   ├── llms.txt          # Master index for the agent
│   │   ├── concepts/         # Atomic concept definitions (Markdown)
│   │   └── examples/         # Examples with inlined XML code
│   ├── vector_index/         # Vector embeddings (Chroma/FAISS)
│   ├── inputs/               # Generated XML simulation inputs
│   └── outputs/              # GEOS simulation results
└── pyproject.toml
```

The `data/` directory uses a structured pipeline to separate raw docs, processed knowledge, and runtime artifacts.

## Populating the Knowledge Base

The agent requires GEOS documentation to be processed into a RAG-optimized format. Follow these steps:

### Step 1: Clone the GEOS Repository

```bash
# Clone GEOS to a temporary location (or use an existing clone)
cd ~/repos  # or your preferred directory
git clone https://github.com/GEOS-DEV/GEOS.git
```

### Step 2: Build the Knowledge Base

Choose **one** of the following methods:

#### Method A: Direct Build (Recommended)
If you have a GEOS repo clone, use this one-step command:

```bash
python scripts/build_knowledge.py --geos-repo ~/repos/GEOS
```

This will:
1. Copy documentation from GEOS repo to `data/source/`
2. Process all documentation into the knowledge base
3. Generate 388 concept files in `data/processed/concepts/`
4. Generate 7 example files (46 examples) in `data/processed/examples/`
5. Create master index at `data/processed/llms.txt`

#### Method B: Two-Step Process
If you want to keep the source docs separate:

```bash
# Step 1: Copy GEOS docs to data/source/
cp -r ~/repos/GEOS/src/docs/sphinx/basicExamples data/source/
cp -r ~/repos/GEOS/src/docs/sphinx/advancedExamples data/source/
cp -r ~/repos/GEOS/src data/source/

# Step 2: Build from local source
python scripts/build_knowledge.py
```

### Step 3: Verify the Build

Run the verification script to check everything was built correctly:

```bash
python scripts/verify_knowledge_base.py
```

This will check:
- Directory structure is correct
- Expected number of files (388 concepts, 7 examples)
- XML is properly inlined in examples
- Master index exists

Alternatively, check manually:
```bash
# Should show ~388 concept files
find data/processed/concepts -name "*.md" | wc -l

# Should show 7 example files
find data/processed/examples -name "*.md" | wc -l

# Should exist and contain index
cat data/processed/llms.txt
```

### What Gets Created

```
data/
├── source/               # Raw GEOS RST files (166 files)
├── processed/
│   ├── concepts/         # 388 atomic concept chunks (theory)
│   ├── examples/         # 7 files containing 46 examples (with XML)
│   └── llms.txt          # Master index for RAG
├── inputs/               # (empty, for runtime XML generation)
└── outputs/              # (empty, for simulation results)
```

For more details, see [data/README.md](data/README.md).

## Configuration

Default model: `z-ai/glm-4.7` (configurable via `--model` flag)

Browse available models at [OpenRouter Models](https://openrouter.ai/models)