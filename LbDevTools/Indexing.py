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
'''
Wrapper for the glimpse command to look for a pattern in an LHCb projects and
its dependencies.

@author Marco Clemencic <marco.clemencic@cern.ch>
@author Florence Ranjard
'''

import os
import sys
import logging
from subprocess import call
from whichcraft import which
from argparse import ArgumentParser
from LbEnv.ProjectEnv.lookup import walkProjectDeps, PREFERRED_PLATFORM
from LbEnv.ProjectEnv.version import expandVersionAlias


# FIXME: this differs from the original Lbglimpse because it searched depth
#        first but to fix it it's better to have a proper dep scan in
#        LbEnv.ProjectEnv.lookup
def paths(project, version):
    processed = set()
    for _, root, deps in walkProjectDeps(project, version):
        deps[:] = set(deps).difference(processed)
        deps.sort()
        processed.update(deps)
        yield root


def main():
    parser = ArgumentParser(
        description='run the glimpse command on the project specified on the '
        'command line and on all the projects it depends on')

    parser.add_argument('pattern', help='what to search in the projects')
    parser.add_argument(
        'project',
        metavar='project/version',
        help='which project/version to start the search from, descending its '
        'dependencies')

    parser.add_argument(
        '-v',
        '--verbose',
        action='store_const',
        dest='log_level',
        const=logging.INFO,
        help='increase verbosity')
    parser.add_argument(
        '-d',
        '--debug',
        action='store_const',
        dest='log_level',
        const=logging.DEBUG,
        help='print debug messages')

    parser.set_defaults(log_level=logging.WARNING)

    args = parser.parse_args()
    logging.basicConfig(level=args.log_level)

    try:
        args.project, args.version = args.project.split('/', 1)
    except ValueError:
        parser.error('invalid format for project/version: %r' % args.project)

    if not which('glimpse'):
        sys.exit('error: glimpse command not available, check the environment')

    if PREFERRED_PLATFORM:
        args.version = expandVersionAlias(args.project, args.version,
                                          PREFERRED_PLATFORM)

    for path in paths(args.project, args.version):
        if os.path.exists(os.path.join(path, '.glimpse_filenames')):
            logging.info('running glimpse in %s', path)
            call(['glimpse', '-y', '-H', path, args.pattern])


if __name__ == '__main__':
    main()
