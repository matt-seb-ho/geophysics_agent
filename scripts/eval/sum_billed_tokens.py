#!/usr/bin/env python3
"""
Print billed token usage for evaluation JSONL logs.

For each .jsonl file in the target directories:

    billed_input_tokens = usage.total_tokens - usage.completion_tokens - usage.cached_tokens
    billed_output_tokens = usage.completion_tokens

Usage:
    uv run python scripts/eval/sum_billed_tokens.py

    uv run python scripts/eval/sum_billed_tokens.py \
        --dir data/eval/experiments_run2_jsonllogs \
        --dir data/eval/experiments_run4_jsonllogs
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


DEFAULT_DIRS = [
    Path("data/eval/experiments_run2_jsonllogs"),
    Path("data/eval/experiments_run4_jsonllogs"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sum billed tokens across JSONL log directories."
    )
    parser.add_argument(
        "--dir",
        dest="dirs",
        action="append",
        type=Path,
        help="Directory containing .jsonl logs. Can be passed multiple times.",
    )
    return parser.parse_args()


def load_json_or_jsonl(path: Path) -> Any:
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        raise ValueError("file is empty")

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        records = []
        for line_number, line in enumerate(raw.splitlines(), start=1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"invalid JSON on line {line_number}: {exc.msg}"
                ) from exc
        if not records:
            raise ValueError("file contains no JSON records")
        return records


def extract_usage(payload: Any, path: Path) -> dict[str, int]:
    if isinstance(payload, dict):
        usage = payload.get("usage")
        if isinstance(usage, dict):
            total_tokens = usage.get("total_tokens")
            completion_tokens = usage.get("completion_tokens")
            cached_tokens = usage.get("cached_tokens", 0)
            if (
                isinstance(total_tokens, int)
                and isinstance(completion_tokens, int)
                and isinstance(cached_tokens, int)
            ):
                return {
                    "total_tokens": total_tokens,
                    "completion_tokens": completion_tokens,
                    "cached_tokens": cached_tokens,
                }
        raise ValueError(f"{path} does not contain a valid top-level usage block")

    if isinstance(payload, list):
        total_tokens = 0
        completion_tokens = 0
        cached_tokens = 0
        found_usage = False

        for record in payload:
            if not isinstance(record, dict):
                continue
            usage = record.get("usage")
            if not isinstance(usage, dict):
                continue
            record_total = usage.get("total_tokens")
            record_completion = usage.get("completion_tokens")
            record_cached = usage.get("cached_tokens", 0)
            if (
                isinstance(record_total, int)
                and isinstance(record_completion, int)
                and isinstance(record_cached, int)
            ):
                total_tokens += record_total
                completion_tokens += record_completion
                cached_tokens += record_cached
                found_usage = True

        if found_usage:
            return {
                "total_tokens": total_tokens,
                "completion_tokens": completion_tokens,
                "cached_tokens": cached_tokens,
            }

    raise ValueError(f"{path} does not contain any valid usage blocks")


def iter_jsonl_files(directory: Path) -> list[Path]:
    if not directory.exists():
        raise FileNotFoundError(f"directory does not exist: {directory}")
    if not directory.is_dir():
        raise NotADirectoryError(f"path is not a directory: {directory}")
    return sorted(directory.glob("*.jsonl"))


def format_int(value: int) -> str:
    return f"{value:,}"


def main() -> int:
    args = parse_args()
    directories = args.dirs or DEFAULT_DIRS

    grand_total_billed_input_tokens = 0
    grand_total_billed_output_tokens = 0

    for directory in directories:
        files = iter_jsonl_files(directory)
        directory_total_billed_input_tokens = 0
        directory_total_billed_output_tokens = 0

        print(directory)
        if not files:
            print("  (no .jsonl files found)")
            print()
            continue

        for path in files:
            payload = load_json_or_jsonl(path)
            usage = extract_usage(payload, path)
            billed_input_tokens = (
                usage["total_tokens"]
                - usage["completion_tokens"]
                - usage["cached_tokens"]
            )
            billed_output_tokens = usage["completion_tokens"]
            directory_total_billed_input_tokens += billed_input_tokens
            directory_total_billed_output_tokens += billed_output_tokens

            print(
                "  "
                f"{path.stem}: usage.total_tokens={format_int(usage['total_tokens'])} "
                f"- usage.completion_tokens={format_int(usage['completion_tokens'])} "
                f"- usage.cached_tokens={format_int(usage['cached_tokens'])} "
                f"= billed_input_tokens={format_int(billed_input_tokens)}; "
                f"billed_output_tokens={format_int(billed_output_tokens)}"
            )

        grand_total_billed_input_tokens += directory_total_billed_input_tokens
        grand_total_billed_output_tokens += directory_total_billed_output_tokens
        print(
            "  "
            f"directory_total_billed_input_tokens={format_int(directory_total_billed_input_tokens)}; "
            f"directory_total_billed_output_tokens={format_int(directory_total_billed_output_tokens)}"
        )
        print()

    print(
        f"total_billed_input_tokens={format_int(grand_total_billed_input_tokens)}"
    )
    print(
        f"total_billed_output_tokens={format_int(grand_total_billed_output_tokens)}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
