# Agent Execution Metrics

This document explains the new agent execution metrics added to the evaluation pipeline.

## Overview

In addition to LLM-based XML evaluation, the system now tracks two additional metrics from JSONL logs:

1. **Tool Error Tracking** - Error rates and failure messages per tool
2. **RAG Retrieval Accuracy** - How often the agent retrieves relevant documentation

## 1. Tool Error Tracking

### What It Measures

- **Total tool calls and errors**: Overall execution statistics
- **Per-tool error rates**: Which tools fail most often
- **Error messages**: Detailed failure information with context

### Why It Matters

High error rates indicate:
- API/infrastructure issues (timeouts, rate limits)
- Tool implementation bugs
- Agent misusing tools (invalid arguments)

### Example Output

```
TOOL EXECUTION SUMMARY
  Total tool calls: 42
  Successful calls: 39
  Failed calls:     3
  Error rate:       7.1%

PER-TOOL STATISTICS
  search_technical          12/15 successful ( 20.0% error rate)
  search_navigator          10/10 successful (  0.0% error rate)
  write_file                 8/ 8 successful (  0.0% error rate)
  run_geos                   6/ 6 successful (  0.0% error rate)

ERROR DETAILS
  Error 1: search_technical
    Type: tool_run_error
    Message: ChromaDB query timeout
```

### Implementation

The script parses JSONL events:
- `tool_run_ok`: Successful tool execution
- `tool_run_error`: Tool raised an exception
- `tool_args_parse_error`: Invalid JSON arguments
- `tool_unknown`: Unknown tool name

## 2. RAG Retrieval Accuracy

### What It Measures

- **Relevant chunks retrieved**: Count of chunks from the expected source document
- **Total chunks retrieved**: All chunks returned by search tools
- **Relevance rate**: `relevant_chunks / total_chunks`
- **Search effectiveness**: % of searches that found at least one relevant chunk

### Why It Matters

Since your test cases are based on GEOS documentation examples, the agent should theoretically retrieve chunks from those same documentation pages. High relevance indicates:
- The RAG system is working correctly
- Embeddings capture semantic similarity well
- The agent is asking good questions

Low relevance may indicate:
- The agent is searching for the wrong things
- Embeddings don't capture the domain well
- The expected document isn't actually the most relevant

### How It Works

1. You provide the expected RST source path (e.g., `"src/docs/sphinx/advancedExamples/edpWellbore/Example.rst"`)
2. The script parses search tool results from JSONL logs
3. Each chunk has `metadata.source_path` (set during indexing)
4. Chunks where `source_path == expected_source_path` are counted as "relevant"

### Example Output

```
RAG RETRIEVAL ACCURACY
  Expected source: src/docs/sphinx/advancedExamples/edpWellbore/Example.rst
  Total searches:  25
  Total chunks:    125
  Relevant chunks: 78 (62.4%)
  Searches with relevant chunks: 20/25 (80.0%)

  Relevant chunks by tool:
    search_technical     45/ 75 ( 60.0%)
    search_navigator     33/ 50 ( 66.0%)
```

### Important Notes

- **This is a proxy metric**: Just because a chunk is from the expected document doesn't mean it's the BEST result. Other documents might also be relevant.
- **Use for relative comparison**: Compare across models/configurations rather than treating as an absolute measure
- **Consider context**: Low relevance might be okay if the agent is creatively solving the problem differently

## Usage Examples

### Standalone Analysis

```bash
# Analyze a single log
uv run python scripts/eval/compute_agent_metrics.py \
    --log data/eval/jsonl_logs/ExampleEDPWellbore.jsonl \
    --source-path "src/docs/sphinx/advancedExamples/edpWellbore/Example.rst"

# Batch analysis
uv run python scripts/eval/compute_agent_metrics.py \
    --logs-dir data/eval/jsonl_logs \
    --source-path "src/docs/sphinx/advancedExamples/edpWellbore/Example.rst" \
    --output metrics.json
```

### Integrated with Batch Evaluation

```bash
# Run experiments with JSONL logging
uv run python scripts/eval/run_experiments_parallel.py \
    --experiments-dir data/eval/experiments_subset \
    --jsonl-log-dir data/eval/jsonl_logs

# Evaluate with all metrics
uv run python scripts/eval/batch_evaluate.py \
    --experiments-dir data/eval/experiments_subset \
    --jsonl-log-dir data/eval/jsonl_logs \
    --source-path "src/docs/sphinx/advancedExamples/edpWellbore/Example.rst" \
    --output full_results.json
```

The batch evaluator will automatically include agent metrics in the summary report.

## Interpreting Results

### Good Signs
- **Error rate < 10%**: Most tool calls succeed
- **RAG relevance > 50%**: Agent is finding relevant docs
- **Search effectiveness > 70%**: Most searches find something useful

### Warning Signs
- **Error rate > 20%**: Infrastructure or implementation issues
- **RAG relevance < 30%**: Agent searching for wrong things or embeddings need improvement
- **Specific tools with high errors**: May indicate tool bugs or API issues

### What to Do

**High error rate:**
1. Check error messages for patterns (timeouts? invalid args?)
2. Increase retries/timeouts in agent configuration
3. Fix tool implementations if bugs found

**Low RAG relevance:**
1. Verify the `--source-path` is correct for the experiment
2. Check if agent is using different (but valid) approaches
3. Inspect actual search queries in JSONL logs
4. Consider if embeddings need retraining

## JSON Output Schema

```json
{
  "log_file": "path/to/log.jsonl",
  "total_events": 156,
  "tool_errors": {
    "total_tool_calls": 42,
    "total_errors": 3,
    "error_rate": 0.071,
    "errors_by_tool": {"search_technical": 3},
    "success_by_tool": {"search_technical": 12, ...},
    "tool_stats": {
      "search_technical": {
        "calls": 15,
        "errors": 3,
        "success": 12,
        "error_rate": 0.2
      },
      ...
    },
    "error_messages": [
      {
        "tool": "search_technical",
        "event_type": "tool_run_error",
        "error": "ChromaDB query timeout",
        "args": {...}
      }
    ]
  },
  "rag_retrieval": {
    "expected_source_path": "src/docs/sphinx/.../Example.rst",
    "total_searches": 25,
    "total_chunks_retrieved": 125,
    "relevant_chunks": 78,
    "relevant_chunk_rate": 0.624,
    "searches_with_relevant": 20,
    "search_relevance_rate": 0.8,
    "relevant_chunks_by_tool": {
      "search_technical": 45,
      "search_navigator": 33
    },
    "total_chunks_by_tool": {
      "search_technical": 75,
      "search_navigator": 50
    }
  }
}
```

## Future Enhancements

Potential additions:
- **Token usage tracking**: Monitor LLM API costs
- **Latency metrics**: Measure tool execution time
- **Search query analysis**: Cluster/analyze what the agent searches for
- **Success correlation**: Correlate RAG relevance with XML scores
