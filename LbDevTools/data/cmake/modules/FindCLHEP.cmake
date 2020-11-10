# - Try to find CLHEP
# Defines:
#
#  CLHEP_FOUND
#  CLHEP_VERSION
#  CLHEP_INCLUDE_DIR
#  CLHEP_INCLUDE_DIRS (not cached)
#  CLHEP_<component>_LIBRARY
#  CLHEP_<component>_FOUND
#  CLHEP_LIBRARIES (not cached)
#  CLHEP_LIBRARY_DIRS (not cached)
#
# Note: version detection inspired by FindBoost.cmake

# Try to delegate to CLHEPConfig.cmake
if(CLHEP_FIND_COMPONENTS)
  set(fwd_components COMPONENTS ${CLHEP_FIND_COMPONENTS})
endif()
find_package(CLHEP ${fwd_components} CONFIG)

set(_CLHEP_COMPONENTS Cast Evaluator Exceptions GenericFunctions Geometry Random RandomObjects RefCount Vector Matrix)

if(TARGET CLHEP::CLHEP)
  # We found CLHEPConfig.cmake, so we set some legacy variables
  foreach(component IN LISTS _CLHEP_COMPONENTS)
    if(TARGET CLHEP::${component})
      set(CLHEP_${component}_LIBRARY CLHEP::${component})
    endif()
  endforeach()
  if(NOT CLHEP_FIND_QUIETLY)
    message(STATUS "Found CLHEP: ${CLHEP_DIR} (found version \"${CLHEP_VERSION}\")")
  endif()
else()

# Legacy implementation
find_path(CLHEP_INCLUDE_DIR CLHEP/ClhepVersion.h
          HINTS $ENV{CLHEP_ROOT_DIR}/include ${CLHEP_ROOT_DIR}/include)
if(CLHEP_INCLUDE_DIR)
  if(NOT DEFINED CLHEP_VERSION)
    file(READ "${CLHEP_INCLUDE_DIR}/CLHEP/ClhepVersion.h" _CLHEP_VERSION_H_CONTENTS)
    string(REGEX REPLACE ".*static std::string String\\(\\)[^\"]*return \"([^\"]*)\".*" "\\1" CLHEP_VERSION "${_CLHEP_VERSION_H_CONTENTS}")
    set(CLHEP_VERSION ${CLHEP_VERSION} CACHE INTERNAL "Detected version of CLHEP")
    message(STATUS "CLHEP version: ${CLHEP_VERSION}")
  endif()
endif()

find_library(CLHEP_MAIN_LIBRARY CLHEP 
               HINTS $ENV{CLHEP_ROOT_DIR}/lib ${CLHEP_ROOT_DIR}/lib)

set(_CLHEP_COMPONENTS Cast Evaluator Exceptions GenericFunctions Geometry Random RandomObjects RefCount Vector Matrix)
foreach(component ${_CLHEP_COMPONENTS})
  find_library(CLHEP_${component}_LIBRARY NAMES CLHEP-${component}-${CLHEP_VERSION}
               HINTS $ENV{CLHEP_ROOT_DIR}/lib ${CLHEP_ROOT_DIR}/lib)
  if (CLHEP_${component}_LIBRARY)
    set(CLHEP_${component}_FOUND 1)
    list(APPEND CLHEP_LIBRARIES ${CLHEP_${component}_LIBRARY})

    get_filename_component(libdir ${CLHEP_${component}_LIBRARY} PATH)
    list(APPEND CLHEP_LIBRARY_DIRS ${libdir})
  else()
    set(CLHEP_${component}_FOUND 0)
  endif()
  mark_as_advanced(CLHEP_${component}_LIBRARY)
endforeach()

if(CLHEP_LIBRARY_DIRS)
  list(REMOVE_DUPLICATES CLHEP_LIBRARY_DIRS)
endif()

set(CLHEP_INCLUDE_DIRS ${CLHEP_INCLUDE_DIR})

# handle the QUIETLY and REQUIRED arguments and set CLHEP_FOUND to TRUE if
# all listed variables are TRUE
INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(CLHEP DEFAULT_MSG CLHEP_INCLUDE_DIR CLHEP_LIBRARIES)

mark_as_advanced(CLHEP_FOUND CLHEP_INCLUDE_DIR)

endif()