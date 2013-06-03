import functools
import inspect
import os
import pipes
import datetime

from fabric.api import run, cd, lcd, local, env, hide, abort

from braid import package, fails


def install():
    package.install(['git'])


def branch(branch, location):
    if fails('/usr/bin/test -d {}/.git'.format(location)):
        run('/usr/bin/git clone {} {}'.format(branch, location))
    else:
        # FIXME: We currently don't check that this the correct branch
        # https://github.com/twisted-infra/braid/issues/5
        with cd(location):
            run('/usr/bin/git fetch origin')
            run('/usr/bin/git reset --hard origin')


def track_calls():
    def decorator(func):
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            track = getattr(env, 'track_calls', False)
            if track:
                # Get the repository where the function is defined
                directory = os.path.dirname(inspect.getsourcefile(func))

                # Check that the repository is clean
                with hide('running'), lcd(directory):
                    repo = local('git rev-parse --show-toplevel', capture=True)

                    with lcd(repo):
                        changes = local('git status --porcelain', capture=True)

                if changes:
                    print (
                        '\nCalls to the task your are running are required to '
                        'be tracked, \nbut your repository is not clean. '
                        'Please commit the changes to\nthe files in the '
                        'following repository before deploying:\n'
                    )
                    print repo
                    for line in changes.splitlines():
                        print '  - ' + changes
                    abort('Dirty repository')
            result = func(*args, **kwargs)
            if track:
                tag_name = 'deploy-{:%Y-%m-%d-%H%M}'.format(datetime.datetime.now())
                tag_message = 'Deployed to {}.'.format(env.host)

                with lcd(repo):
                    local('git tag -a {} -m {}'.format(
                        pipes.quote(tag_name), pipes.quote(tag_message)))
            return result
        return wrapped
    return decorator
