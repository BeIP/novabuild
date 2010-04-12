#!/usr/bin/env python
# -*- coding: utf-8 -*- ex:set sw=4 ts=4 et:

import novabuild.commands as commands
from novabuild.chroot import Chroot
from novabuild.modules import ModuleSet
import sys
import os
import getopt
import traceback

sys.path.insert(0, os.path.abspath('.'))

def usage():
    print 'Usage: ' + sys.argv[0] + ' [command] [options]'
    print
    print 'available commands:'
    print '  prepare        prepare a new build environment'
    print '  list           list the available packages'
    print '  fetch          fetch the requested package'
    print '  fetchall       fetch all the packages'
    print '  build          build a single package'
    print '  buildall       build all the packages'
    print
    print 'Use ' + sys.argv[0] + ' [command] --help for more information.'

try:
    opts, args = getopt.getopt(sys.argv[1:], 'hc:m:',
                               ['help', 'chroot=', 'moduleset='])
except getopt.GetoptError, e:
    # print help information and exit:
    print str(e) # will print something like "option -a not recognized"
    usage()
    sys.exit(2)

chroot_name = None
moduleset_name = None

for o, a in opts:
    if o in ('-h', '--help'):
        usage()
        sys.exit(0)
    elif o in ('-c', '--chroot'):
        chroot_name = a
    elif o in ('-m', '--moduleset'):
        moduleset_name = a

# At least one remaining argument to specify the command.
if len(args) < 1:
    usage()
    sys.exit(2)

# Arguments to pass to the commands
chroot = None
if chroot_name:
    chroot = Chroot(chroot_name)

moduleset = None
if moduleset_name:
    filename = os.path.join('autobuild', 'modulesets', moduleset_name)
    moduleset = ModuleSet(filename)

command = args[0]
args = args[1:]
status = -1

try:

    if command == 'shell':
        status = commands.shell.main(chroot, args)

    elif command == 'prepare':
        status = commands.prepare.main(chroot, args)

    elif command == 'list':
        status = commands.pkglist.main(chroot, moduleset, args)

    elif command == 'fetch':
        status = commands.fetch.main(moduleset, args)

    elif command == 'fetchall':
        status = commands.fetchall.main(moduleset, args)

    elif command == 'build':
        chroot.start_session()
        status = commands.build.main(chroot, moduleset, args)

    elif command == 'buildall':
        chroot.start_session()
        status = commands.buildall.main(chroot, moduleset, args)

    elif command == 'installpackages':
        chroot.start_session()
        status = commands.installpackages.main(chroot, moduleset, args)

except:
    traceback.print_exc()
    status = -1

if chroot is not None:
    chroot.end_session()
sys.exit(status)
