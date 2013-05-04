"""
Collection of utilities to automate the administration of Twisted's
infrastructure. Use this utility to install, update and start/stop/restart
services running on twistedmatrix.com.
"""

"""
This file is a simple entry point, nothing is final about it!
Just experimenting for now.
"""


from braid import base, users
from braid import config

__all__ = ['base', 'config', 'users']

from twisted.python.filepath import FilePath
import imp
p = FilePath(__file__).sibling('services')
for service in p.children():
    fabfile = service.child('fabfile.py')
    if fabfile.exists():
        module = imp.load_source(service.basename(), fabfile.path, fabfile.open())
        if module.config == config:
            del module.config
        globals()[service.basename()] = module
        __all__.append(service.basename())


from fabric.api import local, lcd, task
from twisted.python.util import sibpath
services = {
    'buildbot': 'https://github.com/twisted-infra/twisted-buildbot-configuration',
    'diffresource': 'https://github.com/twisted-infra/diffresource',
    'hiscore': 'http://twistedmatrix.com/~tomprince/hiscore',
    'kenaan': 'https://github.com/twisted-infra/kenaan',
    't-names': 'https://github.com/twisted-infra/t-names',
    'trac-config': 'https://github.com/twisted-infra/trac-config',
    'twisted-website': 'https://code.launchpad.net/~tom.prince/twisted-website/twisted-website-braided',
    }
@task
def cloneService():
    with lcd(sibpath(__file__, 'services')):
        for service, url in services.iteritems():
            if 'github' in url:
                local('git clone {} {}'.format(url, service))
            else:
                local('bzr branch {} {}'.format(url, service))
__all__ += ['cloneService']
