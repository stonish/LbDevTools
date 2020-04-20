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
cmake_minimum_required(VERSION 3.6)

# this check is needed because the toolchain is called when checking the
# compiler (without the proper cache)
if(NOT CMAKE_SOURCE_DIR MATCHES "CMakeTmp")

  find_file(default_toolchain NAMES GaudiDefaultToolchain.cmake
            HINTS ${CMAKE_SOURCE_DIR}/cmake
                  ${CMAKE_CURRENT_LIST_DIR}/cmake)
  if(default_toolchain)
    include(${default_toolchain})
    if(NOT DEFINED CMAKE_USE_CCACHE)
      set(CMAKE_USE_CCACHE "YES" CACHE BOOL "...")
    endif()
  else()
    message(FATAL_ERROR "Cannot find GaudiDefaultToolchain.cmake")
  endif()

  # FIXME: make sure we do not pick up unwanted/problematic projects from LCG
  if(CMAKE_PREFIX_PATH)
    # - ninja (it requires LD_LIBRARY_PATH set to run)
    # - Gaudi (we do not want to use it from LCG)
    # - xenv (conflicts with the version in the build environment)
    list(FILTER CMAKE_PREFIX_PATH EXCLUDE REGEX "(LCG_|lcg/nightlies).*(ninja|Gaudi|xenv)")
  endif()
endif()
