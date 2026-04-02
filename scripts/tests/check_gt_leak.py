import json
import re
from pathlib import Path

import sys

DEFAULT_RUN_DIR = Path("/Users/brianliu/Documents/research/geophysics_agent/data/eval/cursor_composer2/experiments_run1_4")
DEFAULT_GT_DIR = Path("/Users/brianliu/Documents/research/geophysics_agent/data/eval/experiments_gt")

def normalize_text(text):
    # Remove all whitespace to make matching resilient to formatting/indentation changes
    return re.sub(r'\s+', '', text)

def check_leaks(run_dir=DEFAULT_RUN_DIR, gt_dir=DEFAULT_GT_DIR):
    leaks_found = False
    
    tasks = sorted(d for d in run_dir.iterdir() if d.is_dir())
    for task_dir in tasks:
        metadata_file = task_dir / "eval_metadata.json"
        output_file = task_dir / "acpx_output.json"
        
        if not metadata_file.exists() or not output_file.exists():
            continue
            
        try:
            with open(metadata_file, "r") as f:
                metadata = json.load(f)
        except Exception:
            continue
            
        blocked_files = metadata.get("blocked_gt_xml_filenames", [])
        if not blocked_files:
            continue
            
        # Parse acpx_output.json and extract all tool call outputs
        tool_outputs = []
        try:
            with open(output_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        update = data.get("params", {}).get("update", {})
                        if update.get("sessionUpdate") == "tool_call_update" and update.get("status") == "completed":
                            raw_output = update.get("rawOutput", {})
                            if isinstance(raw_output, dict):
                                # Read File tool usually outputs "content"
                                if "content" in raw_output and isinstance(raw_output["content"], str):
                                    tool_outputs.append(raw_output["content"])
                                # Terminal tool usually outputs "stdout"
                                if "stdout" in raw_output and isinstance(raw_output["stdout"], str):
                                    tool_outputs.append(raw_output["stdout"])
                    except Exception:
                        continue
        except Exception as e:
            print(f"Error reading {output_file}: {e}")
            continue
            
        # Normalize tool outputs from this run
        tool_outputs_norm = []
        for out in tool_outputs:
            if out:
                tool_outputs_norm.append(normalize_text(out))
            
        for bf in blocked_files:
            gt_task_dir = gt_dir / task_dir.name
            if not gt_task_dir.exists():
                continue
                
            gt_paths = list(gt_task_dir.rglob("*.xml"))
            actual_gt_path = None
            for p in gt_paths:
                if p.name.lower() == bf.lower():
                    actual_gt_path = p
                    break
                    
            if not actual_gt_path:
                print(f"Warning: Could not find GT file {bf} in {gt_task_dir}")
                continue
                
            try:
                with open(actual_gt_path, "r") as f:
                    gt_content = f.read()
            except Exception as e:
                print(f"Error reading {actual_gt_path}: {e}")
                continue
            
            gt_norm = normalize_text(gt_content)
            
            if len(gt_norm) < 30:
                continue # Ignore extremely short target files to avoid false positives
                
            leak_detected = False
            for out_norm in tool_outputs_norm:
                # Check if the entire normalized GT content is present in the normalized tool output
                # This ensures we are exactly matching the full file content (ignoring whitespace),
                # rather than just checking a 100 character chunk.
                if gt_norm in out_norm:
                    leak_detected = True
                    break
                    
            if leak_detected:
                print(f"[!] LEAK DETECTED in API logs for task: {task_dir.name}")
                print(f"    Agent tool output exactly matches content from GT file: {actual_gt_path}")
                leaks_found = True

    if not leaks_found:
        print("No leaks of GT XML content found in any experiment logs.")
    return leaks_found

if __name__ == "__main__":
    if len(sys.argv) == 3:
        run_d = Path(sys.argv[1])
        gt_d = Path(sys.argv[2])
        sys.exit(1 if check_leaks(run_d, gt_d) else 0)
    else:
        sys.exit(1 if check_leaks() else 0)
