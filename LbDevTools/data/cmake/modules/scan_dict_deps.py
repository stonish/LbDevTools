#!/usr/bin/env python
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
from __future__ import print_function
from __future__ import absolute_import
import re

from os.path import join, exists, isabs


def find_file(filename, searchpath):
    """
    Return the absolute path to filename in the searchpath.

    If filename is already an absolute path, return it as is, if it exists.

    If filename cannot be found, return None.
    """
    if isabs(filename):
        return filename if exists(filename) else None
    try:
        return next(f for f in [join(d, filename) for d in searchpath] if exists(f))
    except StopIteration:
        return None


def find_deps(filename, searchpath, deps=None):
    """
    Return a set with the absolute paths to the files included (directly and
    indirectly) by filename.
    """
    if deps is None:
        deps = set()
    old_deps = set(deps)

    filename = find_file(filename, searchpath)
    if not filename:
        # ignore missing files (useful for generated .h files)
        return deps

    # Look for all "#include" lines in the file, then consider each of the
    # included files, ignoring those already included in the recursion
    INCLUDE_RE = re.compile(r'^\s*#\s*include\s*["<]([^">]*)[">]')
    deps.update(
        f
        for f in (
            find_file(m.group(1), searchpath)
            for m in (INCLUDE_RE.match(l) for l in open(filename))
            if m
        )
        if f
    )
    for included in deps - old_deps:
        find_deps(included, searchpath, deps)

    return deps


def main():
    from optparse import OptionParser

    parser = OptionParser(usage="%prog [options] output_file variable_name headers...")
    parser.add_option("-I", action="append", dest="include_dirs")
    parser.add_option(
        "-M",
        "--for-make",
        action="store_true",
        help="generate Makefile like dependencies (as with gcc "
        '-MD) in which case "variable_name" is the name of the '
        "target",
    )

    opts, args = parser.parse_args()
    if len(args) < 2:
        parser.error("you must specify output file and variable name")

    output, variable = args[:2]
    headers = args[2:]

    old_deps = open(output).read() if exists(output) else None

    # scan for dependencies
    deps = set()
    for filename in headers:
        find_deps(filename, opts.include_dirs, deps)
    deps = sorted(deps)

    # prepare content of output file
    if opts.for_make:
        new_deps = "{target}: {deps}\n".format(target=variable, deps=" ".join(deps))
    else:
        new_deps = "set({deps_var}\n    {deps})\n".format(
            deps="\n    ".join(deps), deps_var=variable
        )

    if new_deps != old_deps:  # write it only if it has changed
        open(output, "w").write(new_deps)
        if old_deps and not opts.for_make:
            print("info: dependencies changed: next build will trigger a reconfigure")


if __name__ == "__main__":  # pragma no cover
    main()
