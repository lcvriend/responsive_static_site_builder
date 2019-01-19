"""
The config module
=================
This site_builder needs access to the following folders:
- The content folder
- The templates folder
- The output folder

These folder locations can be customized by changing their value in the `config.ini` file. However by default the site_builder expects these folders to reside in the main folder.

This module loads the stored paths from `config.ini` in order to make them accessible to the other modules and scripts. Upon initialization it will check if the content, templates and output paths exist. If not, it will set these paths to the default and create the folders if they do not yet exist.

Note that if the template folder is missing completely, then the .html and .css template files will also be missing. Without access to these files the site builder will fail sooner, rather than later.

    Objects in this module
    ----------------------
    - path_config_check (function)
    - PATH_CONFIG (constant)
"""

import configparser
from pathlib import Path


workdir = Path(__file__).resolve().parent.parent

config_file = './config.ini'
config = configparser.ConfigParser()
config.read(config_file)
config_paths = config['PATHS']

PATH_CONFIG = dict()  # Dictionary used by the other scripts and modules

for key in config_paths:
    if key == 'workdir':
        continue
    PATH_CONFIG[key] = Path(config_paths[key])

for key in PATH_CONFIG:
    if not PATH_CONFIG[key].exists():
        print(f'Path to {key} not found: {PATH_CONFIG[key]}')
        PATH_CONFIG[key] = workdir / key
        print(f'Set {key} path to {PATH_CONFIG[key]}')
        if not PATH_CONFIG[key].exists():
            PATH_CONFIG[key].mkdir(parents=True)

config['PATHS'] = {}
config['PATHS']['workdir'] = str(workdir)
config['PATHS']['templates'] = str(PATH_CONFIG['templates'])
config['PATHS']['content'] = str(PATH_CONFIG['content'])
config['PATHS']['output'] = str(PATH_CONFIG['output'])

with open(config_file, 'w') as f:
    config.write(f)
