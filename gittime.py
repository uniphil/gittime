#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    gittime
    ~~~~~~~

    Estimate time spent programming, aided by git commit metadata. More
    documentation and stuff is in the readme.


    Example usage::

        python gittime.py git@github.com:uniphil/commit--blog.git


    For full usage details::

        python gittime.py --help


    :copyright: (c) 2014 by Phil Schleihauf.
    :licence: MIT, see LICENSE for more details.
"""

from __future__ import print_function

import shutil
from tempfile import mkdtemp
from datetime import datetime, timedelta

from pygit2 import clone_repository
from pygit2 import GIT_SORT_TIME, GIT_SORT_REVERSE


try:
    input = raw_input
except NameError:
    pass  # python3


class TempRepo(object):
    """Make a bare repository in a directory for safe isolated inspection."""

    def __init__(self, url):
        self.url = url

    def __enter__(self):
        self.path = mkdtemp()
        try:
            print('cloning {}... '.format(self.url), end='\n\n')
            repo = clone_repository(self.url, self.path, bare=True)
        except Exception as e:
            self.__exit__()  # make sure the temp directory gets cleaned up
            raise e
        return repo

    def __exit__(self, *exc_args):
        shutil.rmtree(self.path, onerror=self.on_cleanup_error)

    def on_cleanup_error(self, raising_fn, path, exc):
        Warn('{:.__name__} failed for {}: {}'.format(raising_fn, path, exc))


class T(object):
    """A namespace for templating functions"""

    indentation = 2
    bullet_character = "*"

    @staticmethod
    def indent_line(line):
        template = "{spaces}{line}"
        spaces = " " * T.indentation
        return template.format(spaces=spaces, line=line)

    @staticmethod
    def indent(message):
        return '\n'.join(map(T.indent_line, message.splitlines()))

    @staticmethod
    def bullet(message):
        template = "{bullet} {firstline}\n{otherlines}"
        lines = message.splitlines()
        return template.format(bullet=T.bullet_character,
                               firstline=lines[0],
                               otherlines=T.indent('\n'.join(lines[1:])))

    @staticmethod
    def nice_time(time_obj):
        return time_obj.strftime('%A, %b %d at %X')

    @staticmethod
    def nice_timedelta(delta_obj):
        if delta_obj is None:
            return 'undefined'
        elif delta_obj < timedelta(seconds=48):
            return '{}s'.format(delta_obj.seconds)
        elif delta_obj < timedelta(minutes=48):
            minutes = float(delta_obj.seconds) / timedelta(minutes=1).seconds
            return '{:.0f}m'.format(minutes)
        elif delta_obj < timedelta(hours=22):
            hours = float(delta_obj.seconds) / timedelta(hours=1).seconds
            return '{:.1f}h'.format(hours)
        else:
            return '{}d'.format(delta_obj.days)

    @staticmethod
    def file_change(change):
        filename, plus, minus = change
        template = '+{plus} -{minus} {filename}'
        return template.format(plus=plus, minus=minus, filename=filename)

    @staticmethod
    def commit_summary(sha1, title, when, author, total_plus, total_minus,
                       changes_by_file):
        template = ("{sha1} {title}\n"
                    "{when} by {author}\n"
                    "Total line changes: +{plus} -{minus}\n"
                      "{changes_by_file}\n")
        changes = '\n'.join(map(T.file_change, changes_by_file))
        return template.format(sha1=sha1[:7],
                               title=title,
                               when=T.nice_time(when),
                               author=author,
                               plus=total_plus,
                               minus=total_minus,
                               changes_by_file=T.indent(changes))


def get_changes(diff):
    total_adds = 0
    total_deletes = 0
    changes_by_file = []
    for patch in diff:
        total_adds += patch.additions
        total_deletes += patch.deletions
        change = (patch.new_file_path, patch.additions, patch.deletions)
        changes_by_file.append(change)
    changes_by_file = sorted(changes_by_file, key=lambda x: -sum(x[1:]))
    return total_adds, total_deletes, changes_by_file


def summarize(repo, commit, previous=None):
    commit_time = datetime.fromtimestamp(commit.commit_time)
    if previous is not None:
        prev_commit_time = datetime.fromtimestamp(previous.commit_time)
        time_since_last_commit = commit_time - prev_commit_time
        diff = previous.tree.diff_to_tree(commit.tree)
    else:
        time_since_last_commit = None
        empty_tree_oid = repo.TreeBuilder().write()
        empty_tree = repo.get(empty_tree_oid)
        diff = empty_tree.diff_to_tree(commit.tree)

    changes = get_changes(diff)
    total_plus, total_minus, changes_by_file = changes

    summary = T.commit_summary(
        sha1=commit.hex,
        title=commit.message.splitlines()[0],
        when=commit_time,
        author=commit.author.email,
        total_plus=total_plus,
        total_minus=total_minus,
        changes_by_file=changes_by_file,
    )
    return T.bullet(summary), time_since_last_commit


def get_estimate(suggestion):
    prompt = 'Estimate hours spent [{}]: '.format(T.nice_timedelta(suggestion))
    while True:
        raw_estimate = input(prompt)
        if raw_estimate == '':
            estimate = suggestion
            break
        try:
            estimated_hours = float(raw_estimate)
            estimate = timedelta(hours=estimated_hours)
            break
        except ValueError:
            print('Parse error: enter an estimated number of hours')
    return estimate



def estimate(repo):
    estimated_total = timedelta(seconds=0)
    chronological = GIT_SORT_TIME | GIT_SORT_REVERSE
    for commit in repo.walk(repo.head.target, chronological):
        previous_commit = None if commit.parents == [] else commit.parents[0]
        summary, suggestion = summarize(repo, commit, previous=previous_commit)

        print(summary, end='\n\n')

        estimated_total += get_estimate(suggestion)
        print('Estimated total: {}'.format(estimated_total), end='\n\n')
    return estimated_total


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Estimate programming time.')
    parser.add_argument('url', help='repository clone URL or local path')
    args = parser.parse_args()
    with TempRepo(args.url) as repo:
        estimated_total = estimate(repo)
    print(estimated_total)
