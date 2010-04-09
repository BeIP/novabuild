# -*- coding: utf-8 -*- ex:set ts=4 et:

import os, sys
from novabuild.run import system
from novabuild.colours import red, blue
from novabuild.misc import check_code
from exceptions import Exception


def fetch(module):
    if (os.path.exists('tarballs/%s' % module['Basename'])):
        print blue("File already exists: '%s'" % module['Basename'])
        return False

    source_type = module['Source-Type']

    if source_type == 'wget':
        code = system('wget -Nc %s -Otarballs/%s' % (module['Source'], module['Basename']))
        check_code(code, module)

    elif source_type == 'git':
        fullname = '%s-%s' % (module.name, module['Version'])
        branch = module.get('Branch', 'master')

        print blue("Cloning the last revision of the remote repository")
        code = system('git clone --depth=1 -- %s tarballs/%s' % (module['Source'], fullname))
        check_code(code, module)

        print blue("Generating tarball")
        code = system('( cd tarballs/%s && git archive --format=tar --prefix=%s/ origin/%s ) | gzip -9 > tarballs/%s' \
                      % (fullname, fullname, branch, module['Basename']))
        check_code(code, module)

        print blue("Removing temporary directory")
        code = system('rm -rf tarballs/%s' % fullname)
        check_code(code, module)

    elif source_type == 'svn':
        tmpdir = '%s-%s' % (module.name, module['Version'])

        print blue("Exporting the SVN snapshot")
        code = system('svn export --force %s tarballs/%s' % (module['Source'], tmpdir))
        check_code(code, module)

        print blue("Generating tarball")
        code = system('cd tarballs && tar czvf %s %s' % (module['Basename'], tmpdir))
        check_code(code, module)

        print blue("Removing temporary directory")
        code = system('rm -rf tarballs/%s' % tmpdir)
        check_code(code, module)

    elif source_type == 'local':
        filename = module['Source']
        if filename.startswith('file://'):
            filename = filename[7:]

        code = system('cp %s tarballs/' % filename)
        check_code(code, module)

    else:
        raise Exception("The '%s' source type is not handled yet" % source_type)

    return True


def main(moduleset, args):
    module = moduleset[args[0]]
    try:
        fetch(module)
        return 0
    except Exception, e:
        print red(e)
        return 1
