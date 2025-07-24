import os
import subprocess
import time
import pygetwindow as gw
import pyautogui
import math
import configparser

# Load configurations from config.ini
config = configparser.ConfigParser()
config.read('config.ini')

# Paths from config.ini
HORNS_FOLDER = config['Paths']['HORNS_FOLDER']
ABEC_EXE_PATH = config['Paths']['ABEC_EXE_PATH']

# Window settings from config.ini
WINDOW_WIDTH = config.getint('WindowSettings', 'WINDOW_WIDTH')
WINDOW_HEIGHT = config.getint('WindowSettings', 'WINDOW_HEIGHT')
WINDOW_X = config.getint('WindowSettings', 'WINDOW_X')
WINDOW_Y = config.getint('WindowSettings', 'WINDOW_Y')

# Pixel check settings from config.ini
COLOR_THRESHOLD = config.getint('PixelCheck', 'COLOR_THRESHOLD')
REF_PIXEL_X = config.getint('PixelCheck', 'REF_PIXEL_X')
REF_PIXEL_Y = config.getint('PixelCheck', 'REF_PIXEL_Y')
REF_COLOR = tuple(map(int, config['PixelCheck']['REF_COLOR'].split(',')))
SOLVE_COLOR = tuple(map(int, config['PixelCheck']['SOLVE_COLOR'].split(',')))
PIXEL_X = config.getint('PixelCheck', 'PIXEL_X')
PIXEL_Y = config.getint('PixelCheck', 'PIXEL_Y')
SPECTRA_COLOR = tuple(map(int, config['PixelCheck']['SPECTRA_COLOR'].split(',')))

# Timeout settings from config.ini
TIMEOUT = config.getint('Timeout', 'TIMEOUT')
MAXSOLVE = config.getint('Timeout', 'MAXSOLVE')
REFTIME = config.getint('Timeout', 'REFTIME')

# Helper function to calculate the Euclidean distance between two colors (RGB)
def color_distance(c1, c2):
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))

# Close any stray windows by checking the start of the window title
def close_strays(partial_titleABAC, partial_titleVACS, timeout=1):
    print(f"Closing all windows starting with: {partial_titleABAC}")
    windows = gw.getAllTitles()
    for title in windows:
        if title.startswith(partial_titleABAC):
            wait_for_window_disappearance(partial_titleABAC, timeout=timeout)
    print(f"Closing all windows starting with: {partial_titleVACS}")
    windows = gw.getAllTitles()
    for title in windows:
        if title.startswith(partial_titleVACS):
            wait_for_window_disappearance(partial_titleVACS, timeout=timeout)

# Start the ABEC program with the file
def start_abec_with_file(program_path, file_path):
    command = f'"{program_path}" "{file_path}"'
    print(f"Starting: {command}")
    subprocess.Popen(command, shell=True)

# Wait until the window is available by checking the start of the window title
def wait_for_window(partial_title, timeout=10):
    print(f"Waiting for a window starting with: {partial_title}")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        windows = gw.getAllTitles()
        for title in windows:
            if title.startswith(partial_title):
                print(f"Window found: {title}")
                return gw.getWindowsWithTitle(title)[0]
        time.sleep(0.1)
    
    print(f"Timeout: No window starting with '{partial_title}' found")
    return None


def wait_for_window_disappearance(partial_title, timeout=10):
    print(f"Waiting for the window with title '{partial_title}' to close...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        windows = gw.getAllTitles()
        if not any(title.startswith(partial_title) for title in windows):
            print(f"Window with title '{partial_title}' has been closed.")
            return True
        time.sleep(0.1)

    # If timeout is reached and the window still exists
    print(f"Timeout: Window with title '{partial_title}' did not close within {timeout} seconds. Retrying to close it...")
    
    # Try to refocus and close the window with Alt+F4 and Enter
    try:
        # Get the window with the given title
        abec_window = gw.getWindowsWithTitle(partial_title)[0]
        
        # Focus the window
        abec_window.activate()
        time.sleep(1)  # Give a brief moment to refocus
        
        # Send Alt+F4 and Enter to close it
        pyautogui.hotkey('alt', 'f4')
        time.sleep(0.5)
        pyautogui.press('enter')
        
        # Wait briefly to check if the window closes
        time.sleep(5)
        
        # Re-check if the window has closed
        if not any(title.startswith(partial_title) for title in gw.getAllTitles()):
            print(f"Window with title '{partial_title}' has been closed successfully.")
            return True
        else:
            print(f"Failed to close the window with title '{partial_title}'.")
            return False
    
    except IndexError:
        print(f"No window with title '{partial_title}' was found to close.")
        return False


# Resize and move the window
def set_window_size_and_position(window):
    window.resizeTo(WINDOW_WIDTH, WINDOW_HEIGHT)
    window.moveTo(WINDOW_X, WINDOW_Y)
    print(f"Window resized to {WINDOW_WIDTH}x{WINDOW_HEIGHT} and moved to ({WINDOW_X}, {WINDOW_Y})")

# Start the solver by pressing F5 followed by Enter
def start_solver(abec_window):
    abec_window.activate()
    time.sleep(0.25)
    print("Starting solver with F5 and Enter...")
    pyautogui.press('f5')
    time.sleep(0.25)
    pyautogui.press('enter')

# Check the color of the reference pixel and apply the timeout to verify correct positioning
def wait_for_reference_pixel(abec_window, reftime=REFTIME):
    print(f"Waiting for the reference pixel at ({REF_PIXEL_X}, {REF_PIXEL_Y}) to match the expected color: {REF_COLOR}")
    start_time = time.time()
    
    while time.time() - start_time < reftime:        
        # Focus the window
        abec_window.activate()
        pyautogui.moveTo(REF_PIXEL_X, REF_PIXEL_Y)
        pixel_color = pyautogui.pixel(REF_PIXEL_X, REF_PIXEL_Y)
        distance = color_distance(pixel_color, REF_COLOR)
        print(f"Reference pixel color: {pixel_color}, distance from expected: {distance:.2f}")
        
        if distance <= COLOR_THRESHOLD:
            print("Reference pixel color is close enough to the expected value.")
            return True
        time.sleep(1)
    
    print(f"Timeout: Reference pixel color did not match the expected value within {reftime} seconds.")
    return False

# Monitor the calculation progress pixel and check if the ABEC window is still open
def monitor_calculation_progress(abec_window, x_pix, y_pix, color, timeout):
    print(f"Monitoring calculation progress at ({x_pix}, {y_pix}) for the expected color: {color}")

    try:
        start_time = time.time()
        while time.time() - start_time < timeout:
            # Check if the ABEC window still exists
            abec_window.activate()
            # Check the color of the calculation progress pixel
            pyautogui.moveTo(x_pix, y_pix)
            pixel_color = pyautogui.pixel(x_pix, y_pix)
            distance = color_distance(pixel_color, color)
            print(f"Calculation progress pixel color: {pixel_color}, distance from expected: {distance:.2f}")

            if distance <= COLOR_THRESHOLD:
                print("Calculation progress pixel color is close enough to the expected value.")
                return True
            time.sleep(max(timeout/100.0, TIMEOUT)) # check every 1% of max time or every TIMEOUT secs
    except Exception as e:
        print(e)
        return False

# Check that ref is correct, then start and monitor progress
def solver_with_retry(abec_window):
    if wait_for_reference_pixel(abec_window, REFTIME):
        start_solver(abec_window)
        return monitor_calculation_progress(abec_window, REF_PIXEL_X, REF_PIXEL_Y, SOLVE_COLOR, MAXSOLVE)
    else:
        print("Timeout reached a third time. Quitting ABEC.")
        abec_window.activate()
        pyautogui.hotkey('alt', 'f4')
        time.sleep(0.25)
        pyautogui.press('enter')
        wait_for_window_disappearance('ABEC3')  # Ensure ABEC is closed before continuing
        return False

# Calculate spectra after verifying progress pixel color
def calculate_spectra(abec_window):
    print("Pressing F7 to calculate spectra...")
    abec_window.activate()
    pyautogui.press('f7')

    # Wait for the progress pixel to indicate calculation progress
    if monitor_calculation_progress(abec_window, PIXEL_X, PIXEL_Y, SPECTRA_COLOR, TIMEOUT):
        print("Pressing Ctrl + F7 to finalize spectra...")
        abec_window.activate()
        pyautogui.hotkey('ctrl', 'f7')
        time.sleep(0.5)
        print("Pressing Enter to confirm the popup...")
        pyautogui.press('enter')
        time.sleep(1)
        print("Closing the program with Alt + F4...")
        pyautogui.hotkey('alt', 'f4')
        time.sleep(0.25)
        pyautogui.press('enter')
#        wait_for_window_disappearance('ABEC3')
        close_strays('ABEC3', 'VacsViewer')

# Iterate through folders and process each project
def process_abec_folders(base_directory, program_path):
    for folder in os.listdir(base_directory):
        folder_path = os.path.join(base_directory, folder)
        
        if not os.path.isdir(folder_path):
            continue
        
        project_file_path = os.path.join(folder_path, "ABEC_FreeStanding", "Project.abec")
        
        if os.path.exists(project_file_path):
            print(f"Closing any stray windows")
            close_strays('ABEC3', 'VacsViewer')
            print(f"Processing: {project_file_path}")
            start_abec_with_file(program_path, project_file_path)
    
            abec_window = wait_for_window('ABEC3')
    
            if abec_window:
                set_window_size_and_position(abec_window)
                time.sleep(1)
                # repeat just in case
                set_window_size_and_position(abec_window)
                time.sleep(1.5)

                # Retry mechanism for the reference pixel check
                if not solver_with_retry(abec_window):
                    print(f"Failed to complete process for {project_file_path}")
                else:
                    calculate_spectra(abec_window)
                    print(f"Process completed successfully for {project_file_path}")

            time.sleep(0.5)
        else:
            print(f"Project.abec file not found in {folder_path}")

#
# Redo logic
# close any open windows
# start process
# wait and check for window
# resize and move window (may need to do this a few times to nudge)
# start solving
# monitor until max solving timeout
# wait
# start spectra calc
# monitor until max spectra timeout
# wait
# (check for VACS window?)
# Save spectra
#

# Main
if __name__ == "__main__":
    process_abec_folders(HORNS_FOLDER, ABEC_EXE_PATH)
