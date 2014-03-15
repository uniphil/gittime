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
    :licence: MPL, see LICENSE for more details.
"""

from __future__ import print_function

import shutil
from tempfile import mkdtemp
from datetime import datetime, timedelta

from pygit2 import clone_repository


class TempRepo(object):
    """Make a bare repository in a directory for safe isolated inspection."""

    def __init__(self, url):
        self.url = url

    def __enter__(self):
        self.path = mkdtemp()
        try:
            repo = clone_repository(self.url, self.path, bare=True)
            print('cloning {} to {}...'.format(self.url, self.path))
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
                       by_file, time_since):
        template = ("{sha1} {title}\n"
                    "{when} by {author}\n"
                    "Total line changes: +{plus} -{minus}\n"
                      "{changes_by_file}\n"
                    "Time since previous commit: {time_since}")
        changes = '\n'.join(map(T.file_change, by_file))
        return template.format(sha1=sha1[:7],
                               title=title,
                               when=T.nice_time(when),
                               author=author,
                               plus=total_plus,
                               minus=total_minus,
                               changes_by_file=T.indent(changes),
                               time_since=T.nice_timedelta(time_since))



def summarize(commit):
    when = datetime.now()
    since = timedelta(minutes=18)
    changes = [
        ('some_file.txt', 2, 20),
        ('file1.jpg', 5, 0),
    ]
    summary = T.commit_summary('asdf', 'Hello', when, 'uniphil@gmail.com',
                                21, 2, changes, since)
    return T.bullet(summary)


def estimate(repo):
    print()
    print(summarize('asdf'))
    print()



if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Estimate programming time.')
    parser.add_argument('url', help='repository clone URL or local path')
    args = parser.parse_args()
    with TempRepo(args.url) as repo:
        time_info = estimate(repo)
    print(time_info)