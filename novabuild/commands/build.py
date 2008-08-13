# -*- coding: utf-8 -*- ex:set ts=4 et:

import os, sys, glob
from novabuild.debcontrol import PackageControlParser
from novabuild.run import system
from novabuild.colours import red, blue
from novabuild.chroot import Chroot
from exceptions import Exception
from email.Utils import formatdate

# Do we need to update the changelog?
def changelog_is_up_to_date(filename, version):
    line = file(filename, 'r').readline()
    return version in line

# Update the changelog with a new entry.
def prepend_changelog_entry(new_filename, old_filename, package, version, message):
    fp = file(new_filename, 'w')
    fp.write("%s (%s) stable; urgency=low\n\n" % (package, version))
    print message.split('\n')
    for line in message.split('\n'):
        fp.write("  %s\n" % line);
    fp.write(" -- Damien Sandras <dsandras@novacom.be>  %s\n\n" % formatdate(localtime=True))

    # ... and put the old content in.
    fp2 = file(old_filename, 'r')
    for line in fp2:
        fp.write(line)


def check_code(code, module):
    if code != 0:
        raise Exception("Could not build package %s" % module.name)


def get_dependencies(chroot, BUILD_DIR):
    control = PackageControlParser()
    control.read(os.path.join(BUILD_DIR, 'debian/control'))
    dependencies = control.source.get('Build-Depends', '')
    return [i.strip().split(None, 1)[0] for i in dependencies.split(',')]

def build(chroot, module):
    TARBALL = os.path.join('tarballs', module['Basename'])

    if not os.path.exists(TARBALL):
        raise Exception("You must fetch the package '%s' before building it." % module.name)

    BUILD_ROOT = os.path.join(chroot.get_home_dir(), 'tmp-build-dir')
    BUILD_DIR = os.path.join (BUILD_ROOT, '%s-%s' % (module.name, module['Version']))
    DEBIAN_DIR = os.path.join('debian', 'debian-%s' % module.name)

    print blue("Uncompressing '%s'" % TARBALL)

    code = chroot.system('rm -rf /home/%s/tmp-build-dir' % chroot.user, root=True)
    check_code(code, module)

    code = system('mkdir -p %s' % BUILD_ROOT)
    check_code(code, module)

    if TARBALL.endswith('.tar.bz2'):
        code = system('tar xjf %s -C %s' % (TARBALL, BUILD_ROOT))
        check_code(code, module)
    elif TARBALL.endswith('.tar.gz') or TARBALL.endswith('.tgz'):
        code = system('tar xzf %s -C %s' % (TARBALL, BUILD_ROOT))
        check_code(code, module)
    elif TARBALL.endswith('.zip'):
        code = system('unzip %s -d %s' % (TARBALL, BUILD_ROOT))
        check_code(code, module)
    else:
        raise Exception("Cannot find the type of the archive.")


    # Kernel packages have to be handled specially.
    if module['Module'] == 'linux':
        print blue("Building '%s' '%s'" % (module['Module'], module['Version']))
        code = system('cp debian/config-%s-i386 %s/.config' % (module['Version'], BUILD_DIR))
        check_code(code, module)

        code = chroot.system('make-kpkg --revision=novacom.i386.3.0 kernel_image kernel_headers kernel_source',
                             cwd=chroot.abspath('~/tmp-build-dir/linux-%s' % module['Version']), root=True)
        check_code(code, module)

    else:
        code = system('mv %s/* %s' % (BUILD_ROOT, BUILD_DIR))
        #check_code(code, module)  FIXME: we don't want to fail when "cannot move to itself"

        code = system('cp -r %s %s/debian' % (DEBIAN_DIR, BUILD_DIR))
        check_code(code, module)

        print blue('Installing dependencies')
        code = chroot.system('apt-get install %s' % ' '.join(get_dependencies(chroot, BUILD_DIR)), root=True)
        check_code(code, module)

        # Write a new changelog entry...
        version = "%s-novacom.%s" % (module['Version'], module['Build-Number'])
        changelog_file = "%s/debian/changelog" % BUILD_DIR

        if not changelog_is_up_to_date(changelog_file, version):
            print blue("Update ChangeLog")
            old_file = "%s/changelog" % DEBIAN_DIR
            prepend_changelog_entry(changelog_file, old_file, module.name, version, "* New build.")

            # backup the new changelog file
            code = system('cp -f %s %s' % (changelog_file, old_file))
            check_code (code, module)

        print blue("Building '%s' '%s'" % (module.name, module['Version']))
        code = chroot.system('dpkg-buildpackage', root=True, cwd='/home/%s/tmp-build-dir/%s-%s'
                             % (chroot.user, module.name, module['Version']))
        check_code(code, module)

    packages_to_install = [i.strip() for i in module['Install'].split(',')]
    if packages_to_install != []:
        print blue("Installing packages '%s'" % "', '".join(packages_to_install))
        packages = [os.path.basename(i) for i in glob.glob(chroot.abspath('~/tmp-build-dir/*.deb', internal=False))]
        for package in packages:
            if package.split('_',1)[0] in packages_to_install:
                code = chroot.system("dpkg -i %s" % chroot.abspath('~/tmp-build-dir/%s' % package), root=True)
                check_code(code, module)

    code = system('mv -f %s/*.deb repository/' % BUILD_ROOT)


def main(chroot, moduleset, args):
    module = moduleset[args[0]]

    try:
        build(chroot, module)

    except Exception, e:
        print red(e)
        sys.exit(1)
