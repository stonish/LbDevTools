#!/usr/bin/env python
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
'''
Helpers to manipulate source files
Check that each git tracked source file in the current directory contains a
copyright statement.
'''
from __future__ import print_function

import os
import re
from itertools import islice
from datetime import date

COPYRIGHT_SIGNATURE = re.compile(r'\bcopyright\b', re.I)
CHECKED_FILES = re.compile(
    r'.*(\.(i?[ch](pp|xx|c)?|cc|hh|py|C|cmake|[yx]ml|qm[ts]|dtd|xsd|ent|bat|[cz]?sh)|'
    r'CMakeLists.txt)$')

COPYRIGHT_STATEMENT = '''
(c) Copyright {} CERN for the benefit of the LHCb Collaboration

This software is distributed under the terms of the GNU General Public
Licence version 3 (GPL Version 3), copied verbatim in the file "COPYING".

In applying this licence, CERN does not waive the privileges and immunities
granted to it by virtue of its status as an Intergovernmental Organization
or submit itself to any jurisdiction.
'''

# see https://www.python.org/dev/peps/pep-0263 for the regex
ENCODING_DECLARATION = re.compile(
    r'^[ \t\f]*#.*?coding[:=][ \t]*([-_.a-zA-Z0-9]+)')

CLANG_FORMAT_VERSION = '7'
YAPF_VERSION = '0.24.0'
FORMATTABLE_LANGUAGES = ['c', 'py']


def is_script(path):
    '''
    Check if a given file starts with the magic sequence '#!'.
    '''
    with open(path, 'rb') as f:
        return f.read(2) == b'#!'


def to_check(path):
    '''
    Check if path is meant to contain a copyright statement.
    '''
    return os.path.isfile(path) and (bool(CHECKED_FILES.match(path))
                                     or is_script(path))


def has_copyright(path):
    '''
    Check if there's a copyright signature in the first 100 lines of a file.
    '''
    with open(path) as f:
        return any(COPYRIGHT_SIGNATURE.search(l) for l in islice(f, 100))


def get_files(reference=None):
    '''
    Return iterable with the list of names of files to check.
    '''
    from subprocess import check_output
    if reference is None:
        all = check_output(['git', 'ls-files',
                            '-z']).rstrip('\x00').split('\x00')
    else:
        prefix_len = len(
            check_output(['git', 'rev-parse', '--show-prefix']).strip())
        all = (path[prefix_len:] for path in check_output([
            'git', 'diff', '--name-only', '--no-renames', '--diff-filter=MA',
            '-z', reference + '...', '.'
        ]).rstrip('\x00').split('\x00'))
    return (path for path in all if to_check(path))


def report(filenames, inverted=False, target=None):
    '''
    Print a report with the list of filenames.

    If porcelain is True, print only the names without descriptive message.
    '''
    print(
        ('The following {} files {}contain a copyright statement:\n- ').format(
            len(filenames), '' if inverted else 'do not '),
        end='')
    print('\n- '.join(filenames))
    if not inverted:
        if target:
            print('\nYou can fix the {} files without copyright statement '
                  'with:\n\n  $ lb-check-copyright --porcelain {} '
                  '| xargs -r lb-add-copyright\n'.format(
                      len(filenames), target))
        else:
            print('\nyou can fix them with the command lb-add-copyright\n')


def to_comment(text, lang_family='#', width=80):
    r'''
    Convert a chunk of text into comment for source files.

    The parameter lang_family can be used to tune the style of the comment:

        - 'c' for C/C++
        - '#' (default) for Python, shell, etc.
        - 'xml' for XML files

    >>> print(to_comment('a\nb\nc\n'), end='')
    ###############################################################################
    # a                                                                           #
    # b                                                                           #
    # c                                                                           #
    ###############################################################################
    >>> print(to_comment('a\nb\nc\n', 'c'), end='')
    /*****************************************************************************\
    * a                                                                           *
    * b                                                                           *
    * c                                                                           *
    \*****************************************************************************/
    >>> print(to_comment('a\nb\nc\n', 'xml'), end='')
    <!--
        a
        b
        c
    -->
    '''
    if lang_family == 'c':
        head = '/{}\\'.format((width - 3) * '*')
        line = '* {:%d} *' % (width - 5)
        tail = '\\{}/'.format((width - 3) * '*')
    elif lang_family in ('#', 'py'):
        head = (width - 1) * '#'
        line = '# {:%d} #' % (width - 5)
        tail = head
    elif lang_family == 'xml':
        head = '<!--'
        line = '    {}'
        tail = '-->'
    else:
        raise ValueError('invalid language family: {}'.format(lang_family))

    data = [head]
    data.extend(line.format(l.rstrip()).rstrip() for l in text.splitlines())
    data.append(tail)
    data.append('')
    return '\n'.join(data)


def lang_family(path):
    '''
    Detect language family of a file.
    '''
    if re.match(r'.*\.(xml|xsd|dtd|html?|qm[ts]|ent)$', path):
        return 'xml'
    elif re.match(r'.*\.(i?[ch](pp|xx|c)?|cc|hh|C|opts)$', path):
        return 'c'
    elif re.match(r'.*\.py$', path) or re.match(r'^#!.*python',
                                                open(path).readline(120)):
        return 'py'
    else:
        return '#'


def find_encoding_declaration_line(lines, limit=2):
    '''
    Look for encoding declaration line (PEP-263) in a file and return the index
    of the line containing it, or None if not found.
    '''
    for i, l in enumerate(islice(lines, limit)):
        if ENCODING_DECLARATION.match(l):
            return i


def add_copyright_to_file(path, year=None):
    '''
    Add copyright statement to the given file for the specified year (or range
    of years).  If the year argument is not specified, the current year is
    used.
    '''
    lang = lang_family(path)
    text = to_comment(
        COPYRIGHT_STATEMENT.format(year or date.today().year).strip(), lang)
    with open(path, 'rb') as f:
        data = f.readlines()

    offset = 0
    encoding_offset = find_encoding_declaration_line(data)
    if encoding_offset is not None:
        offset = encoding_offset + 1
    elif data[0].startswith('#!'):
        offset = 1
    elif lang == 'xml':
        offset = 1 if not path.endswith('.ent') else 0
        for l in data:
            if l.strip():
                # lcgdict selection files are a bit special
                if 'lcgdict' in l or '<!--' in l:
                    offset = 0
                break

    data.insert(offset, text)
    with open(path, 'wb') as f:
        f.writelines(data)


def call_formatter(cmd, input):
    '''
    Return the formatted version of the given file.
    '''
    from subprocess import Popen, PIPE, CalledProcessError
    p = Popen(cmd, stdout=PIPE, stdin=PIPE)
    out, _ = p.communicate(input)
    if p.returncode:
        raise CalledProcessError(p.returncode, cmd)
    return out


def get_git_root(path):
    from subprocess import Popen, PIPE
    if not os.path.isdir(path):
        path = os.path.dirname(path)
    p = Popen(['git', 'rev-parse', '--show-toplevel'],
              cwd=path,
              stdout=PIPE,
              stderr=PIPE)
    out, _ = p.communicate()
    if p.returncode == 0:
        return out.strip()
    else:
        return None


def find_clang_format(path):
    while not os.path.isdir(path):
        path = os.path.dirname(path)
    while True:
        parent = os.path.dirname(path)
        if os.path.exists(os.path.join(path, '.clang-format')):
            return path
        elif parent != path:
            path = parent
        else:
            return None  # root dir reached


_found_clang_format_dirs = []


def ensure_clang_format_style(path):
    from logging import debug
    path = os.path.abspath(path)
    global _found_clang_format_dirs
    if not any(
            os.path.commonprefix([d, path]) for d in _found_clang_format_dirs):
        base = find_clang_format(path)
        if base:
            debug('found .clang-format in %s', base)
            _found_clang_format_dirs.append(base)
        else:
            base = get_git_root(path)
            debug('found .git top dir in %s', base)
            if base:
                from LbDevTools import createClangFormat
                createClangFormat(os.path.join(base, '.clang-format'))
                _found_clang_format_dirs.append(base)


# --- Scripts


def check_copyright():
    from argparse import ArgumentParser
    parser = ArgumentParser(description='''
    Check that each git tracked source file in the current directory contains a
    copyright statement.
    ''')
    parser.add_argument(
        'reference',
        nargs='?',
        help='commit-ish to use as reference to only check changed file')
    parser.add_argument(
        '--porcelain',
        action='store_true',
        help='only print the list of files w/o copyright')
    parser.add_argument(
        '-z',
        action='store_const',
        dest='separator',
        const='\x00',
        help='when using --porcelain, paths are separated with NUL character')
    parser.add_argument(
        '--inverted',
        action='store_true',
        help='list files w/ copyright, instead of w/o (Default)')
    parser.set_defaults(inverted=False, separator='\n')

    args = parser.parse_args()

    missing = [
        path for path in get_files(args.reference)
        if os.stat(path).st_size and not (args.inverted ^ has_copyright(path))
    ]
    if missing:
        missing.sort()
        if not args.porcelain:
            report(missing, args.inverted, args.reference)
        else:
            print(args.separator.join(missing), end=args.separator)
        exit(1)


def add_copyright():
    from argparse import ArgumentParser
    parser = ArgumentParser(
        description='Add standard LHCb copyright statement to files.')
    parser.add_argument('files', nargs='+', help='files to modify')
    parser.add_argument(
        '--year', help='copyright year specification (default: current year)')
    parser.add_argument(
        '--force',
        action='store_true',
        help='add copyright also to non supported file types')

    args = parser.parse_args()

    for path in args.files:
        if not args.force and not to_check(path):
            print('warning: cannot add copyright to {} (file type not '
                  'supported)'.format(path))
        elif has_copyright(path):
            print('warning: {} already has a copyright statement'.format(path))
        else:
            add_copyright_to_file(path, args.year)


def format():
    from argparse import ArgumentParser
    import logging
    parser = ArgumentParser(description='Reformat C++ and Python files.')
    parser.add_argument(
        'files',
        nargs='*',
        help='files to modify (empty list means all git tracked files)')
    parser.add_argument(
        '--clang-format-version',
        help='version of clang-format to use '
        '(default: %(default)s)')
    parser.add_argument(
        '--yapf-version', help='version of yapf to use (default: %(default)s)')
    parser.add_argument(
        '--debug',
        action='store_const',
        const=logging.DEBUG,
        dest='log_level',
        help='print debug messages')
    parser.add_argument(
        '-n', '--dry-run', action='store_true', help='do not modify the files')
    parser.add_argument(
        '--format-patch',
        help='create a patch file with the changes, '
        'in this mode the first file argument is interpreted '
        'as reference branch')
    parser.add_argument(
        '-P',
        '--pipe',
        metavar='LANGUAGE',
        choices=FORMATTABLE_LANGUAGES,
        help='format from stdin to stdout (allowed values: %s)' %
        FORMATTABLE_LANGUAGES)
    parser.set_defaults(
        files=[],
        clang_format_version=CLANG_FORMAT_VERSION,
        yapf_version=YAPF_VERSION,
        log_level=logging.WARNING)

    args = parser.parse_args()
    logging.basicConfig(level=args.log_level)

    if args.format_patch and args.pipe:
        parser.error('incompatible options --format-patch and -P/--pipe')

    if args.format_patch and len(args.files) > 1:
        parser.error('wrong number of arguments: at most one argument must be '
                     'provided when using --format-patch')

    if args.pipe and args.files:
        parser.error('cannot process explicit files in --pipe mode')

    from logging import debug, warning
    from subprocess import check_output, CalledProcessError
    from whichcraft import which
    from difflib import unified_diff

    # look for the required commands
    for clang_format_cmd in [
            'clang-format-{}', 'lcg-clang-format-{}', 'lcg-clang-format-{}.0',
            'lcg-clang-format-{}.0.0'
    ]:
        clang_format_cmd = which(
            clang_format_cmd.format(args.clang_format_version))
        if clang_format_cmd:
            debug('using clang-format: %s', clang_format_cmd)
            break
    else:
        (parser.error if args.pipe == 'c' else warning)(
            'clang-format-%s not found: C/C++ formatting not available' %
            args.clang_format_version)

    yapf_cmd = which('yapf')
    bad_yapf = (parser.error if args.pipe == 'py' else warning)
    if not yapf_cmd:
        bad_yapf('yapf not found: Python formatting not available')
    else:
        yapf_found_version = check_output([yapf_cmd, '--version']).split()[-1]
        if yapf_found_version == args.yapf_version:
            debug('using yapf: %s', yapf_cmd)
        else:
            bad_yapf('wrong yapf version %s (%s required): '
                     'Python formatting not available' % (yapf_found_version,
                                                          args.yapf_version))
            yapf_cmd = None

    def can_format(path):
        if to_check(path):
            lang = lang_family(path)
            if ((clang_format_cmd and lang == 'c')
                    or (yapf_cmd and lang == 'py')):
                return lang
        return None

    if not args.pipe:
        if not args.files:
            args.files = filter(can_format, get_files())
        elif args.format_patch:
            # if we have args for --format-patch, it's a reference commit
            args.files = filter(can_format, get_files(args.files[0]))

    if args.pipe:
        import sys
        if args.pipe == 'c':
            ensure_clang_format_style(os.getcwd())
            cmd = [clang_format_cmd, '-style=file', '-fallback-style=none']
        else:
            cmd = yapf_cmd
        debug('cmd %s', cmd)
        print(call_formatter(cmd, sys.stdin.read()), end='')
    patch = []
    for path in args.files:
        lang = can_format(path)
        if lang:
            if lang == 'c':
                ensure_clang_format_style(path)
                cmd = [
                    clang_format_cmd, '-style=file', '-fallback-style=none',
                    '-assume-filename=' + path
                ]
            else:
                cmd = yapf_cmd
            try:
                with open(path) as f:
                    input = f.read()
                output = call_formatter(cmd, input)
                if args.format_patch:
                    patch.extend(
                        unified_diff(
                            input.splitlines(True), output.splitlines(True),
                            os.path.join('a', path), os.path.join('b', path)))
                elif output != input:
                    if args.dry_run:
                        print(path, 'should be changed')
                    else:
                        debug('%s changed', path)
                        with open(path, 'w') as f:
                            f.write(output)
            except CalledProcessError as err:
                warning('could not format %r: %s', path, err)
        else:
            warning('cannot format %s (file type not supported)', path)

    # check if we need to create a patch file
    if patch:
        # we found some
        from email.message import Message
        from email.utils import formatdate
        msg = Message()
        msg.add_header('From', 'Gitlab CI <noreply@cern.ch>')
        msg.add_header('Date', formatdate())
        msg.add_header('Subject', '[PATCH] Fixed formatting')
        msg.set_payload('\n'.join([
            'patch generated by {}'.format(
                '{CI_PROJECT_URL}/-/jobs/{CI_JOB_ID}'.format(
                    **os.environ) if 'CI' in os.environ else 'standalone job'),
            '', '', ''.join(patch)
        ]))
        if args.format_patch == '-':
            print(msg.as_string())
        else:
            if (os.path.dirname(args.format_patch)
                    and not os.path.isdir(os.path.dirname(args.format_patch))):
                os.makedirs(os.path.dirname(args.format_patch))
            with open(args.format_patch, 'wb') as patchfile:
                patchfile.write(msg.as_string())
            print(
                '=======================================',
                ' You can fix formatting with:',
                '',
                sep='\n')
            if 'CI' in os.environ:
                print('   curl {CI_PROJECT_URL}/-/jobs/{CI_JOB_ID}/'
                      'artifacts/raw/{0} | '
                      'git am'.format(args.format_patch, **os.environ))
            else:
                print('   git am {}'.format(args.format_patch))
            print('', '=======================================', sep='\n')
        exit(1)


if __name__ == '__main__':
    # when invoked as a script, call the function with the same name
    # (check_copyright if no match)
    import sys
    name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
    if name.startswith('lb-'):  # special cases
        name = name[3:].replace('-', '_')
    main = globals().get(name, check_copyright)
    main()
