#!/usr/bin/env python3
"""Script to create experiment folders from example_pairs.jsonl"""

import json
import re
import os
from pathlib import Path

def clean_title(title):
    """Strip spaces and punctuation from title to create folder name"""
    # Remove common reStructuredText markers
    cleaned = title.replace('.. _', '').replace(':', '')
    # Remove all non-alphanumeric characters (except hyphens)
    cleaned = re.sub(r'[^a-zA-Z0-9-]', '', cleaned)
    return cleaned

def main():
    # Paths
    jsonl_file = Path('/home/brianliu/geophysics_agent/data/eval/example_pairs.jsonl')
    experiments_dir = Path('/home/brianliu/geophysics_agent/data/eval/experiments')
    
    # Create experiments directory if it doesn't exist
    experiments_dir.mkdir(parents=True, exist_ok=True)
    
    # Read JSONL file and process each row
    with open(jsonl_file, 'r') as f:
        for line_num, line in enumerate(f, 1):
            try:
                data = json.loads(line.strip())
                
                # Get title and natural_language_spec
                title = data.get('title', '')
                natural_language_spec = data.get('natural_language_spec', '')
                
                if not title:
                    print(f"Warning: Line {line_num} has no title, skipping")
                    continue
                
                # Create folder name
                folder_name = clean_title(title)
                if not folder_name:
                    print(f"Warning: Line {line_num} resulted in empty folder name, skipping")
                    continue
                
                # Create experiment folder
                experiment_folder = experiments_dir / folder_name
                experiment_folder.mkdir(exist_ok=True)
                
                # Create inputs and outputs subdirectories
                (experiment_folder / 'inputs').mkdir(exist_ok=True)
                (experiment_folder / 'outputs').mkdir(exist_ok=True)
                
                # Create instructions.txt with natural_language_spec
                instructions_file = experiment_folder / 'instructions.txt'
                with open(instructions_file, 'w') as inst_f:
                    inst_f.write(natural_language_spec)
                
                print(f"Created: {experiment_folder}")
                
            except json.JSONDecodeError as e:
                print(f"Error parsing line {line_num}: {e}")
            except Exception as e:
                print(f"Error processing line {line_num}: {e}")
    
    print("\nDone!")

if __name__ == '__main__':
    main()
