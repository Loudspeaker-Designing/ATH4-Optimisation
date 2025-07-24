import os
import subprocess
import configparser
from pathlib import Path

# Load configurations from config.ini
config = configparser.ConfigParser()
config.read('config.ini')

# Access paths from config.ini
CONFIGS_FOLDER = config['Paths']['CONFIGS_FOLDER']
ATH_EXE_PATH = config['Paths']['ATH_EXE_PATH']
HORNS_FOLDER = config['Paths']['HORNS_FOLDER']


def run_ath_for_configs(config_dir, ath_exe_path, base_directory):
    # Get all .cfg files from the config directory
    config_files = [f for f in os.listdir(config_dir) if f.endswith('.cfg')]

    # Get list of any existing ABEC3 project directories
    existing_proj = [f for f in os.listdir(base_directory) if os.path.isdir(os.path.join(base_directory, f))]

    # Execute ath.exe for each config file
    for config_file in config_files:
        if(Path(config_file).stem in existing_proj):
            print(f'Project directory already exists, skipping: {Path(config_file).stem}')
            continue

        config_path = os.path.join(config_dir, config_file)

        command = [ath_exe_path, config_path]

        # Run the command and capture output
        print(f"Running: {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True)

        # Output success or error
        if result.returncode == 0:
            print(f"Success: {config_file}")
            print(result.stdout)
        else:
            print(f"Error running {config_file}: {result.stderr}")

# Main execution
if __name__ == "__main__":
    run_ath_for_configs(CONFIGS_FOLDER, ATH_EXE_PATH, HORNS_FOLDER)
