from fabric.api import sudo

from braid.info import distroFamily

fedoraEquivs = {
        'python-gmpy': 'gmpy',
        'python-subvertpy': 'subvertpy',
        'python-gobject': 'pygobject2',
        'python-soappy': 'SOAPpy',
        'python-dev': 'python-devel',
        }


def install(packages):
    """
    Install a list of packages.
    """
    if distroFamily() == 'debian':
        sudo('apt-get --yes --quiet install {}'.format(" ".join(packages)))
    else:
        packages = [fedoraEquivs.get(package, package) for package in packages]
        sudo('yum install -y {}'.format(" ".join(packages)))
