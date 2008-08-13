# -*- coding: utf-8 -*- ex:set ts=4 et:

from novabuild.commands.build import build
from novabuild.colours import red, blue
import sys

def main(chroot, moduleset, args):
    status = 0

    for module in moduleset:
        try:
            print blue("Building '%s'" % module.name)
            build(chroot, module)
        except Exception, e:
            print red(e)
            status = 1

    sys.exit(status)
