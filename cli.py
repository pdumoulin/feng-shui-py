#!/usr/bin/python3

"""Backup and restore machine configurations."""

import argparse
import os
import shlex
import shutil
import subprocess

HOME_DIR = os.path.expanduser('~')
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

PACKAGE_COMMAND_MAP = {
    'brew': {
        'cmds': {
            'list': 'brew bundle list --file {filepath}',
            'backup': 'brew bundle dump -f --file {filepath}',
            'restore': 'brew bundle install --no-upgrade --file {filepath}'
        },
        'filename': 'Brewfile'
    },
    'apt-clone': {
        'cmds': {
            'list': 'apt-clone info {filepath}',
            'backup': 'apt-clone clone {filepath}',
            'restore': 'sudo apt-clone restore {filepath}'
        },
        'filename': 'apt-clone.tar.gz'
    },
    'pip': {
        'cmds': {
            'list': 'cat {filepath}',
            'backup': 'pip freeze --no-python-version-warning',
            'restore': 'pip install -r {filepath}'
        },
        'filename': 'pip-freeze.txt'
    }
}


def main():
    """Entrypoint for script execution."""
    # set defaults based on env vars
    default_conf_varname = 'FS_CONF'
    default_conf_dir = os.getenv(
        default_conf_varname,
        os.path.join(SCRIPT_DIR, 'conf')
    )
    default_env_varname = 'FS_ENV'
    default_env = os.getenv(default_env_varname)
    default_box_varname = 'FS_BOX'
    default_box = os.getenv(default_box_varname)

    # top level parser for shared args
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--conf',
        default=default_conf_dir,
        help=f'override default conf dir: "{default_conf_dir}"')
    parser.add_argument(
        '--env',
        type=str,
        default=default_env,
        help=f'override default env dir: "{default_env}"')
    parser.add_argument(
        '--box',
        type=str,
        default=default_box,
        help=f'override default box dir: "{default_box}"')

    subparser = parser.add_subparsers(dest='command')

    # sub-parser for symlinking process
    link_subparser = subparser.add_parser(
        'link',
        help='symlink files from conf storage dir to home dir')
    link_subparser.add_argument(
        '-g',
        action='store_true',
        help='apply global settings')
    link_subparser.add_argument(
        '-f',
        action='store_true',
        help='do not prompt on remove/move step')
    link_subparser.add_argument(
        '-b',
        action='store_true',
        help='create backup if file already exists')
    link_subparser.set_defaults(func=link)

    # sub-parser for init process
    init_subparser = subparser.add_parser(
        'init',
        help='initialize new conf storage dir')
    init_subparser.add_argument(
        '--clone',
        nargs=2,
        help='two values, "env box" to clone files from')
    init_subparser.set_defaults(func=init)

    # sub-parser for store process
    store_subparser = subparser.add_parser(
        'store',
        help='move file from home dir to conf storage dir')
    store_subparser.add_argument(
        'target',
        type=str,
        help='file or dir to move and symlink, must be in home dir')
    store_subparser.add_argument(
        '-f',
        action='store_true',
        help='do not prompt on overwrite')
    store_subparser.add_argument(
        '-g',
        action='store_true',
        help='store in global conf dir')
    store_subparser.set_defaults(func=store)

    # sub-parser for package process
    package_subparser = subparser.add_parser(
        'package',
        help='manage system installed packages')
    package_subparser.add_argument(
        'cmd',
        choices=PACKAGE_COMMAND_MAP.keys(),
        help='package management category')
    package_subparser.add_argument(
        'action',
        choices=set(sum(
            [
                list(PACKAGE_COMMAND_MAP[k]['cmds'].keys())
                for k, v in PACKAGE_COMMAND_MAP.items()
            ],
            []
        )),
        help='operation to perform')
    package_subparser.set_defaults(func=package)

    # sub-parser for clean process
    clean_subparser = subparser.add_parser(
        'clean',
        help='remove broken symlinks in home dir')
    clean_subparser.add_argument(
        '-f',
        action='store_true',
        help='do not prompt on remove')
    clean_subparser.set_defaults(func=clean)

    # read in args
    args = parser.parse_args()

    # additional custom args validation
    if not args.env:
        print(f'env not set in --env or "${default_env_varname}", please set it now: ', end='')  # noqa:E501
        args.env = input().lower()
        if not args.env:
            fatal('Invalid input!')
    if not args.box:
        print(f'box not set in --box or "${default_box_varname}", please set it now: ', end='')  # noqa:E501
        args.box = input().lower()
        if not args.box:
            fatal('Invalid input!')

    # format args into dirs
    args.box_conf = os.path.join(args.conf, 'boxes', args.env, args.box)
    args.global_conf = os.path.join(args.conf, 'global')
    del args.env
    del args.box

    # verify conf directory exists
    if not os.path.isdir(args.conf):
        fatal(f'"{args.conf}" does not exist!')
    if not os.path.isdir(args.box_conf) and args.command != 'init':
        fatal(f'"{args.box_conf}" does not exist! Use "init" command to create it.')  # noqa:E501

    # run the actual process
    if 'func' not in args:
        parser.print_help()
        exit(1)
    args.func(args)


def init(args):
    """Create conf dir."""
    box_target = args.box_conf
    global_target = args.global_conf

    # verify file isn't at targets
    if os.path.isfile(box_target):
        fatal('box conf at {box_target} is a file')
    if os.path.isfile(global_target):
        fatal('global conf at {global_target} is a file')

    # create global conf dir if not exists
    if not os.path.isdir(global_target):
        os.makedirs(global_target)
        debug(f'created {global_target}')
    else:
        debug(f'exists {global_target}')

    if args.clone:
        # copy existing dir into new one
        clone_source = os.path.join(args.conf, 'boxes', args.clone[0], args.clone[1])  # noqa:E501
        if not os.path.isdir(clone_source):
            fatal(f'"{clone_source}" does not exist!')
        if os.path.exists(box_target):
            fatal(f'Cannot clone into existing location at "{box_target}"!')
        shutil.copytree(
            clone_source,
            box_target
        )
        debug(f'Cloned into {box_target}')
    else:
        # create box conf dir if not exists
        if not os.path.isdir(box_target):
            os.makedirs(box_target)
            debug(f'created {box_target}')
        else:
            debug(f'exists {box_target}')


def store(args):
    """Move file from home dir to conf dir and symlink."""
    target = os.path.normpath(args.target)

    # handle global dir flag
    destination_dir = args.box_conf
    if args.g:
        destination_dir = args.global_conf

    # validate source can be moved
    if not target.startswith(HOME_DIR):
        fatal(f'"{target}" must be in "{HOME_DIR}"!')
    if os.path.islink(target):
        fatal(f'"{target}" cannot be a symlink!')
    if not os.path.exists(target):
        fatal(f'"{target}" does not exist!')

    # check overwrite on destination
    destination = os.path.join(
        destination_dir,
        os.path.basename(target)
    )
    if os.path.exists(destination):
        if not args.f and not query_yes_no(f'overwrite at "{destination}"?'):  # noqa:E501
            exit(1)

    # move and symlink to homr dir
    shutil.move(
        target,
        destination
    )
    os.symlink(
        destination,
        os.path.join(
            HOME_DIR,
            os.path.basename(target)
        )
    )


def package(args):
    """Manage installed packages."""
    try:
        command = PACKAGE_COMMAND_MAP[args.cmd]['cmds'][args.action]
    except KeyError:
        fatal(f'"{args.action}" action not implemented for "{args.cmd}"')
    filename = PACKAGE_COMMAND_MAP[args.cmd]['filename']
    filepath = os.path.join(args.box_conf, filename)
    try:
        command_formatted = command.format(filepath=filepath)
        if command == command_formatted:
            f = open(filepath, 'w')
            cmd(command, stdout=f)
        else:
            cmd(command_formatted)
    except subprocess.CalledProcessError:
        pass


def clean(args):
    """Remove broken symlinks."""
    for item in os.listdir(HOME_DIR):
        full_path = os.path.join(HOME_DIR, item)
        if os.path.islink(full_path) and not os.path.exists(os.readlink(full_path)):  # noqa:E501
            if args.f or query_yes_no(f'unlink at "{full_path}"?'):
                os.unlink(full_path)
                debug(f'removed {full_path}')


def link(args):
    """Create symlinks in home dir from saved conf dir."""
    # build list of files to symlink from
    files = []

    # optionally add global files
    if args.g:
        add_files(args.global_conf, files)

    # add files specific to box in args
    add_files(args.box_conf, files)

    # remove files and create symlinks
    for file_tuple in files:
        print('')

        directory = file_tuple[0]
        filename = file_tuple[1]

        # symlink source and target
        source = os.path.join(directory, filename)
        target = os.path.join(HOME_DIR, filename)

        # remove file(s) existing in home dir
        if os.path.isdir(target) and not os.path.islink(target):
            warn('skipping dir "%s"' % target)
            continue
        elif os.path.isfile(target) or os.path.islink(target):
            if args.f or query_yes_no('remove file at "%s"?' % target):

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
    ignore_extensions = ['.swp', '.swo', '.bk']
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


def cmd(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        verbose=True
        ):
    """Run shell command.

    Args:
        command (str): command to run
        stdout (subprocess.PIPE): where to capture stdout
        stderr (subprocess.PIPE): where to capture stderr
        verbose (bool): print command input and output

    Returns:
        subprocess.CompletedProcess

    Raises:
        subprocess.CalledProcessError
    """
    def vprint(string):
        if verbose:
            print(string)
    vprint(f'$ {command}')
    command = shlex.split(command)
    try:
        result = subprocess.run(
            command,
            stdout=stdout,
            stderr=stderr,
            encoding='utf-8',
            check=True  # exception on non-zero code
        )
    except subprocess.CalledProcessError as e:
        vprint(e.stderr)
        raise e
    vprint(result.stdout)
    return result


def query_yes_no(question, default='yes'):
    """Query user for yes/no input.

    Args:
        question (str): prompt for user
        default (str): set option with if no user input

    Returns:
        bool: user selection
    """
    valid = {
        'yes': True,
        'y': True,
        'no': False,
        'n': False
    }
    if default is None:
        prompt = '[y/n]'
    elif default == 'yes':
        prompt = '[Y/n]'
    elif default == 'no':
        prompt = '[y/N]'
    else:
        raise ValueError(f'invalid default answer: "{default}"')

    while True:
        print(f'{question} {prompt}: ', end='')
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            print(f'invalid voice "{choice}" from {[x for x in valid.keys()]}')


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
