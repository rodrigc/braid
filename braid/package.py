from fabric.api import sudo

from braid.info import distroFamily

def install(packages):
    """
    Install a list of packages.
    """
    if distroFamily() == 'debian':
        sudo('apt-get --yes --quiet install {}'.format(" ".join(packages)))
    else:
        sudo('yum install -y {}'.format(" ".join(packages)))
