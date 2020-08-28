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
"""Generate release notes draft.

See `lb-gen-release-notes --help` for details.

"""
from __future__ import print_function

from __future__ import absolute_import
import re
import os
import sys
import argparse
import itertools
import json
import logging
import datetime
import gitlab
from collections import OrderedDict
from jinja2 import Environment, FileSystemLoader

import subprocess

from LbDevTools import __version__
import six


def rel_project_path(path, to):
    """Return the common path component.

    >>> rel_project_path('lhcb/LHCb', 'lhcb/Lbcom')
    'LHCb'
    >>> rel_project_path('gaudi/Gaudi', 'lhcb/Lbcom')
    'gaudi/Gaudi'
    >>> rel_project_path('lhcb/LHCb', 'lhcb/LHCb')
    ''

    """
    path = path.split("/")
    to = to.split("/")
    parts = list(
        itertools.dropwhile(
            lambda x: x[0] < len(to) and to[x[0]] == x[1], enumerate(path)
        )
    )
    return "/".join(list(zip(*parts))[1]) if parts else ""


def getOutput(*args, **kwargs):
    """
    Helper function to get the standard output of a command.

    If the command fails, raise CalledProcessError (see subprocess.check_call).
    """
    logging.debug("getting output of %s", subprocess.list2cmdline(args[0]))
    kwargs["stdout"] = subprocess.PIPE
    do_strip = not kwargs.pop("no_strip", False)
    proc = subprocess.Popen(*args, **kwargs)
    out, _ = proc.communicate()
    if proc.returncode:
        raise subprocess.CalledProcessError(proc.returncode, args[0])
    if do_strip:
        out = out.strip()
    # logging.debug('\n==============\n%s==============', out)
    return out


def git(*args, **kwargs):
    """
    Helper function to call git.
    """
    args[0].insert(0, "git")
    logging.debug("calling %s", args[0])
    subprocess.check_call(*args, **kwargs)


def git_o(*args, **kwargs):
    """
    Helper function to get the output of a call to git.
    """
    args[0].insert(0, "git")
    return getOutput(*args, **kwargs).decode()


def ref_names(repo, commit):
    """
    Return matching ref names for a given commit.
    """
    result = git_o(["log", "-1", "--decorate=full", "--pretty=%d", commit], cwd=repo)
    return [x.strip() for x in result[1:-1].split(",")]


def find_merge_request_id(repo, merge_commit, second_parent):
    """
    Find a merge request iid given a merge commit and its second parent.

    First tries to match the second parent to a merge request ref name.
    If this fails (e.g. for squashed commits), a match is attempted
    based on the merge commit message.
    """
    names = ref_names(repo, second_parent)
    m = [
        re.match(r"^refs/remotes/origin/merge-requests/(\d+)$", name) for name in names
    ]
    m = [_f for _f in m if _f]
    if m:
        if len(m) > 1:
            logging.warning(
                "Multiple merge requests associated with {}: {}. "
                "Taking the first.".format(second_parent, [i.group(1) for i in m])
            )
        return int(m[0].group(1))
    logging.debug(
        "Second parent of {} ({}) does not correspond to a merge "
        "request ref.".format(merge_commit, second_parent)
    )
    # For squashed commits, the MR reference stays at the last MR commit
    # while the second parent is the new squashed commit. It is hard to
    # precisely match the commits, so let's look at the merge commit message
    message = git_o(["show", "-s", "--format=%B", merge_commit], cwd=repo)
    m = re.search("^See merge request [^ ]*!([0-9]+)$", message, re.MULTILINE)
    if m:
        return int(m.group(1))
    logging.warning(
        "Could not find MR for {} based on second parent ({}) refs or commit "
        "message.\nDid you squash _and_ modify message or did you even push "
        "directly from the command line?".format(merge_commit, second_parent)
    )
    return None


def find_merge_requests_git(project, repo, since, until=""):
    """
    Find GitLab merge requests using the git commit history.
    """
    git(
        [
            "fetch",
            "-q",
            "origin",
            "+refs/merge-requests/*/head:refs/remotes/origin/merge-requests/*",
        ],
        cwd=repo,
    )
    log = git_o(
        [
            "log",
            "--first-parent",
            "--parents",
            "--merges",
            "--pretty=oneline",
            "--no-color",
            "{}..{}".format(since, until),
        ],
        cwd=repo,
    )
    commits = [line.split()[:3] for line in log.splitlines()]
    iids = [find_merge_request_id(repo, commit[0], commit[2]) for commit in commits]
    iids = [iid for iid in iids if iid]
    # .list(iids=iids) produces a wrong query, so do it semi-manually:
    # TODO fix this in a future version of python-gitlab
    mrs = project.mergerequests.list(all=True, **{"iids[]": iids}) if iids else []
    if len(mrs) != len(iids):
        raise RuntimeError(
            "Could not list all {} MRs, got {}".format(len(iids), len(mrs))
        )
    return mrs


def find_project_fullname(repo):
    """
    Find the GitLab full project name given a git repository.

    The project name is inferred from the url of the 'origin' remote.
    """
    remotes = git_o(["remote", "-v"], cwd=repo)
    for remote in remotes.splitlines():
        m = re.match(r"^origin\s+.*gitlab\.cern\.ch.*/([^/]+/[^/]+)\.git", remote)
        if m:
            return m.group(1)
    logging.error("Could not find gitlab project with `git remote -v`.")
    sys.exit(1)


def guess_project_fullname(name):
    return ("gaudi/" if name == "Gaudi" else "lhcb/") + name


def find_merge_requests_milestone(project, milestone_title):
    """
    Find GitLab merge requests with a given milestone.
    """
    try:
        milestones = [
            m
            for m in project.milestones.list(search=milestone_title)
            if m.title == milestone_title
        ]
    except gitlab.GitlabAuthenticationError:
        logging.error("Milestones cannot be retrieved: provide GitLab token.")
        return []

    if not milestones:
        logging.debug(
            "Milestone {} not found in GitLab project {}".format(
                milestone_title, project.name
            )
        )
        return []
    elif len(milestones) > 1:
        logging.error(
            "Multiple milestones {} found in GitLab project {}".format(
                milestone_title, project.name
            )
        )
        sys.exit(1)

    milestone = milestones[0]
    return list(milestone.merge_requests())


def find_merge_request_issues(mr, project_fullname):
    """
    Find references to GitLab issues or JIRA tasks in title/description.
    """

    def norm(group, name, issue):
        if not name:
            return issue
        else:
            if not group:
                group = project_fullname.rsplit("/", 1)[0] + "/"
            return rel_project_path(group + name, project_fullname) + issue

    jira_re = r"[A-Z][A-Z]+-[0-9]+"
    jira_tasks = re.findall(jira_re, mr.title) + re.findall(jira_re, mr.description)
    gl_re = r"(?:((?:[^/\s]+/)*)([^/\s]+))?(#[0-9]+)"
    gl_issues = [
        norm(*m)
        for m in re.findall(gl_re, mr.title) + re.findall(gl_re, mr.description)
    ]
    return sorted(set(gl_issues)) + sorted(set(jira_tasks))


def find_merge_requests(server, repo, since, milestone):
    """"""
    project_fullname = find_project_fullname(repo)
    project = server.projects.get(project_fullname)
    git_mrs = find_merge_requests_git(project, repo, since)
    gitlab_mrs = find_merge_requests_milestone(project, milestone)
    logging.debug("Found these MRs in git history: {}".format(git_mrs))
    logging.debug("Found these MRs in GitLab: {}".format(gitlab_mrs))

    if not gitlab_mrs:
        logging.warning(
            "No merge requests found with {} milestone for {}".format(
                milestone, project_fullname
            )
        )
    else:
        # Cross-check git repo with GitLab
        for mr in git_mrs:
            if mr.id not in [x.id for x in gitlab_mrs]:
                logging.warning("Milestone not set for MR {}".format(mr.web_url))
        for mr in gitlab_mrs:
            if mr.id not in [x.id for x in git_mrs]:
                logging.warning(
                    "MR {} is not merged in current branch "
                    "after tag {} (state {})".format(mr.web_url, since, mr.state)
                )
                git_mrs.append(mr)

    for mr in git_mrs:
        mr.issue_refs = find_merge_request_issues(mr, project_fullname)
        mr.fullname = project_fullname
    return git_mrs


def find_dependencies(stack_config, project_name):
    all_deps = OrderedDict()
    remaining = [project_name]
    while remaining:
        dependencies = set().union(
            *(stack_config.get(name, (None, None, []))[2] for name in remaining)
        )
        remaining = []
        for d in dependencies:
            assert d not in all_deps, "circular dependency detected"
            all_deps[d] = stack_config[d]
            remaining.append(d)
    return all_deps


def get_template(template, template_paths):
    """
    Return a jinja2.Template from a name and a search path list.

    Some useful functions are added to the environment such that
    they can be used in the template:
    - select_mrs: filter MRs based on labels,
    - order_by_label: order MRs according to labels,
    - mdindent: indent a block of text the markdown way,
    - label_ref: print a reference to a label,
    - sentence: capitalize first character.
    """

    def select_mrs(mrs, labels, used=None):
        """
        Return unused MRs that match some labels.

        `labels` can be of the form `['one', ['two', 'three']]`,
        which will match any MR that "has 'one' or (has 'two' and has
        'three')". `labels=[[]]` will match everything.
        """
        label_sets = [
            set([ls] if isinstance(ls, six.string_types) else ls) for ls in labels
        ]
        label_sets = [set(l.lower() for l in ls) for ls in label_sets]
        matches = []
        for mr in mrs:
            if used is not None and mr.id in used:
                continue
            mr_labels = [l.lower() for l in mr.labels]
            if any(ls.issubset(mr_labels) for ls in label_sets):
                if used is not None:
                    used.append(mr.id)
                matches.append(mr)
        return matches

    def mdindent(s, width=2, indentfirst=False):
        return "  \n".join(
            width * (indentfirst or i > 0) * " " + line
            for i, line in enumerate(s.splitlines())
        )

    def find_tasks(mr):
        import warnings

        warnings.warn(
            "find_tasks is deprecated, instead please use\n"
            '{% if mr.issue_refs %} [{{mr.issue_refs|join(",")}}]{% endif %}'
        )
        pattern = r"[A-Z]+-[0-9]+"
        tasks = sorted(
            set(re.findall(pattern, mr.title) + re.findall(pattern, mr.description))
        )
        return "[{}]".format(",".join(tasks)) if tasks else ""

    def order_by_label(mrs, label_order):
        """Order MRs according to label_order."""
        label_order = [l.lower() for l in label_order]

        def key(mr):
            labels = [l.lower() for l in mr.labels]
            k = [i for i, l in enumerate(label_order) if l in labels]
            return k if k else [len(label_order)]  # sort unlabelled to the end

        return sorted(mrs, key=key)

    def label_ref(label):
        return ('~"{}"' if " " in label else "~{}").format(label)

    def mr_ref(mr, relative_to=""):
        return rel_project_path(mr.fullname, relative_to) + mr.reference

    env = Environment(
        autoescape=False,
        loader=FileSystemLoader(template_paths),
        trim_blocks=False,
        lstrip_blocks=False,
    )
    env.globals["select_mrs"] = select_mrs
    env.globals["find_tasks"] = find_tasks  # for backward compatibility
    env.globals["order_by_label"] = order_by_label
    env.filters["mdindent"] = mdindent
    env.filters["label_ref"] = label_ref
    env.filters["mr_ref"] = mr_ref
    env.filters["sentence"] = lambda s: s[0].upper() + s[1:]

    return env.get_template(template)


def main(args=None):
    parser = argparse.ArgumentParser(
        description="Generate release notes draft.",
        epilog="""
Example:
  Change directory to a full project clone, checkout the release branch
  and call %(prog)s:

    $ git clone https://:@gitlab.cern.ch:8443/lhcb/Hlt.git
    $ cd Hlt
    $ git checkout -b v27r0-release master  # assuming release from master
    $ %(prog)s v26r6 v27r0

  The project template `ReleaseNotes/release_notes_template.md` is used
  if it exists and otherwise a default template is taken. The draft
  release notes are written under `ReleaseNotes/` by default.
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version", action="version", version="%(prog)s {}".format(__version__)
    )
    parser.add_argument("previous", nargs="?", help="Previous (base) release")
    parser.add_argument("target", nargs="?", help="Target release")
    parser.add_argument("-s", "--stack", help="Path to json defining stack versions")
    parser.add_argument(
        "-t",
        "--template",
        default="release_notes_template.md",
        help="Template filename (searched in {repo}/ReleaseNotes and LbScripts)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="{repo}/ReleaseNotes/{target}{ext}",
        help="Output file",
    )
    parser.add_argument("-C", "--repo", default=".", help="Path to git repo")
    # branch?
    parser.add_argument(
        "--token", help="GitLab access token (defaults to $GITLAB_TOKEN)"
    )
    parser.add_argument("--debug", action="store_true", help="Increase verbosity")
    args = parser.parse_args(args)

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if not args.stack and not (args.previous and args.target):
        parser.error("Both previous and target versions need to be given.")

    project_fullname = find_project_fullname(args.repo)
    project_name = project_fullname.split("/")[-1]

    stack_config = None
    dependencies = {}
    if args.stack:
        with open(args.stack) as f:
            stack_config = json.load(f)
        dependencies = find_dependencies(stack_config, project_name)

    if not args.previous and stack_config:
        args.previous = stack_config[project_name][0]
        assert args.previous, "previous version not set in json"
    if not args.target and stack_config:
        args.target = stack_config[project_name][1]
        assert args.target, "target version not set in json"

    template_paths = [
        os.path.join(args.repo, "ReleaseNotes"),
        os.path.join(os.path.dirname(__file__), "templates"),
    ]
    logging.debug("Searching for templates in {}".format(template_paths))

    args.output = args.output.format(
        repo=args.repo, target=args.target, ext=os.path.splitext(args.template)[1]
    )

    if os.path.exists(args.output):
        logging.error("Output {} exists, aborting...".format(args.output))
        sys.exit(1)
    if not args.token:
        try:
            args.token = os.environ["GITLAB_TOKEN"]
        except KeyError:
            logging.warning(
                "Querying GitLab without token will disable some features.\n"
                "Either set $GITLAB_TOKEN or use --token.\nA token can be "
                "obtained from https://gitlab.cern.ch/profile/personal_access_tokens"
            )

    template = get_template(args.template, template_paths)
    print("Using template {}".format(template.filename))

    server = gitlab.Gitlab("https://gitlab.cern.ch/", args.token)
    mrs = find_merge_requests(server, args.repo, args.previous, args.target)

    def get_dep_mrs():
        dep_mrs = []
        for name, (previous, target, _) in dependencies.items():
            if target and previous and target != previous:
                dep_mrs.extend(
                    find_merge_requests(
                        server,
                        repo=os.path.join(os.path.dirname(args.stack), name),
                        since=previous,
                        milestone=target,
                    )
                )
        return dep_mrs

    project_deps = []
    for name, (_, ver, _) in dependencies.items():
        if name == "LCG":
            ver, text = ver.split(" ", 1) if " " in ver else (ver, "")
            project_deps.append(
                "LCG [{ver}](http://lcginfo.cern.ch/release/{ver}/) {text}".format(
                    ver=ver, text=text
                )
            )
        else:
            repo = os.path.join(os.path.dirname(args.stack), name)
            relpath = rel_project_path(guess_project_fullname(repo), project_fullname)
            project_deps.append(
                "{name} [{ver}]({dots}/{relpath}/-/tags/{ver})".format(
                    name=name,
                    ver=ver,
                    dots="/".join([".."] * (len(relpath.split("/")) + 1)),
                    relpath=relpath,
                )
            )

    context = {
        "project": project_name,
        "project_fullname": project_fullname,
        "project_deps": project_deps,
        "project_prev_tag": args.previous,
        "version": args.target,
        "date": datetime.date.today(),
        "merge_requests": mrs,
        "get_dep_mrs": get_dep_mrs,
    }
    with open(args.output, "w") as f:
        f.write(template.render(context))
    print("Release notes draft written to {}.".format(args.output))
