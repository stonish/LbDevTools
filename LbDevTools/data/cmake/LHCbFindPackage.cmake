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

include_guard(GLOBAL) # Protect from multiple include (global scope, because
                      # everything defined in this file is globally visible)

#[========================================================================[.rst:
.. code-block:: cmake

  lhcb_find_package(project ...)

Special wrapper around ``find_package`` allowing a project to be in the same
*master project* and to extend the search to include projects deployed in
directories like ``<PROJECT>/<PROJECT>_<VERSION>/InstalArea/<platform>``.
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
                file(GLOB ps "${p}/${PROJECT}/${PROJECT}_*/InstallArea/${LHCB_PLATFORM}")
                list(SORT ps ORDER DESCENDING)
                list(APPEND CMAKE_PREFIX_PATH ${ps})
            endforeach()
        endif()
        find_package(${ARGV})
        if(DEFINED old_CMAKE_PREFIX_PATH)
            set(CMAKE_PREFIX_PATH ${old_CMAKE_PREFIX_PATH})
        endif()
        unset(old_CMAKE_PREFIX_PATH)
    endif()
endmacro()
