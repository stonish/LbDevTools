################################################################################
#
# Generic Makefile to simplify the use of CMake projects
# ------------------------------------------------------
#
# This simple Makefile is meant to provide a simplified entry point for the
# configuration and build of CMake-based projects that use a default toolchain
# (as it is the case for Gaudi-based projects).
#
# Only a few targets are actually provided: all the main targets are directly
# delegated to the CMake Makefile.
#
# Main targets:
#
#     all
#         (default) build everything
#
#     test [*]_
#         run the declared tests
#
#     install
#         populate the InstallArea with the products of the build
#
#     clean
#         remove build products from the build directory
#
#     purge [*]_
#         deep clean of the build, including InstallArea
#         (requires re-configuration)
#
#     help
#         print the list of available targets
#
#     configure [*]_
#         force an explicit CMake configuration
#
#     full-configure [*]_
#         wipe the CMake cache and force full configuration
#         (the binaries are not removed so, possibly not rebuilt)
#
# :Author: Marco Clemencic
#
# .. [*] Targets defined by this Makefile.
#
################################################################################

# settings
CMAKE := cmake
CMAKE_WITH_INSTALL := $(shell $(CMAKE) --help | grep -q -- --install && echo YES)
CTEST := ctest
NINJA := $(shell which ninja 2> /dev/null)

ifneq ($(wildcard $(CURDIR)/toolchain.cmake),)
  override CMAKEFLAGS += -DCMAKE_TOOLCHAIN_FILE=$(CURDIR)/toolchain.cmake
endif
ifneq ($(wildcard $(CURDIR)/cache_preload.cmake),)
  override CMAKEFLAGS += -C$(CURDIR)/cache_preload.cmake
endif

ifndef BINARY_TAG
  ifdef CMAKECONFIG
    BINARY_TAG := ${CMAKECONFIG}
  else
    ifdef CMTCONFIG
      BINARY_TAG := ${CMTCONFIG}
    endif
  endif
endif

ifeq ($(BINARY_TAG)$(BUILDDIR),)
$(error one of BINARY_TAG, CMTCONFIG or BUILDDIR must be defined)
endif
BUILDDIR := $(CURDIR)/build.$(BINARY_TAG)

ifneq ($(wildcard $(BUILDDIR)/Makefile),)
  # force the use of GNU Make if the build was using it
  USE_MAKE := 1
endif
ifneq ($(wildcard $(BUILDDIR)/build.ninja),)
  ifeq ($(NINJA),)
    # make sure we have ninja if we configured with it
    $(error $(BUILDDIR) was configured for Ninja, but it is not in the path)
  endif
endif

ifneq ($(NINJA),)
  ifeq ($(USE_MAKE),)
    ifeq ($(shell grep "NO_NINJA" CMakeLists.txt),)
      USE_NINJA := 1
    endif
  endif
endif

# build tool
ifneq ($(USE_NINJA),)
  # enable Ninja
  override CMAKEFLAGS += -GNinja
  BUILD_CONF_FILE := build.ninja
  BUILDFLAGS := $(NINJAFLAGS)
  ifneq ($(VERBOSE),)
    BUILDFLAGS := -v $(BUILDFLAGS)
  endif
else
  BUILD_CONF_FILE := Makefile
endif
BUILD_CMD := $(CMAKE) --build $(BUILDDIR) --target
CONFIG_CMD := $(CMAKE) -S $(CURDIR) -B $(BUILDDIR) $(CMAKEFLAGS)

# default target
all:

# deep clean
purge:
	$(RM) -r $(BUILDDIR) $(CURDIR)/InstallArea/$(BINARY_TAG)
	find $(CURDIR) "(" -name "InstallArea" -prune -o -name "*.pyc" ")" -a -type f -exec $(RM) -v \{} \;

# delegate any target to the build directory (except 'purge')
ifneq ($(MAKECMDGOALS),purge)
%: $(BUILDDIR)/$(BUILD_CONF_FILE) FORCE
	+$(BUILD_CMD) $* -- $(BUILDFLAGS)
endif

# aliases
.PHONY: configure test FORCE
ifneq ($(wildcard $(BUILDDIR)/$(BUILD_CONF_FILE)),)
configure:
	$(CONFIG_CMD)
else
configure: $(BUILDDIR)/$(BUILD_CONF_FILE)
endif
	@ # do not delegate further

# Note: in principle this should delegate to "make configure" after removing the files to generate
#       but this does not work because of how make handles recursion
full-configure:
	$(RM) $(BUILDDIR)/$(BUILD_CONF_FILE) $(BUILDDIR)/CMakeCache.txt
	$(CONFIG_CMD)

# This wrapping around the test target is used to ensure the generation of
# the XML output from ctest.
test: $(BUILDDIR)/$(BUILD_CONF_FILE)
	$(RM) -r $(BUILDDIR)/Testing $(BUILDDIR)/html
	-cd $(BUILDDIR) && $(CTEST) -T test $(ARGS)
	+@if [ -x $(DEVTOOLS_DATADIR)/cmake/CTestXML2HTML ] ; then \
             cd $(BUILDDIR) && $(DEVTOOLS_DATADIR)/cmake/CTestXML2HTML ; \
         else \
             $(BUILD_CMD) HTMLSummary ; \
         fi

ifeq ($(VERBOSE),)
# less verbose install (see GAUDI-1018)
# (emulate the default CMake install target)
install: all
ifeq ($(CMAKE_WITH_INSTALL),YES)
	$(CMAKE) --install $(BUILDDIR) | grep -v "^-- Up-to-date:"
else
	cd $(BUILDDIR) && $(CMAKE) -P cmake_install.cmake | grep -v "^-- Up-to-date:"
endif
endif

# ensure that the target are always passed to the CMake Makefile
FORCE:
	@ # dummy target

# Makefiles are used as implicit targets in make, but we should not consider
# them for delegation.
$(MAKEFILE_LIST):
	@ # do not delegate further

# trigger CMake configuration
$(BUILDDIR)/$(BUILD_CONF_FILE):
	$(CONFIG_CMD)
