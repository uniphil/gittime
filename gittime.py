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
        if delta_obj < timedelta(seconds=48):
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
    def commit_summary(running_total, sha1, title, when, author,
                       total_plus, total_minus, changes_by_file):
        prepender = "\nRunning total: {total}\n\n".format(total=running_total)
        template = ("{sha1} {title}\n"
                    "{when} by {author}\n"
                    "Total line changes: +{plus} -{minus}\n"
                      "{changes_by_file}\n")
        changes = '\n'.join(map(T.file_change, changes_by_file))
        details = template.format(sha1=sha1[:7],
                                  title=title,
                                  when=T.nice_time(when),
                                  author=author,
                                  plus=total_plus,
                                  minus=total_minus,
                                  changes_by_file=T.indent(changes))
        return prepender + T.bullet(details)

    @staticmethod
    def prompt(suggestion):
        template = 'Estimate hours spent{default}: '
        if suggestion is not None:
            nice_time = T.nice_timedelta(suggestion)
            default = ' [{suggestion}]'.format(suggestion=nice_time)
        else:
            default = ''
        return template.format(default=default)

    @staticmethod
    def cant_guess_initial():
        template = ('Input required: Since this is the initial commit, all '
                    'bets are off for how long it took. Make a guess.')
        return T.bullet(template.format())

    @staticmethod
    def input_error(bad_value):
        template = ('Input error: "{}" doesn\'t look like a number and I\'m '
                    'just a computer :(')
        return T.bullet(template.format(bad_value))


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


def summarize(total, repo, commit, previous):
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
        running_total=total,
        sha1=commit.hex,
        title=commit.message.splitlines()[0],
        when=commit_time,
        author=commit.author.email,
        total_plus=total_plus,
        total_minus=total_minus,
        changes_by_file=changes_by_file,
    )
    return summary, time_since_last_commit


def get_estimate(suggestion):
    while True:
        raw_estimate = input(T.prompt(suggestion))
        if raw_estimate == '' and suggestion is not None:
            estimate = suggestion
            break
        if raw_estimate == '' and suggestion is None:
            print(T.cant_guess_initial())
            continue
        try:
            estimated_hours = float(raw_estimate)
        except ValueError as e:
            print(T.input_error(raw_estimate))
        else:
            estimate = timedelta(hours=estimated_hours)
            break
    return estimate


def user_range_walker(repo, start, end, author_email):
    start_marker = None
    fast_forwarding = None
    if start is not None:
        start_oid_marker = repo.revparse_single(start).oid
        fast_forwarding = True
    if end is not None:
        end_oid = repo.revparse_single(end).oid
    else:
        end_oid = repo.head.target
    chronological = GIT_SORT_TIME | GIT_SORT_REVERSE
    for commit in repo.walk(end_oid, chronological):
        if fast_forwarding:
            if commit.oid == start_oid_marker:
                fast_forwarding = False
            else:
                continue
        if author_email is not None and commit.author.email != author_email:
            continue
        yield commit


def estimate(repo, start=None, end=None, author_email=None):
    total = timedelta(seconds=0)

    for commit in user_range_walker(repo, start, end, author_email):
        previous_commit = None if commit.parents == [] else commit.parents[0]
        summary, suggestion = summarize(total, repo, commit, previous_commit)
        print(summary, end='\n\n')
        total += get_estimate(suggestion)

    return total


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        description='Estimate programming time with prompts of git metadata.')
    parser.add_argument('url', help='repository clone URL or local path')
    parser.add_argument('start', nargs='?', help='revision to start from, like HEAD~10 or d7c7c04')
    parser.add_argument('end', nargs='?', help='stop at this revision, like HEAD~2 or 8dfa01d')
    parser.add_argument('-u', '--user', metavar='email', help='only suggest commits authored by this email address')
    args = parser.parse_args()
    with TempRepo(args.url) as repo:
        estimated_total = estimate(repo, args.start, args.end, args.user)
    print(estimated_total)
