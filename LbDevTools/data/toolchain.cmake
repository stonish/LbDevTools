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

if(NOT DEFINED GAUDI_OLD_STYLE_PROJECT)
  file(STRINGS "${PROJECT_SOURCE_DIR}/CMakeLists.txt" _top_cmakelists)
  set(GAUDI_OLD_STYLE_PROJECT NO)
  foreach(_line IN LISTS _top_cmakelists)
    if(_line MATCHES "^[^#]*gaudi_project")
      set(GAUDI_OLD_STYLE_PROJECT YES)
      break()
    endif()
  endforeach()
  set(GAUDI_OLD_STYLE_PROJECT ${GAUDI_OLD_STYLE_PROJECT} CACHE BOOL "true if the top level CMakeLists file contains a call to gaudi_project")
endif()

if(NOT GAUDI_OLD_STYLE_PROJECT AND "$ENV{GAUDI_OLD_STYLE_PROJECT}" STREQUAL "")
  # for new style CMake projects, or vanilla CMake projects
  if("$ENV{BINARY_TAG}" STREQUAL "" OR "$ENV{LCG_VERSION}" STREQUAL "")
    message(FATAL_ERROR "The environment variables BINARY_TAG and LCG_VERSION mut be set for new style CMake projects")
  endif()
  find_file(LCG_TOOLCHAIN NAMES $ENV{BINARY_TAG}.cmake PATH_SUFFIXES lcg-toolchains/LCG_$ENV{LCG_VERSION})
  if(LCG_TOOLCHAIN)
    include(${LCG_TOOLCHAIN})
    # after including the toolchain, set some LHCb defaults
    find_program(CCACHE_COMMAND NAMES ccache)
    if(CCACHE_COMMAND)
      set(CMAKE_C_COMPILER_LAUNCHER "${CCACHE_COMMAND}" CACHE PATH "...")
      set(CMAKE_CXX_COMPILER_LAUNCHER "${CCACHE_COMMAND}" CACHE PATH "...")
    endif()
    if(NOT DEFINED GAUDI_USE_INTELAMPLIFIER)
      set(GAUDI_USE_INTELAMPLIFIER "YES" CACHE BOOL "...")
    endif()
    if(NOT DEFINED GAUDI_LEGACY_CMAKE_SUPPORT)
      set(GAUDI_LEGACY_CMAKE_SUPPORT "YES" CACHE BOOL "...")
    endif()
    if(NOT DEFINED CMAKE_INSTALL_PREFIX OR CMAKE_INSTALL_PREFIX_INITIALIZED_TO_DEFAULT)
      set(CMAKE_INSTALL_PREFIX "${PROJECT_SOURCE_DIR}/InstallArea/$ENV{BINARY_TAG}" CACHE BOOL "...")
    endif()
  else()
    message(FATAL_ERROR "Cannot find LCG $ENV{LCG_VERSION} $ENV{BINARY_TAG} toolchain")
  endif()
else()

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

  # Make sure that when the toolchain is invoked again it uses this branch
  set(ENV{GAUDI_OLD_STYLE_PROJECT} "${CMAKE_SOURCE_DIR}")
endif()
endif()
