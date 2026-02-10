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
        
        # Use command substitution with proper quoting
        uv run geos-agent --instruction "$(cat "$instructions_file")" --workspace "$experiment_dir" --log "$experiment_dir/log.json"
        
        echo "Completed: $experiment_name"
        echo ""
    fi
done

echo "All experiments completed!"
