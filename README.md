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

## Configuration

Default model: `z-ai/glm-4.7` (configurable via `--model` flag)

Browse available models at [OpenRouter Models](https://openrouter.ai/models)

## TO-DO
* Figure out how to organize GEOS docs for optimal tool calling
* Figure out effective parsing of user intent to search for applicable docs