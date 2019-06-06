###############################################################################
# (c) Copyright 2019 CERN                                                     #
#                                                                             #
# This software is distributed under the terms of the GNU General Public      #
# Licence version 3 (GPL Version 3), copied verbatim in the file "COPYING".   #
#                                                                             #
# In applying this licence, CERN does not waive the privileges and immunities #
# granted to it by virtue of its status as an Intergovernmental Organization  #
# or submit itself to any jurisdiction.                                       #
###############################################################################
__author__ = 'Ben Couturier <ben.couturier@cern.ch>'

import os
import logging
import stat
import sys
import json

from string import Template
from subprocess import call

import LbEnv.ProjectEnv
from LbEnv.ProjectEnv.version import DEFAULT_VERSION, expandVersionAlias
from LbEnv.ProjectEnv.lookup import findProject
from LbEnv.ProjectEnv import EnvSearchPathEntry
from LbEnv import fixProjectCase
from LbDevTools import createGitIgnore, createClangFormat, DATA_DIR


def project_name(name):
    """
    make sure name is a valid identifier
    """
    import re
    if not re.match(r'^[a-z_][0-9a-z_]*$', name, re.IGNORECASE):
        raise ValueError('invalid name')
    return name


class UserProject:

    @staticmethod
    def create(project, version, platform, path=None, name=None,
               nightly=None, with_git=True, enable_fortran=False,
               dev_dirs=None, siteroot="/cvmfs/lhcb.cern.ch/lib"):
        """ Create a local LHCb project that depends on the LHCb project/version passed in argument """

        if project is None or version is None or platform is None:
            raise Exception("Project, version and platform should all be specified")

        if path is None:
            path = os.path.abspath(os.curdir())

        # Checking if the version is an alias and returning the real one
        project = fixProjectCase(project)
        version = expandVersionAlias(project, version, platform)

        try:

            projectDir = findProject(project, version, platform)
            logging.info('using %s %s from %s', project, version, projectDir)

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
            sys.exit(err.code)

        # Create the dev project
        if not name:
            name = '{project}Dev_{version}'.format(project=project, version=version)
            local_project, local_version = project + 'Dev', version
        else:
            local_project, local_version = name, 'HEAD'

        devProjectDir = os.path.join(path, name)

        logging.debug('creating directory "%s"', devProjectDir)
        if with_git:
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
            with_fortran='FORTRAN' if enable_fortran else '',
            cmt_project=name,
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

        if nightly:
            data['slot'], data['day'], data['base'] = nightly
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
        if dev_dirs and use_cmake:
            logging.debug('creating "%s"', 'searchPath.cmake')
            dest = os.path.join(devProjectDir, 'searchPath.cmake')
            with open(dest, 'w') as f:
                f.write('# Search path defined from lb-dev command line\n')
                f.write(dev_dirs.toCMake())

        if dev_dirs and use_cmt:
            for shell in ('sh', 'csh'):
                build_env_name = 'build_env.' + shell
                logging.debug('creating "%s"', build_env_name)
                dest = os.path.join(devProjectDir, build_env_name)
                with open(dest, 'w') as f:
                    f.write('# Search path defined from lb-dev command line\n')
                    f.write(dev_dirs.toCMT(shell))

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

        # add a default .clang-format file
        upstream_style_file = os.path.join(projectDir, os.pardir, os.pardir,
                                           '.clang-format')
        dev_style_file = os.path.join(devProjectDir, '.clang-format')
        if os.path.exists(upstream_style_file):
            with open(dev_style_file, 'w') as f:
                f.write('# Copied from {}\n'.format(upstream_style_file))
                f.writelines(open(upstream_style_file))
        else:
            # use default
            createClangFormat(dev_style_file)

        if with_git:
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

        with open(os.path.join(devProjectDir, 'configuration.json'), 'w') as f:
            json.dump(f, data)

    def __init__(self, project_path):
        """ Constructor for the user project instance, loading data from disk """
        None

