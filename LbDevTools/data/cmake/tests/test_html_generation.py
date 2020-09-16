from __future__ import print_function
from __future__ import absolute_import
import os
from os.path import join, curdir, dirname
from subprocess import Popen, PIPE

class Test:


    def test_simple(self):
        base_dir = dirname(__file__)
        proc = Popen(["../../../CTestXML2HTML"], stdout=PIPE, stderr=PIPE, cwd=join(base_dir, "data", "html"))
        out, _ = proc.communicate()
        #print(out)
        expected_out = "Converting *Test.xml files from . to HTML format in htmlProcess the file : ./Test.xmlSome tests failed:  FAIL: 1  ERROR: 0"
        assert out.decode().replace('\n', '') == expected_out
    