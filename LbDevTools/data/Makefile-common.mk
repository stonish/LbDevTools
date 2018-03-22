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

ifeq ($(wildcard cmt/project.cmt),)
# we cannot use the CMT version if we do not have a cmt/project.cmt
override USE_CMT =
else
ifeq ($(wildcard CMakeLists.txt),)
# if we have a cmt/project.cmt, but not a CMakeLists.txt, force use CMT
override USE_CMT = 1
endif
endif

ifeq ($(USE_CMT),)
include $(DEVTOOLS_DATADIR)/Makefile-cmake.mk
else
include $(DEVTOOLS_DATADIR)/Makefile-cmt.mk
endif
