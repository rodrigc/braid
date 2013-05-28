from fabric.api import *
from fabric import api as _api

from braid import info as _info

def sudo(*args, **kwargs):
    func = _api.run if _info.isRoot() else _api.sudo 
    func(*args, **kwargs)
