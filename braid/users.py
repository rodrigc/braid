from __future__ import print_function, absolute_import
from fabric.api import task, run, hide, sudo, cd, put, quiet

from twisted.python.filepath import FilePath


SERVICE_USER_MIN_UID = 997
SERVICE_USER_MAX_UID = 999

REAL_USER_MIN_UID = 1000
REAL_USER_MAX_UID = 65533

SERVICES_CONFIG_DIR = '/etc/braid/services'


def getUsers():
    users = []

    with hide('everything'):
        db = run('cat /etc/passwd')

    for line in db.splitlines():
        user, _, uid, _, _, _, _ = line.split(':')
        users.append((int(uid), user))
    users.sort()
    return users


def getUsersInRange(start, end):
    return [u for u in getUsers() if start <= u[0] <= end]


def getServiceUsers():
    # TODO: Is this enough? Shall we list dirs in /srv instead?
    return getUsersInRange(SERVICE_USER_MIN_UID, SERVICE_USER_MAX_UID)


def getRealUsers():
    return getUsersInRange(REAL_USER_MIN_UID, REAL_USER_MAX_UID)


@task
def listServices():
    """
    List all service specific users.

    This currently ignores all users created by installed packages, such as
    postgres or www-data.
    """
    print()
    for uid, user in getServiceUsers():
        print(' * {:10s} {}'.format(user, uid))


@task
def listReal():
    """
    List all real users.
    """
    print()
    for uid, user in getRealUsers():
        print(' * {:10s} {}'.format(user, uid))


@task
def create(username, homeBase='/home'):
    """
    Creates a new user for everyday use.
    """
    return sudo('useradd --base-dir {} --user-group --create-home '
                '--shell /bin/bash {}'.format(homeBase, username))


def rebuildKeys(service):
    with quiet():
        sudo('cat {0}/{1}/admins/*.keys {0}/{1}/uploaded_keys/*.keys > '
             '{0}/{1}/authorized_keys'.format(SERVICES_CONFIG_DIR, service))

    # TODO: Execute this only once on service creation?
    setupServiceSSH(service)


def uploadServiceAdminKey(name, keyfile, service):
    sudo('mkdir -p {}/{}/uploaded_keys'.format(SERVICES_CONFIG_DIR, service))
    # TODO: What do we want to do if the file already exists? Overwrite, append
    # or raise an error?
    put(keyfile, '{}/{}/uploaded_keys/{}.keys'.format(
        SERVICES_CONFIG_DIR, service, name), use_sudo=True)
    rebuildKeys(service)


def makeServiceAdmin(user, service):
    sudo('mkdir -p {}/{}/admins'.format(SERVICES_CONFIG_DIR, service))
    sudo('ln -fs ~{}/.ssh/authorized_keys {}/{}/admins/{}.keys'.format(
        user, SERVICES_CONFIG_DIR, service, user))
    rebuildKeys(service)


def setupServiceSSH(service):
    with cd('~{}'.format(service)):
        sudo('mkdir -p .ssh', user=service)
        # TODO: Shall we prefer to copy the file instead of linking it?
        sudo('ln -fs {}/{}/authorized_keys .ssh/authorized_keys'.format(
            SERVICES_CONFIG_DIR, service), user=service)


def canAdmin(user, service):
    with quiet():
        return run('ls {}/{}/admins/{}.keys'.format(SERVICES_CONFIG_DIR,
                                                    service, user)).succeeded


@task
def uploadkeys(name, keyfile, *services):
    """
    Upload keys to give admin rights to services.
    """
    if not services:
        services = [u for _, u in getServiceUsers()]

    for service in services:
        uploadServiceAdminKey(name, keyfile, service)


@task
def deletekeys(name, *services):
    """
    Remove the named keys from the server.
    """
    if not services:
        services = [u for _, u in getServiceUsers()]

    for service in services:
        with quiet():
            rm = sudo('rm {}/{}/uploaded_keys/{}.keys'.format(
                SERVICES_CONFIG_DIR, service, name))
        if rm.succeeded:
            rebuildKeys(service)


@task
def setadmin(user, *services):
    """
    Enable a user to login as different services.
    """
    if not services:
        services = [u for _, u in getServiceUsers()]

    for service in services:
        makeServiceAdmin(user, service)


@task
def unsetadmin(user, *services):
    """
    Revoke admin rights for a user.
    """
    if not services:
        services = [u for _, u in getServiceUsers()]

    for service in services:
        with quiet():
            rm = sudo('rm -rf {}/{}/admins/{}.keys'.format(SERVICES_CONFIG_DIR,
                                                           service, user))
        if rm.succeeded:
            rebuildKeys(service)


def makeTable(data, headers, cols):
    output = []
    assert len(headers) == len(cols)

    row = '|' + '|'.join([' {{:{}{}s}} '.format(*c) for c in cols]) + '|'
    sep = '+' + '+'.join(['-' * (s[1] + 2) for s in cols]) + '+'

    output.append(sep)
    output.append(row.format(*headers))
    output.append(sep)

    for dataRow in data:
        assert len(dataRow) == len(cols)
        output.append(row.format(*dataRow))

    output.append(sep)
    return '\n'.join(output)


@task
def adminreport():
    """
    Print a summary of users and keys with admin rights.
    """
    services = [service for _, service in getServiceUsers()]
    users = getRealUsers()

    data = []

    for uid, user in users:
        permissions = [canAdmin(user, service) for service in services]

        if not any(permissions):
            continue

        permissions = ['*' if p else ' ' for p in permissions]
        data.append([user, str(uid)] + permissions)

    if data:
        print('\n' + makeTable(
            data,
            ['User', 'UID'] + services,
            [('<', 12), ('^', 5)] + [('^', len(s)) for s in services]
        ))
    else:
        print('\nNo users with admin rights.')

    with quiet():
        keys = run('ls -1 {}/*/uploaded_keys/*.keys'.format(
            SERVICES_CONFIG_DIR))

    if keys.succeeded:
        allowed = {}

        for key in keys.splitlines():
            key = FilePath(key)
            name, _ = key.basename().rsplit('.', 1)
            service = key.parent().parent().basename()
            allowed.setdefault(name, set()).add(service)

        data = []

        for key, allowed_services in allowed.iteritems():
            permissions = [service in allowed_services for service in services]
            permissions = ['*' if p else ' ' for p in permissions]
            data.append([key] + permissions)

        print('\n' + makeTable(
            data,
            ['Key file'] + services,
            [('<', 20)] + [('^', len(s)) for s in services]
        ))
    else:
        print('\nNo manually uploaded keys.')
