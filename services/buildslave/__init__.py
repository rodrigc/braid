import os
from cStringIO import StringIO

from fabric.api import run, put, settings, env
from fabric.contrib.files import upload_template

from braid import package, pip
from braid.twisted import service

from twisted.python.filepath import FilePath

env.python = 'system'

class Buildslave(service.Service):

    logDir = '~/run'

    def task_install(self,
                slavename,
                hostInfo,
                buildmaster='buildbot.twistedmatrix.com',
                port=9987,
                adminInfo='Tom Prince <buildbot@twistedmatrix.com>'):
        """
        Install buildslave
        """
        # Twisted's dependencies
        # (ubuntu/debian version)
        package.install([
            'python-pyasn1',
            'python-crypto',
            'python-gmpy',
            'python-gobject',
            'python-soappy',
            #'python-subunit',
            'python-dev',
            'bzr',
            'gcc',
            'subversion',
            'python-pip',
            ])

        # rpmbuild
        # pydoctor
        # latex
        # subunit

        self.bootstrap()

        with settings(user='buildslave'):
            pip.install('bzr-svn')
            pip.install('buildbot-slave')
            pip.install('bzr+https://code.launchpad.net/~mwhudson/pydoctor/dev@594#egg=pydoctor')
            pip.install(" ".join([
                'pep8==1.3.3',
                'pylint==0.25.1',
                'logilab-astng==0.23.1',
                'logilab-common==0.59.0'
                ]))

            tacFile = FilePath(__file__).sibling('buildbot.tac')
            upload_template(tacFile.path, os.path.join(self.runDir, 'buildbot.tac'),
                    context={
                        'buildmaster': buildmaster,
                        'port': port,
                        'slavename': slavename,
                        })

            infoPath = os.path.join(self.runDir, 'info')
            run('mkdir -p {}'.format(infoPath))
            put(StringIO(adminInfo), os.path.join(infoPath, 'admin'))
            put(StringIO(hostInfo), os.path.join(infoPath, 'host'))

            startFile = FilePath(__file__).sibling('start')
            put(startFile.path, os.path.join(self.binDir, 'start'), mode=0755)

globals().update(Buildslave('buildslave').getTasks())
