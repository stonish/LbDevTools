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

import logging
import os
from LbDevTools.UserProject import UserProject


def test_creation():
    os.environ["CMAKE_PREFIX_PATH"] = "/cvmfs/lhcb.cern.ch/lib/lhcb:/cvmfs/lhcb.cern.ch/lib/lcg/releases:/cvmfs/lhcb.cern.ch/lib/lcg/app/releases:/cvmfs/lhcb.cern.ch/lib/lcg/external:/cvmfs/lhcb.cern.ch/lib/contrib:/cvmfs/lhcb.cern.ch/lib/var/lib/LbEnv/417/stable/x86_64-centos7/lib/python2.7/site-packages/LbDevTools/data/cmake"
    logging.getLogger().setLevel(logging.DEBUG)
    p = UserProject.create("DaVinci", "v50r4", "x86_64-centos7-gcc8-opt", path="/tmp")
    assert os.path.exists(os.path.join("/tmp", "DaVinciDev_v50r4", "configuration.json"))

    p2 = UserProject("/tmp/DaVinciDev_v50r4")

    p.build()