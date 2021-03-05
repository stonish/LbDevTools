cmake_minimum_required(VERSION 3.15)

project(${local_project}
    VERSION ${local_version}
    LANGUAGES CXX${with_fortran})

# Enable tests support
include(CTest)

# Load "lhcb_find_package" function
include(${datadir}/cmake/LHCbFindPackage.cmake)

include($${CMAKE_CURRENT_LIST_DIR}/cmake/${local_project}Dependencies.cmake)

set(GAUDI_PREFER_LOCAL_TARGETS TRUE)
lhcb_add_subdirectories(
    # -- begin: list of subdirectories --
    # -- end: list of subdirectories --
)

# Final configuration steps
set(GAUDI_LEGACY_CMAKE_SUPPORT TRUE)
lhcb_finalize_configuration(NO_EXPORT)

# Enable Ganga integration
include(${datadir}/cmake/GangaTools.cmake)
enable_ganga_integration()
