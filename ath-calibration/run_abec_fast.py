import os
import time
import configparser
from pywinauto.application import Application

# Load configurations from config.ini
config = configparser.ConfigParser()
config.read('config.ini')

# Paths from config.ini
HORNS_FOLDER = config['Paths']['HORNS_FOLDER']
ABEC_EXE_PATH = config['Paths']['ABEC_EXE_PATH']

# Simulation parameters from config.ini
SIMTYPE = config.getint('Simulation', 'SimType')
if SIMTYPE == 1:
    SIMTYPE = 'ABEC_InfiniteBaffle'
elif SIMTYPE == 2:
    SIMTYPE = 'ABEC_FreeStanding'
else:
    raise ValueError("Invalid SimType in config.ini. Must be 1 or 2.")

# Timeout settings from config.ini
TIMEOUT = config.getint('Timeout', 'TIMEOUT')
MAXSOLVE = config.getint('Timeout', 'MAXSOLVE')
MAXSPECTRA = config.getint('Timeout', 'MAXSPECTRA')


# Iterate through folders and process each project
def process_abec_folders(base_directory, program_path):
    for folder in os.listdir(base_directory):
        folder_path = os.path.join(base_directory, folder)
        
        if not os.path.isdir(folder_path):
            continue
        
        project_file_path = os.path.join(folder_path, SIMTYPE, "Project.abec")

        if os.path.exists(os.path.join(folder_path, SIMTYPE, 'Results', 'Spectrum_ABEC.txt')):
            print(f'Spectrum results already exist, skipping: {folder_path}')
            continue

        if os.path.exists(project_file_path):
            print(f"Processing: {project_file_path}")
            command = f'"{program_path}" "{project_file_path}"'
            print(f"Starting: {command}")
            # app = Application(backend='uia').start(command)
            app = Application().start(command)
            # app = Application().connect(title_re=r'ABEC3')
            window = None
            window = app.window(title_re = r'ABEC3')
            print(f'Got ABEC3 window')
            window.set_focus()
            print(f'Turn off VACS output')
            window.menu_select('Spectra -> Output ways VCAS -> Off')
            print("Starting solver")
            window.menu_select('Solving -> Start solving')
            confirm = app.window(title_re="Confirm")
            confirm.OKButton.click()
            print(f'Waiting for Solver...')
            time.sleep(TIMEOUT)
            try:
                app.wait_cpu_usage_lower(1, timeout=MAXSOLVE)
            except TimeoutError:
                print(f"Solver did not finish within {MAXSOLVE} seconds. Exiting...")
                continue
            except Exception as e:
                print(e)
            print("Calculating spectra...")
            window.menu_select('Spectra -> Start calculation')
            print(f'Waiting for Spectra...')
            time.sleep(TIMEOUT)
            try:
                app.wait_cpu_usage_lower(1, timeout=MAXSPECTRA)
            except TimeoutError:
                print(f"Spectrum did not finish within {MAXSPECTRA} seconds. Exiting...")
                continue
            except Exception as e:
                print(e)
            print("Saving spectra")
            window.menu_select('Spectra -> Export data as text')
            confirm = app.window(title_re="Information")
            confirm.OKButton.click()
            print("Closing program")
            window.menu_select('Project -> Exit')
            confirm = app.window(title_re="Confirmation")
            confirm['Close ABECButton'].click()
        else:
            print(f"Project.abec file not found in {folder_path}")

# Main
if __name__ == "__main__":
    process_abec_folders(HORNS_FOLDER, ABEC_EXE_PATH)
