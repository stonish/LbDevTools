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
import logging
from subprocess import call
from optparse import OptionParser
from LbConfiguration.SP2.lookup import walkProjectDeps, PREFERRED_PLATFORM
from LbConfiguration.SP2.version import expandVersionAlias

# FIXME: this differs from the original Lbglimpse because it searched depth first
#        but to fix it it's better to have a proper dep scan in SP2.lookup
def paths(project, version):
    processed = set()
    for _, root, deps in walkProjectDeps(project, version):
        deps[:] = set(deps).difference(processed)
        deps.sort()
        processed.update(deps)
        yield root

def main():
    parser = OptionParser(usage='%prog [options] pattern [<project>/<version>|<project> <version>]',
                          description='run the glimpse command on the project '
                                      'specified on the command line and on all '
                                      'the projects it depends on')

    parser.add_option('-v', '--verbose', action='store_const',
                      dest='log_level', const=logging.INFO,
                      help='increase verbosity')
    parser.add_option('-d', '--debug', action='store_const',
                      dest='log_level', const=logging.DEBUG,
                      help='print debug messages')

    parser.set_defaults(log_level=logging.WARNING)

    opts, args = parser.parse_args()
    logging.basicConfig(level=opts.log_level)

    try:
        pattern = args.pop(0)
        if len(args) == 1:
            args = args[0].split('/')
        project, version = args
    except (IndexError, ValueError):
        parser.error('wrong number of arguments')

    version = expandVersionAlias(project, version, PREFERRED_PLATFORM)

    for path in paths(project, version):
        if os.path.exists(os.path.join(path, '.glimpse_filenames')):
            logging.info('running glimpse in %s', path)
            call(['glimpse', '-y', '-H', path, pattern])


if __name__ == '__main__':
    main()
