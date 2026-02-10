
import os
import shutil
import json
import re
from pathlib import Path

# Import constants to get GEOS_SOURCE_DIR
# We need to add the src directory to sys.path to import modules from there if running from root
import sys
sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))

from geos_agent.constants import GEOS_SOURCE_DIR, DATA_DIR

def clean_title(title):
    """
    Cleans the title to simple alphanumeric string.
    Removes punctuation and spaces.
    e.g. ".. _TutorialHydraulicFractureWithAdvancedXML:" -> "TutorialHydraulicFractureWithAdvancedXML"
    """
    # Remove all characters that are not alphanumeric
    return re.sub(r'[^a-zA-Z0-9]', '', title)

def resolve_path(base_dir, file_path):
    """
    Resolves the file path relative to the GEOS source directory.
    - Removes '../' prefixes.
    - If path starts with 'docs/', prepends 'src/'.
    """
    # Remove ../ prefixes
    clean_path = file_path
    while clean_path.startswith("../"):
        clean_path = clean_path[3:]
    
    # Check for docs/ prefix
    if clean_path.startswith("docs/"):
        clean_path = "src/" + clean_path
        
    return base_dir / clean_path

def main():
    experiments_dir = DATA_DIR / "eval" / "experiments"
    experiments_gt_dir = DATA_DIR / "eval" / "experiments_gt"
    jsonl_path = DATA_DIR / "eval" / "example_pairs.jsonl"
    
    print(f"GEOS Source Dir: {GEOS_SOURCE_DIR}")
    print(f"Experiments Dir: {experiments_dir}")
    print(f"Target GT Dir: {experiments_gt_dir}")

    if not experiments_dir.exists():
        print(f"Error: Experiments directory not found: {experiments_dir}")
        return

    # 1. Get list of experiment names from experiments folder
    # We assume the folder names in 'experiments' are the ground truth for which experiments to generate
    if not experiments_dir.exists():
         print("No experiments directory found.")
         return

    experiment_names = [d.name for d in experiments_dir.iterdir() if d.is_dir()]
    print(f"Found {len(experiment_names)} experiments in {experiments_dir}")

    # 2. Load example_pairs.jsonl
    experiments_data = {}
    with open(jsonl_path, 'r') as f:
        for line in f:
            if not line.strip():
                continue
            entry = json.loads(line)
            title = entry.get('title', '')
            cleaned_title = clean_title(title)
            experiments_data[cleaned_title] = entry

    # 3. Process each experiment
    for exp_name in experiment_names:
        if exp_name not in experiments_data:
            print(f"Warning: No matching data found for experiment '{exp_name}' in jsonl. Skipping.")
            continue
        
        print(f"Processing {exp_name}...")
        entry = experiments_data[exp_name]
        
        # Create directories
        exp_gt_path = experiments_gt_dir / exp_name
        inputs_dir = exp_gt_path / "inputs"
        outputs_dir = exp_gt_path / "outputs"
        
        # Clean and recreate if exists
        if exp_gt_path.exists():
            shutil.rmtree(exp_gt_path)
        
        inputs_dir.mkdir(parents=True, exist_ok=True)
        outputs_dir.mkdir(parents=True, exist_ok=True)
        
        # Process Inputs
        input_files = entry.get('input_files', [])
        # Deduplicate and clean paths
        unique_inputs = set()
        for p in input_files:
             # Remove ../ strictly for deduplication check logic if needed, 
             # but here we rely on the resolved path for uniqueness? 
             # The user prompt said: "there may be multilple paths of the same file with the difference that same go back (../../) but just strip them of the "../" and find all unique paths"
             
             # Let's normalize the string first for uniq check
             clean_p_str = p
             while clean_p_str.startswith("../"):
                 clean_p_str = clean_p_str[3:]
             unique_inputs.add(clean_p_str)

        # Helper to find file with fallback
        def find_source_file(rel_path, entry):
            # 1. Try standard resolution
            if rel_path.startswith("docs/"):
                final_rel_path = "src/" + rel_path
            else:
                final_rel_path = rel_path
            
            primary_path = GEOS_SOURCE_DIR / final_rel_path
            if primary_path.exists():
                return primary_path
            
            # 2. Try rst_path directory
            rst_path = entry.get('rst_path', '')
            if rst_path:
                # rst_path is like "src/docs/sphinx/..."
                # We want the directory containing the rst file
                rst_dir = GEOS_SOURCE_DIR / Path(rst_path).parent
                fallback_path = rst_dir / Path(rel_path).name
                if fallback_path.exists():
                    return fallback_path
            
            # 3. Try inputFiles/<directory> fallback
            # Extract distinct directories under inputFiles/ from strict input_files list
            potential_dirs = set()
            for p in entry.get('input_files', []):
                 clean_p = p
                 while clean_p.startswith("../"):
                     clean_p = clean_p[3:]
                 
                 parts = clean_p.split('/')
                 try:
                     idx = parts.index('inputFiles')
                     if idx + 1 < len(parts):
                         # Found inputFiles/<subdir>
                         potential_dirs.add(Path('inputFiles') / parts[idx+1])
                 except ValueError:
                     continue
            
            matches = []
            missing_filename = Path(rel_path).name
            for p_dir in potential_dirs:
                candidate = GEOS_SOURCE_DIR / p_dir / missing_filename
                if candidate.exists():
                    matches.append(candidate)
            
            if len(matches) == 1:
                return matches[0]
            elif len(matches) > 1:
                print(f"  Warning: multiple matches found for {missing_filename} in {potential_dirs}. Skipping.")
                return primary_path # Fail so original logic holds

            return primary_path # Return primary so we can log the missing path

        for cleaned_rel_path in unique_inputs:
            src_file = find_source_file(cleaned_rel_path, entry)
            dst_file = inputs_dir / Path(cleaned_rel_path).name
            
            if src_file.exists():
                try:
                    if src_file.is_dir():
                        # If destination exists, remove it first to ensure clean copy or use dirs_exist_ok=True
                        if dst_file.exists():
                            shutil.rmtree(dst_file)
                        shutil.copytree(src_file, dst_file)
                    else:
                        shutil.copy2(src_file, dst_file)
                    # print(f"  Copied input: {src_file.name}")
                except Exception as e:
                    print(f"  Error copying {src_file}: {e}")
            else:
                print(f"  Warning: Input file not found: {src_file} (and fallbacks failed)")

        # Process Outputs
        # User said: "for the output files, do the same thing but find all "exepcted_outputs" and copy and paste them."
        expected_outputs = entry.get('expected_outputs', [])
        unique_outputs = set()
        for p in expected_outputs:
             clean_p_str = p
             while clean_p_str.startswith("../"):
                 clean_p_str = clean_p_str[3:]
             unique_outputs.add(clean_p_str)
             
        for cleaned_rel_path in unique_outputs:
            src_file = find_source_file(cleaned_rel_path, entry)
            dst_file = outputs_dir / Path(cleaned_rel_path).name
             
            if src_file.exists():
                try:
                    if src_file.is_dir():
                        if dst_file.exists():
                            shutil.rmtree(dst_file)
                        shutil.copytree(src_file, dst_file)
                    else:
                        shutil.copy2(src_file, dst_file)
                    # print(f"  Copied output: {src_file.name}")
                except Exception as e:
                     print(f"  Error copying {src_file}: {e}")
            else:
                print(f"  Warning: Output file not found: {src_file} (and fallback failed)")

    print("Done generating ground truth experiments.")

if __name__ == "__main__":
    main()
