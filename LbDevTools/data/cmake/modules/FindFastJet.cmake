###############################################################################
# (c) Copyright 2000-2021 CERN for the benefit of the LHCb Collaboration      #
#                                                                             #
# This software is distributed under the terms of the GNU General Public      #
# Licence version 3 (GPL Version 3), copied verbatim in the file "COPYING".   #
#                                                                             #
# In applying this licence, CERN does not waive the privileges and immunities #
# granted to it by virtue of its status as an Intergovernmental Organization  #
# or submit itself to any jurisdiction.                                       #
###############################################################################
# - Locate FastJet library
# Defines:
#
#  FASTJET_FOUND
#  FASTJET_INCLUDE_DIR
#  FASTJET_INCLUDE_DIRS (not cached)
#  FASTJET_LIBRARY
#  FASTJET_LIBRARIES (not cached)
#  FASTJET_LIBRARY_DIRS (not cached)
#
# Imports:
#
#  FastJet::FastJet

find_path(FASTJET_INCLUDE_DIR fastjet/version.hh
          HINTS $ENV{FASTJET_ROOT_DIR}/include ${FASTJET_ROOT_DIR}/include)

find_library(FASTJET_LIBRARY NAMES fastjet
             HINTS $ENV{FASTJET_ROOT_DIR}/lib ${FASTJET_ROOT_DIR}/lib)

# handle the QUIETLY and REQUIRED arguments and set FASTJET_FOUND to TRUE if
# all listed variables are TRUE
INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(FastJet DEFAULT_MSG FASTJET_INCLUDE_DIR FASTJET_LIBRARY)

mark_as_advanced(FASTJET_FOUND FASTJET_INCLUDE_DIR FASTJET_LIBRARY)

set(FASTJET_INCLUDE_DIRS ${FASTJET_INCLUDE_DIR})
set(FASTJET_LIBRARIES ${FASTJET_LIBRARY})
get_filename_component(FASTJET_LIBRARY_DIRS ${FASTJET_LIBRARY} PATH)

if(TARGET FastJet::FastJet)
    return()
endif()
if(FastJet_FOUND)
  add_library(FastJet::FastJet IMPORTED INTERFACE)
  target_include_directories(FastJet::FastJet SYSTEM INTERFACE ${FastJet_INCLUDE_DIRS})
  target_link_libraries(FastJet::FastJet INTERFACE ${FastJet_LIBRARY})
endif()
