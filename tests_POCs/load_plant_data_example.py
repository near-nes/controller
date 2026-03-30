from pathlib import Path

from complete_control.plant.plant_models import PlantPlotData


def load_and_display_plant_data(filepath: Path):
    """
    Loads a JointData JSON file and prints its contents.
    """
    if not filepath.exists():
        print(f"Error: File not found at {filepath}")
        print(
            "Please ensure you have a generated plant result file (e.g., joint_0.json) in a 'data' directory."
        )
        print(
            "You would typically generate this by running a simulation that records plant data."
        )
        return

    try:
        plant_data = PlantPlotData.load(filepath)
        joint_data = plant_data.joint_data[0]

        print(f"--- Plant Data for Joint ---")
        print(f"Position (rad) shape: {joint_data.pos_rad.shape}")
        print(f"Velocity (rad/s) shape: {joint_data.vel_rad_s.shape}")
        print(f"End-effector Position (m) shape: {joint_data.pos_ee_m.shape}")
        print(f"End-effector Velocity (m/s) shape: {joint_data.vel_ee_m_s.shape}")
        print(f"Spike Rate Positive (Hz) shape: {joint_data.spk_rate_pos_hz.shape}")
        print(f"Spike Rate Negative (Hz) shape: {joint_data.spk_rate_neg_hz.shape}")
        print(f"Spike Rate Net (Hz) shape: {joint_data.spk_rate_net_hz.shape}")
        print(f"Input Command Torque shape: {joint_data.input_cmd_torque.shape}")
        print(
            f"Input Command Total Torque shape: {joint_data.input_cmd_total_torque.shape}"
        )

        print("\nSample Data (first 5 elements):")
        print(f"Pos (rad): {joint_data.pos_rad[:5]}")
        print(f"Vel (rad/s): {joint_data.vel_rad_s[:5]}")

    except Exception as e:
        print(f"An error occurred while loading or parsing the file: {e}")


if __name__ == "__main__":
    # Placeholder path - you need to replace this with a real path from your runs directory
    sample_file_path = Path("../runs/20250703_163352/data/robotic/plant_data.json")

    print(f"Attempting to load data from: {sample_file_path}")
    load_and_display_plant_data(sample_file_path)
