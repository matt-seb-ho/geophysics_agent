#!/bin/bash
# Script to run geos-agent on each experiment in the subset

set -e

# Get the script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
EXPERIMENTS_DIR="$PROJECT_ROOT/data/eval/experiments_subset"

# Change to project root to ensure uv can be found
cd "$PROJECT_ROOT"

# Iterate through each directory in experiments_subset
for experiment_dir in "$EXPERIMENTS_DIR"/*; do
    if [ -d "$experiment_dir" ]; then
        experiment_name=$(basename "$experiment_dir")
        instructions_file="$experiment_dir/instructions.txt"
        inputs_dir="$experiment_dir/inputs"
        outputs_dir="$experiment_dir/outputs"
        
        echo "========================================"
        echo "Running experiment: $experiment_name"
        echo "========================================"
        
        if [ ! -f "$instructions_file" ]; then
            echo "Error: instructions.txt not found in $experiment_dir"
            continue
        fi
        
        # Change to experiment directory
        cd "$experiment_dir"
        
        # Run geos-agent with the instructions from file (using cat to ensure proper reading)
        echo "Running: uv run geos-agent with instructions from instructions.txt"
        echo "Workspace: $experiment_dir"
        
        # Define eval preamble to prepend to instructions
        EVAL_PREAMBLE="You are being evaluated on your ability to author GEOS XML input files from a natural language specification. Use the documentation search tools (search_navigator, search_technical, search_schema) to learn GEOS XML syntax and patterns, then author the configuration files yourself. You can read files with read_file or grep_search and modify them with write_file or edit_file. If a tool blocks access to a file, move on and rely on documentation search instead.\n\n--- BEGIN SIMULATION SPECIFICATION ---\n\n"
        
        # Read the instructions logic
        raw_instructions=$(cat "$instructions_file")
        full_instructions=$(echo -e "${EVAL_PREAMBLE}${raw_instructions}")
        
        # Use command substitution with proper quoting
        uv run geos-agent --instruction "$full_instructions" --workspace "$experiment_dir" --log "$experiment_dir/log.json"
        
        echo "Completed: $experiment_name"
        echo ""
    fi
done

echo "All experiments completed!"
