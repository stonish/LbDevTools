from __future__ import print_function
from __future__ import absolute_import
import os
from os.path import join, dirname, exists, abspath
from subprocess import Popen, PIPE

"""
Test the CTestXML2HTML command.
It does not take arguments so we change the pwd to the test directory to invoke it on the file stored there.
"""


class Test:
    def test_simple(self):
        """ Basic test that checks that the output of the command is correct on a simple Test.xml """
        base_dir = dirname(__file__)

        # The file is ../CTestXML2HTML. We take the abspath as we'll run in the test directory
        bin_dir = dirname(base_dir)
        cmd = abspath(join(bin_dir, "CTestXML2HTML"))
        assert exists(cmd)

        proc = Popen(
            [cmd],
            stdout=PIPE,
            stderr=PIPE,
            cwd=join(base_dir, "data", "html"),
        )
        out, _ = proc.communicate()
        expected_out = "Converting *Test.xml files from . to HTML format in htmlProcess the file : ./Test.xmlSome tests failed:  FAIL: 1  ERROR: 0"
        assert out.decode().replace("\n", "") == expected_out
