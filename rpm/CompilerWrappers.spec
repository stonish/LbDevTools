Name:       CompilerWrappers
# IMPORTANT: update version and/or release to deploy a new RPM
Version:    3
Release:    5
Vendor:     LHCb
Summary:    Wrappers for available compiler versions.
License:    GPLv3

Group: LHCb

BuildArch: noarch
AutoReqProv: no
Prefix: /opt/LHCbSoft
Provides: /bin/sh
Provides: /bin/bash

%define _buildshell /bin/bash

%description
Wrappers for available compiler versions.

%prep
# we have no source, so nothing here

%build
set +x
source /cvmfs/lhcb.cern.ch/lib/LbEnv
export PATH=${HOME}/rpmbuild/SOURCES:${PATH}
echo using $(which lb-gen-compiler-wrapper)
rm -rf bin
for host_os in x86_64-slc5 x86_64-slc6 x86_64-centos7 ; do
  mkdir -p bin/$host_os
  for command in gcc g++ c++ gfortran ; do
    for version in 4.3.{2,3,4,5} 4.4.{0,1,3} 4.5.{0,2,3} 4.6.{1,2,3} \
                   4.7.{0,1,2} 4.8.{0,1,4} 4.9.{0,1,2,3} \
                   5.{1,2,3}.0 6.{1,2,3,4}.0 7.{1,2,3}.0 8.{1,2,3}.0 \
                   9.{1,2,3}.0 \
                   10.1.0 ; do
      echo generating bin/$host_os/lcg-${command}-${version}
      lb-gen-compiler-wrapper $host_os bin/$host_os/lcg-${command}-${version} || true
    done
  done
  for command in clang clang++ \
            clang-{apply-replacements,check,format,include-fixer,modernize,query,refactor,rename,tidy} ; do
    for version in 2.{7,8} 3.{0,1,2,3,4,5,6,7} 3.7.{0,1} 3.8 3.8.0 3.9 3.9.0 \
                   {5,6,7,8,10}.0.0; do
      echo generating bin/$host_os/lcg-${command}-${version}
      lb-gen-compiler-wrapper $host_os bin/$host_os/lcg-${command}-${version} || true
    done
  done
done
find . -type f -exec sed -i "s#/cvmfs/lhcb\.cern\.ch/lib#<<prefix>>#g" \{} \;

%install
mkdir -p %{buildroot}/opt/LHCbSoft/bin
cp -av bin/. %{buildroot}/opt/LHCbSoft/bin/.

%post -p /bin/bash
find ${RPM_INSTALL_PREFIX}/bin -type f -name "lcg-*-*" -exec sed -i "s#<<prefix>>#${RPM_INSTALL_PREFIX}#g" \{} \;

%files
%defattr(-,root,root)
/opt/LHCbSoft

%changelog
# let skip this for now
