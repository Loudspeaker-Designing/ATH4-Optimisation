import os
import numpy as np
import configparser

# Initialize configuration readers
config = configparser.ConfigParser()
params = configparser.ConfigParser()

# Load configurations from config.ini and params.ini
config.read('config.ini')
params.read('params.ini')

# Access paths from config.ini
CONFIGS_FOLDER = config['Paths']['CONFIGS_FOLDER']

SIMTYPE = config.getint('Simulation', 'SimType')

# Define parameter ranges using params.ini or default values if None
def get_range_or_default(param_name):
    range_value = params['Params'].get(param_name, "None").split('#')[0].strip()
    
    if range_value == "None":
        default_param_name = param_name.replace('_range', '')
        return [float(params['Defaults'][default_param_name])] if default_param_name in params['Defaults'] else []
    start, stop, steps = map(str.strip, range_value.split(','))
    return np.linspace(float(start), float(stop), int(steps))

# Retrieve parameter ranges or default values
a_values = get_range_or_default('a_range')
x_values = get_range_or_default('x_range')
c_values = get_range_or_default('c_range')

# Load the base config template from base_template.txt
with open('base_template.txt', 'r') as file:
    base_config_content = file.read()

# Function to generate config content with updated parameters
def generate_config_content(a, x, c, simtype=SIMTYPE):
    ang = a / (x + c)
    c1 = c
    p1x = x
    p2x = (x + c) * np.cos(ang) - c
    p2y = (x + c) * np.sin(ang)
    p3y = np.sqrt((x + c)**2 - c**2)
    return base_config_content.format(c1=c1, p1x=p1x, p2x=p2x, p2y=p2y, p3y=p3y, SimType=simtype)

# Main script to generate config files with different parameter combinations
def generate_configs(output_directory):
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    for c in c_values:
        for x in x_values:
            for a in a_values:
                config_content = generate_config_content(a, x, c, simtype=SIMTYPE)
                filename = f"c-{c:.1f}_x-{x:.1f}_a-{a:.1f}.cfg"
                filepath = os.path.join(output_directory, filename)
                if os.path.exists(filepath):
                    print(f'File exist, skipping: {filename}')
                    continue
                with open(filepath, 'w') as config_file:
                    config_file.write(config_content)
                print(f"Created: {filename}")

if __name__ == "__main__":
    generate_configs(CONFIGS_FOLDER)
