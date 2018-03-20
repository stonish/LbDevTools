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

import logging
import subprocess

__all__ = (
    'git',
    'git_o',
)

def getOutput(*args, **kwargs):
    '''
    Helper function to get the standard output of a command.

    If the command fails, raise CalledProcessError (see subprocess.check_call).
    '''
    logging.debug('getting output of %s', subprocess.list2cmdline(args[0]))
    kwargs['stdout'] = subprocess.PIPE
    do_strip = not kwargs.pop('no_strip', False)
    proc = subprocess.Popen(*args, **kwargs)
    out, _ = proc.communicate()
    if proc.returncode:
        raise subprocess.CalledProcessError(proc.returncode, args[0])
    if do_strip:
        out = out.strip()
    # logging.debug('\n==============\n%s==============', out)
    return out


def git(*args, **kwargs):
    '''
    Helper function to call git.
    '''
    args[0].insert(0, 'git')
    logging.debug('calling %s', args[0])
    subprocess.check_call(*args, **kwargs)


def git_o(*args, **kwargs):
    '''
    Helper function to get the output of a call to git.
    '''
    args[0].insert(0, 'git')
    return getOutput(*args, **kwargs)
