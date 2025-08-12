import json
from pathlib import Path

from complete_control.neural.neural_models import PopulationSpikes


def load_and_display_population_data(filepath: Path):
    """
    Loads a PopulationSpikes JSON file and prints its contents.
    """
    if not filepath.exists():
        print(f"Error: File not found at {filepath}")
        print(
            "Please ensure you have a generated population result file (e.g., planner_p.json) in a 'data' directory."
        )
        print(
            "You can generate one by running a simulation that uses the updated data_handling.py."
        )
        return

    try:
        with open(filepath, "r") as f:
            data = json.load(f)

        pop_spikes = PopulationSpikes.model_validate(data)

        print(f"--- Population Data for: {pop_spikes.label} ---")
        print(f"Population Size: {pop_spikes.population_size}")
        print(f"Neuron Model: {pop_spikes.neuron_model}")
        print(f"Number of Spikes: {len(pop_spikes.senders)}")
        print(
            f"Sample GIDs (first 5): {pop_spikes.gids[:5] if pop_spikes.gids.size > 0 else 'N/A'}"
        )
        print(
            f"Sample Spike Senders (first 5): {pop_spikes.senders[:5] if pop_spikes.senders.size > 0 else 'N/A'}"
        )
        print(
            f"Sample Spike Times (first 5): {pop_spikes.times[:5] if pop_spikes.times.size > 0 else 'N/A'}"
        )

    except Exception as e:
        print(f"An error occurred while loading or parsing the file: {e}")


if __name__ == "__main__":
    sample_file_path = Path("../runs/20250703_163058/data/neural/planner_p.json")

    print(f"Attempting to load data from: {sample_file_path}")
    load_and_display_population_data(sample_file_path)
