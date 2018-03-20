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
Implementation of LHCb special Git subcommands.
'''
__author__ = 'Marco Clemencic <marco.clemencic@cern.ch>'

import logging
from subprocess import call, check_call, check_output, CalledProcessError
from argparse import ArgumentParser

PROTOCOLS_URLS = {
    'ssh': 'ssh://git@gitlab.cern.ch:7999/',
    'krb5': 'https://:@gitlab.cern.ch:8443/',
    'https': 'https://gitlab.cern.ch/',
}
DEFAULT_PROTOCOL = 'krb5'


def project_url(project, protocol):
    '''
    Return the url to the Git repository of the project for a given protocol.
    '''
    from LbEnv import fixProjectCase
    # FIXME: get source uri from SoftConfDB
    uri = 'gitlab-cern:{}/{}'.format(
        'lhcb' if project.lower() != 'gaudi' else 'gaudi',
        fixProjectCase(project)
    )
    return PROTOCOLS_URLS[protocol] + uri.split(':', 1)[-1]


def use():
    '''
    Implementation of `git lb-use` command.
    '''

    parser = ArgumentParser(prog='git lb-use')

    parser.add_argument('project', help='project which history to fetch')
    parser.add_argument('url', nargs='?',
                        metavar='repository_url',
                        help='alternative repository to use, instead of the '
                        'standard one')

    parser.add_argument('-p', '--protocol',
                        choices=PROTOCOLS_URLS,
                        help='which protocol to use to connect to gitlab; '
                        'the default is defined by the config option '
                        'lb-use.protocol, or {} if not set'
                        .format(DEFAULT_PROTOCOL))

    parser.add_argument('-q', '--quiet', action='store_const',
                        dest='log_level', const=logging.WARNING,
                        help='be more quiet')
    parser.add_argument('-v', '--verbose', action='store_const',
                        dest='log_level', const=logging.DEBUG,
                        help='be more verbose')

    parser.set_defaults(log_level=logging.INFO)

    args = parser.parse_args()
    logging.basicConfig(level=args.log_level)

    if not args.protocol:
        try:
            args.protocol = check_output(
                ['git', 'config', '--get', 'lb-use.protocol']).strip()
        except CalledProcessError:
            args.protocol = DEFAULT_PROTOCOL

    if not args.url:
        args.url = project_url(args.project, args.protocol)

    logging.info("calling: git remote add -f '%s' '%s'",
                 args.project, args.url)

    try:
        # define a remote "$project", overwrite it if it already exists
        old_remote = check_output(
            ['git', 'config', '--get', 'remote.{}.url'.format(args.project)]
        ).strip()
        # the remote is defined
        logging.warning("overwriting existing remote '%s' (was %s)",
                        args.project, old_remote)
        call(['git', 'remote', 'rm', args.project])
    except CalledProcessError:
        pass

    try:
        check_call(['git', 'remote', 'add', args.project, args.url])
        check_call(['git', 'config',
                    'remote.{}.tagopt'.format(args.project), '--no-tags'])
        check_call(['git', 'config', '--add',
                    'remote.{}.fetch'.format(args.project),
                    '+refs/tags/*:refs/tags/{}/*'.format(args.project)])
        cmd = ['git', 'fetch']
        if args.log_level < logging.INFO:
            cmd.append('-v')
        elif args.log_level > logging.INFO:
            cmd.append('-q')
        cmd.append(args.project)
        check_call(cmd)
    except CalledProcessError as err:
        logging.error('command failed: %s', err.cmd)
        exit(err.returncode)
