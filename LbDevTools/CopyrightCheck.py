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
Check that each git tracked source file in the current directory contains a
copyright statement.
'''
from __future__ import print_function

import os
import re
from itertools import islice
from datetime import date

COPYRIGHT_SIGNATURE = re.compile(r'Copyright\s*(\(c\)\s*)?\d+(-\d+)?', re.I)
CHECKED_FILES = re.compile(
    r'.*(\.(i?[ch](pp|xx)?|cc|hh|py|C|cmake|[yx]ml|qm[ts]|dtd|bat|[cz]?sh)|'
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
ENCODING_DECLARATION = re.compile(r'^[ \t\f]*#.*?coding[:=][ \t]*([-_.a-zA-Z0-9]+)')


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


def report(filenames, inverted=False):
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
    elif lang_family == '#':
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
    if re.match(r'.*\.(xml|dtd|html?|qm[ts])$', path):
        return 'xml'
    elif re.match(r'.*\.(i?[ch](pp|xx)?|cc|hh|C|opts)$', path):
        return 'c'
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
        offset = 1
        for l in data:
            if l.strip():
                # lcgdict selection files are a bit special
                if 'lcgdict' in l or '<!--' in l:
                    offset = 0
                break

    data.insert(offset, text)
    with open(path, 'wb') as f:
        f.writelines(data)


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
            report(missing, args.inverted)
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

    args = parser.parse_args()

    for path in args.files:
        if has_copyright(path):
            print('warning: {} already has a copyright statement'.format(path))
        else:
            add_copyright_to_file(path, args.year)


if __name__ == '__main__':
    # when invoked as a script, call the function with the same name
    # (check_copyright if no match)
    import sys
    name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
    main = globals().get(name, check_copyright)
    main()
