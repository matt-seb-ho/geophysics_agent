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
├── data/
│   ├── inputs/         # User input files and generated XML input files go here
│   └── outputs/        # GEOS simulation results go here
└── pyproject.toml
```

The `data/` directory is gitignored and keeps simulation data separate from source code.

## Configuration

Default model: `z-ai/glm-4.7` (configurable via `--model` flag)

Browse available models at [OpenRouter Models](https://openrouter.ai/models)

## TO-DO
* Figure out how to organize GEOS docs for optimal tool calling
* Figure out effective parsing of user intent to search for applicable docs