"""Cross platform command wrapper."""

import platform
import subprocess
import sys

# configuration for mapping commands cross env
commands = {
    'copy': {
        'linux': 'xclip -i',
        'darwin': 'pbcopy',
        'windows': 'clip'
    },
    'paste': {
        'linux': 'xclip -o',
        'darwin': 'pbpaste',
        'windows': 'paste'
    }
}
options = commands.keys()

# operating system type identifier
plat = platform.system().lower()

# read in command name
if len(sys.argv) == 1:
    exit('ARGV[1] command missing!')
command = sys.argv[1]

# verify command is supported
if command not in options:
    options_str = '|'.join(options)
    exit(f'command "{command}" not in supported commands "{options_str}"!')

# check if platform support command
if plat not in commands[command]:
    exit(f'platform "{plat}" not supported for command "{command}"')

# run the command
subprocess.run(commands[command][plat])
