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
import datetime
import json
import os
import re
import shutil
import tempfile
from subprocess import check_call
from LbDevTools import ReleaseNotes


class TestScript(object):
    STACK = {
        "LCG": ["96b with ROOT 6.18.04", "96b with ROOT 6.18.04", []],
        "Gaudi": ["v33r0", "v33r0", ["LCG"]],
        "LHCb": ["v50r6", "v51r0", ["Gaudi"]],
        "Lbcom": ["v30r6", "v31r0", ["LHCb"]],
    }
    PROJECT = "Lbcom"

    @classmethod
    def setup_class(cls):
        cls.old_path = os.getcwd()
        cls.path = tempfile.mkdtemp()
        os.chdir(cls.path)

        # Setup some minimal stack
        for p, (_, v1, _) in cls.STACK.items():
            if p not in ["Gaudi", "LCG"]:
                check_call(
                    [
                        "git",
                        "clone",
                        "-q",
                        "https://gitlab.cern.ch/lhcb/{}.git".format(p),
                    ]
                )
                check_call(["git", "checkout", "-q", v1], cwd=p)

        os.chdir(cls.PROJECT)
        # force the use of the template from LbDevTools:
        os.remove("ReleaseNotes/release_notes_template.md")

    @classmethod
    def teardown_class(cls):
        os.chdir(cls.old_path)
        shutil.rmtree(cls.path)

    def test_versions(self):
        v_prev, v_next, _ = self.STACK[self.PROJECT]
        ReleaseNotes.main([v_prev, v_next, "-o", "output1.md"])
        self.check_output("output1.md", check_deps=False)

    def test_stack_json(self):
        # stack.json file must be in the directory containing the clones
        with open("../stack.json", "w") as f:
            json.dump(self.STACK, f)

        ReleaseNotes.main(["-s", "../stack.json", "-o", "output2.md"])
        self.check_output("output2.md")

    def check_output(self, path, check_deps=True):
        with open(path) as f:
            output = f.read()
        lines = output.splitlines()

        project, v_prev, v_next, _ = [self.PROJECT] + self.STACK[self.PROJECT]

        # check preamble
        assert "{} {} {}".format(datetime.date.today(), project, v_next) in lines[0]
        assert re.search(r"relative to {}.*{}".format(project, v_prev), output)
        # check for changes
        assert (
            '~Calo ~"MC checking" | Allow relations changes in ' "LHCb, !385 (@graven)"
        ) in output
        if check_deps:
            assert re.search(r"LHCb.*{}".format(self.STACK["LHCb"][1]), output)
            # check for highlights from upstream projects
            assert (
                "~Decoding ~Muon | Improve MuonRawToHits, " "LHCb!2177 (@rvazquez)"
            ) in output
