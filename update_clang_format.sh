#!/bin/bash -e

# Find ourselves (for the destination location)
rootdir=$(cd $(dirname $0); pwd)
datadir=${rootdir}/LbDevTools/data

dest=${datadir}/default.clang-format
source=https://gitlab.cern.ch/gaudi/Gaudi/raw/v30r3/.clang-format

dest=$(realpath -m "${dest}")

if [ -e "${dest}" ] ; then
	mv -v "${dest}" "${dest}".bk
fi

mkdir -pv $(dirname "${dest}")

echo "Downloading ${source}"
echo "# Copy of ${source}" > "${dest}"
curl -L "${source}" >> "${dest}"

echo "Created ${dest}"

git add $dest
git commit -m "Updated default.clang-format from ${source}" $dest
