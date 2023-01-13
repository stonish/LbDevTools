cmake_minimum_required(VERSION 3.15)
${optional_lcg_layer}
project(${local_project}
    VERSION ${local_version}
    LANGUAGES CXX${with_fortran})

# Enable tests support
include(CTest)

# Load "lhcb_find_package" function
include(${datadir}/cmake/LHCbFindPackage.cmake)

# Get the list of projects we are working on
execute_process(
    COMMAND git remote
    WORKING_DIRECTORY $${CMAKE_SOURCE_DIR}
    OUTPUT_VARIABLE enabled_projects
    ERROR_QUIET OUTPUT_STRIP_TRAILING_WHITESPACE)
# (this is a trick to split a atring into a list of words)
string(REGEX MATCHALL "[a-zA-Z0-9]+" enabled_projects "$${enabled_projects}")
# Set flags to inherit private dependencies of the projects we work on
foreach(p IN LISTS enabled_projects)
    set(WITH_$${p}_PRIVATE_DEPENDENCIES TRUE)
endforeach()

list(PREPEND CMAKE_MODULE_PATH $${PROJECT_SOURCE_DIR}/cmake)
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
