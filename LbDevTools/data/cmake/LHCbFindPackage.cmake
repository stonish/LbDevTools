###############################################################################
# (c) Copyright 2021 CERN for the benefit of the LHCb Collaboration           #
#                                                                             #
# This software is distributed under the terms of the GNU General Public      #
# Licence version 3 (GPL Version 3), copied verbatim in the file "COPYING".   #
#                                                                             #
# In applying this licence, CERN does not waive the privileges and immunities #
# granted to it by virtue of its status as an Intergovernmental Organization  #
# or submit itself to any jurisdiction.                                       #
###############################################################################
#[========================================================================[.rst:
LHCbFindPackage
===============

This module provide the special :cmake:command:`lhcb_find_package` that
implements the special lookup policy required by LHCb deployment model.

#]========================================================================]

include_guard(GLOBAL) # Protect from multiple include (global scope, because
                      # everything defined in this file is globally visible)

#[========================================================================[.rst:
.. cmake:command:: lhcb_find_package

    .. code-block:: cmake

        lhcb_find_package(project ...)

    Special wrapper around :cmake:command:`find_package` allowing a
    project to be in the same *master project* as the required project and
    to extend the search to include projects deployed in directories like
    ``<PROJECT>/<PROJECT>_<VERSION>/InstalArea/<platform>``
    (i.e. following LHCb deployment policy).

    If the special variable :cmake:variable:`<Project>_EXACT_VERSION` is
    set to a version string, the search will be restricted to the the exact
    version. This is useful for the case where we need to pick up older
    versions of projects.
#]========================================================================]
macro(lhcb_find_package project)
    # check if we are in a master project and the project requested is available
    # from the master project
    if(CMAKE_SOURCE_DIR STREQUAL PROJECT_SOURCE_DIR
            OR NOT EXISTS "${CMAKE_SOURCE_DIR}/${project}/CMakeLists.txt")
        # otherwise we look for it
        unset(old_CMAKE_PREFIX_PATH)
        if(NOT ${project}_FOUND AND DEFINED LHCB_PLATFORM)
            # extend the normal search path if we have to look for the project
            # and we have an LHCB_PLATFORM to append to InstallArea
            string(TOUPPER "${project}" PROJECT)
            set(old_CMAKE_PREFIX_PATH ${CMAKE_PREFIX_PATH})
            file(TO_CMAKE_PATH "$ENV{CMAKE_PREFIX_PATH}" env_CMAKE_PREFIX_PATH)
            foreach(p IN LISTS old_CMAKE_PREFIX_PATH env_CMAKE_PREFIX_PATH)
                file(GLOB ps
                    "${p}/${project}/InstallArea/${LHCB_PLATFORM}"
                    "${p}/${project}_*/InstallArea/${LHCB_PLATFORM}"
                    "${p}/${PROJECT}/${PROJECT}_*/InstallArea/${LHCB_PLATFORM}"
                )
                if(ps)
                    list(SORT ps ORDER DESCENDING)
                    list(APPEND CMAKE_PREFIX_PATH ${ps})
                endif()
            endforeach()
        endif()
        set(_args ${ARGV})
        if(DEFINED ${project}_EXACT_VERSION)
            # Use the exact version requested for the project
            list(POP_FRONT _args)  # remove project name
            list(POP_FRONT _args _arg1)  # remove version (if any)
            if(NOT _arg1 MATCHES "^[0-9.]+$")
                # not a version, keep it
                list(INSERT _args 0 ${_arg1})
            endif()
            unset(_arg1)
            # add back the project name, version and require exact match
            list(INSERT _args 0 ${project} ${${project}_EXACT_VERSION} EXACT)
            message(STATUS "lhcb_find_package: forcing ${project} version to ${${project}_EXACT_VERSION}")
        endif()
        find_package(${_args})
        unset(_args)
        if(DEFINED ${project}_EXACT_VERSION AND ${project}_FOUND AND NOT ${project}_VERSION STREQUAL ${project}_EXACT_VERSION)
            message(FATAL_ERROR "Version mismatch: requested ${project}/${${project}_EXACT_VERSION} exact match but found ${${project}_VERSION}")
        endif()
        if(DEFINED old_CMAKE_PREFIX_PATH)
            set(CMAKE_PREFIX_PATH ${old_CMAKE_PREFIX_PATH})
        endif()
        unset(old_CMAKE_PREFIX_PATH)
    endif()
endmacro()
