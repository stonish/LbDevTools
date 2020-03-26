build_tool=cmake

DEVTOOLS_DATADIR := ${datadir}

ifeq ($$(wildcard build.conf),build.conf)
include build.conf
endif


# Make sure BINARY_TAG and CMTCONFIG are set and consistent.
# If one is not set, take the value from the other.
# If none is set, use the default platform from build.conf.
ifeq ($$(BINARY_TAG)$$(CMTCONFIG),)
  ifeq ($$(CMTCONFIG),)
    BINARY_TAG := $$(platform)
  else
    BINARY_TAG := $$(CMTCONFIG)
  endif
  export BINARY_TAG := $$(BINARY_TAG)
endif
ifeq ($$(CMTCONFIG),)
  CMTCONFIG := $$(BINARY_TAG)
  export CMTCONFIG := $$(CMTCONFIG)
endif
ifneq ($$(BINARY_TAG),$$(CMTCONFIG))
  $$(error Invalid environment: inconsistent values for BINARY_TAG and CMTCONFIG)
endif

ifeq ($$(build_tool),cmake)
######## CMake case ########

include $$(DEVTOOLS_DATADIR)/Makefile-cmake.mk

else
######### CMT case #########

ifeq ($$(wildcard build_env.sh),build_env.sh)
CMTPROJECTPATH := $$(shell bash -c ". build_env.sh ; printenv CMTPROJECTPATH")
endif

all:
%:
	@env CMTPROJECTPATH="$$(CMTPROJECTPATH)" DEVTOOLS_DATADIR="$$(DEVTOOLS_DATADIR)" $$(MAKE) -f $$(DEVTOOLS_DATADIR)/Makefile-cmt.mk $$*

endif
