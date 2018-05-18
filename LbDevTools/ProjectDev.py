###############################################################################
# (c) Copyright 2018 CERN                                                     #
#                                                                             #
# This software is distributed under the terms of the GNU General Public      #
# Licence version 3 (GPL Version 3), copied verbatim in the file "COPYING".   #
#                                                                             #
# In applying this licence, CERN does not waive the privileges and immunities #
# granted to it by virtue of its status as an Intergovernmental Organization  #
# or submit itself to any jurisdiction.                                       #
###############################################################################
__author__ = 'Marco Clemencic <marco.clemencic@cern.ch>'

import os
import logging
import stat
import sys

from string import Template

import LbEnv.ProjectEnv
from LbEnv.ProjectEnv.version import DEFAULT_VERSION, expandVersionAlias
from LbEnv import fixProjectCase
from LbDevTools import createGitIgnore, DATA_DIR, __version__


def main():
    '''
    Script to generate a local development project.
    '''
    from optparse import OptionParser
    from LbEnv.ProjectEnv.options import (
        addSearchPath, addOutputLevel, addPlatform, addListing, checkPlatform)
    from LbEnv.ProjectEnv.lookup import findProject, MissingProjectError
    from subprocess import call

    parser = OptionParser(
        usage='%prog [options] Project[/version]',
        version='%prog {}'.format(__version__))

    addSearchPath(parser)
    addOutputLevel(parser)
    addPlatform(parser)
    addListing(parser)

    parser.add_option(
        '--name',
        action='store',
        help='Name of the local project [default: "<proj>Dev_<vers>"].')

    parser.add_option(
        '--dest-dir',
        action='store',
        help='Where to create the local project [default: %default].')

    parser.add_option(
        '--git',
        action='store_true',
        help='Initialize git repository in the generated directory [default, '
        'if git is available].')

    parser.add_option(
        '--no-git',
        action='store_false',
        dest='git',
        help='Do not initialize the git local repository.')

    try:
        from LbEnv import which
        has_git = bool(which('git'))
    except ImportError:
        has_git = True

    parser.set_defaults(dest_dir=os.curdir, git=has_git)

    opts, args = parser.parse_args()

    logging.basicConfig(level=opts.log_level)

    opts.platform = checkPlatform(parser, opts.platform)

    if len(args) == 1:
        if '/' in args[0]:
            args[0:1] = args[0].split('/')
        else:
            args.append(DEFAULT_VERSION)
    elif len(args) == 2:
        logging.warning('deprecated version specification: '
                        'use "lb-dev ... %s/%s" instead', *args)

    try:
        project, version = args
        version = expandVersionAlias(project, version, opts.platform)
    except ValueError:
        parser.error('wrong number of arguments')

    project = fixProjectCase(project)

    try:
        from LbEnv.ProjectEnv.lookup import InvalidNightlySlotError
        from LbEnv.ProjectEnv.script import localNightlyHelp
        if isinstance(opts.nightly, InvalidNightlySlotError):
            sys.stderr.write(
                localNightlyHelp(
                    parser.prog or os.path.basename(sys.argv[0]), opts.nightly,
                    project, opts.platform
                    if opts.platform not in ('best', None) else '$CMTCONFIG',
                    sys.argv[1:]))
            sys.exit(64)
        if opts.help_nightly_local:
            if not opts.nightly:
                parser.error('--help-nightly-local must be specified in '
                             'conjunction with --nightly')
            sys.stdout.write(
                localNightlyHelp(
                    parser.prog or os.path.basename(sys.argv[0]),
                    InvalidNightlySlotError(opts.nightly[0], opts.nightly[1],
                                            []),
                    project,
                    opts.platform
                    if opts.platform not in ('best', None) else '$CMTCONFIG', [
                        a for a in sys.argv[1:]
                        if not '--help-nightly-local'.startswith(a)
                    ],
                    error=False))
            sys.exit()
    except ImportError:
        # old version of LbEnv
        # (before https://gitlab.cern.ch/lhcb-core/LbEnv/merge_requests/19)
        pass

    if opts.user_area and not opts.no_user_area:
        from LbEnv.ProjectEnv import EnvSearchPathEntry, SearchPathEntry
        if os.environ['User_release_area'] == opts.user_area:
            opts.dev_dirs.insert(0, EnvSearchPathEntry('User_release_area'))
        else:
            opts.dev_dirs.insert(0, SearchPathEntry(opts.user_area))

    # FIXME: we need to handle common options like --list in a single place
    if opts.list:
        from LbEnv.ProjectEnv.lookup import listVersions
        for entry in listVersions(project, opts.platform):
            print '%s in %s' % entry
        sys.exit(0)
    if opts.list_platforms:
        from LbEnv.ProjectEnv.lookup import listPlatforms
        platforms = listPlatforms(project, version)
        if platforms:
            print '\n'.join(platforms)
        sys.exit(0)

    if not opts.name:
        opts.name = '{project}Dev_{version}'.format(
            project=project, version=version)
        local_project, local_version = project + 'Dev', version
    else:
        local_project, local_version = opts.name, 'HEAD'

    devProjectDir = os.path.join(opts.dest_dir, opts.name)

    if os.path.exists(devProjectDir):
        parser.error('directory "%s" already exist' % devProjectDir)

    # ensure that the project we want to use can be found

    # prepend dev dirs to the search path
    if opts.dev_dirs:
        LbEnv.ProjectEnv.path[:] = opts.dev_dirs + LbEnv.ProjectEnv.path

    try:
        try:
            projectDir = findProject(project, version, opts.platform)
            logging.info('using %s %s from %s', project, version, projectDir)
        except MissingProjectError, x:
            parser.error(str(x))

        # Check if it is a CMake-enabled project
        use_cmake = os.path.exists(
            os.path.join(projectDir, project + 'Config.cmake'))
        if not use_cmake:
            logging.warning('%s %s does not seem a CMake project', project,
                            version)

        # Check if it is a CMT-enabled project
        use_cmt = os.path.exists(
            os.path.join(projectDir, os.pardir, os.pardir, 'cmt',
                         'project.cmt'))

        if not use_cmake and not use_cmt:
            logging.error('neither CMake nor CMT configuration found '
                          '(are you using the right CMTCONFIG?)')
            exit(1)
    except SystemExit as err:
        if opts.nightly:
            try:
                from LbEnv.ProjectEnv.lookup import InvalidNightlySlotError
                from LbEnv.ProjectEnv.script import localNightlyHelp
                sys.stderr.write(
                    localNightlyHelp(
                        parser.prog or os.path.basename(sys.argv[0]),
                        InvalidNightlySlotError(opts.nightly[0],
                                                opts.nightly[1], []), project,
                        opts.platform if opts.platform not in ('best', None)
                        else '$CMTCONFIG', sys.argv[1:]))
            except ImportError:
                # old version of LbEnv
                # (before https://gitlab.cern.ch/lhcb-core/LbEnv/merge_requests/19)
                pass
        sys.exit(err.code)

    # Create the dev project
    if not os.path.exists(opts.dest_dir):
        logging.debug('creating destination directory "%s"', opts.dest_dir)
        os.makedirs(opts.dest_dir)

    logging.debug('creating directory "%s"', devProjectDir)
    if opts.git:
        call(['git', 'init', '--quiet', devProjectDir])
    else:
        os.makedirs(devProjectDir)

    data = dict(
        project=project,
        version=version,
        search_path=' '.join(['"%s"' % p for p in LbEnv.ProjectEnv.path]),
        search_path_repr=repr(LbEnv.ProjectEnv.path),
        search_path_env=os.pathsep.join(LbEnv.ProjectEnv.path),
        # we use cmake if available
        build_tool=('cmake' if use_cmake else 'cmt'),
        PROJECT=project.upper(),
        local_project=local_project,
        local_version=local_version,
        cmt_project=opts.name,
        datadir=DATA_DIR)

    # FIXME: improve generation of searchPath files, so that they match the command line
    templateDir = os.path.join(
        os.path.dirname(__file__), 'templates', 'lb-dev')
    templates = [
        'CMakeLists.txt', 'toolchain.cmake', 'Makefile', 'searchPath.py',
        'build.conf', 'run'
    ]
    # generated files that need exec permissions
    execTemplates = set(['run'])

    if opts.nightly:
        data['slot'], data['day'], data['base'] = opts.nightly
    else:
        data['slot'] = data['day'] = data['base'] = ''

    # for backward compatibility, we create the CMT configuration and env helpers
    if use_cmt:
        templates += ['cmt/project.cmt']
        os.makedirs(os.path.join(devProjectDir, 'cmt'))

    for templateName in templates:
        t = Template(open(os.path.join(templateDir, templateName)).read())
        logging.debug('creating "%s"', templateName)
        dest = os.path.join(devProjectDir, templateName)
        with open(dest, 'w') as f:
            f.write(t.substitute(data))
        if templateName in execTemplates:
            mode = (stat.S_IMODE(os.stat(dest).st_mode) | stat.S_IXUSR
                    | stat.S_IXGRP)
            os.chmod(dest, mode)

    # generate searchPath.cmake
    if opts.dev_dirs and use_cmake:
        logging.debug('creating "%s"', 'searchPath.cmake')
        dest = os.path.join(devProjectDir, 'searchPath.cmake')
        with open(dest, 'w') as f:
            f.write('# Search path defined from lb-dev command line\n')
            f.write(opts.dev_dirs.toCMake())

    if opts.dev_dirs and use_cmt:
        for shell in ('sh', 'csh'):
            build_env_name = 'build_env.' + shell
            logging.debug('creating "%s"', build_env_name)
            dest = os.path.join(devProjectDir, build_env_name)
            with open(dest, 'w') as f:
                f.write('# Search path defined from lb-dev command line\n')
                f.write(opts.dev_dirs.toCMT(shell))

    # When the project name is not the same as the local project name, we need a
    # fake *Sys package for SetupProject (CMT only).
    if use_cmt and project != local_project:
        t = Template(
            open(os.path.join(templateDir, 'cmt/requirements_')).read())
        templateName = os.path.join(local_project + 'Sys', 'cmt/requirements')
        os.makedirs(os.path.dirname(os.path.join(devProjectDir, templateName)))
        logging.debug('creating "%s"', templateName)
        open(os.path.join(devProjectDir, templateName), 'w').write(
            t.substitute(data))
        if use_cmake:  # add a CMakeLists.txt to it
            with open(
                    os.path.join(devProjectDir, local_project + 'Sys',
                                 'CMakeLists.txt'), 'w') as cml:
                cml.write('gaudi_subdir({0} {1})\n'.format(
                    local_project + 'Sys', local_version))

    if opts.git:
        createGitIgnore(
            os.path.join(devProjectDir, '.gitignore'), selfignore=False)
        call(['git', 'add', '.'], cwd=devProjectDir)
        call(
            [
                'git', 'commit', '--quiet', '-m',
                'initial version of satellite project\n\n'
                'generated with:\n\n'
                '    %s\n' % ' '.join(sys.argv)
            ],
            cwd=devProjectDir)

    # Success report
    msg = '''
Successfully created the local project {0} in {1}

To start working:

  > cd {2}
  > git lb-use {3}
  > git lb-checkout {3}/vXrY MyPackage

then

  > make
  > make test

and optionally (CMake only)

  > make install

You can customize the configuration by editing the files 'build.conf' and
'CMakeLists.txt' (see http://cern.ch/gaudi/CMake for details).
'''

    print msg.format(opts.name, opts.dest_dir, devProjectDir, project)
