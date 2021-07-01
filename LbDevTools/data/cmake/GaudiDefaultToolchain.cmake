set(CMAKE_MODULE_PATH ${CMAKE_CURRENT_LIST_DIR} ${CMAKE_MODULE_PATH})

include(GaudiToolchainMacros)

init()
find_projects(projects tools ${CMAKE_SOURCE_DIR}/CMakeLists.txt)
# look for GaudiProjectConfig.cmake in upstream projects, CMAKE_PREFIX_PATH and here
set(_GaudiProjectSearchPath)
foreach(_p IN LISTS projects)
  if(${_p}_ROOT_DIR)
    if(NOT ${_p}_ROOT_DIR STREQUAL CMAKE_SOURCE_DIR)
      list(APPEND _GaudiProjectSearchPath ${${_p}_ROOT_DIR}/InstallArea/${BINARY_TAG}/cmake)
    endif()
    list(APPEND _GaudiProjectSearchPath ${${_p}_ROOT_DIR}/cmake)
  endif()
endforeach()
list(APPEND _GaudiProjectSearchPath ${CMAKE_PREFIX_PATH})
find_path(GaudiProject_DIR NAMES GaudiProjectConfig.cmake
          NO_PACKAGE_ROOT_PATH NO_CMAKE_PATH NO_CMAKE_ENVIRONMENT_PATH NO_SYSTEM_ENVIRONMENT_PATH
          HINTS ${_GaudiProjectSearchPath} ${CMAKE_CURRENT_LIST_DIR})
if(GaudiProject_DIR)
  message(STATUS "Found GaudiProjectConfig.cmake in ${GaudiProject_DIR}")
else()
  message(STATUS "GaudiProjectConfig.cmake not found")
endif()

if(heptools_version)
  include(UseHEPTools)
  use_heptools(${heptools_version})
else()
  include(InheritHEPTools)
  inherit_heptools()
endif()

set_paths_from_projects(${tools} ${projects})

# LHCB_PLATFORM is used in LHCbFindPackage.cmake instead of BINARY_TAG
if(NOT DEFINED LHCB_PLATFORM)
  set(LHCB_PLATFORM "${BINARY_TAG}")
endif()

# set legacy variables for backward compatibility
if(NOT EXISTS "${GaudiProject_DIR}/BinaryTagUtils.cmake")
  # with newer versions of Gaudi these variables are set after the toolchain,
  # but we have to set them here for old versions

  # if we actually found an LCG info file, we use the informations from there
  if(LCG_TOOLCHAIN_INFO)
    string(REGEX MATCH ".*/LCG_externals_(.+)\\.txt" out "${LCG_TOOLCHAIN_INFO}")
    set(LCG_platform ${CMAKE_MATCH_1})

    # set LCG_ARCH, LCG_COMP and LCG_TYPE
    parse_binary_tag(LCG "${CMAKE_MATCH_1}")

    set(LCG_HOST_ARCH "${CMAKE_HOST_SYSTEM_PROCESSOR}")
    set(LCG_SYSTEM ${LCG_ARCH}-${LCG_OS}-${LCG_COMP})
    set(LCG_system ${LCG_SYSTEM}-opt)
    set(LCG_BUILD_TYPE ${LCG_TYPE})

    # match old-style LCG_COMP value
    set(LCG_COMP "${BINARY_TAG_COMP_NAME}")
    string(REPLACE "." "" LCG_COMPVERS "${BINARY_TAG_COMP_VERSION}")

    # Convert LCG_BUILD_TYPE to CMAKE_BUILD_TYPE
    if(LCG_BUILD_TYPE STREQUAL "opt")
      set(type Release)
    elseif(LCG_BUILD_TYPE STREQUAL "dbg")
      set(type Debug)
    elseif(LCG_BUILD_TYPE STREQUAL "cov")
      set(type Coverage)
    elseif(LCG_BUILD_TYPE STREQUAL "pro")
      set(type Profile)
    else()
      message(FATAL_ERROR "LCG build type ${type} not supported.")
    endif()
    set(CMAKE_BUILD_TYPE ${type} CACHE STRING
        "Choose the type of build, options are: empty, Debug, Release, Coverage, Profile, RelWithDebInfo, MinSizeRel.")
  endif()
elseif(EXISTS "${GaudiProject_DIR}/../GaudiConfig.cmake")
  # Special workaround for Gaudi v28r2
  file(READ "${GaudiProject_DIR}/../GaudiConfig.cmake" out)
  if(out MATCHES "Gaudi_VERSION v28r2")
    string(REGEX MATCH ".*/LCG_externals_(.+)\\.txt" out "${LCG_TOOLCHAIN_INFO}")
    set(LCG_platform ${CMAKE_MATCH_1}
        CACHE STRING "Platform ID for the AA project binaries.")
  endif()
endif()
