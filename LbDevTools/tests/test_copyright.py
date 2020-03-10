###############################################################################
# (c) Copyright 2018 CERN                                                     #
#                                                                             #
# This software is distributed under the terms of the GNU General Public      #
# Licence version 3 (GPL Version 3), copied verbatim in the file "COPYING".   #
#                                                                             #
# In applying this licence, CERN does not waive the privileges and immunities #
# granted to it by virtue of its status as an Intergovernmental Organization  #
# or submit itself to any jurisdiction.                                       #
###############################################################################
from __future__ import print_function

from __future__ import absolute_import
from os.path import join, dirname, splitext, basename
from os import remove, mkdir, rmdir
from shutil import rmtree

import LbDevTools.SourceTools as C
import tempfile


DATA_DIR = join(dirname(__file__), "data")


def test_is_script():
    assert C.is_script(join(DATA_DIR, "a_script"))
    assert not C.is_script(join(DATA_DIR, "not_a_script"))


def test_to_check():
    for to_check, name in (
        (True, "a_script"),
        (False, "not_a_script"),
        (True, "source.py"),
        (True, "source.cpp"),
        (True, "source.xml"),
        (False, "."),
    ):
        assert C.to_check(join(DATA_DIR, name)) is to_check


def test_has_copyright():
    assert C.has_copyright(splitext(__file__)[0] + ".py")
    assert not C.has_copyright(join(DATA_DIR, "a_script"))


def test_get_filenames_in_path():
    temp_folder = tempfile.mkdtemp(prefix="")
    try:
        temp1 = tempfile.NamedTemporaryFile(
            prefix="temp1", suffix=".txt", dir=temp_folder
        )
        temp2 = tempfile.NamedTemporaryFile(
            prefix="temp2", suffix=".txt", dir=temp_folder
        )
        file_names = [basename(temp1.name), basename(temp2.name)]

        files_in_path = C.get_filenames(temp_folder)

        assert file_names.sort() == files_in_path.sort()
    finally:
        rmtree(temp_folder)


def test_find_strings_in_list():
    strings = ["string1", "string2"]
    list_items = ["item1", {}, "string1", "item3"]

    strings_in_list = C.find_strings_in_list(strings, list_items)

    assert ["string1"] == strings_in_list


def test_find_strings_in_empty_list():
    strings = ["string1", "string2"]
    list_items = []

    strings_in_list = C.find_strings_in_list(strings, list_items)

    assert [] == strings_in_list


def test_get_non_empty_filenames():
    # A normal directory is created here because tempfile.TemporaryDirectory()
    # creates a folder-like object, instead of a real directory and
    #  scandir cannot handle it
    mkdir("./temp")
    temp1 = tempfile.NamedTemporaryFile(
        delete=False, prefix="temp1", suffix=".txt", dir="./temp"
    )
    temp2 = tempfile.NamedTemporaryFile(prefix="temp2", suffix=".txt", dir="./temp")

    temp1.write(b"some string")
    temp1.close()

    file_names = [basename(temp1.name)]

    non_empty_files_in_path = C.get_non_empty_filenames("./temp")
    rmtree("./temp")

    assert file_names == non_empty_files_in_path
