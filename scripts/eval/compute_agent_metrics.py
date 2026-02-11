#!/usr/bin/env python3
"""
Compute agent execution metrics from JSONL logs.

Extracts metrics like:
1. Tool error counts (per-tool failure rates)
2. RAG retrieval accuracy (% of chunks from correct source document)

Usage:
    # Analyze a single log file
    uv run python scripts/eval/compute_agent_metrics.py \
        --log data/eval/logs/ExampleEDPWellbore.jsonl

    # With expected source path for RAG accuracy
    uv run python scripts/eval/compute_agent_metrics.py \
        --log data/eval/logs/ExampleEDPWellbore.jsonl \
        --source-path "src/docs/sphinx/advancedExamples/edpWellbore/Example.rst"

    # Batch analysis
    uv run python scripts/eval/compute_agent_metrics.py \
        --logs-dir data/eval/logs \
        --output data/eval/agent_metrics.json
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import defaultdict, Counter


class Colors:
    """Terminal colors for output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def parse_jsonl_log(log_path: Path) -> List[Dict[str, Any]]:
    """
    Parse a conversation log file into a list of event records.

    Supports two formats:
    1. JSON: Single object with {tool_calls, tool_responses, ...} (agent conversation log)
    2. JSONL: One JSON object per line (legacy event-based format)

    In JSON mode, tool_calls and tool_responses are paired and converted into
    event records compatible with the metrics computation functions.

    Args:
        log_path: Path to log file (JSON or JSONL)

    Returns:
        List of event dictionaries
    """
    raw = log_path.read_text(encoding='utf-8')

    # Try loading as a single JSON object first (conversation log format)
    try:
        data = json.loads(raw)
        if isinstance(data, dict) and "tool_calls" in data:
            return _convert_json_log_to_events(data)
    except json.JSONDecodeError:
        pass

    # Fall back to line-by-line JSONL
    events = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
            events.append(event)
        except json.JSONDecodeError as e:
            print(f"Warning: Failed to parse line in {log_path}: {e}")
            continue
    return events


def _convert_json_log_to_events(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convert a conversation log JSON object into event records.

    Pairs tool_calls with tool_responses by ID and determines success/failure
    by inspecting the response content.

    Args:
        data: Conversation log dict with tool_calls and tool_responses

    Returns:
        List of event dicts with keys: event, tool, args, result_preview, error
    """
    tool_calls = data.get("tool_calls", [])
    tool_responses = data.get("tool_responses", [])

    # Index responses by tool_call_id for fast lookup
    response_by_id = {}
    for tr in tool_responses:
        tc_id = tr.get("tool_call_id")
        if tc_id:
            response_by_id[tc_id] = tr.get("content", "")

    events = []
    for tc in tool_calls:
        tc_id = tc.get("id")
        tool_name = tc.get("tool_name", "unknown")
        args_raw = tc.get("arguments", "{}")

        # Parse arguments
        try:
            args = json.loads(args_raw) if isinstance(args_raw, str) else args_raw
        except json.JSONDecodeError:
            args = {"raw": args_raw}

        # Get paired response content
        content = response_by_id.get(tc_id, "")

        # Determine success or failure from response content
        is_error = False
        error_msg = ""
        try:
            parsed = json.loads(content) if isinstance(content, str) else content
            if isinstance(parsed, dict) and "error" in parsed:
                is_error = True
                error_msg = parsed["error"]
        except (json.JSONDecodeError, TypeError):
            # Non-JSON content; check for error prefixes
            if isinstance(content, str) and content.strip().lower().startswith("error"):
                is_error = True
                error_msg = content[:200]

        event = {
            "tool": tool_name,
            "args": args,
            "result_preview": content,
        }

        if is_error:
            event["event"] = "tool_run_error"
            event["error"] = error_msg
        else:
            event["event"] = "tool_run_ok"

        events.append(event)

    return events


def compute_tool_error_metrics(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute tool error statistics from log events.

    Args:
        events: List of log event dictionaries

    Returns:
        Dictionary with error metrics:
        {
            "total_tool_calls": int,
            "total_errors": int,
            "error_rate": float,
            "errors_by_tool": {tool_name: count},
            "success_by_tool": {tool_name: count},
            "error_messages": [{tool, error, args}],
            "tool_stats": {tool_name: {calls, errors, success, error_rate}}
        }
    """
    tool_calls = Counter()
    tool_errors = Counter()
    error_messages = []

    for event in events:
        event_type = event.get("event")
        tool_name = event.get("tool")

        if event_type == "tool_run_ok":
            tool_calls[tool_name] += 1

        elif event_type in ["tool_run_error", "tool_args_parse_error", "tool_unknown"]:
            tool_calls[tool_name] += 1
            tool_errors[tool_name] += 1

            # Extract error details
            error_detail = {
                "tool": tool_name,
                "event_type": event_type,
                "error": event.get("error", "Unknown error"),
                "args": event.get("args", {}),
            }

            # Add exception info if available
            if "exception" in event:
                error_detail["exception"] = event["exception"]

            error_messages.append(error_detail)

    # Compute per-tool statistics
    tool_stats = {}
    all_tools = set(tool_calls.keys()) | set(tool_errors.keys())

    for tool in all_tools:
        calls = tool_calls.get(tool, 0)
        errors = tool_errors.get(tool, 0)
        success = calls - errors

        tool_stats[tool] = {
            "calls": calls,
            "errors": errors,
            "success": success,
            "error_rate": errors / calls if calls > 0 else 0.0
        }

    total_calls = sum(tool_calls.values())
    total_errors = sum(tool_errors.values())

    return {
        "total_tool_calls": total_calls,
        "total_errors": total_errors,
        "error_rate": total_errors / total_calls if total_calls > 0 else 0.0,
        "errors_by_tool": dict(tool_errors),
        "success_by_tool": {tool: tool_calls[tool] - tool_errors.get(tool, 0)
                            for tool in tool_calls},
        "error_messages": error_messages,
        "tool_stats": tool_stats
    }


def extract_search_results(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract search results from tool execution events.

    Handles the actual search tool output format where results are under the
    "results" key (not "chunks"). Each result item contains fields like
    title, source/source_path, breadcrumbs, etc.

    Args:
        events: List of log event dictionaries

    Returns:
        List of search result dictionaries with metadata
    """
    search_results = []

    for event in events:
        event_type = event.get("event")
        tool_name = event.get("tool")

        # Only process successful search tool calls
        if event_type != "tool_run_ok":
            continue

        if tool_name not in ["search_navigator", "search_technical"]:
            continue

        # Parse the result to extract search results
        result_preview = event.get("result_preview", "")

        try:
            result_obj = json.loads(result_preview) if isinstance(result_preview, str) else result_preview

            if isinstance(result_obj, dict) and "results" in result_obj:
                results = result_obj["results"]

                search_results.append({
                    "tool": tool_name,
                    "query": result_obj.get("query", event.get("args", {}).get("query", "")),
                    "num_results": len(results),
                    "results": results,
                })

        except (json.JSONDecodeError, TypeError):
            continue

    return search_results


def compute_rag_retrieval_metrics(
    events: List[Dict[str, Any]],
    expected_source_path: str
) -> Dict[str, Any]:
    """
    Compute RAG retrieval accuracy metrics.

    Measures how often the agent retrieves results from the expected source document.

    Source path is extracted from result items using:
    - "source" key (SearchNavigatorTool format)
    - "source_path" key (SearchTechnicalTool format)

    Args:
        events: List of log event dictionaries
        expected_source_path: Expected RST source path (e.g., "src/docs/sphinx/.../Example.rst")

    Returns:
        Dictionary with retrieval metrics
    """
    search_results = extract_search_results(events)

    total_searches = len(search_results)
    total_results = 0
    relevant_results = 0
    searches_with_relevant = 0
    relevant_by_tool = Counter()
    total_by_tool = Counter()

    for search in search_results:
        tool = search["tool"]
        results = search["results"]
        num_results = len(results)

        total_results += num_results
        total_by_tool[tool] += num_results

        # Count relevant results (matching source_path)
        search_has_relevant = False

        for result in results:
            # Navigator uses "source", technical uses "source_path"
            source_path = result.get("source") or result.get("source_path", "")

            if source_path == expected_source_path:
                relevant_results += 1
                relevant_by_tool[tool] += 1
                search_has_relevant = True

        if search_has_relevant:
            searches_with_relevant += 1

    return {
        "expected_source_path": expected_source_path,
        "total_searches": total_searches,
        "total_chunks_retrieved": total_results,
        "relevant_chunks": relevant_results,
        "relevant_chunk_rate": relevant_results / total_results if total_results > 0 else 0.0,
        "searches_with_relevant": searches_with_relevant,
        "search_relevance_rate": searches_with_relevant / total_searches if total_searches > 0 else 0.0,
        "relevant_chunks_by_tool": dict(relevant_by_tool),
        "total_chunks_by_tool": dict(total_by_tool)
    }


def analyze_log(
    log_path: Path,
    expected_source_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze a single JSONL log file.

    Args:
        log_path: Path to JSONL log file
        expected_source_path: Optional expected RST source path for RAG accuracy

    Returns:
        Dictionary with all metrics
    """
    events = parse_jsonl_log(log_path)

    result = {
        "log_file": str(log_path),
        "total_events": len(events),
        "tool_errors": compute_tool_error_metrics(events)
    }

    if expected_source_path:
        result["rag_retrieval"] = compute_rag_retrieval_metrics(events, expected_source_path)

    return result


def print_metrics_report(metrics: Dict[str, Any], verbose: bool = True):
    """
    Print a formatted metrics report.

    Args:
        metrics: Metrics dictionary from analyze_log
        verbose: Whether to print detailed breakdown
    """
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}AGENT EXECUTION METRICS{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.ENDC}")

    print(f"\nLog file: {metrics['log_file']}")
    print(f"Total events: {metrics['total_events']}")

    # Tool error metrics
    tool_metrics = metrics["tool_errors"]

    print(f"\n{Colors.BOLD}TOOL EXECUTION SUMMARY{Colors.ENDC}")
    print(f"  Total tool calls: {tool_metrics['total_tool_calls']}")
    print(f"  Successful calls: {tool_metrics['total_tool_calls'] - tool_metrics['total_errors']}")
    print(f"  Failed calls:     {tool_metrics['total_errors']}")

    error_rate = tool_metrics['error_rate']
    if error_rate > 0.2:
        color = Colors.FAIL
    elif error_rate > 0.1:
        color = Colors.WARNING
    else:
        color = Colors.OKGREEN

    print(f"  Error rate:       {color}{error_rate:.1%}{Colors.ENDC}")

    # Per-tool breakdown
    if verbose and tool_metrics['tool_stats']:
        print(f"\n{Colors.BOLD}PER-TOOL STATISTICS{Colors.ENDC}")

        # Sort by number of calls
        sorted_tools = sorted(
            tool_metrics['tool_stats'].items(),
            key=lambda x: x[1]['calls'],
            reverse=True
        )

        for tool_name, stats in sorted_tools:
            calls = stats['calls']
            errors = stats['errors']
            success = stats['success']
            tool_error_rate = stats['error_rate']

            # Color code based on error rate
            if tool_error_rate > 0.5:
                status_color = Colors.FAIL
            elif tool_error_rate > 0.2:
                status_color = Colors.WARNING
            elif errors > 0:
                status_color = Colors.OKCYAN
            else:
                status_color = Colors.OKGREEN

            print(f"  {tool_name:25} {status_color}{success:3}/{calls:3} successful "
                  f"({tool_error_rate:5.1%} error rate){Colors.ENDC}")

    # Error messages
    if verbose and tool_metrics['error_messages']:
        print(f"\n{Colors.BOLD}ERROR DETAILS{Colors.ENDC}")

        # Show first 5 errors
        for i, error in enumerate(tool_metrics['error_messages'][:5], 1):
            print(f"\n  {Colors.FAIL}Error {i}: {error['tool']}{Colors.ENDC}")
            print(f"    Type: {error['event_type']}")
            print(f"    Message: {error['error']}")
            if verbose and 'args' in error and error['args']:
                print(f"    Args: {json.dumps(error['args'], indent=6)}")

        if len(tool_metrics['error_messages']) > 5:
            print(f"\n  ... and {len(tool_metrics['error_messages']) - 5} more errors")

    # RAG retrieval metrics
    if "rag_retrieval" in metrics:
        rag = metrics["rag_retrieval"]

        print(f"\n{Colors.BOLD}RAG RETRIEVAL ACCURACY{Colors.ENDC}")
        print(f"  Expected source: {rag['expected_source_path']}")
        print(f"  Total searches:  {rag['total_searches']}")
        print(f"  Total chunks:    {rag['total_chunks_retrieved']}")

        relevant_chunks = rag['relevant_chunks']
        relevant_rate = rag['relevant_chunk_rate']

        if relevant_rate > 0.5:
            color = Colors.OKGREEN
        elif relevant_rate > 0.2:
            color = Colors.OKCYAN
        else:
            color = Colors.WARNING

        print(f"  Relevant chunks: {color}{relevant_chunks} ({relevant_rate:.1%}){Colors.ENDC}")

        searches_with_relevant = rag['searches_with_relevant']
        search_relevance = rag['search_relevance_rate']

        if search_relevance > 0.7:
            color = Colors.OKGREEN
        elif search_relevance > 0.4:
            color = Colors.OKCYAN
        else:
            color = Colors.WARNING

        print(f"  Searches with relevant chunks: {color}{searches_with_relevant}/{rag['total_searches']} "
              f"({search_relevance:.1%}){Colors.ENDC}")

        if verbose and rag['relevant_chunks_by_tool']:
            print(f"\n  {Colors.BOLD}Relevant chunks by tool:{Colors.ENDC}")
            for tool, count in rag['relevant_chunks_by_tool'].items():
                total = rag['total_chunks_by_tool'].get(tool, 0)
                rate = count / total if total > 0 else 0.0
                print(f"    {tool:20} {count:3}/{total:3} ({rate:5.1%})")

    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.ENDC}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Compute agent execution metrics from JSONL logs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    # Input options
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--log",
        "-l",
        type=Path,
        help="Path to single JSONL log file"
    )
    group.add_argument(
        "--logs-dir",
        "-d",
        type=Path,
        help="Path to directory with JSONL logs (batch mode)"
    )

    # RAG accuracy option
    parser.add_argument(
        "--source-path",
        "-s",
        type=str,
        help="Expected RST source path for RAG retrieval accuracy"
    )

    # Output options
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Path to save metrics JSON (optional)"
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Minimal output (no detailed breakdown)"
    )

    args = parser.parse_args()

    # Single log mode
    if args.log:
        if not args.log.exists():
            print(f"{Colors.FAIL}Error: Log file not found: {args.log}{Colors.ENDC}")
            sys.exit(1)

        metrics = analyze_log(args.log, args.source_path)

        if not args.quiet:
            print_metrics_report(metrics, verbose=True)
        else:
            print(f"Error rate: {metrics['tool_errors']['error_rate']:.1%}")
            if "rag_retrieval" in metrics:
                print(f"RAG accuracy: {metrics['rag_retrieval']['relevant_chunk_rate']:.1%}")

        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with open(args.output, 'w') as f:
                json.dump(metrics, f, indent=2)
            print(f"Metrics saved to: {args.output}")

    # Batch mode
    elif args.logs_dir:
        if not args.logs_dir.exists():
            print(f"{Colors.FAIL}Error: Logs directory not found: {args.logs_dir}{Colors.ENDC}")
            sys.exit(1)

        log_files = sorted(args.logs_dir.glob("*.jsonl"))

        if not log_files:
            print(f"{Colors.WARNING}No JSONL files found in {args.logs_dir}{Colors.ENDC}")
            sys.exit(1)

        print(f"{Colors.BOLD}Analyzing {len(log_files)} log files...{Colors.ENDC}\n")

        all_metrics = []
        for log_file in log_files:
            print(f"{Colors.OKCYAN}Processing: {log_file.name}{Colors.ENDC}")

            metrics = analyze_log(log_file, args.source_path)
            all_metrics.append(metrics)

            if not args.quiet:
                error_rate = metrics['tool_errors']['error_rate']
                print(f"  Error rate: {error_rate:.1%}")

                if "rag_retrieval" in metrics:
                    rag_rate = metrics['rag_retrieval']['relevant_chunk_rate']
                    print(f"  RAG accuracy: {rag_rate:.1%}")

        # Aggregate statistics
        print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}AGGREGATE STATISTICS{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.ENDC}\n")

        total_calls = sum(m['tool_errors']['total_tool_calls'] for m in all_metrics)
        total_errors = sum(m['tool_errors']['total_errors'] for m in all_metrics)
        avg_error_rate = total_errors / total_calls if total_calls > 0 else 0.0

        print(f"Total tool calls: {total_calls}")
        print(f"Total errors: {total_errors}")
        print(f"Average error rate: {avg_error_rate:.1%}")

        if args.source_path:
            rag_metrics = [m['rag_retrieval'] for m in all_metrics if 'rag_retrieval' in m]
            if rag_metrics:
                total_chunks = sum(m['total_chunks_retrieved'] for m in rag_metrics)
                relevant_chunks = sum(m['relevant_chunks'] for m in rag_metrics)
                avg_rag_rate = relevant_chunks / total_chunks if total_chunks > 0 else 0.0

                print(f"\nRAG retrieval:")
                print(f"  Total chunks retrieved: {total_chunks}")
                print(f"  Relevant chunks: {relevant_chunks}")
                print(f"  Average relevance rate: {avg_rag_rate:.1%}")

        if args.output:
            output_data = {
                "total_logs": len(all_metrics),
                "aggregate": {
                    "total_tool_calls": total_calls,
                    "total_errors": total_errors,
                    "average_error_rate": avg_error_rate
                },
                "individual_metrics": all_metrics
            }

            if args.source_path and rag_metrics:
                output_data["aggregate"]["rag"] = {
                    "total_chunks": total_chunks,
                    "relevant_chunks": relevant_chunks,
                    "average_relevance_rate": avg_rag_rate
                }

            args.output.parent.mkdir(parents=True, exist_ok=True)
            with open(args.output, 'w') as f:
                json.dump(output_data, f, indent=2)

            print(f"\nMetrics saved to: {args.output}")

        print(f"{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.ENDC}\n")


if __name__ == "__main__":
    main()
