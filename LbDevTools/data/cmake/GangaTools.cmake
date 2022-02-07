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

#.rst
# GangaTools
# ----------
#
# Define functions to enable integration of a project with Ganga.
#

CMAKE_MINIMUM_REQUIRED(VERSION 3.0.0)

set(GANGA_BINARY_DIR ${CMAKE_BINARY_DIR}/ganga
    CACHE PATH "Working directory for building project distribution kit for Ganga.")
set(GANGA_INPUT_SANDBOX_FILE ${GANGA_BINARY_DIR}/input-sandbox.tgz
    CACHE FILEPATH "Filename for Ganga input sandbox file.")
mark_as_advanced(GANGA_BINARY_DIR GANGA_INPUT_SANDBOX_FILE)

function(ganga_create_job_runner)
  file(MAKE_DIRECTORY ${GANGA_BINARY_DIR})

  # scan build.conf (if present) and prepare the corresponding options for lb-run
  if(EXISTS ${CMAKE_SOURCE_DIR}/build.conf)
    file(STRINGS ${CMAKE_SOURCE_DIR}/build.conf build_conf_lines)
    foreach(l ${build_conf_lines})
      if(l MATCHES "nightly_base=.+")
        string(REPLACE "nightly_base=" "--nightly-base " nightly_base_opt "${l}")
      elseif(l MATCHES "nightly_day=.+")
        string(REPLACE "nightly_day=" "" nightly_day "${l}")
      elseif(l MATCHES "nightly_slot=.+")
        string(REPLACE "nightly_slot=" "--nightly " nightly_slot_opt "${l}")
      endif()
    endforeach()
    if(nightly_slot_opt AND nightly_day)
      set(nightly_slot_opt "${nightly_slot_opt} ${nightly_day}")
    endif()
  endif()

  if(ENV{MYSITEROOT} STREQUAL "")
    set(default_siteroot /cvmfs/lhcb.cern.ch/lib)
  else()
    set(default_siteroot $ENV{MYSITEROOT})
  endif()
  file(WRITE ${GANGA_BINARY_DIR}/run
       "#!/bin/sh
base_dir=\$(cd \$(dirname \$0) && pwd)
exec lb-run ${nightly_base_opt} ${nightly_slot_opt} --siteroot=\${MYSITEROOT:-${default_siteroot}} -c ${BINARY_TAG} --path-to-project \${base_dir}/${CMAKE_PROJECT_NAME}_${CMAKE_PROJECT_VERSION} \"$@\"
")
  if(UNIX)
    execute_process(COMMAND chmod 755 ${GANGA_BINARY_DIR}/run)
  endif()
endfunction()

function(ganga_input_sandbox)
  set(dist_base_dir ${GANGA_BINARY_DIR}/${CMAKE_PROJECT_NAME}_${CMAKE_PROJECT_VERSION})

  if(TARGET post-install)
    # only old-style CMake projects have a post-install target
    set(POST_INSTALL_COMMANDS
      COMMAND mkdir -p ${CMAKE_INSTALL_PREFIX}/python
      COMMAND ${CMAKE_MAKE_PROGRAM} post-install
    )
  else()
    set(POST_INSTALL_COMMANDS)
  endif()
  add_custom_target(ganga-clean-install
                    COMMAND rm -r -f ${CMAKE_INSTALL_PREFIX}
                    COMMAND ${CMAKE_MAKE_PROGRAM} install
                    ${POST_INSTALL_COMMANDS}
                    COMMENT "Preparing InstallArea for input sandbox")

  set(copy_sources)
  foreach(src CMakeLists.txt cmt ${packages})
    if(EXISTS ${CMAKE_SOURCE_DIR}/${src})
      if(IS_DIRECTORY ${CMAKE_SOURCE_DIR}/${src})
        set(copy_sources ${copy_sources}
            COMMAND mkdir -p ${dist_base_dir}/${src}
            COMMAND cp -a ${src}/. ${dist_base_dir}/${src}/.)
      else()
        set(copy_sources ${copy_sources}
            COMMAND cp -a ${src} ${dist_base_dir}/${src})
      endif()
    endif()
  endforeach()
  add_custom_target(ganga-dist-prepare
                    COMMAND rm -r -f ${dist_base_dir}
                    COMMAND mkdir -p ${dist_base_dir}/InstallArea/${BINARY_TAG}
                    ${copy_sources}
                    COMMAND cp -a InstallArea/${BINARY_TAG}/. ${dist_base_dir}/InstallArea/${BINARY_TAG}/.
                    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
                    DEPENDS ganga-clean-install)

  add_custom_target(ganga-input-sandbox
                    COMMAND rm -f ${GANGA_INPUT_SANDBOX_FILE}
                    COMMAND tar -c -z -f ${GANGA_INPUT_SANDBOX_FILE}
                            run ${CMAKE_PROJECT_NAME}_${CMAKE_PROJECT_VERSION}
                    WORKING_DIRECTORY ${GANGA_BINARY_DIR}
                    DEPENDS ganga-dist-prepare
                    COMMENT "Preparing input sandbox tarball")
endfunction()

function(enable_ganga_integration)
  if("${CMAKE_INSTALL_PREFIX}" STREQUAL "${CMAKE_SOURCE_DIR}/InstallArea/${BINARY_TAG}")
    ganga_create_job_runner()
    ganga_input_sandbox()
  else()
    message(WARNING "ganga-input-sandbox is not supported for non standard installation")
  endif()
endfunction()
