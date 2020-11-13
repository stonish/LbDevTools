###############################################################################
# (c) Copyright 2020 CERN for the benefit of the LHCb Collaboration           #
#                                                                             #
# This software is distributed under the terms of the GNU General Public      #
# Licence version 3 (GPL Version 3), copied verbatim in the file "COPYING".   #
#                                                                             #
# In applying this licence, CERN does not waive the privileges and immunities #
# granted to it by virtue of its status as an Intergovernmental Organization  #
# or submit itself to any jurisdiction.                                       #
###############################################################################
#
# Reset the modification times of the files in a git repo to the
# last commit affecting them.
#

import argparse
import os
import sys
import time
from git import Repo


def build_file_list(rootdir, fileset):
    """ Build the list of files in the repo """
    for subdir, dirs, files in os.walk(rootdir):
        reldir = subdir
        for file in files:
            if subdir.startswith(rootdir):
                reldir = subdir[len(rootdir) :]
            fileset.add(os.path.join(reldir, file).lstrip(os.sep))
        dirs[:] = [d for d in dirs if d != ".git"]


def main():

    parser = argparse.ArgumentParser(
        description="Reset the files modification time based on git commits"
    )
    parser.add_argument(
        "repopath", metavar="repository_path", type=str, help="The git repo to process"
    )
    args = parser.parse_args()

    # Created the Repo and collect the list of files in the workdir
    with Repo(args.repopath) as repo:
        if repo.is_dirty():
            raise RuntimeError(
                "Can only reset times on repositories when no files have been modified"
            )
        fileset = set()
        build_file_list(repo.working_dir, fileset)

        # Now iterating on commits to set the file modification date
        # We use the statistics available with each commit to know whether they have been
        # modified in that commit (this is easier that doing the diffs between the commit tree
        # and the one for the previous commit)
        for commit in list(repo.iter_commits()):
            if len(fileset) == 0:
                # we're done, all file mtimes have been set
                break

            for f in commit.stats.files:
                if f in fileset:
                    mtime = commit.committed_date
                    fullpath = os.path.join(repo.working_dir, f)
                    os.utime(fullpath, times=(mtime, mtime))
                    fileset.remove(f)


if __name__ == "__main__":
    main()
