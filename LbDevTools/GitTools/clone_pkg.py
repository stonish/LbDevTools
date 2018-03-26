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

import logging
from subprocess import CalledProcessError
from LbDevTools.GitTools import git, git_o


BASE_URLS = {
    'ssh': 'ssh://git@gitlab.cern.ch:7999',
    'krb5':  'https://:@gitlab.cern.ch:8443',
    'https': 'https://gitlab.cern.ch',
}


def get_default_protocol():
    try:
        return git_o(['config', '--get', 'lb-use.protocol'])
    except CalledProcessError:
        return 'krb5'


def get_latest_tag(path):
    from subprocess import PIPE
    try:
        return git_o(['describe', '--match', '*', '--abbrev=0', '--tags'],
                     stderr=PIPE, cwd=path)
    except CalledProcessError:
        logging.debug('no tag in current branch of %s', path)
        from LbEnv.ProjectEnv.version import isValidVersion, versionKey
        all_tags = [v for v in git_o(['tag'], cwd=path).split()
                    if isValidVersion('', v)]
        all_tags.sort(key=versionKey)
        if all_tags:
            return all_tags[-1]
        return None


def main():
    import os
    from os.path import join, exists, basename
    from argparse import ArgumentParser
    parser = ArgumentParser(description='wrapper around "git clone" to get '
                            'data packages')

    parser.add_argument('url', nargs='?', help='git URL to use')
    parser.add_argument('name', help='name of the data package')

    git_group = parser.add_argument_group("'git clone' arguments")
    git_group.add_argument('-o', '--origin', metavar='NAME',
                           help="use NAME instead of 'origin' to track "
                           "upstream")
    git_group.add_argument('-b', '--branch',
                           help='checkout BRANCH instead of the remote\'s '
                           'HEAD')

    parser.add_argument('-v', '--verbose', action='store_const',
                        const=logging.INFO, dest='log_level')
    parser.add_argument('-d', '--debug', action='store_const',
                        const=logging.DEBUG, dest='log_level')

    parser.set_defaults(log_level=logging.WARNING)

    args = parser.parse_args()
    logging.basicConfig(level=args.log_level)

    if not args.url:
        args.url = '{}/lhcb-datapkg/{}.git'.format(
            BASE_URLS[get_default_protocol()],
            args.name
        )

    try:
        cmd = ['clone']
        if args.log_level <= logging.INFO:
            cmd.append('-v')
        if args.branch:
            cmd.append('--branch=' + args.branch)
        cmd.extend([args.url, args.name])
        git(cmd)

        logging.debug('initializing data package')
        old_xml_env = join(args.name,
                           args.name.replace('/', '_') + 'Environment.xml')
        if not exists(old_xml_env):
            logging.debug(' - adding %s', basename(old_xml_env))
            os.symlink(basename(old_xml_env.replace('Environment.xml',
                                                    '.xenv')),
                       old_xml_env)

        # guess version aliases
        version_aliases = ['v999r999']
        if exists(join(args.name, 'cmt', 'requirements')):
            for l in open(join(args.name, 'cmt', 'requirements')):
                l = l.strip()
                if l.startswith('version'):
                    version = l.split()[1]
                    version_aliases.append(version[:version.rfind('r')]
                                           + 'r999')
                    break
        else:
            version = get_latest_tag(args.name)
            if version:
                version_aliases.append(version[:version.rfind('r')] + 'r999')
        logging.debug(' - creating links %s in %s', version_aliases, args.name)
        for version in version_aliases:
            os.symlink(os.curdir, join(args.name, version))

    except CalledProcessError as exc:
        exit(exc.returncode)
