import os
from cStringIO import StringIO

from fabric.api import run, put, settings
from fabric.contrib.files import upload_template

from braid import package, pip
from braid.twisted import service

from twisted.python.filepath import FilePath

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
        package.install('python-pyasn1')
        package.install('python-crypto')
        package.install('python-gmpy')
        package.install('python-gobject')
        package.install('python-soappy')
        #package.install('python-subunit')
        package.install('python-dev')
        package.install('bzr')
        package.install('gcc')
        package.install('subversion')

        package.install('python-pip')

        # rpmbuild
        # pydoctor
        # latex
        # subunit

        self.bootstrap(python='python')

        with settings(user='buildslave'):
            pip.install('bzr-svn', python='python')
            pip.install('buildbot-slave', python='python')

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
