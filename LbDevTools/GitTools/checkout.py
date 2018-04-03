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
import git
import logging
from argparse import ArgumentParser
from LbDevTools.GitTools.common import (add_verbosity_argument,
                                        handle_verbosity_argument,
                                        add_version_argument)


def main():
    '''
    Implementation of `git lb-checkout` command.
    '''

    parser = ArgumentParser(prog='git lb-checkout')
    add_version_argument(parser)

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

    add_verbosity_argument(parser)

    parser.set_defaults(do_commit=True)

    args = parser.parse_args()
    handle_verbosity_argument(args)

    try:
        repo = git.Repo(search_parent_directories=True)
    except git.InvalidGitRepositoryError:
        logging.error('current directory is not a Git repository')
        exit(1)

    # check that the commit-ish is valid
    try:
        commit = repo.commit(args.commit)
    except git.BadName:
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
             for l in repo.git.branch(remotes=True,
                                      contains=args.commit).splitlines()
             if '/' in l),
            # try with tags
            (l.strip().split('/', 1)[0]
             for l in repo.git.tag(contains=args.commit).splitlines()
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

        # get the qualified path (if checkout was called from a subdirectory)
        full_path = os.path.relpath(os.path.join(os.getcwd(), args.path),
                                    repo.working_dir)
        repo.git.checkout(args.commit, '--', full_path)

        configfile = os.path.join(repo.working_dir, '.git-lb-checkout')

        with git.GitConfigParser(configfile, read_only=False) as conf:
            section = 'lb-checkout "{}.{}"'.format(remote, full_path)
            if not conf.has_section(section):
                conf.add_section(section)
            conf.set(section, 'base', repo.commit('HEAD').hexsha)
            conf.set(section, 'imported', commit.hexsha)

        repo.index.add([configfile])
        diffs = repo.head.commit.diff()

        if not diffs:
            logging.warning('no change')
            return

        if args.do_commit:
            repo.index.commit('added {path} from {remote} ({commit})'.format(
                path=full_path, remote=remote, commit=args.commit
            ))

        logging.info('checked out %s from %s (%s)',
                     full_path, remote, args.commit)
        if args.log_level <= logging.DEBUG:
            [logging.debug(' %s  %s', d.change_type, d.b_path) for d in diffs]

        if os.path.exists(os.path.join(repo.working_dir, 'CMakeLists.txt')):
            # "touch" top CMakeLists.txt
            os.utime(os.path.join(repo.working_dir, 'CMakeLists.txt'), None)

    except Exception as err:
        logging.error('%s: %s', type(err).__name__, err)
        exit(1)
