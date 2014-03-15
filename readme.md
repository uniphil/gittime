Git Time
========

Estimate time spent programming with git metadata. Gittime shows you metadata.
You make guesses.

UI cues taken from [acoomans](https://github.com/acoomans)'s similarly named
[gittime](https://github.com/acoomans/gittime).


Install
-------

Requires [pygit2](https://github.com/libgit2/pygit2). On linux, if you like
virtualenv, save yourself a headache with [venvgit2](https://github.com/uniphil/venvgit2).

No current plans to throw this on pypi or anything, it's mostly a one-off (which
may become a several-off) for myself to come up with some hours on some projects.


Usage
-----

```bash
$ ./gittime.py --help
usage: gittime.py [-h] [-a email] url [start] [end]

Estimate programming time with prompts of git metadata.

positional arguments:
  url                   repository clone URL or local path
  start                 revision to start from, like HEAD~10 or d7c7c04
  end                   stop at this revision, like HEAD~2 or 8dfa01d

optional arguments:
  -h, --help            show this help message and exit
  -a email, --author email
                        only suggest commits authored by this email address
```


### Example

```bash
$ ./gittime.py ~/code/commitblog HEAD~3 HEAD~2 --author uniphil@gmail.com
cloning /home/phil/code/commitblog...


Running total: 0:00:00

* 9312708 Add a 404 page (fix #22)
  Friday, Mar 14 at 00:52:35 by uniphil@gmail.com
  Total line changes: +44 -1
    +25 -0 templates/not-found.html
    +12 -1 static/css/main.css
    +7 -0 commitblog.py

Estimate hours spent [29m]: 

Running total: 0:29:08

* 4bf2fd4 rename blog-commit to blog-post
  Friday, Mar 14 at 00:53:08 by uniphil@gmail.com
  Total line changes: +26 -26
    +0 -25 templates/blog-commit.html
    +25 -0 templates/blog-post.html
    +1 -1 commitblog.py

Estimate hours spent [33s]: .5


Total estimated time: 0:59:08
```

gittime will set the default time estimate to the timedelta since the last
commit. It's not smart. You're smart. Think while using this.
