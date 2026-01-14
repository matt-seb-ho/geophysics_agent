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

The agent requires a processed local knowledge base to function. Run these three steps to set up the RAG pipeline:

1. **Clone the GEOS Repository**:
```bash
# Clone to a temporary location
git clone [https://github.com/GEOS-DEV/GEOS.git](https://github.com/GEOS-DEV/GEOS.git) ~/repos/GEOS
```


2. **Build the Knowledge Base**:
This parses raw docs into atomic concepts and examples with inlined XML.
```bash
python scripts/build_knowledge.py --geos-repo ~/repos/GEOS
```


3. **Initialize the Vector Store**:
This generates embeddings for the knowledge base and saves them locally.
```bash
python scripts/build_vector_index.py
```



## Usage

Run the agent with your natural language instruction:

```bash
uv run geos-agent "Create a simulation for multiphase flow in a porous medium"
```

## Project Structure

```
geophysics_agent/
├── src/geos_agent/     # Agent source code
├── scripts/
│   ├── mine_examples.py      # Parse GEOS examples
│   ├── build_knowledge.py    # Build atomic knowledge base
│   └── build_vector_index.py # Generate vector embeddings
├── data/
│   ├── source/               # Raw GEOS docs
│   ├── processed/            # Cleaned RAG knowledge base
│   ├── vector_index/         # Vector embeddings (ChromaDB)
│   ├── inputs/               # Generated XML simulation inputs
│   └── outputs/              # GEOS simulation results
└── pyproject.toml
```