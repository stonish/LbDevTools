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


def test_script():
    STACK = {
        "LCG": ["96b with ROOT 6.18.04", "96b with ROOT 6.18.04", []],
        "Gaudi": ["v33r0", "v33r0", ["LCG"]],
        "LHCb": ["v50r6", "v51r0", ["Gaudi"]],
        "Lbcom": ["v30r6", "v31r0", ["LHCb"]],
    }

    old_path = os.getcwd()
    path = tempfile.mkdtemp()
    os.chdir(path)
    try:
        # Setup some minimal stack
        with open("stack.json", "w") as f:
            json.dump(STACK, f)

        for p, (_, v1, _) in STACK.items():
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

        project = "Lbcom"
        # Run the script entry point
        os.chdir(project)
        # force the use of the template from LbDevTools:
        os.remove("ReleaseNotes/release_notes_template.md")
        ReleaseNotes.main(["-s", "../stack.json", "-o", "output.md"])

        with open("output.md") as f:
            output = f.read()
        lines = output.splitlines()

        # check preamble
        assert (
            "{} {} {}".format(datetime.date.today(), project, STACK[project][1])
            in lines[0]
        )
        assert re.search(r"LHCb.*{}".format(STACK["LHCb"][1]), output)
        assert re.search(
            r"relative to {}.*{}".format(project, STACK[project][0]), output
        )
        # check for changes
        assert (
            '~Calo ~"MC checking" | Allow relations changes in ' "LHCb, !385 (@graven)"
        ) in output
        # check for highlights from upstream projects
        assert (
            "~Decoding ~Muon | Improve MuonRawToHits, " "LHCb!2177 (@rvazquez)"
        ) in output
    finally:
        os.chdir(old_path)
        shutil.rmtree(path)
