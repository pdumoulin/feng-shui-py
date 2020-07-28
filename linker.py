#!/usr/bin/python3

"""linker.

CLI script to create symlinks in home directory to files located within this
project.
"""

import argparse
import os


def main():
    """Entrypoint for script execution."""
    home_dir = os.path.expanduser('~')
    script_dir = os.path.dirname(os.path.realpath(__file__))
    default_conf_dir = os.path.join(script_dir, 'conf')

    # parse and return CLI arguments.
    parser = argparse.ArgumentParser()
    parser.add_argument('environment', type=str,
                        help='category of box')
    parser.add_argument('box', type=str,
                        help='box specific settings')
    parser.add_argument('--conf', required=False,
                        help='override default conf dir @ "%s"'
                        % default_conf_dir,
                        default=default_conf_dir)
    parser.add_argument('-g', action='store_true',
                        help='apply global settings')
    parser.add_argument('-f', action='store_true',
                        help='do not prompt on remove/move step')
    parser.add_argument('-b', action='store_true',
                        help='create backup if file already exists')
    parser.add_argument('-s', action='store_true',
                        help='create links for scripts')
    args = parser.parse_args()
    conf_dir = args.conf

    # build list of files to symlink from
    files = []

    # optionally add global files
    if args.g:
        global_dir = os.path.join(conf_dir, 'global')
        add_files(global_dir, files)

    # optionally add script files
    if args.s:
        script_dir = os.path.join(script_dir, 'scripts')
        add_files(script_dir, files)

    # add files specific to box in args
    box_dir = os.path.join(conf_dir, 'boxes', args.environment, args.box)
    add_files(box_dir, files)

    # remove files and create symlinks
    for file_tuple in files:
        print('')

        directory = file_tuple[0]
        filename = file_tuple[1]

        # symlink source and target
        source = os.path.join(directory, filename)
        target = os.path.join(home_dir, filename)

        # remove file(s) existing in home dir
        if os.path.isdir(target) and not os.path.islink(target):
            warn('skipping dir "%s"' % target)
            continue
        elif os.path.isfile(target) or os.path.islink(target):
            if args.f or prompt('remove file at "%s"?' % target):

                # backup if file is not symlink and option is on
                if args.b and not os.path.islink(target):
                    os.rename(target, '%s.bk' % target)
                    debug('moved "%s"' % target)
                else:
                    os.remove(target)
                    debug('removed "%s"' % target)

            else:
                warn('not linking "%s"' % target)
                continue
        else:
            debug('nothing at "%s"' % target)

        # create the symlink
        os.symlink(source, target)
        debug('created "%s" -> "%s"' % (source, target))

    print('')


def add_files(directory: str, files: list) -> None:
    """Build file list.

    Append tuples of (directory, filename) to file list.

    Args:
        directory (str): Directory path to add files from.
        files (list): File list to add files to.

    Returns:
        None: files list is modified

    """
    if not os.path.isdir(directory):
        fatal('"%s" is not a dir' % directory)
    ignore_extensions = ['.swp', '.swo', '.bk', '.txt']
    files += [
        (directory, x)
        for x in os.listdir(directory)
        if extension(x) not in ignore_extensions
    ]


def extension(file_path: str) -> str:
    """Extract file extension.

    Args:
        file_path (str): File location.

    Returns:
        str: File extension, including period.

    """
    _, extension = os.path.splitext(file_path)
    return extension


def prompt(message: str) -> bool:
    """Yes/No user prompt.

    Args:
        message (str): Text to present to user for choice.

    Returns:
        bool: Yes/No response from user.

    """
    yes_options = ['y', 'yes']
    no_options = ['n', 'no']
    message_prompt = '%s [y/n]: ' % message
    user_input = input(message_prompt).lower()
    if user_input in yes_options:
        return True
    if user_input in no_options:
        return False
    return prompt(message)


def debug(message):
    """Print debug level message."""
    print('DEBUG: %s' % message)


def warn(message):
    """Print warning level message."""
    print('WARNING: %s' % message)


def error(message):
    """Print error level message."""
    print('ERROR: %s' % message)


def fatal(message):
    """Print fatal level message and exit."""
    print('EXIT: %s' % message)
    exit()


if __name__ == '__main__':
    main()
