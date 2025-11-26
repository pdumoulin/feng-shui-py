#!/usr/bin/python3

import argparse
import inspect
import logging
import os
import shutil
import sys

import packagers
import utils

HOME_DIR = os.path.expanduser("~")
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

logging.basicConfig(
    level=logging.DEBUG,
    stream=sys.stdout,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# map package cli choice to classname
PACKAGE_OPTION_MAP = {
    x[0].lower(): x[0]
    for x in inspect.getmembers(packagers, inspect.isclass)
    if not x[0].startswith("Abstract")
}


def main() -> None:
    # set defaults based on env vars
    default_conf_varname = "FS_CONF"
    default_conf_dir = os.getenv(default_conf_varname, os.path.join(SCRIPT_DIR, "conf"))
    default_env_varname = "FS_ENV"
    default_env = os.getenv(default_env_varname)
    default_box_varname = "FS_BOX"
    default_box = os.getenv(default_box_varname)

    # top level parser for shared args
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--conf",
        default=default_conf_dir,
        help=f'override default conf dir: "{default_conf_dir}"',
    )
    parser.add_argument(
        "--env",
        type=str,
        default=default_env,
        help=f'override default env dir: "{default_env}"',
    )
    parser.add_argument(
        "--box",
        type=str,
        default=default_box,
        help=f'override default box dir: "{default_box}"',
    )

    subparser = parser.add_subparsers(dest="command")

    # sub-parser for symlinking process
    link_subparser = subparser.add_parser(
        "link", help="symlink files from conf storage dir to home dir"
    )
    link_subparser.add_argument("-g", action="store_true", help="apply global settings")
    link_subparser.add_argument(
        "-f", action="store_true", help="do not prompt on remove/move step"
    )
    link_subparser.add_argument(
        "-b", action="store_true", help="create backup if file already exists"
    )
    link_subparser.set_defaults(func=link)

    # sub-parser for init process
    init_subparser = subparser.add_parser(
        "init", help="initialize new conf storage dir"
    )
    init_subparser.add_argument(
        "--clone", nargs=2, help='two values, "env box" to clone files from'
    )
    init_subparser.set_defaults(func=init)

    # sub-parser for store process
    store_subparser = subparser.add_parser(
        "store", help="move file from home dir to conf storage dir"
    )
    store_subparser.add_argument(
        "target", type=str, help="file or dir to move and symlink, must be in home dir"
    )
    store_subparser.add_argument(
        "-f", action="store_true", help="do not prompt on overwrite"
    )
    store_subparser.add_argument(
        "-g", action="store_true", help="store in global conf dir"
    )
    store_subparser.set_defaults(func=store)

    # sub-parser for package process
    package_subparser = subparser.add_parser(
        "package", help="manage system installed packages"
    )
    package_subparser.add_argument(
        "cmd",
        choices=PACKAGE_OPTION_MAP.keys(),
        type=str.lower,
        help="package management category",
    )
    package_subparser.add_argument(
        "action",
        choices=[
            x
            for x in dir(packagers.AbstractPackager)
            if callable(getattr(packagers.AbstractPackager, x))
            and not x.startswith("_")
        ],
        type=str.lower,
        help="operation to perform",
    )
    package_subparser.set_defaults(func=package)

    # sub-parser for clean process
    clean_subparser = subparser.add_parser(
        "clean", help="remove broken symlinks in home dir"
    )
    clean_subparser.add_argument(
        "-f", action="store_true", help="do not prompt on remove"
    )
    clean_subparser.set_defaults(func=clean)

    # read in args
    args = parser.parse_args()

    # additional custom args validation
    if not args.env:
        print(
            f'env not set in --env or "${default_env_varname}", please set it now: ',
            end="",
        )
        args.env = input().lower()
        if not args.env:
            fatal("Invalid input!")
    if not args.box:
        print(
            f'box not set in --box or "${default_box_varname}", please set it now: ',
            end="",
        )
        args.box = input().lower()
        if not args.box:
            fatal("Invalid input!")

    # format args into dirs
    args.box_conf = box_dirname(args.conf, args.env, args.box)
    args.global_conf = os.path.join(args.conf, "global")

    # verify conf directory exists
    if not os.path.isdir(args.conf):
        fatal(f'"{args.conf}" does not exist!')
    if not os.path.isdir(args.box_conf) and args.command != "init":
        fatal(f'"{args.box_conf}" does not exist! Use "init" command to create it.')

    # run the actual process
    if "func" not in args:
        parser.print_help()
        exit(1)
    args.func(args)


def box_dirname(conf_dirname: str, env: str, box: str) -> str:
    if os.path.basename(box) != box:
        raise ValueError(f"box '{box}' is invalid")
    if os.path.basename(env) != env:
        raise ValueError(f"env '{env}' is invalid")
    return os.path.join(conf_dirname, "boxes", env, box)


def init(args: argparse.Namespace) -> None:
    box_target = args.box_conf
    global_target = args.global_conf

    # verify file isn't at targets
    if os.path.isfile(box_target):
        fatal("box conf at {box_target} is a file")
    if os.path.isfile(global_target):
        fatal("global conf at {global_target} is a file")

    # create global conf dir if not exists
    if not os.path.isdir(global_target):
        os.makedirs(global_target)
        logger.debug(f"created {global_target}")
    else:
        logger.debug(f"exists {global_target}")

    if args.clone:
        # copy existing dir into new one
        clone_source = box_dirname(args.conf, args.clone[0], args.clone[1])
        if not os.path.isdir(clone_source):
            fatal(f'"{clone_source}" does not exist!')
        if os.path.exists(box_target):
            fatal(f'Cannot clone into existing location at "{box_target}"!')
        shutil.copytree(clone_source, box_target)
        logger.debug(f"Cloned into {box_target}")
    else:
        # create box conf dir if not exists
        if not os.path.isdir(box_target):
            os.makedirs(box_target)
            logger.debug(f"created {box_target}")
        else:
            logger.debug(f"exists {box_target}")


def store(args: argparse.Namespace) -> None:
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
    destination = os.path.join(destination_dir, os.path.basename(target))
    if os.path.exists(destination):
        if not args.f and not utils.query_yes_no(f'overwrite at "{destination}"?'):
            exit(1)

    # move and symlink to homr dir
    shutil.move(target, destination)
    os.symlink(destination, os.path.join(HOME_DIR, os.path.basename(target)))


def package(args: argparse.Namespace) -> None:
    packager_classname = PACKAGE_OPTION_MAP[args.cmd]
    package_dir = os.path.join(args.box_conf, "pkg")
    if not os.path.isdir(package_dir):
        os.makedirs(package_dir)
    packager = getattr(packagers, packager_classname)(package_dir)
    try:
        packager.verify()
        if args.action != "verify":
            getattr(packager, args.action)()
    except NotImplementedError:
        fatal(f'Action "{args.action}" not available for "{args.cmd}"!')
    except packagers.exceptions.SudoException:
        print(f"""
Access denied, may need to try the following command as root...

sudo {os.path.abspath(sys.argv[0])} --env {args.env} --box {args.box} {args.command} {args.cmd} {args.action}
        """)  # noqa: E501
        exit(13)
    except Exception as e:
        logger.debug(str(type(e)))
        fatal(str(e))


def clean(args: argparse.Namespace) -> None:
    for item in os.listdir(HOME_DIR):
        full_path = os.path.join(HOME_DIR, item)
        if os.path.islink(full_path) and not os.path.exists(os.readlink(full_path)):
            if args.f or utils.query_yes_no(f'unlink at "{full_path}"?'):
                os.unlink(full_path)
                logger.debug(f"removed {full_path}")


def link(args: argparse.Namespace) -> None:
    # build list of files to symlink from
    files: list[tuple] = []

    # optionally add global files
    if args.g:
        add_files(args.global_conf, files)

    # add files specific to box in args
    add_files(args.box_conf, files)

    # remove files and create symlinks
    for file_tuple in files:
        print("")

        directory = file_tuple[0]
        filename = file_tuple[1]

        # symlink source and target
        source = os.path.join(directory, filename)
        target = os.path.join(HOME_DIR, filename)

        # remove file(s) existing in home dir
        if os.path.isdir(target) and not os.path.islink(target):
            logger.warn('skipping dir "%s"' % target)
            continue
        elif os.path.islink(target) and os.readlink(target) == source:
            logger.warn('skipping already linked "%s"' % target)
            continue
        elif os.path.isfile(target) or os.path.islink(target):
            if args.f or utils.query_yes_no('remove file at "%s"?' % target):
                # backup if file is not symlink and option is on
                if args.b and not os.path.islink(target):
                    os.rename(target, "%s.bk" % target)
                    logger.debug('moved "%s"' % target)
                else:
                    os.remove(target)
                    logger.debug('removed "%s"' % target)

            else:
                logger.warn('not linking "%s"' % target)
                continue
        else:
            logger.debug('nothing at "%s"' % target)

        # create the symlink
        os.symlink(source, target)
        logger.debug('created "%s" -> "%s"' % (source, target))

    print("")


def add_files(directory: str, files: list[tuple]) -> None:
    if not os.path.isdir(directory):
        fatal('"%s" is not a dir' % directory)
    ignore_extensions = [".swp", ".swo", ".bk"]
    files += [
        (directory, x)
        for x in os.listdir(directory)
        if extension(x) not in ignore_extensions
    ]


def extension(file_path: str) -> str:
    _, extension = os.path.splitext(file_path)
    return extension


def fatal(message: str, code: int = 1) -> None:
    logger.critical(message)
    exit(code)


if __name__ == "__main__":
    main()
