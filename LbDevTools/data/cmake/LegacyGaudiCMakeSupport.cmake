###############################################################################
# (c) Copyright 2019-2021 CERN for the benefit of the LHCb Collaboration      #
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
# make sure we have a BINARY_TAG CMake variable set
if(NOT BINARY_TAG AND NOT "$ENV{BINARY_TAG}" STREQUAL "")
  set(BINARY_TAG $ENV{BINARY_TAG})
endif()

# map LCG_VERSION to heptools_version
# (LCG_VERSION value may contain the "LCG_" prefix)
string(REGEX REPLACE "^LCG_" "" heptools_version ${LCG_VERSION})

# get an uppercase version of the CMAKE_BUILD_TYPE
# (useful later to inspect build-type specific properties)
string(TOUPPER "${CMAKE_BUILD_TYPE}" _build_type_upcase)

# When we use a platform like x86_64-centos7-gcc9+py3-opt we delegate from
# LCG_XY to LCG_XYpython3, so we have to drop the suffix, otherwise other
# projects may add it twice.
if(heptools_version MATCHES "python3$" AND BINARY_TAG MATCHES "\\+py3")
  string(REPLACE "python3" "" heptools_version ${heptools_version})
endif()
if(heptools_version MATCHES "python2$" AND BINARY_TAG MATCHES "\\+py2")
  string(REPLACE "python2" "" heptools_version ${heptools_version})
endif()

# gather project info
# - find subdirectories
get_property(subdirs DIRECTORY PROPERTY SUBDIRECTORIES)
# - found packages
get_property(packages_found GLOBAL PROPERTY PACKAGES_FOUND)
# - targets
get_property(targets DIRECTORY ${CMAKE_SOURCE_DIR} PROPERTY BUILDSYSTEM_TARGETS)
foreach(subdir IN LISTS subdirs)
  get_property(sub_targets DIRECTORY ${subdir} PROPERTY BUILDSYSTEM_TARGETS)
  list(APPEND targets ${sub_targets})
endforeach()
#   (ignore CTest special targets)
list(FILTER targets EXCLUDE REGEX "^(Experimental|Nightly|Continuous)")
# - external libraries
set(ext_libraries)
foreach(target IN LISTS targets)
  get_target_property(_tgt_type ${target} TYPE)
  if(NOT _tgt_type STREQUAL "INTERFACE_LIBRARY")
    get_target_property(_libs ${target} LINK_LIBRARIES)
    list(APPEND ext_libraries ${_libs})
  endif()
endforeach()
list(REMOVE_DUPLICATES ext_libraries)
#   (ignore local targets in external libraries)
list(REMOVE_ITEM ext_libraries ${targets})


# generate metadata file
# - variable to record the content of the metadata content
set(metadata)
# - record LCG and system (i.e. platform without opt level)
string(APPEND metadata "set(${PROJECT_NAME}_heptools_version ${heptools_version})\n")
string(APPEND metadata "set(${PROJECT_NAME}_heptools_system ${LCG_SYSTEM})\n")
# - list subdirectories
string(APPEND metadata "list(APPEND known_packages\n")
foreach(subdir IN LISTS subdirs)
  file(GLOB subdir RELATIVE ${CMAKE_SOURCE_DIR} ${subdir})
  string(APPEND metadata "     ${subdir}\n")
endforeach()
string(APPEND metadata ")\n")
# - write metadata file and schedule install
file(WRITE ${CMAKE_BINARY_DIR}/.metadata.cmake "${metadata}")
install(FILES ${CMAKE_BINARY_DIR}/.metadata.cmake
        DESTINATION "lib/cmake/${PROJECT_NAME}")

# update LD_LIBRARY_PATH for extenal libraries not in the toolchain
file(TO_CMAKE_PATH "$ENV{LD_LIBRARY_PATH}" _lib_dirs)
foreach(_lib IN LISTS ext_libraries)
  set(_lib_file)
  if(TARGET "${_lib}")
    get_target_property(_tgt_type ${_lib} TYPE)
    if(NOT _tgt_type STREQUAL "SHARED_LIBRARY")
      continue() # we only consider shared libraries for LD_LIBRARY_PATH
    endif()
    # scan target for all IMPORTED_LOCATION variants
    # (stop at the first found, starting by the current CMAKE_BUILD_TYPE)
    get_target_property(_lib_file ${_lib} IMPORTED_LOCATION)
    if(NOT _lib_file)
      get_target_property(_configs ${_lib} IMPORTED_CONFIGURATIONS)
      if(_build_type_upcase)
        list(PREPEND _config ${_build_type_upcase})
      endif()
      foreach(_config IN LISTS _configs)
        get_target_property(_lib_file ${_lib} IMPORTED_LOCATION_${_config})
        if(_lib_file)
          break()
        endif()
      endforeach()
    endif()
  elseif(EXISTS "${_lib}") # it's a file
    set(_lib_file "${_lib}")
  endif() # ignore all other cases
  if(_lib_file)
    # get the directory name and prepend it to LD_LIBRARY_PATH
    # if not there yet and not a system dir
    get_filename_component(_lib_dir "${_lib_file}" DIRECTORY)
    if(NOT _lib_dir IN_LIST _lib_dirs AND NOT _lib_dir MATCHES "^(/usr(/local)?)?/lib(32|64)?$")
      list(PREPEND _lib_dirs "${_lib_dir}")
      set(ENV{LD_LIBRARY_PATH} "${_lib_dir}:$ENV{LD_LIBRARY_PATH}")
      message(STATUS "added ${_lib_dir} to LD_LIBRARY_PATH")
    endif()
  endif()
endforeach()

# generate <project>.xenv file
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

# - special environment variables to be propagated for sanitizer builds
if(_build_type_upcase MATCHES "^(A|L|T|UB)SAN$")
  string(TOLOWER "${CMAKE_BUILD_TYPE}" _sanitizer_name)
  string(APPEND xenv_data
"  <env:set variable=\"PRELOAD_SANITIZER_LIB\">lib${_sanitizer_name}.so</env:set>
  <env:set variable=\"${_build_type_upcase}_OPTIONS\">${SANITIZER_OPTIONS_${_build_type_upcase}}</env:set>
")
endif()

string(APPEND xenv_data "</env:config>\n")

# - make the environment relocatable (from LCG_releases_base)
string(REPLACE "${LCG_releases_base}" "\${LCG_releases_base}" xenv_data "${xenv_data}")
string(CONFIGURE "${xenv_data}" xenv_data @ONLY)
# - write .xenv file and schedule install
file(WRITE ${CMAKE_BINARY_DIR}/${PROJECT_NAME}.xenv "${xenv_data}")
install(FILES ${CMAKE_BINARY_DIR}/${PROJECT_NAME}.xenv DESTINATION .)

# generate manifest.xml
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
foreach(pack IN LISTS packages_found)
  string(APPEND manifest_data "      <package name=\"${pack}\" />\n")
endforeach()
string(APPEND manifest_data
"    </packages>
</heptools>
</manifest>
")
# - write manifest.xml file and schedule install
file(WRITE ${CMAKE_BINARY_DIR}/manifest.xml "${manifest_data}")
install(FILES ${CMAKE_BINARY_DIR}/manifest.xml DESTINATION .)

# default install prefix when building in legacy mode
set(CMAKE_INSTALL_PREFIX ${CMAKE_SOURCE_DIR}/InstallArea/${BINARY_TAG})
