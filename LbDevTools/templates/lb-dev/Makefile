build_tool=cmake

DEVTOOLS_DATADIR := ${datadir}

ifeq ($$(wildcard build.conf),build.conf)
include build.conf
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
