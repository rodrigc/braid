from fabric.api import sudo

from braid.info import distroFamily

def install(package):
    if distroFamily() == 'debian':
        sudo('apt-get --yes --quiet install {}'.format(package))
    else:
        sudo('yum install -y {}'.format(package))
