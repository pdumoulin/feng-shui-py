"""Advanced git operations wrapped in maintainable python."""

import argparse
import os
import shlex
import subprocess


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    parser_sync = subparsers.add_parser('sync-upstream')
    parser_sync.add_argument(
        '--branch', type=str, required=True,
        help='branch to sync')
    parser_sync.add_argument(
        '--location', type=str, required=True,
        help='upstream location to sync from')
    parser_sync.set_defaults(func=sync_upstream)

    parser_rebase = subparsers.add_parser('rebase')
    parser_rebase.add_argument(
        '--branch', type=str, required=True,
        help='branch to rebase on top of')
    parser_rebase.set_defaults(func=rebase)

    parser_force_push = subparsers.add_parser('force-push')
    parser_force_push.set_defaults(func=force_push)

    args = parser.parse_args()
    if 'func' in args:
        try:
            get_repo_name()
        except subprocess.CalledProcessError as e:
            if 'not a git repository' not in e.stderr:
                raise e
            _exit('current dir is not git repo')
            raise e
        args.func(args)
        print('Finished!')
    else:
        parser.print_help()


def sync_upstream(args):
    upstream_org = args.location
    target_branch = args.branch
    repo_name = get_repo_name()
    start_branch = get_current_branch()
    remote_name = 'upstream'
    try:
        _run(f'git remote add {remote_name} {upstream_org}/{repo_name}.git')
    except subprocess.CalledProcessError as e:
        error = e.stderr.rstrip()
        if error != 'fatal: remote upstream already exists.':
            raise e
    _run('git remote -v')
    _run(f'git fetch {remote_name}')
    checkout_branch(target_branch)
    _run(f'git merge {remote_name}/{target_branch}')
    checkout_branch(start_branch)


def force_push(args):
    origin_name = get_origin_name()
    branch_name = get_current_branch()
    if _query_yes_no(f'force push to {origin_name}?'):
        _run(f'git push origin -f {branch_name}')
    else:
        _exit('force push canceled')


def rebase(args):
    target_branch = args.branch
    if is_rebase_active():
        _exit('rebase is already in progress')
    stashed = False
    if is_dirty():
        if _query_yes_no('stash modified files and continue?'):
            _run('git stash')
            stashed = True
        else:
            _exit('working directory is dirty and changes not stashed')
    _run(f'git rebase -i {target_branch}', None, None)
    if is_rebase_active():
        _run('git rebase --abort')
        if stashed:
            _run('git stash pop')
        _exit('rebase did not complete')


def is_dirty():
    result = _run('git status -s --untracked-files=no')
    return bool(result.stdout)


def is_rebase_active():
    try:
        _run('git rebase --show-current-patch')
    except subprocess.CalledProcessError as e:
        error = e.stderr.rstrip()
        if error != 'fatal: No rebase in progress?':
            raise e
        return False
    return True


def checkout_branch(branch_name):
    _run(f'git checkout {branch_name}')


def get_origin_name():
    result = _run('git remote get-url origin')
    return result.stdout.rstrip()


def get_repo_name():
    result = _run('git rev-parse --show-toplevel')
    base_dir = result.stdout.rstrip()
    return os.path.split(base_dir)[-1]


def get_current_branch():
    result = _run('git rev-parse --abbrev-ref HEAD')
    return result.stdout.rstrip()


def _query_yes_no(question, default='yes'):
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


def _run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE):
    print(f'$ {command}')
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
        print(e.stderr)
        raise e
    print(result.stdout)
    return result


def _exit(message):
    exit(f'Exiting! {message}')


if __name__ == '__main__':
    main()
