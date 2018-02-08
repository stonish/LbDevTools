#!/usr/bin/env python
# -*- coding: utf-8 -*-
###############################################################################
# (c) Copyright 2018 CERN                                                     #
#                                                                             #
# This software is distributed under the terms of the GNU General Public      #
# Licence version 3 (GPL Version 3), copied verbatim in the file "LICENSE".   #
#                                                                             #
# In applying this licence, CERN does not waive the privileges and immunities #
# granted to it by virtue of its status as an Intergovernmental Organization  #
# or submit itself to any jurisdiction.                                       #
###############################################################################
import sys
from LbUtils.Script import Script

def setup():
    pass

def teardown():
    pass


class TestScript(Script):
    """ Just a test """

    def defineOpts(self):
        """ Script specific options """
        parser = self.parser
        parser.add_option("-t", "--test1",
                          dest = "test1",
                          action = "store_true",
                          help = "Test1")

        parser.add_option("--test_action",
                          dest = "action",
                          action = "store",
                          default = "a",
                          help = "Test action")


    def main(self):
        """ Main method for bootstrap and parsing the options. """
        opts = self.options
        args = self.args


def test_basic_script():
    s = TestScript()
    s.run()
    print(s.options)
