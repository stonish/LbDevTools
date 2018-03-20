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

import os
import logging
from subprocess import (call, check_call, check_output, CalledProcessError,
                        Popen, PIPE)
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


def checkout():
    '''
    Implementation of `git lb-checkout` command.
    '''

    parser = ArgumentParser(prog='git lb-checkout')

    parser.add_argument('commit', metavar='branch',
                        help='name of the branch/tag/commit used to get data '
                        'from (e.g. LHCb/master)')
    parser.add_argument('path',
                        help='name of a file or directory to checkout from '
                        'the specified branch')

    parser.add_argument('-c', '--commit', action='store_true',
                        dest='do_commit',
                        help='commit immediately after checkout (default)')
    parser.add_argument('--no-commit', action='store_false',
                        dest='do_commit',
                        help='do not commit after checkout')

    parser.add_argument('-q', '--quiet', action='store_const',
                        dest='log_level', const=logging.WARNING,
                        help='be more quiet')
    parser.add_argument('-v', '--verbose', action='store_const',
                        dest='log_level', const=logging.DEBUG,
                        help='be more verbose')

    parser.set_defaults(log_level=logging.INFO,
                        do_commit=True)

    args = parser.parse_args()
    logging.basicConfig(level=args.log_level)

    # check that the commit-ish is valid
    proc = Popen(['git', 'rev-parse', '--verify', args.commit + '^{commit}'],
                 stdout=PIPE, stderr=PIPE)
    commit_id = proc.communicate()[0].strip()
    if proc.returncode:
        logging.error("invalid reference: %s", args.commit)
        logging.error("did you forget to call 'git lb-use'?")
        exit(1)

    if '/' in args.commit:
        remote = args.commit.split('/', 1)[0]
    else:  # find the remote containing the commit
        from itertools import chain
        # try with branches and tags
        remotes = chain(
            # try with branches
            (l.strip().split('/', 1)[0]
             for l in check_output(['git', 'branch', '--remotes',
                                     '--contains', args.commit]).splitlines()
             if '/' in l),
            # try with tags
            (l.strip().split('/', 1)[0]
             for l in check_output(['git', 'tag',
                                    '--contains', args.commit]).splitlines()
             if '/' in l),
        )
        try:
            remote = remotes.next()
        except StopIteration:
            logging.error('cannot find the remote repository containing %s',
                          args.commit)
            exit(1)

    try:
        # FIXME: we should allow only checkout of "packages"
        #        the list can be obtained with
        #          git ls-tree --name-only -r LHCb/master | sed -n 's@/CMakeLists.txt@@p'
        args.path = args.path.rstrip('/')
        check_call(['git', 'checkout', args.commit, '--', args.path])

        # get the qualified path (if checkout was called from a subdirectory)
        prefix = check_output(['git', 'rev-parse', '--show-prefix']).strip()
        full_path = prefix + args.path
        root = check_output(['git', 'rev-parse', '--show-toplevel']).strip()
        config_file = os.path.join(root, '.git-lb-checkout')

        check_call(['git', 'config', '-f', config_file,
                    'lb-checkout.{}.{}.base'.format(remote, full_path),
                    check_output(['git', 'rev-parse', 'HEAD']).strip()])
        check_call(['git', 'config', '-f', config_file,
                    'lb-checkout.{}.{}.imported'.format(remote, full_path),
                    commit_id])
        check_call(['git', 'add', config_file])

        if args.do_commit:
            check_call(['git', 'commit', '-m',
                        'added {path} from {remote} ({commit})'.format(
                            path=full_path, remote=remote, commit=args.commit
                        )])

        if os.path.exists(os.path.join(root, 'CMakeLists.txt')):
            # "touch" top CMakeLists.txt
            os.utime(os.path.join(root, 'CMakeLists.txt'), None)
    except CalledProcessError as err:
        logging.error('command failed: %s', err.cmd)
        exit(err.returncode)
