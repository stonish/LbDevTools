###############################################################################
# (c) Copyright 2020 CERN                                                     #
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
import os
import sys
from LbDevTools import DATA_DIR
from nose import with_setup

sys.path.insert(0, os.path.join(DATA_DIR, "cmake", "modules"))
import scan_dict_deps as sdd


def test_find_file():
    abs_path = os.path.abspath(DATA_DIR)
    abs_not_exists = os.path.join(abs_path, "dummy")

    assert sdd.find_file(abs_path, None) == abs_path
    assert sdd.find_file(abs_not_exists, None) is None

    assert sdd.find_file(os.path.basename(__file__), []) is None
    assert sdd.find_file(os.path.basename(__file__), sys.path) == __file__


def test_find_deps():
    deps = set()
    test_data_dir = os.path.join(os.path.dirname(__file__), "data", "sdd")
    expected = [
        os.path.join(test_data_dir, f) for f in ("first.h", "nested.h", "second.h")
    ]

    sdd.find_deps("main.h", [test_data_dir], deps)
    deps = sorted(deps)

    assert deps == expected

    assert sdd.find_deps("dummy", []) == set()
