from fabric.api import run, env

from braid import info


def install(package, python=None):
    if python is None:
        python = env.get('python', 'pypy')

    pip = 'pip'
    if python == 'pypy':
        pip = '~pypy/bin/pip'
    elif python == 'system':
        #FIXME https://github.com/twisted-infra/braid/issue/5
        if info.distroFamily() == 'fedora':
            pip = 'pip-python'
        else:
            pip = 'pip'
    run('{} install --user {}'.format(pip, package))
