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
from subprocess import (check_call, check_output, CalledProcessError,
                        Popen, PIPE)
from argparse import ArgumentParser


def main():
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
