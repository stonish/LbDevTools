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


CODE = r'''
if ! declare -F _git >/dev/null ; then
  if [ -e ] ; then
    source /etc/bash_completion.d/git
  fi
fi

__git_lb_projects=
__git_lb_compute_projects ()
{
  : ${__git_lb_projects:=$(python -c 'from LbEnv import getProjectNames as ps; print " ".join(p for p in sorted(ps()) if p.upper()!=p)')}
}

_git_lb_use ()
{
  local i c=1 b=-1
  while [ $c -lt $COMP_CWORD ]; do
    i="${COMP_WORDS[c]}"
    case "$i" in
      -*) ;;
      *) ((b++)) ;;
    esac
    ((c++))
  done

  local cur="${COMP_WORDS[COMP_CWORD]}"
  case "$cur" in
  --protocol=*)
    __gitcomp "krb5 ssh https" "" "${cur##--protocol=}"
    ;;
  --*)
    __gitcomp "--version --protocol= --quiet --verbose --debug"
    ;;
  *)
    case "$b" in
      0)
        __git_lb_compute_projects
        __gitcomp "$__git_lb_projects" ;;
      # FIXME: this is not really working
      # 1)
      #   COMPREPLY=($(compgen \
      #     -W "https://:@gitlab.cern.ch:8443/lhcb/ ssh://git@gitlab.cern.ch:7999/lhcb/ https://gitlab.cern.ch/lhcb/" \
      #     -- "$cur"))
      #         ;;
      *) COMPREPLY=() ;;
    esac
  esac
}

_git_lb_checkout ()
{
  local i c=1 b=-1
  while [ $c -lt $COMP_CWORD ]; do
    i="${COMP_WORDS[c]}"
    case "$i" in
      -*) ;;
      *) ((b++)) ;;
    esac
    ((c++))
  done

  local cur="${COMP_WORDS[COMP_CWORD]}"
  case "$cur" in
  --*)
    __gitcomp "--commit --no-commit --list --version --quiet --verbose --debug"
    ;;
  *)
    case $b in
    0)
      if [[ "$cur" != */* ]] ; then
        COMPREPLY=($(compgen -W "$(git remote)" -S / -- "$cur"))
      else
        __gitcomp "$(__git_refs | grep "^${cur}")"
      fi
      ;;
    1)
      __gitcomp "$(git ls-tree --name-only -r ${COMP_WORDS[$((COMP_CWORD-1))]} | sed -En 's#(.*)/CMakeLists.txt#\1#p')"
      ;;
    esac
  esac
}

_git_lb_push ()
{
  local i c=1 b=-1
  while [ $c -lt $COMP_CWORD ]; do
    i="${COMP_WORDS[c]}"
    case "$i" in
    -*) ;;
    *) ((b++)) ;;
    esac
    ((c++))
  done

  local cur="${COMP_WORDS[COMP_CWORD]}"
  case "$cur" in
  --*)
    __gitcomp "--keep-temp-branch --version --quiet --verbose --debug"
    ;;
  *)
    case $b in
    0)
      __gitcomp "$(git remote)"
      ;;
    1)
      if [ -z "$cur" ] ; then
        COMPREPLY=($USER-)
      fi
      ;;
    esac
  esac
}
'''


def main():
    '''
    Print a shell script that enables shell completion.
    '''
    print(CODE)


if __name__ == '__main__':
    main()
