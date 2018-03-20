from __future__ import print_function
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
__author__ = 'Marco Clemencic <marco.clemencic@cern.ch>'

import sys
import os
import re
import logging
from subprocess import Popen, PIPE, CalledProcessError, check_call
from collections import defaultdict
from shutil import rmtree
from LbDevTools.GitTools import git, git_o

try:
    from tempfile import TemporaryDirectory
except ImportError:
    import os as _os
    import warnings as _warnings
    from tempfile import mkdtemp
    # FIXME: backport from Python 3.2 (see http://stackoverflow.com/a/19299884)
    class TemporaryDirectory(object):
        """Create and return a temporary directory.  This has the same
        behavior as mkdtemp but can be used as a context manager.  For
        example:

            with TemporaryDirectory() as tmpdir:
                ...

        Upon exiting the context, the directory and everything contained
        in it are removed.
        """

        def __init__(self, suffix="", prefix="tmp", dir=None):
            self._closed = False
            self.name = None # Handle mkdtemp raising an exception
            self.name = mkdtemp(suffix, prefix, dir)

        def __repr__(self):
            return "<{0} {1!r}>".format(self.__class__.__name__, self.name)

        def __enter__(self):
            return self.name

        def cleanup(self, _warn=False):
            if self.name and not self._closed:
                try:
                    self._rmtree(self.name)
                except (TypeError, AttributeError) as ex:
                    # Issue #10188: Emit a warning on stderr
                    # if the directory could not be cleaned
                    # up due to missing globals
                    if "None" not in str(ex):
                        raise
                    print("ERROR: {0!r} while cleaning up {1!r}".format(ex, self,),
                          file=_sys.stderr)
                    return
                self._closed = True
                if _warn:
                    # It should be ResourceWarning, but it exists only in Python 3
                    self._warn("Implicitly cleaning up {1!r}".format(self),
                               UserWarning)

        def __exit__(self, exc, value, tb):
            self.cleanup()

        def __del__(self):
            # Issue a ResourceWarning if implicit cleanup needed
            self.cleanup(_warn=True)

        # XXX (ncoghlan): The following code attempts to make
        # this class tolerant of the module nulling out process
        # that happens during CPython interpreter shutdown
        # Alas, it doesn't actually manage it. See issue #10188
        _listdir = staticmethod(_os.listdir)
        _path_join = staticmethod(_os.path.join)
        _isdir = staticmethod(_os.path.isdir)
        _islink = staticmethod(_os.path.islink)
        _remove = staticmethod(_os.remove)
        _rmdir = staticmethod(_os.rmdir)
        _warn = _warnings.warn

        def _rmtree(self, path):
            # Essentially a stripped down version of shutil.rmtree.  We can't
            # use globals because they may be None'ed out at shutdown.
            for name in self._listdir(path):
                fullname = self._path_join(path, name)
                try:
                    isdir = self._isdir(fullname) and not self._islink(fullname)
                except OSError:
                    isdir = False
                if isdir:
                    self._rmtree(fullname)
                else:
                    try:
                        self._remove(fullname)
                    except OSError:
                        pass
            try:
                self._rmdir(path)
            except OSError:
                pass


def git_config(name, value=None, configfile=None, cwd='.'):
    '''
    Get or set git config variables.
    '''
    cmd = ['config']
    if configfile:
        cmd.extend(['--file', configfile])
    cmd.append(name)
    if value is None:
        return git_o(cmd, cwd=cwd)
    git(cmd + [value], cwd=cwd)

def commits_list(*args, **kwargs):
    '''
    Get list of git commit ids (wrapper around 'git log').
    '''
    return git_o(['log', '--pretty=format:%H'] + list(args),
                 cwd=kwargs.get('cwd', '.')).splitlines()

def commits_cmp(a, b):
    '''
    History wise comparison function for commit ids.

    Used as cmp argument to a sorting function, the commits are sorted from the
    oldest to the newest.
    '''
    if a == b:
        return 0
    if commits_list('{0}..{1}'.format(a, b)):
        return -1
    return 1

def is_subdir(a, b):
    '''
    Return True if 'a' is a subdirectory of 'b' (or a == b).
    '''
    return a == b or a.startswith(b + '/')


def main():
    '''Main function of the script.'''
    from optparse import OptionParser
    parser = OptionParser(usage='%prog [<options>] <repository> <branch> [<path> ..]')

    parser.add_option('-v', '--verbose',
                      action='store_const', const=logging.INFO,
                      dest='loglevel',
                      help='print more messages')

    parser.add_option('-d', '--debug',
                      action='store_const', const=logging.DEBUG,
                      dest='loglevel',
                      help='print debug messages')

    parser.add_option('-k', '--keep-temp-branch',
                      action='store_true',
                      dest='keep_temp',
                      default = False,
                      help='keep temporary branch after push instead of deleting (default=off)')

    parser.set_defaults(loglevel=logging.WARNING)

    opts, args = parser.parse_args()

    if len(args) < 2:
        parser.error('wrong number of arguments')

    remote, branch = args[:2]
    paths = set(args[2:])

    logging.basicConfig(level=opts.loglevel)

    topdir = git_o(['rev-parse', '--show-toplevel'])
    logging.info('using repository at %s', topdir)
    os.chdir(topdir)

    cfggroup = 'lb-checkout.{0}'.format(remote)

    configfile = '.git-lb-checkout'
    if not os.path.exists(configfile):
        configfile = None

    # find packages (directories) from the requested remote
    pkgs = dict((pkg, {'base': git_config('.'.join([cfggroup, pkg, 'base']),
                                          configfile=configfile),
                       'imported': git_config('.'.join([cfggroup, pkg, 'imported']),
                                              configfile=configfile)})
                 for pkg in [m.group(1)
                             for m in map(re.compile(r'^{0}\.(.*)\.base'.format(cfggroup)).match,
                                          git_config('--list', configfile=configfile).splitlines())
                             if m])

    if not pkgs:
        print("No lb-checkout path found for project {0}".format(remote))
        remotes = [m.group(1) for m in map(re.compile(r'^{0}\.([^.]*)\..*\.base'.format('lb-checkout')).match,git_config('--list', configfile=configfile).splitlines()) if m]
        if 0 == len(remotes):
            print("No lb-checkouts made")
        else:
            print("Possible projects are:")
            for m in set(remotes):
                print ("  {0}".format(m))
        sys.exit(1)

    # compare the known packages to the list on the command line:
    # we take all packages that are subdirs of the specified paths
    if paths:
        new_pkgs = {}
        for path in paths:
            for pkg in pkgs:
                if is_subdir(pkg, path):
                    new_pkgs[pkg] = pkgs[pkg]
        pkgs = new_pkgs

    if not pkgs:
        print('no directory selected, check your options')
        sys.exit(1)

    logging.info('considering directories %s', pkgs.keys())

    # dictionary of dictionaries of sets
    commits_to_consider = defaultdict(lambda:defaultdict(set))
    for pkg in pkgs:
        first = True
        for commit in reversed(commits_list(pkgs[pkg]['base'] + '..', '--', pkg)):
            commits_to_consider[commit]['packages'].add(pkg)
            if first:
                commits_to_consider[commit]['first'].add(pkg)
                first = False

    if not commits_to_consider:
        print('error: nothing to push')
        sys.exit(1)

    # we want to stage the commits in a temporary branch before pushing it to
    # the remote
    branches = git_o(['branch'])
    tmp_branch_name = branch
    cnt = 1
    while tmp_branch_name in branches:
        tmp_branch_name = '{0}-tmp{1}'.format(branch, cnt)
        cnt += 1
    if tmp_branch_name != branch:
        logging.info('using temporary branch name %s', tmp_branch_name)

    try:
        pushurl = git_config('remote.{0}.pushurl'.format(remote))
    except CalledProcessError:
        pushurl = git_config('remote.{0}.url'.format(remote))

    with TemporaryDirectory() as tmpdir:
        tmprepo = os.path.join(tmpdir, remote)
        check_call(['git', 'clone', '--quiet', '--no-checkout',
                    '--reference', topdir, topdir, tmprepo])
        first = True
        for commit in sorted(commits_to_consider, cmp=commits_cmp):
            logging.info('applying commit %s', commit)
            commit_info = commits_to_consider[commit]
            if commit_info['first']:
                logging.debug('first commit for dirs: %s',
                              list(commit_info['first']))
            for pkg in commit_info['first']:
                if first:
                    git(['checkout', '--quiet',
                         '-b', tmp_branch_name, pkgs[pkg]['imported']],
                         cwd=tmprepo)
                    first = False
                else:
                    git(['merge', '--quiet', pkgs[pkg]['imported']],
                        cwd=tmprepo)
                rmtree(os.path.join(tmprepo, pkg))
                git(['checkout', '--quiet', commit, '--', pkg], cwd=tmprepo)
            pkgs_to_patch = list(commit_info['packages'] - commit_info['first'])
            if pkgs_to_patch:
                patch = git_o(['log', '--no-color', '-p', '-n', '1', commit, '--'] +
                              pkgs_to_patch, cwd=tmprepo, no_strip=True)
                if patch:
                    proc = Popen(['git', 'apply', '--index'], stdin=PIPE, cwd=tmprepo)
                    proc.communicate(patch)
                    if proc.returncode:
                        raise CalledProcessError(proc.returncode, ['git', 'apply', '--index'])
            if git_o(['status', '--porcelain'], cwd=tmprepo):
                git(['commit', '-C', commit], cwd=tmprepo)
            else:
                logging.info('no changes')
        git(['push', '--quiet', 'origin', tmp_branch_name], cwd=tmprepo)

    try:
        git(['push', remote, '{0}:{1}'.format(tmp_branch_name, branch)])
    except:
        logging.error("Failed to push to %s",remote)
        logging.warning("Command was 'git push %s %s:%s'", remote, tmp_branch_name, branch)
        if opts.keep_temp:
            logging.error("Keeping temporary branch %s", tmp_branch_name)
        else:
            logging.warning("For inspection with vanilla git (e.g. --force) use")
            logging.warning(" git lb-push --keep-temp-branch ...")
        logging.info("")
        logging.info("Possible reasons are: no push permission or branch with the same name exists and cannot be fast-forwarded.")
    else:
        new_base = git_o(['rev-parse', 'HEAD'])
        new_imported = git_o(['rev-parse', tmp_branch_name])
        for pkg in pkgs:
            git_config('.'.join(['lb-checkout', remote, pkg, 'base']), new_base,
                       configfile=configfile)
            git_config('.'.join(['lb-checkout', remote, pkg, 'imported']), new_imported,
                       configfile=configfile)
    finally:
        if opts.keep_temp:
            logging.warning('Keeping branch %s. It\'s up to you to delete it.', tmp_branch_name)
        else:
            git_o(['branch', '-D', tmp_branch_name])
