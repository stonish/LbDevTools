#!/bin/bash
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
#
# Simple script to update the copy of the CMake support modules from Gaudi.
#

git_url=https://gitlab.cern.ch/gaudi/Gaudi.git

# Check if we have all the commands we need.
for c in git ; do
    if which $c >/dev/null 2>&1 ; then
        # good
        true
    else
        echo "Cannot find required command '$c'."
        exit 1
    fi
done

# Find ourselves (for the destination location)
rootdir=$(cd $(dirname $0); pwd)
datadir=${rootdir}/LbDevTools/data

# Branch to use.
if [ -n "$1" ] ; then
    remote_id=$1
else
    remote_id=master
fi

notes_file=$rootdir/cmake_modules.notes

echo "Clean destination directory"
git rm -rf $datadir/cmake
git reset HEAD $datadir/cmake/GangaTools.cmake
git checkout $datadir/cmake/GangaTools.cmake

echo "Importing the files from ${remote_id}"
git clone --mirror $git_url gaudi_tmp
(
    cd gaudi_tmp
    git archive ${remote_id} cmake | \
        tar -x -v -C $datadir -f -

    git archive ${remote_id} Makefile | \
        tar -x -v -C $datadir --transform 's/$/-cmake.mk/' -f -

    git archive ${remote_id} GaudiPolicy/scripts/quick-merge | \
        tar -x -v -C $datadir --transform 's@GaudiPolicy/scripts@cmake@' -f -
    # just to make sure the directory GaudiPolicy is not kept by mistake
    rm -rf $datadir/GaudiPolicy

)
revision=$(cd gaudi_tmp && git describe --tags --match 'v*')
rm -rf gaudi_tmp

git add $datadir/cmake $datadir/Makefile-cmake.mk
git commit -m "Updated CMake support modules from Gaudi ${revision}" $datadir/cmake $datadir/Makefile-cmake.mk
