# - Locate VDT math library
# Defines:
#
#  VDT_FOUND
#  VDT_INCLUDE_DIR
#  VDT_INCLUDE_DIRS (not cached)
#  VDT_LIBRARIES
#
# Imports:
#
#  VDT::vdt
#
find_path(VDT_INCLUDE_DIR vdt/vdtcore_common.h
          HINTS $ENV{VDT_ROOT_DIR}/include ${VDT_ROOT_DIR}/include)
find_library(VDT_LIBRARIES NAMES vdt
          HINTS $ENV{VDT_ROOT_DIR}/lib ${VDT_ROOT_DIR}/lib)

set(VDT_INCLUDE_DIRS ${VDT_INCLUDE_DIR})

# handle the QUIETLY and REQUIRED arguments and set VDT_FOUND to TRUE if
# all listed variables are TRUE
INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(VDT DEFAULT_MSG VDT_INCLUDE_DIR VDT_LIBRARIES)

mark_as_advanced(VDT_FOUND VDT_INCLUDE_DIR VDT_LIBRARIES)

if(TARGET VDT::vdt)
    return()
endif()
if(VDT_FOUND)
  add_library(VDT::vdt INTERFACE IMPORTED)
  target_include_directories(VDT::vdt SYSTEM INTERFACE "${VDT_INCLUDE_DIR}")
  target_link_libraries(VDT::vdt INTERFACE "${VDT_LIBRARIES}")
  # Display the imported target for the user to know
  if(NOT ${CMAKE_FIND_PACKAGE_NAME}_FIND_QUIETLY)
    message(STATUS "  Import target: VDT::vdt")
  endif()
endif()
