#!/usr/bin/env python
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
import os


def createProjectMakefile(dest, overwrite=False):
    '''Write the generic Makefile for CMT projects.
    @param dest: the name of the destination file
    @param overwrite: flag to decide if an already present file has to be kept
                      or not (default is False)
    '''
    import logging
    if overwrite or not os.path.exists(dest):
        logging.debug("Creating '%s'", dest)
        with open(dest, "w") as f:
            f.write("include ${LBCONFIGURATIONROOT}/data/Makefile\n")
        return True
    return False


def createToolchainFile(dest, overwrite=False):
    '''Write the generic toolchain.cmake file needed by CMake-based projects.
    @param dest: destination filename
    @param overwrite: flag to decide if an already present file has to be kept
                      or not (default is False)
    '''
    import logging
    if overwrite or not os.path.exists(dest):
        logging.debug("Creating '%s'", dest)
        with open(dest, "w") as f:
            f.write("include($ENV{LBUTILSROOT}/data/toolchain.cmake)\n")
        return True
    return False


def createGitIgnore(dest, overwrite=False, extra=None, selfignore=True):
    '''Write a generic .gitignore file, useful for git repositories.
    @param dest: destination filename
    @param overwrite: flag to decide if an already present file has to be kept
                      or not (default is False)
    @param extra: list of extra patterns to add
    @param selfignore: if the .gitignore should include itself
    '''
    import logging
    if overwrite or not os.path.exists(dest):
        logging.debug("Creating '%s'", dest)
        patterns = ['/InstallArea/', '/build.*/', '*.pyc', '*~', '.*.swp']
        if selfignore:
            patterns.insert(0, '/.gitignore')  # I like it as first entry
        if extra:
            patterns.extend(extra)

        with open(dest, "w") as f:
            f.write('\n'.join(patterns))
            f.write('\n')
        return True
    return False


def initProject(path, overwrite=False):
    '''
    Initialize the sources for an LHCb project for building.

    Create the (generic) special files required for building LHCb/Gaudi
    projects.

    @param path: path to the root directory of the project
    @param overwrite: whether existing files should be overwritten, set it to
                      True to overwrite all of them or to a list of filenames
    '''
    extraignore = []
    factories = [
        ('Makefile', createProjectMakefile),
        ('toolchain.cmake', createToolchainFile),
        ('.gitignore',
         lambda dest, overwrite: createGitIgnore(dest, overwrite, extraignore)
         ),
    ]

    # handle the possible values of overwrite to always have a set of names
    if overwrite in (False, None):
        overwrite = set()
    elif overwrite is True:
        overwrite = set(f[0] for f in factories)
    elif isinstance(overwrite, basestring):
        overwrite = set([overwrite])
    else:
        overwrite = set(overwrite)

    for filename, factory in factories:
        if factory(
                os.path.join(path, filename), overwrite=filename in overwrite):
            extraignore.append('/' + filename)
