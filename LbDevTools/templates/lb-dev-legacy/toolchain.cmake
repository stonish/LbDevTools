cmake_minimum_required(VERSION 3.6)

# Use lb-dev command line search path, if defined.
if(EXISTS $${CMAKE_CURRENT_SOURCE_DIR}/searchPath.cmake)
  include($${CMAKE_CURRENT_SOURCE_DIR}/searchPath.cmake)
endif()

if(CMAKE_PREFIX_PATH)
  list(REMOVE_DUPLICATES CMAKE_PREFIX_PATH)
endif()

# this check is needed because the toolchain is called when checking the
# compiler (without the proper cache)
if(NOT CMAKE_SOURCE_DIR MATCHES "CMakeTmp")
  find_path(gaudi_cmake_modules NAMES GaudiToolchainMacros.cmake
            HINTS ${datadir}/cmake)
  if(NOT gaudi_cmake_modules)
    message(FATAL_ERROR "Cannot find GaudiToolchainMacros.cmake")
  endif()

  # find the projects we use
  set(CMAKE_MODULE_PATH $${gaudi_cmake_modules} $${CMAKE_MODULE_PATH})
  include(GaudiToolchainMacros)
  init()
  find_projects(projects tools $${CMAKE_SOURCE_DIR}/CMakeLists.txt)

  # Use the toolchain used by the project we derive from
  list(GET projects 1 first_used_project)

  if(first_used_project STREQUAL "GAUDI" 
     OR NOT EXISTS $${$${first_used_project}_ROOT_DIR}/toolchain.cmake)
    # special case for Gaudi and projects without a specific toolchain
    include(${datadir}/toolchain.cmake)
  else()
    # special case for Gauss (needs a fix in Gauss toolchain.cmake)
    if(EXISTS $${$${first_used_project}_ROOT_DIR}/generators_versions.txt)
      file(READ $${$${first_used_project}_ROOT_DIR}/generators_versions.txt generators_versions)
      string(REGEX REPLACE "[ \t\n]+" ";" generators_versions "$${generators_versions}")
      set(generators_versions $${generators_versions})
    endif()

    set(ENV{LBUTILSROOT} ${datadir}/..)
    message(STATUS "Using toolchain from $${$${first_used_project}_ROOT_DIR}")
    include($${$${first_used_project}_ROOT_DIR}/toolchain.cmake)
  endif()

  # FIXME: make sure we do not pick up unwanted/problematic projects from LCG
  if(CMAKE_PREFIX_PATH)
    # - ninja (it requires LD_LIBRARY_PATH set to run)
    # - Gaudi (we do not want to use it from LCG)
    list(FILTER CMAKE_PREFIX_PATH EXCLUDE REGEX "(LCG_|lcg/nightlies).*(ninja|Gaudi)")
  endif()
endif()
