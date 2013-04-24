from __future__ import print_function
from fabric.api import task, run, hide, sudo, cd


SERVICE_USER_MIN_UID = 500
SERVICE_USER_MAX_UID = 999

REAL_USER_MIN_UID = 1000
REAL_USER_MAX_UID = 65533


def getUsers():
    users = []

    with hide('everything'):
        db = run('cat /etc/passwd')

    for line in db.splitlines():
        user, _, uid, _, _, _, _ = line.split(':')
        users.append((int(uid), user))
    users.sort()
    return users


@task
def listServices():
    """
    List all service specific users.

    This currently ignores all users created by installed packages, such as
    postgres or www-data.
    """
    print()
    for uid, user in getUsers():
        if SERVICE_USER_MIN_UID <= uid <= SERVICE_USER_MAX_UID:
            print(' * {:10s} {}'.format(user, uid))


@task
def listReal():
    """
    List all real users.
    """
    print()
    for uid, user in getUsers():
        if REAL_USER_MIN_UID <= uid <= REAL_USER_MAX_UID:
            print(' * {:10s} {}'.format(user, uid))


@task
def create(username, homeBase='/home'):
    """
    Creates a new user for everyday use.
    """
    return sudo('useradd --base-dir {} --user-group --create-home '
                '--shell /bin/bash {}'.format(homeBase, username))


def rebuildKeys(service):
    sudo('cat /etc/braid/services/{0}/admins/*.keys > /etc/braid/services/{0}/authorized_keys'.format(service))


def makeServiceAdmin(user, service):
    sudo('mkdir -p /etc/braid/services/{}/admins'.format(service))
    sudo('ln -fs ~{}/.ssh/authorized_keys /etc/braid/services/{}/admins/{}.keys'.format(user, service, user))
    rebuildKeys(service)


#    with cd('~{}'.format(service)):
#        # Enforce .ssh directory
#        sudo('mkdir -p .ssh', user=service)
#
#        # Add keys to authorized keys file
#        sudo('cat ~{}/.ssh/authorized_keys >> .ssh/authorized_keys'.format(user))
#
#        # Remove duplicate keys
#        # TODO: Does this always work?
#        sudo('sort -u .ssh/authorized_keys -o .ssh/authorized_keys')
#
#        # Enforce correct ownership and permissions
#        sudo('chown {0}:{0} .ssh .ssh/authorized_keys'.format(service))
#        sudo('chmod 0600 .ssh/authorized_keys')


@task
def makeAdmin(user, *services):
    if not services:
        # TODO: Get all services
        pass

    for service in services:
        makeServiceAdmin(user, service)

