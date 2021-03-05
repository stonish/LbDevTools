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
#[========================================================================[.rst:
LegacyGaudiCMakeSupport.cmake
=============================

Compatibility layer to be able to use new style (modern) CMake projects
from old style (GaudiProjectConfig) projects.

When included at the end of a project configuration file, this module
scans the configuration of the project to generate the metadata artifacts
old style projects need for their own configuration.

We also initialize ``CMAKE_INSTALL_PREFIX`` to the old style value.

``.metadata.cmake``
-------------------
Old style projects add some special information to the generated
``${PROJECT_NAME}Config.cmake``. New style projects do not, so we produce a
special file called ``.metadata.cmake`` to fill the gap.

This file sets the variables

  ``${PROJECT_NAME}_heptools_version``
      the version of LCG used for the build
  ``${PROJECT_NAME}_heptools_system``
      the LCG platform used (without optimization level)
  ``known_packages`` (append)
      list of subdirectory in this projects (expected downstream for
      subdirectory dependencies)
  ``gaudi_target_namespaces`` (append)
      used to resolve namespaced targets in ``gaudi_add_*`` functions

Finally we load all the ``.metadata.cmake`` files of the projects we
depend on.

``${PROJECT_NAME}.xenv``
------------------------
The environment of old style projects is set by the ``xenv`` tool, which
processes ``.xenv`` files, so we have to produce one that mimics the old
behaviour.

For the environment file we start from the current environment and we
extend the ``LD_LIBRARY_PATH`` using the directory needed by all targets
we build.

Then we prepare the ``${PROJECT_NAME}.xenv`` file so that it sets ``PATH``,
``LD_LIBRARY_PATH``, ``PYTHONPATH`` and ``ROOT_INCLUDE_PATH`` to the
current value plus the entries from the current project.

We add to the environment all the changes declared in the global property
``${PROJECT_NAME}_ENVIRONMENT`` (filled, for example, by the command
``lhcb_env`` in ``LHCbConfigUtils.cmake``).

Since the generated ``${PROJECT_NAME}.xenv`` must be relocatable we apply
a set of relocation rules (some built-in, some user provided via the global
property ``ENVIRONMENT_RELOCATION_RULES``) to the file.
A relocation rule is a string in the format::

    <original string> ==> <relocation string>

For example ``"/path/to/lcg/releases ==> ${LCG_releases_base}"``.
For each relocation rule that uses a variable as relocation string, we
inject a *default* value for the variable, then, for all cases, we replace
in the file all occurrences of the original string with the relocation one.

``manifest.xml``
This file is used by ``lb-run`` an by the packaging to discover the
dependencies of the project.

It contains some platform information, the list of LHcb projects, the list
of data packages and the list of external targets used.

#]========================================================================]
if(NOT CMAKE_SOURCE_DIR STREQUAL CMAKE_CURRENT_SOURCE_DIR)
  message(WARNING "LegacyGaudiCMakeSupport is ignored in subprojects")
  return()
endif()
message(STATUS "Enabling compatibility with old-style CMake builds")
########################################
# Old style config compatibility layer #
########################################
# make sure we have a BINARY_TAG CMake variable set
if(NOT BINARY_TAG)
  if(NOT "$ENV{BINARY_TAG}" STREQUAL "")
    set(BINARY_TAG $ENV{BINARY_TAG})
  elseif(LHCB_PLATFORM)
    set(BINARY_TAG ${LHCB_PLATFORM})
  else()
    message(AUTHOR_WARNING "BINARY_TAG not set")
  endif()
endif()

# default install prefix when building in legacy mode
if(CMAKE_INSTALL_PREFIX_INITIALIZED_TO_DEFAULT)
  set(CMAKE_INSTALL_PREFIX "${CMAKE_SOURCE_DIR}/InstallArea/${BINARY_TAG}"
    CACHE PATH "Install prefix" FORCE)
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
# - found (LHCb) data packages
get_property(data_packages_found GLOBAL PROPERTY DATA_PACKAGES_FOUND)
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
# - environment
if(${PROJECT_NAME}_ENVIRONMENT)
  string(REPLACE "\$" "\\\$" value "${${PROJECT_NAME}_ENVIRONMENT}")
  string(APPEND metadata "set(${PROJECT_NAME}_ENVIRONMENT ${value})\n")
endif()
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
      message(DEBUG "added ${_lib_dir} to LD_LIBRARY_PATH")
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
@RELOC_DEFAULTS@")

set(relocations
  "${LCG_releases_base} ==> \${LCG_releases_base}"
  "${PROJECT_SOURCE_DIR} ==> \${${PROJECT_NAME_UPCASE}_PROJECT_ROOT}"
)
foreach(pack IN LISTS packages_found)
  string(TOUPPER "${pack}" pack_upcase)
  if(DEFINED ${pack_upcase}_PROJECT_ROOT)
    list(APPEND relocations "${${pack_upcase}_PROJECT_ROOT} ==> \${${pack_upcase}_PROJECT_ROOT}")
  endif()
endforeach()

string(APPEND xenv_data
"  <env:set variable=\"GAUDIAPPNAME\">${PROJECT_NAME}</env:set>
  <env:set variable=\"GAUDIAPPVERSION\">${PROJECT_VERSION}</env:set>
  <env:set variable=\"${PROJECT_NAME_UPCASE}_PROJECT_ROOT\">\${.}/../../</env:set>
  <env:prepend variable=\"PATH\">$ENV{PATH}</env:prepend>
  <env:prepend variable=\"LD_LIBRARY_PATH\">$ENV{LD_LIBRARY_PATH}</env:prepend>
  <env:prepend variable=\"PYTHONPATH\">$ENV{PYTHONPATH}</env:prepend>
  <env:set variable=\"PYTHONHOME\">$ENV{PYTHONHOME}</env:set>
  <env:prepend variable=\"ROOT_INCLUDE_PATH\">$ENV{ROOT_INCLUDE_PATH}</env:prepend>
")

# - special environment variables to be propagated for sanitizer builds
if(_build_type_upcase MATCHES "^(A|L|T|UB)SAN$")
  string(TOLOWER "${CMAKE_BUILD_TYPE}" _sanitizer_name)
  string(APPEND xenv_data
"  <env:set variable=\"PRELOAD_SANITIZER_LIB\">lib${_sanitizer_name}.so</env:set>
  <env:set variable=\"${_build_type_upcase}_OPTIONS\">${SANITIZER_OPTIONS_${_build_type_upcase}}</env:set>
")
endif()

get_property(env_instructions GLOBAL PROPERTY ${PROJECT_NAME}_ENVIRONMENT)
while(env_instructions)
  list(POP_FRONT env_instructions action)
  if(action MATCHES "^SET|PREPEND|APPEND|DEFAULT\$")
    string(TOLOWER "${action}" action)
    list(POP_FRONT env_instructions variable)
    if(action STREQUAL "unset")
      set(value)
    else()
      list(POP_FRONT env_instructions value)
    endif()
    string(APPEND xenv_data "  <env:${action} variable=\"${variable}\">${value}</env:${action}>\n")
  else()
    message(FATAL_ERROR "invalid environment action ${action}")
  endif()
endwhile()

if(PROJECT_NAME MATCHES "^(Gaudi|Detector|GitCondDB)\$")
  # these projects have support for LHCb old style installation, but
  # do not use lhcb_env for the environment, so they need special treatment
  string(APPEND xenv_data
"  <env:prepend variable=\"PATH\">\${.}/bin</env:prepend>
  <env:prepend variable=\"LD_LIBRARY_PATH\">\${.}/lib</env:prepend>
  <env:prepend variable=\"PYTHONPATH\">\${.}/python</env:prepend>
  <env:prepend variable=\"ROOT_INCLUDE_PATH\">\${.}/include</env:prepend>
")
endif()

string(APPEND xenv_data "</env:config>\n")

# - make the environment relocatable
#   - list of user relocation replacements, used to make the environment relocatable,
#     in the form of "<build-time-value> ==> <relocatable-version>"
get_property(user_relocations GLOBAL PROPERTY ENVIRONMENT_RELOCATION_RULES)
set(RELOC_DEFAULTS "")
foreach(reloc IN LISTS relocations user_relocations)
  if(reloc MATCHES "^(.*) ==> (.*)\$")
    set(_from "${CMAKE_MATCH_1}")
    set(_to "${CMAKE_MATCH_2}")
    string(REPLACE "${_from}/" "${_to}/" xenv_data "${xenv_data}")
    if(_to MATCHES "^\\\$\\{([^}]+)\\}\$" AND NOT _from STREQUAL "${PROJECT_SOURCE_DIR}")
      string(APPEND RELOC_DEFAULTS "  <env:default variable=\"${CMAKE_MATCH_1}\">${_from}</env:default>\n")
    endif()
  else()
    message(FATAL_ERROR "invalid relocation rule '${reloc}', it must be in the form 'string ==> string'")
  endif()
endforeach()
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
set(projects)
foreach(pack IN LISTS packages_found)
  if("${${pack}_DIR}${${pack}_ROOT_DIR}" MATCHES "/InstallArea/")
    # it looks like an LHCb project, so we treat it differently
    list(APPEND projects ${pack})
  else()
    string(APPEND manifest_data "      <package name=\"${pack}\" ")
    if(DEFINED ${pack}_VERSION)
      string(APPEND manifest_data "version=\"${${pack}_VERSION}\" ")
    endif()
    string(APPEND manifest_data "/>\n")
  endif()
endforeach()
string(APPEND manifest_data "    </packages>\n  </heptools>\n")

if(projects)
  string(APPEND manifest_data "  <used_projects>\n")
  foreach(project IN LISTS projects)
    string(APPEND manifest_data "    <project name=\"${project}\" version=\"${${project}_VERSION}\" />\n")
  endforeach()
  string(APPEND manifest_data "  </used_projects>\n")
endif()

if(data_packages_found)
  string(APPEND manifest_data "  <used_data_pkgs>\n")
  foreach(pack IN LISTS data_packages_found)
    if(pack MATCHES "^([^:]*):(.*)\$")
      string(APPEND manifest_data "    <package name=\"${CMAKE_MATCH_1}\" version=\"${CMAKE_MATCH_2}\" />\n")
    else()
      string(APPEND manifest_data "    <package name=\"${pack}\" version=\"*\" />\n")
    endif()
  endforeach()
  string(APPEND manifest_data "  </used_data_pkgs>\n")
endif()

string(APPEND manifest_data "</manifest>\n")

# - write manifest.xml file and schedule install
file(WRITE ${CMAKE_BINARY_DIR}/manifest.xml "${manifest_data}")
install(FILES ${CMAKE_BINARY_DIR}/manifest.xml DESTINATION .)

# now we know if we use other LHCb projects and for those we have to pull
# the metadata file from our metadatafile
if(projects)
  file(APPEND ${CMAKE_BINARY_DIR}/.metadata.cmake
"# helper to resolve library names to the correct targets
list(APPEND gaudi_target_namespaces ${PROJECT_NAME} ${projects})
# get metadata from upstream projects
foreach(_p IN ITEMS ${projects})
    if(EXISTS \"\${\${_p}_DIR}/.metadata.cmake\")
        include(\"\${\${_p}_DIR}/.metadata.cmake\")
    endif()
endforeach()\n")
endif()
