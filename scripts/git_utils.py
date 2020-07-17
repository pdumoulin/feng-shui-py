"""Advanced git operations wrapped in maintainable python."""

import argparse
import os
import re
import shlex
import subprocess
import webbrowser

ORIGIN_NAME = 'origin'
UPSTREAM_NAME = 'upstream'

def main():

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    parser_pr = subparsers.add_parser('pull-request')
    parser_pr.add_argument(
        '--branch', type=str, required=True,
        help='branch to merge into')
    parser_pr.set_defaults(func=pull_request)

    parser_browser = subparsers.add_parser('open-browser')
    parser_browser.add_argument(
        '--remote', type=str, required=True,
        choices=[UPSTREAM_NAME, ORIGIN_NAME],
        help='remote repo to open')
    parser_browser.add_argument(
        '--location', type=str, required=False, default='',
        help='file or dir to open in browser')
    parser_browser.set_defaults(func=open_browser)

    parser_sync = subparsers.add_parser('sync-upstream')
    parser_sync.add_argument(
        '--branch', type=str, required=True,
        help='branch to sync')
    parser_sync.add_argument(
        '--account', type=str, required=True,
        help='upstream github account to sync from')
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
            repo_name = get_repo_name()
        except subprocess.CalledProcessError as e:
            if 'not a git repository' not in e.stderr:
                raise e
            _exit('current dir is not git repo')
        args.func(args, repo_name)
        print('Finished!')
    else:
        parser.print_help()


def pull_request(args, repo_name):
    target_branch = args.branch
    branch_name = get_current_branch()
    remotes = get_remotes()
    remote_name = UPSTREAM_NAME if is_fork(remotes) else ORIGIN_NAME
    target_account = remotes[remote_name]['push']['account']
    origin_account = remotes[ORIGIN_NAME]['push']['account']
    url = f'https://github.com/{target_account}/{repo_name}/compare/{target_branch}...{origin_account}:{branch_name}?expand=1'  # noqa:E501
    webbrowser.open(url)


def open_browser(args, repo_name):
    current_branch = get_current_branch()
    working_dir = get_repo_working_dir()
    target_path = os.path.join(working_dir, args.location)
    remotes = get_remotes()
    try:
        target_account = remotes[args.remote]['push']['account']
    except KeyError:
        _exit(f'unable to find remote at {args.remote}')
    url = f'https://github.com/{target_account}/{repo_name}/tree/{current_branch}/{target_path}'  # noqa:E501
    webbrowser.open(url)


def sync_upstream(args, repo_name):
    upstream_location = f'git@github.com:{args.account}/{repo_name}.git'
    target_branch = args.branch
    remotes = get_remotes()
    if upstream_location == remotes[ORIGIN_NAME]['push']['url']:
        _exit(f'upstream identical to origin for {upstream_location}')
    if UPSTREAM_NAME not in remotes:
        _run(f'git remote add {UPSTREAM_NAME} {upstream_location}')
        remotes = get_remotes()
    start_branch = get_current_branch()
    try:
        _run(f'git fetch {UPSTREAM_NAME}')
    except subprocess.CalledProcessError as e:
        _run(f'git remote remove {UPSTREAM_NAME}')
        _exit(f'unable to fetch {UPSTREAM_NAME} at {upstream_location}')
    stashed = False
    if start_branch != target_branch:
        try:
            checkout_branch(target_branch)
        except subprocess.CalledProcessError as e:
            error = e.stderr.rstrip()
            if error.startswith('error: Your local changes to the following files would be overwritten by checkout'):  # noqa:E501
                if _query_yes_no('stash modified files and continue?'):
                    _run('git stash')
                    stashed = True
                    checkout_branch(target_branch)
            else:
                raise e
    _run(f'git merge {UPSTREAM_NAME}/{target_branch}')
    if start_branch != target_branch:
        checkout_branch(start_branch)
    if stashed:
        _run('git stash pop')


def force_push(args, repo_name):
    origin_url = get_remote_url(ORIGIN_NAME, 'push')
    branch_name = get_current_branch()
    if _query_yes_no(f'force push to {origin_url}?'):
        _run(f'git push {ORIGIN_NAME} -f {branch_name}')
    else:
        _exit('force push canceled')


def rebase(args, repo_name):
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
    try:
        _run(f'git rebase -i {target_branch}', None, None)
    except subprocess.CalledProcessError as e:
        if _query_yes_no('rebase failed! abort?', default='no'):
            _run('git rebase --abort')
            if stashed:
                _run('git stash pop')
        else:
            _run('git status')
            print('1. Resolve conflicts in "Unmerged paths" file list')
            print('2. $ git add <conflict-files>')
            print('3. $ git rebase --continue')
            print('Start over using $ git rebase --abort')
            if stashed:
                print('Warning: you have stashed changes!')
        _exit('rebase did not complete!')


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


def get_remote_url(remote_name, action):
    remotes = get_remotes()
    return remotes[remote_name][action]['url']


def is_fork(remotes):
    if UPSTREAM_NAME in remotes:
        return remotes[UPSTREAM_NAME]['push'] != remotes[ORIGIN_NAME]['push']
    return False


def get_remotes():
    remotes = {}
    result = _run('git remote -v')
    for line in result.stdout.rstrip().split('\n'):
        parts = re.split('\t| ', line)
        remote_name = parts[0]
        remote_url = parts[1]
        remote_action = parts[2].replace('(', '').replace(')', '')
        if remote_name not in remotes:
            remotes[remote_name] = {}
        if remote_action not in remotes[remote_name]:
            remotes[remote_name][remote_action] = ''
        remotes[remote_name][remote_action] = {
            'url': remote_url,
            'account': re.split(':|/', remote_url)[1]
        }
    return remotes


def get_repo_working_dir():
    result = _run('git rev-parse --show-prefix')
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
