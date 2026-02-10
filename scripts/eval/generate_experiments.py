import json
import re
from pathlib import Path

def clean_title(title):
    """
    Strips punctuation and spaces from the title.
    """
    # Remove all characters that are not alphanumeric
    return re.sub(r'[^a-zA-Z0-9]', '', title)

def main():
    # Resolve paths relative to this script
    # Script is in geophysics_agent/scripts/eval/
    # Data is in geophysics_agent/data/eval/
    base_dir = Path(__file__).resolve().parent.parent.parent
    data_dir = base_dir / 'data' / 'eval'
    input_jsonl = data_dir / 'example_pairs.jsonl'
    experiments_dir = data_dir / 'experiments'

    if not input_jsonl.exists():
        print(f"Error: {input_jsonl} does not exist.")
        return

    # Create experiments directory if it doesn't exist
    experiments_dir.mkdir(parents=True, exist_ok=True)

    print(f"Reading from {input_jsonl}...")
    print(f"Generating experiments in {experiments_dir}...")

    count = 0
    with open(input_jsonl, 'r') as f:
        for line in f:
            if not line.strip():
                continue
            
            try:
                data = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"Skipping invalid JSON line: {e}")
                continue

            title = data.get('title', '')
            folder_name = clean_title(title)

            if not folder_name:
                print(f"Skipping entry with empty cleaned title. Original: '{title}'")
                continue

            # Create experiment folder
            exp_path = experiments_dir / folder_name
            exp_path.mkdir(exist_ok=True)

            # Create subfolders
            (exp_path / 'inputs').mkdir(exist_ok=True)
            (exp_path / 'outputs').mkdir(exist_ok=True)

            # Create instructions file
            spec = data.get('natural_language_spec', '')
            with open(exp_path / 'instructions.txt', 'w') as out:
                out.write(spec)
            
            count += 1

    print(f"Successfully generated {count} experiment folders.")

if __name__ == "__main__":
    main()
