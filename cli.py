#!/usr/bin/python3

"""Backup and restore machine configurations."""

import argparse
import glob
import inspect
import os
import shutil
from venv import EnvBuilder

import packagers

from utils import cmd
from utils import query_yes_no


HOME_DIR = os.path.expanduser('~')
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

# map package cli choice to classname
PACKAGE_OPTION_MAP = {
    x[0].lower(): x[0]
    for x in inspect.getmembers(packagers, inspect.isclass)
    if not x[0].startswith('Abstract')
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
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
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
        choices=PACKAGE_OPTION_MAP.keys(),
        type=str.lower,
        help='package management category')
    package_subparser.add_argument(
        'action',
        choices=[
            x
            for x in dir(packagers.AbstractPackager)
            if callable(getattr(packagers.AbstractPackager, x))
            and not x.startswith('_')
        ],
        type=str.lower,
        help='operation to perform')
    package_subparser.set_defaults(func=package)

    # sub-parser for python venv process
    venv_subparser = subparser.add_parser(
        'venv',
        help='manage user level python venv',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    venv_subparser.add_argument(
        '--loc',
        type=str,
        default=f'{HOME_DIR}/venv',
        help='where to create and access user virtual environment'
    )
    venv_subparser.add_argument(
        '--req',
        type=str,
        default=f'{HOME_DIR}/*requirements.txt',
        help='glob or filename used to match requirements files to install'
    )
    venv_subparser.set_defaults(func=venv)

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


def venv(args):
    """Manage user python venv."""
    venv_dir = args.loc
    req_glob = args.req

    # create venv if not exists or user wants to overwrite
    create = True
    if os.path.isdir(venv_dir):
        choice = query_yes_no(
            f'venv exists at {venv_dir}, remove it?', default='no')
        if choice:
            shutil.rmtree(venv_dir)
            debug(f'removed {venv_dir}')
        else:
            create = False
    if create:
        env_builder = EnvBuilder(clear=False, with_pip=True)
        env_builder.create(venv_dir)

    # venv binaries
    venv_pip = f'{venv_dir}/bin/pip3'

    # find requirements files(s)
    files = [req_glob] if os.path.isfile(req_glob) else glob.glob(req_glob)

    # install requirements
    for f in files:
        cmd(f'cat {f}')
        choice = query_yes_no(
            'install the above packages?',
            default='yes')
        if choice:
            cmd(f'{venv_pip} install -r {f}')

    # print next steps
    print(f"""
Add the following to your .bashrc

    PATH="{venv_dir}/bin:$PATH"

Then restart your shell!
    """)


def package(args):
    """Manage installed packages."""
    packager_classname = PACKAGE_OPTION_MAP[args.cmd]
    package_dir = os.path.join(args.box_conf, 'pkg')
    if not os.path.isdir(package_dir):
        os.makedirs(package_dir)
    packager = getattr(packagers, packager_classname)(package_dir)
    try:
        packager.verify()
        if args.action != 'verify':
            getattr(packager, args.action)()
    except NotImplementedError:
        fatal(f'Action "{args.action}" not available for "{args.cmd}"!')
    except Exception as e:
        debug(type(e))
        fatal(e)


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
        elif os.path.islink(target) and os.readlink(target) == source:
            warn('skipping already linked "%s"' % target)
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
