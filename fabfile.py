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
