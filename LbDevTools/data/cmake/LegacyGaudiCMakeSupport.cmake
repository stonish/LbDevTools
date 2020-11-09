###############################################################################
# (c) Copyright 2019-2020 CERN for the benefit of the LHCb Collaboration      #
#                                                                             #
# This software is distributed under the terms of the GNU General Public      #
# Licence version 3 (GPL Version 3), copied verbatim in the file "COPYING".   #
#                                                                             #
# In applying this licence, CERN does not waive the privileges and immunities #
# granted to it by virtue of its status as an Intergovernmental Organization  #
# or submit itself to any jurisdiction.                                       #
###############################################################################
########################################
# Old style config compatibility layer #
########################################
if(NOT BINARY_TAG AND NOT "$ENV{BINARY_TAG}" STREQUAL "")
  set(BINARY_TAG $ENV{BINARY_TAG})
endif()
string(REGEX REPLACE "^LCG_" "" heptools_version ${LCG_VERSION})

# When we use a platform like x86_64-centos7-gcc9+py3-opt we delegate from
# LCG_XY to LCG_XYpython3, so we have to drop the suffix, otherwise other
# projects may add it twice.
if(heptools_version MATCHES "python3$" AND BINARY_TAG MATCHES "\\+py3")
  string(REPLACE "python3" "" heptools_version ${heptools_version})
endif()

# variable to record the content of the metadata file
set(metadata)
# gather project infos
# - detect LCG and system (i.e. platform without opt level)
string(APPEND metadata "set(${PROJECT_NAME}_heptools_version ${heptools_version})\n")
string(APPEND metadata "set(${PROJECT_NAME}_heptools_system ${LCG_SYSTEM})\n")
# gather project infos
# - subdirectories
get_property(subdirs DIRECTORY PROPERTY SUBDIRECTORIES)
string(APPEND metadata "list(APPEND known_packages\n")
foreach(subdir IN LISTS subdirs)
  file(GLOB subdir RELATIVE ${CMAKE_SOURCE_DIR} ${subdir})
  string(APPEND metadata "     ${subdir}\n")
endforeach()
string(APPEND metadata ")\n")

file(WRITE ${CMAKE_BINARY_DIR}/.metadata.cmake "${metadata}")
install(FILES ${CMAKE_BINARY_DIR}/.metadata.cmake
        DESTINATION "lib/cmake/${PROJECT_NAME}")

# - dependencies
set(targets)
foreach(subdir IN LISTS subdirs)
  get_property(sub_targets DIRECTORY ${subdir} PROPERTY BUILDSYSTEM_TARGETS)
  list(APPEND targets ${sub_targets})
endforeach()
message(STATUS "targets:")
foreach(target IN LISTS targets)
  message(STATUS "- ${target}")
endforeach()


# Note: this is equivalent to the environment used at configure/build time,
#       derived from the toolchain (or the view), so it does not contain
#       the bare minimum of externals (it's a superset)
string(TOUPPER "${PROJECT_NAME}" PROJECT_NAME_UPCASE)
set(xenv_data
"<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<env:config xmlns:env=\"EnvSchema\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xsi:schemaLocation=\"EnvSchema EnvSchema.xsd \">
  <env:default variable=\"LCG_releases_base\">@LCG_releases_base@</env:default>
  <env:set variable=\"GAUDIAPPNAME\">${PROJECT_NAME}</env:set>
  <env:set variable=\"GAUDIAPPVERSION\">${PROJECT_VERSION}</env:set>
  <env:set variable=\"${PROJECT_NAME_UPCASE}_PROJECT_ROOT\">\${.}/../../</env:set>
  <env:prepend variable=\"PATH\">$ENV{PATH}</env:prepend>
  <env:prepend variable=\"PATH\">\${.}/bin</env:prepend>
  <env:prepend variable=\"LD_LIBRARY_PATH\">$ENV{LD_LIBRARY_PATH}</env:prepend>
  <env:prepend variable=\"LD_LIBRARY_PATH\">\${.}/lib</env:prepend>
  <env:prepend variable=\"PYTHONPATH\">$ENV{PYTHONPATH}</env:prepend>
  <env:prepend variable=\"PYTHONPATH\">\${.}/python</env:prepend>
  <env:set variable=\"PYTHONHOME\">$ENV{PYTHONHOME}</env:set>
  <env:prepend variable=\"ROOT_INCLUDE_PATH\">$ENV{ROOT_INCLUDE_PATH}</env:prepend>
  <env:prepend variable=\"ROOT_INCLUDE_PATH\">\${.}/include</env:prepend>
")

# special environment variables to be propagated for sanitizer builds
string(TOUPPER "${CMAKE_BUILD_TYPE}" _build_type_up)
if(_build_type_up MATCHES "^(A|L|T|UB)SAN$")
  string(TOLOWER "${CMAKE_BUILD_TYPE}" _sanitizer_name)
  string(APPEND xenv_data
"  <env:set variable=\"PRELOAD_SANITIZER_LIB\">lib${_sanitizer_name}.so</env:set>
  <env:set variable=\"${_build_type_up}_OPTIONS\">${SANITIZER_OPTIONS_${_build_type_up}}</env:set>
")
endif()

string(APPEND xenv_data "</env:config>\n")

string(REPLACE "${LCG_releases_base}" "\${LCG_releases_base}" xenv_data "${xenv_data}")
string(CONFIGURE "${xenv_data}" xenv_data @ONLY)
file(WRITE ${CMAKE_BINARY_DIR}/${PROJECT_NAME}.xenv "${xenv_data}")
install(FILES ${CMAKE_BINARY_DIR}/${PROJECT_NAME}.xenv DESTINATION .)

set(manifest_data
"<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<manifest>
  <project name=\"${PROJECT_NAME}\" version=\"${PROJECT_VERSION}\" />
  <heptools>
    <version>${heptools_version}</version>
    <binary_tag>${BINARY_TAG}</binary_tag>
    <lcg_platform>${LCG_PLATFORM}</lcg_platform>
    <lcg_system>${LCG_SYSTEM}</lcg_system>
    <packages>
")

get_property(packages_found GLOBAL PROPERTY PACKAGES_FOUND)
foreach(pack IN LISTS packages_found)
  string(APPEND manifest_data "      <package name=\"${pack}\" />\n")
endforeach()

string(APPEND manifest_data
"    </packages>
</heptools>
</manifest>
")

file(WRITE ${CMAKE_BINARY_DIR}/manifest.xml "${manifest_data}")
install(FILES ${CMAKE_BINARY_DIR}/manifest.xml DESTINATION .)

set(CMAKE_INSTALL_PREFIX ${CMAKE_SOURCE_DIR}/InstallArea/${BINARY_TAG})
