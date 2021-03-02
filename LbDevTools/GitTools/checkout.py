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
from __future__ import absolute_import
from __future__ import print_function

__author__ = "Marco Clemencic <marco.clemencic@cern.ch>"

import os
import git
import logging
from argparse import ArgumentParser
from difflib import get_close_matches
from LbDevTools.GitTools.common import (
    add_verbosity_argument,
    handle_verbosity_argument,
    add_version_argument,
)


def _checkout(repo, commit, remote, path, configfile):
    logging.debug("checking out %s", path)
    repo.git.checkout(commit, "--", path)

    with git.GitConfigParser(configfile, read_only=False) as conf:
        section = 'lb-checkout "{}.{}"'.format(remote, path)
        if not conf.has_section(section):
            conf.add_section(section)
        conf.set(section, "base", repo.commit("HEAD").hexsha)
        conf.set(section, "imported", repo.commit(commit).hexsha)


def get_packages_of(repo, commit):
    """
    Get packages of repo at certain commit. Packages contain either a CmakeLists.txt or a requirements file

    Args:
        repo (Repo): The repository in which we are searching for packages
        commit (String): The commit in which we are searching for packages

    Returns:
        a set of strings representing packages
    """
    cmakelist_packages = get_packages_that_contain("/CMakeLists.txt", repo, commit)
    requirements_packages = get_packages_that_contain("/requirements", repo, commit)
    # Packages that contain CMakeLists.txt files, have them at the top directory of the package
    # while requirements files are inside a cmt folder, therefore we need to go one level higher
    # so, we remove the '/cmt' from the end of the path
    requirements_packages = set(
        path.rsplit("/", 1)[0] for path in requirements_packages
    )

    return cmakelist_packages.union(requirements_packages)


def get_packages_that_contain(file_name, repo, commit):
    """
    Get packages of repo at certain commit that contain a certain file

    Args:
        file_name (String): The name of the file we are searching for
        repo (Repo): The repository in which we are searching for packages
        commit (String): The commit in which we are searching for packages

    Returns:
        a set of strings representing packages
    """
    return set(
        os.path.dirname(b.path)
        for b in repo.commit(commit).tree.traverse()
        if b.path.endswith(file_name)
    )


def main():
    """
    Implementation of `git lb-checkout` command.
    """

    parser = ArgumentParser(prog="git lb-checkout")
    add_version_argument(parser)

    parser.add_argument(
        "commit",
        metavar="branch",
        help="name of the branch/tag/commit used to get data "
        "from (e.g. LHCb/master)",
    )
    parser.add_argument(
        "path",
        nargs="?",
        help="name of a file or directory to checkout from " "the specified branch",
    )

    parser.add_argument(
        "-c",
        "--commit",
        action="store_true",
        dest="do_commit",
        help="commit immediately after checkout (default)",
    )
    parser.add_argument(
        "--no-commit",
        action="store_false",
        dest="do_commit",
        help="do not commit after checkout",
    )

    parser.add_argument(
        "-l",
        "--list",
        action="store_true",
        help="print the list of packages available from the " "requested branch",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="ignore check for valid subdirectories",
    )

    add_verbosity_argument(parser)

    parser.set_defaults(do_commit=True)

    args = parser.parse_args()
    handle_verbosity_argument(args)

    if bool(args.list) == bool(args.path):
        parser.error("one and only one of --list and path should be specified")

    try:
        repo = git.Repo(search_parent_directories=True)
    except git.InvalidGitRepositoryError:
        logging.error("current directory is not a Git repository")
        exit(1)

    # check that the commit-ish is valid
    try:
        repo.commit(args.commit)
    except git.BadName:
        logging.error("invalid reference: %s", args.commit)
        candidates = get_close_matches(
            args.commit,
            [
                r.name
                for r in repo.references
                if isinstance(r, (git.TagReference, git.RemoteReference))
            ],
        )
        if candidates:
            logging.error(
                "did you mean this?"
                if len(candidates) == 1
                else "did you mean one of these?"
            )
            [logging.error("    %s", c) for c in candidates]
        else:
            logging.error("did you forget to call 'git lb-use'?")
        exit(1)

    if "/" in args.commit:
        remote = args.commit.split("/", 1)[0]
    else:  # find the remote containing the commit
        from itertools import chain

        # try with branches and tags
        remotes = chain(
            # try with branches
            (
                l.strip().split("/", 1)[0]
                for l in repo.git.branch(
                    remotes=True, contains=args.commit
                ).splitlines()
                if "/" in l
            ),
            # try with tags
            (
                l.strip().split("/", 1)[0]
                for l in repo.git.tag(contains=args.commit).splitlines()
                if "/" in l
            ),
        )
        try:
            remote = next(remotes)
        except StopIteration:
            logging.error(
                "cannot find the remote repository containing %s", args.commit
            )
            exit(1)

    try:
        pkgs = get_packages_of(repo, args.commit)

        if args.list:
            print("\n".join(sorted(pkgs)))
            return

        # FIXME: this does not take into account multilevel hats
        hats = set(os.path.dirname(pkg) for pkg in pkgs)

        args.path = args.path.rstrip("/")

        # get the qualified path (if checkout was called from a subdirectory)
        full_path = os.path.relpath(
            os.path.join(os.getcwd(), args.path), repo.working_dir
        )

        if full_path in pkgs or args.force:
            paths = [full_path]
        elif full_path in hats:
            hat = full_path + "/"
            paths = [path for path in pkgs if path.startswith(hat)]
            paths.sort()
        else:
            paths = []

        if not paths:
            logging.error('"%s" is not a valid path', full_path)
            candidates = get_close_matches(full_path, list(pkgs) + list(hats))
            if candidates:
                logging.error(
                    "did you mean this?"
                    if len(candidates) == 1
                    else "did you mean one of these?"
                )
                [logging.error("    %s", c) for c in candidates]
            exit(1)

        configfile = os.path.join(repo.working_dir, ".git-lb-checkout")

        for path in paths:
            _checkout(repo, args.commit, remote, path, configfile)

        repo.index.add([configfile])

        top_cmake = os.path.join(repo.working_dir, "CMakeLists.txt")
        if os.path.exists(top_cmake):
            # try to add the added subdirectory to the list
            # - read the top CMakeLists.txt
            with open(top_cmake) as f:
                lines = f.readlines()
            # - look for the subdirectories markers
            start = end = -1
            for i, l in enumerate(lines):
                if start < 0 and "begin: list of subdirectories" in l:
                    start = i
                elif end < 0 and "end: list of subdirectories" in l:
                    end = i
            # - if we have something that make sense, we just add the
            #   required lines at the end (not trying to be too clever)
            if end > start:
                lines.insert(end, "    {}\n".format("\n    ".join(paths)))
                with open(top_cmake, "w") as f:
                    f.writelines(lines)
                repo.index.add([top_cmake])

        diffs = repo.head.commit.diff()

        if not diffs:
            logging.warning("no change")
            return

        if args.do_commit:
            if len(paths) == 1:
                msg = "added {path} from {remote} ({commit})".format(
                    path=paths[0], remote=remote, commit=args.commit
                )
            else:
                msg = "added from {remote} ({commit}):\n - {paths}".format(
                    remote=remote, commit=args.commit, paths="\n - ".join(paths)
                )
            repo.index.commit(msg)

        logging.info(
            "checked out %s from %s (%s)", ", ".join(paths), remote, args.commit
        )
        if args.log_level <= logging.DEBUG:
            [logging.debug(" %s  %s", d.change_type, d.b_path) for d in diffs]

        if os.path.exists(top_cmake):
            # "touch" top CMakeLists.txt to make sure we force a reconfigure
            os.utime(top_cmake, None)

    except Exception as err:
        logging.error("%s: %s", type(err).__name__, err)
        exit(1)
