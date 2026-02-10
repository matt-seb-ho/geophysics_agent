# Geophysicist.ai

A minimal AI agent for GEOS/GEOSX geophysics workflows.

## Setup

1. **Install dependencies**:
```bash
uv sync
```

2. **Configure Environment**:
Set your OpenRouter API key in a `.env` file:
```
OPENROUTER_API_KEY=your_key_here
```



## Knowledge Base & Vector Store Setup

The agent uses a dual-collection RAG pipeline. Run these steps to set up the knowledge base:

1. **Clone the GEOS Repository**:
```bash
git clone https://github.com/GEOS-DEV/GEOS.git data/geos_source
```

2. **Parse RST Docs into Chunks**:
```bash
uv run python scripts/parse_rst_chunks.py --source-dir data/geos_source
```
This generates:
- `data/chunks/navigator/chunks.json` — prose chunks for conceptual navigation
- `data/chunks/technical/chunks.json` — XML shadow embeddings for code lookup
- `data/nav_graph.json` — documentation hierarchy

3. **Build the Vector Index**:
```bash
uv run python scripts/build_vector_index.py
```
This embeds the chunks and creates the ChromaDB collections (`geos_navigator`, `geos_technical`).


## Usage

Run the agent with your natural language instruction:

```bash
uv run geos-agent "Create a simulation for multiphase flow in a porous medium"
```

### Configuration Options

The agent supports various configuration options through the `AgentConfig` class:

```bash
# Example with custom retry settings
uv run geos-agent \
  --instruction "Your instruction" \
  --model "moonshotai/kimi-k2.5" \
  --max-steps 100 \
  --workspace . \
  --log logs/run.jsonl
```

**API Retry Configuration** (new in this version):

The agent now includes robust error handling with configurable retry logic for API failures:

- `max_retries` (default: 3) - Maximum number of retry attempts for API calls
- `retry_delay` (default: 1.0) - Initial delay between retries in seconds
- `retry_backoff` (default: 2.0) - Exponential backoff multiplier for retry delays
- `retry_on_timeout` (default: True) - Retry on timeout errors
- `retry_on_rate_limit` (default: True) - Retry on rate limit errors (HTTP 429)
- `retry_on_server_error` (default: True) - Retry on server errors (HTTP 5xx)

These settings help ensure the agent can recover from transient API failures without crashing. Configure them programmatically:

```python
from geos_agent.agent_config import AgentConfig

config = AgentConfig(
    model="moonshotai/kimi-k2.5",
    max_retries=5,
    retry_delay=2.0,
    retry_backoff=2.5
)
```

**GEOS Primer Context** (recommended):

By default, the agent loads `GEOS_PRIMER.md` into its context at startup (`include_primer=True`). This primer provides:
- High-level overview of GEOS capabilities and architecture
- XML structure, conventions, and common solver patterns
- Documentation roadmap for efficient RAG searches
- Quick reference for units, common pitfalls, and debugging tips

This helps the agent understand GEOS fundamentals before querying the RAG system, improving response accuracy. You can disable it if needed:

```python
config = AgentConfig(
    include_primer=False  # Disable primer to reduce context size
)
```

## Project Structure

```
geophysics_agent/
├── src/geos_agent/           # Agent source code
├── scripts/
│   ├── parse_rst_chunks.py   # Parse RST → JSON chunks
│   └── build_vector_index.py # Embed chunks → ChromaDB
├── data/
│   ├── geos_source/          # Cloned GEOS repository
│   ├── chunks/               # Parsed JSON chunks (navigator + technical)
│   ├── vector_db/            # ChromaDB vector database
│   ├── nav_graph.json        # Documentation hierarchy
│   ├── inputs/               # Generated XML simulation inputs
│   └── outputs/              # GEOS simulation results
└── pyproject.toml
```

## RAG Architecture

The agent uses a **dual-collection RAG system** optimized for technical documentation with large code examples.

### Navigator Collection (`geos_navigator`)

**Purpose**: High-level conceptual discovery — helps the agent understand *what topics exist* and navigate the documentation hierarchy.

**What's embedded**:
- **Document chunks**: Title + first paragraph (intro)
- **Section chunks**: Section header + first 2 sentences

**How it's used**:
1. Agent receives a broad query ("tell me about hydraulic fracturing")
2. Searches Navigator to find relevant documents/sections
3. Uses breadcrumbs and hierarchy to provide context
4. Can traverse `nav_graph.json` to find related topics

### Technical Collection (`geos_technical`)

**Purpose**: Code/syntax lookup — helps the agent find *how to implement* specific features.

**What's embedded** (shadow embeddings):
- Prose context (3 lines preceding the code reference in the docs)
- XML tag vocabulary (e.g., `"Uses XML tags: InternalMesh, Solver, Problem"`)
- Key attribute values (e.g., `"names: mesh1; types: SinglePhaseFlow"`)

**Why shadow embeddings?** Raw XML doesn't embed well semantically. By embedding the *description* of what the code does plus tag/attribute vocabulary, natural language queries like "how do I define a mesh?" can match technical chunks.

**Lazy code loading**: XML is not stored in the database. Each chunk stores:
- `xml_reference`: Path to the source XML file
- `line_range`: Markers or line numbers to extract

When the agent needs actual code, it calls `fetch_code` to extract the snippet on-demand.