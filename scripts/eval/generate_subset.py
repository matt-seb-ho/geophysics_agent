import shutil
from pathlib import Path

def main():
    # Helper list of experiments to include in the subset
    # These match the cleaned titles of the specific experiments requested
    subset_names = [
        "AdvancedExampleViscoDruckerPrager",
        "AdvancedWellboreExampleNonLinearThermalDiffusionTemperatureDependentVolumetricHeatCapacity",
        "ExampleEDPWellbore",
        "TutorialDeadOilEgg",
        "TutorialHydraulicFractureWithAdvancedXML"
    ]

    # Resolve paths
    base_dir = Path(__file__).resolve().parent.parent.parent
    data_dir = base_dir / 'data' / 'eval'
    experiments_dir = data_dir / 'experiments'
    subset_dir = data_dir / 'experiments_subset'

    if not experiments_dir.exists():
        print(f"Error: Source directory {experiments_dir} does not exist.")
        print("Please run generate_experiments.py first.")
        return

    # Re-create the subset directory
    if subset_dir.exists():
        print(f"Cleaning existing subset directory: {subset_dir}")
        shutil.rmtree(subset_dir)
    
    subset_dir.mkdir(parents=True, exist_ok=True)

    print(f"Creating subset in {subset_dir}...")
    
    success_count = 0
    for name in subset_names:
        src = experiments_dir / name
        dst = subset_dir / name
        
        if src.exists():
            shutil.copytree(src, dst)
            print(f"Copied: {name}")
            success_count += 1
        else:
            print(f"Warning: Experiment '{name}' not found in {experiments_dir}")

    print(f"Subset generation complete. {success_count}/{len(subset_names)} experiments copied.")

if __name__ == "__main__":
    main()
